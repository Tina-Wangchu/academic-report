# timestamp_manager.py - Implementation Detail

## 模块概述

**模块名称**: 定时报告时间戳管理（timestamp_manager.py）— 定时/增量模式支撑
**版本**: 1.0.0
**完成日期**: 2026-07-13
**状态**: ✅ 已完成（单元测试 15 项全通过）

---

## 功能说明

持久化每个「主题」的**上次报告时间戳**到 `~/.hermes/academic_scholar_timestamps.json`
（`{topic_key: last_run_iso}`），供 `pipeline` 增量分支计算 `[上次, 现在]` 检索窗口。

**主要能力**:
- 🔑 确定性 `topic_key`：`(query, research_field)` → 可读前缀 + md5 短 hash（防碰撞）。
- 📖 `get_last_run(key)`：取上次报告时间；缺失/非法 → `None`。
- ✏️ `update_last_run(key, when=None)`：原子写（tmp + `os.replace`，自动建缺失目录）。
- 🛡️ 防御加载：缺失/损坏 JSON / 非 dict → `{}`（绝不抛异常）。
- 🏭 单例 `get_timestamp_manager()`（对齐 `get_config_manager` / `get_rate_limiter`）。

---

## 架构设计

```
TimestampManager(file_path=get_timestamp_file_path())
 ├── topic_key(query, field) -> str            # 静态：safe_filename 前缀 + md5[:10]
 ├── _load() -> Dict[str, str]                 # 防御性 JSON 读
 ├── get_last_run(key) -> Optional[datetime]   # fromisoformat，非法→None
 └── update_last_run(key, when=None) -> datetime  # 原子写

get_timestamp_manager() -> TimestampManager    # 全局单例
main()                                          # CLI: 查看 / --reset <key|all>
```

**复用**：`utils.get_timestamp_file_path()`（既定存储路径）、`utils.safe_filename()`。

---

## 关键设计决策

| 决策 | 理由 |
|------|------|
| ISO-8601 字符串持久化 | 可排序、与 `to_dict()` 风格一致；`fromisoformat` 无损回环 |
| 可读前缀 + 短 hash 的 key | 便于人工排查；hash 防碰撞与特殊字符问题 |
| tmp + `os.replace` 原子写 | 同盘原子、Windows 亦然；防中途崩溃产生撕裂文件 |
| 损坏文件按空处理 | 最坏情况：各主题从基线重跑；绝不因文件问题阻塞主流程 |
| 单例 | 与项目其它 manager 一致；pipeline 反复调用零开销 |

---

## 测试（`test/test_timestamp_manager.py`，15 项）

| 类 | 覆盖点 |
|----|--------|
| `TestTopicKey` | 确定性、不同 field/query 不同 key、含 hash 段 |
| `TestLoad` | 缺失文件→{}、损坏 JSON→{}、非 dict→{}、非法 ISO→None |
| `TestRoundTrip` | update→get、默认 now、覆盖写、多主题独立 |
| `TestAtomicWrite` | 无 `.tmp` 残留、保留既有键、建缺失目录 |

不联网，用 `tmp_path` 注入文件路径。

---

## 已知限制

1. **单进程假设**：同主题多进程会 JSON 读-改-写竞争（原子写防撕裂，不防 lost-update）。多进程需加文件锁（`fcntl`/`msvcrt.locking`，按平台分）。
2. **时区**：`datetime.now()` 本地 naive；持久化 ISO 由 `fromisoformat` 回环，保持 naive-local 一致。
3. **损坏即重置**：损坏文件→空，等于各主题从基线重跑（丢失历史）。可选：写前 `utils.create_backup` 备份损坏文件。

---

**最后更新**: 2026-07-13
