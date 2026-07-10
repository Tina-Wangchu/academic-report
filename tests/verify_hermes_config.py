#!/usr/bin/env python3
"""
Hermes Agent Markdown配置最终验证
"""

import os
import yaml
from pathlib import Path

def check_hermes_config():
    """检查Hermes配置是否都设置为Markdown"""

    hermes_skill = Path(r"C:\Users\lanpi\AppData\Local\hermes\skills\academic\paper-email-service")

    print("=" * 60)
    print("Hermes Agent 配置验证")
    print("检查是否所有配置都已设置为Markdown")
    print("=" * 60)
    print()

    # [1/5] 检查配置文件
    print("[1/5] 检查配置文件...")
    print("-" * 40)

    try:
        with open(hermes_skill / 'config' / 'default_config.yaml', 'r', encoding='utf-8') as f:
            default_config = yaml.safe_load(f)
        format_default = default_config.get('report_defaults', {}).get('format', 'NOT_FOUND')
        print(f"✓ default_config.yaml - report_defaults.format: {format_default}")

        with open(hermes_skill / 'config' / 'user_config.yaml', 'r', encoding='utf-8') as f:
            user_config = yaml.safe_load(f)
        format_user = user_config.get('custom_defaults', {}).get('report_format', 'NOT_FOUND')
        print(f"✓ user_config.yaml - custom_defaults.report_format: {format_user}")

        if format_default == 'markdown' and format_user == 'markdown':
            print("✅ 配置文件检查通过")
        else:
            print("❌ 配置文件仍有问题")
    except Exception as e:
        print(f"❌ 配置文件检查失败: {e}")

    print()

    # [2/5] 检查核心脚本
    print("[2/5] 检查核心脚本...")
    print("-" * 40)

    scripts = {
        'workflow_executor.py': hermes_skill / 'scripts' / 'workflow_executor.py',
        'config_manager.py': hermes_skill / 'scripts' / 'config_manager.py',
        'paper_email_service.py': hermes_skill / 'scripts' / 'paper_email_service.py',
        'validators.py': hermes_skill / 'scripts' / 'utils' / 'validators.py',
        'formatters.py': hermes_skill / 'scripts' / 'utils' / 'formatters.py'
    }

    all_good = True
    for name, path in scripts.items():
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()

            has_markdown = "'markdown'" in content or '"markdown"' in content
            has_pdf = "'pdf'" in content or '"pdf"' in content

            if has_markdown and not has_pdf:
                print(f"✓ {name}: OK (markdown配置)")
            elif has_pdf:
                print(f"⚠ {name}: 仍有pdf引用")
                all_good = False
            else:
                print(f"? {name}: 配置不确定")
        else:
            print(f"❌ {name}: 文件不存在")
            all_good = False

    if all_good:
        print("✅ 核心脚本检查通过")
    else:
        print("❌ 核心脚本仍有问题")

    print()

    # [3/5] 检查报告生成器
    print("[3/5] 检查报告生成器...")
    print("-" * 40)

    report_gen = Path(r"C:\Users\lanpi\AppData\Local\hermes\skills\academic\report-generator\scripts\generate_report.py")
    if report_gen.exists():
        with open(report_gen, 'r', encoding='utf-8') as f:
            content = f.read()

        has_truncate = 'def truncate' in content
        has_markdown_output = 'Markdown report generated' in content

        if not has_truncate and has_markdown_output:
            print("✓ 报告生成器: OK (无截取，Markdown输出)")
        elif has_truncate:
            print("⚠ 报告生成器: 仍有截取函数")
        else:
            print("✓ 报告生成器: 基本正常")
    else:
        print("❌ 报告生成器: 文件不存在")

    print()

    # [4/5] 检查文件扩展名配置
    print("[4/5] 检查文件扩展名配置...")
    print("-" * 40)

    workflow_file = hermes_skill / 'scripts' / 'workflow_executor.py'
    with open(workflow_file, 'r', encoding='utf-8') as f:
        workflow_content = f.read()

    has_md_extension = "'.md\"" in workflow_content or '".md' in workflow_content
    has_markdown_comment = 'Markdown format' in workflow_content
    has_pdf_extension = "'.pdf\"" in workflow_content or '".pdf' in workflow_content

    if has_md_extension and has_markdown_comment and not has_pdf_extension:
        print("✓ workflow_executor.py: 正确使用.md扩展名")
        print("✅ 文件扩展名配置检查通过")
    elif has_pdf_extension:
        print("❌ workflow_executor.py: 仍在使用.pdf扩展名")
    else:
        print("? workflow_executor.py: 配置不确定")

    print()

    # [5/5] 总结
    print("[5/5] 验证总结...")
    print("-" * 40)

    if all_good and format_default == 'markdown' and format_user == 'markdown':
        print("✅ 所有配置检查通过！")
        print()
        print("现在可以在Hermes Agent中测试：")
        print()
        print("📢 请对Hermes说：")
        print('   "请为我搜索统计学领域这一周的最新研究成果，把报告发送到我的邮箱"')
        print()
        print("预期结果：")
        print("  ✓ 生成Markdown格式报告（.md文件）")
        print("  ✓ 摘要完整显示，无截取")
        print("  ✓ 发送到您的邮箱")
        print()
    else:
        print("❌ 还有配置问题需要解决")
        print("请重新检查配置文件")

if __name__ == "__main__":
    check_hermes_config()
