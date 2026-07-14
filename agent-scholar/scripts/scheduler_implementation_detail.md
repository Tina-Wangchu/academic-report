# scheduler.py - Implementation Detail

## 模块概述

**模块名称**: 定时增量报告调度器（scheduler.py）— 定时报告模式入口
**版本**: 1.0.0
**完成日期**: 2026-07-13
**状态**: ✅ 已完成（单元测试 15 项：增量分支 + 调度循环）

---

## 功能说明

**进程内定时**调度器（不依赖 Hermes）：解析「每周一/每个月/每天」等周期短语，
**立即首次触发**（建立增量基线），之后按周期调用 `pipeline.run_pipeline(incremental=True)`，
每次仅检索 `[上次报告时间, 现在]` 的增量论文并发报告。

**主要能力**:
- 🕐 周期解析：`IntentParser._extract_schedule` → token → `utils.schedule_interval` → `timedelta`。
- 🔁 主循环：首次立即触发 → 按 interval 周期触发；分段 sleep（≤5s）以便 SIGINT 及时响应。
- 🧪 `--once`：触发一次即退出（测试）；`--dry-run`：只打印周期/下次触发，不运行。
- 🛑 SIGINT 优雅退出（不强杀正在跑的 pipeline）。
- ⏰ 可选 cron：`pip install croniter` 后用 `--cron "0 9 * * 1"`（5 字段）；未安装则降级到周期短语。
- 📧 收件人默认 `get_config_manager().get_email_recipient()`。

---

## 架构设计

```
scheduler.run(user_input, recipient, once, dry_run, ...)
 ├── IntentParser().parse(input) → 取 schedule token；无定时短语→默认 weekly
 ├── interval = schedule_interval(token)         # utils 共享映射
 ├── dry_run? → 打印周期/下次触发，return 0
 ├── next_fire = now                             # 首次立即触发
 └── while _RUNNING:
       ├─ sleep 到 next_fire（分段，可被 SIGINT 中断）
       ├─ run_pipeline(input, incremental=True, ...)   # 增量：[last_run, now]
       └─ once? → return 0 ；否则 next_fire = now + interval（或 cron 下次）
```

**复用**：`pipeline.run_pipeline(incremental=True)`、`utils.schedule_interval`、
`intent_parser.IntentParser`、`config_manager.get_email_recipient`。

---

## 单次搜索 vs 定时增量

| 维度 | 单次搜索 | 定时增量 |
|---|---|---|
| 触发 | `pipeline.py` 一次性 | `scheduler.py` 循环 / `--incremental` |
| 时间窗口 | 用户指定（近1年/3年…） | `[上次报告, 现在]`；首次=周期长度 |
| 论文范围 | 窗口内全部 | 仅上次报告后的新论文（客户端按年兜底） |
| 状态 | 无 | `~/.hermes/academic_scholar_timestamps.json` |
| 时间戳更新 | 从不 | 仅邮件发送成功后（pipeline 内） |
| 入口 | `pipeline.py main()` | `scheduler.py main()` |

---

## 关键设计决策

| 决策 | 理由 |
|------|------|
| 进程内 `while/sleep` 循环（非 cron 守护） | 用户选定；命令行立即可用、可测试，不依赖 Hermes |
| 首次立即触发 | 无时间戳时建立基线，下次起才有「增量」可言 |
| 分段 sleep（≤5s） | 让 SIGINT 能在 ~5s 内响应，而非阻塞到下个周期 |
| croniter 导入守卫 | 不硬加依赖；有则支持 `--cron`，无则降级周期短语 |
| 失败不更新时间戳 | `run_pipeline` 内部保证：邮件失败/异常→不写时间戳，下期重覆盖同样窗口 |

---

## 测试（`test/test_scheduler.py`，15 项）

**增量分支**（Fake PaperSearcher/PaperFilter/ReportGenerator/EmailSender + FakeTimestampManager）：
- 显式 `--incremental` 跑通 + 客户端年份过滤
- 首次回退到周期窗口
- 时间戳：`--no-email` 更新 / 邮件成功更新 / **邮件失败不更新**
- 空增量：跳过邮件且不更新
- `--no-incremental` 不走增量

**调度循环**（monkeypatch `scheduler.run_pipeline` + 收件人）：
- `--once` 触发恰好一次；`--dry-run` 不调 pipeline
- 非定时输入默认 weekly 仍可跑
- 无收件人 → return 1
- `_RUNNING=False` 循环退出

---

## 已知限制

1. **周期对齐**：首版 `now+interval`，「每周一」会逐次漂移；未来可加 weekday 对齐（或用 `--cron`）。
2. **长任务 > 周期**：`run_pipeline` 同步；若单次耗时超过 interval，下一轮立即触发（可接受）。
3. **单进程**：同主题多进程会时间戳竞争（见 timestamp_manager 限制）。
4. **S2 年粒度**：增量过滤只能按年兜底（详见 pipeline 增量分支注释）。

---

**最后更新**: 2026-07-13
