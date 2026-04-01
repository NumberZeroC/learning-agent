#!/usr/bin/env python3
"""
测试板块涨幅排序修改

验证点：
1. evening_analysis.py 按 avg_change 排序
2. capital_fetcher.py 按 avg_change 排序
3. 报告输出显示"板块涨幅 TOP5"
"""

import sys
import re
from pathlib import Path

def check_file(filepath, expected_patterns, description):
    """检查文件是否包含预期模式"""
    print(f"\n{'='*60}")
    print(f"检查：{description}")
    print(f"文件：{filepath}")
    print(f"{'='*60}")
    
    if not Path(filepath).exists():
        print(f"❌ 文件不存在")
        return False
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    all_passed = True
    for pattern_desc, pattern in expected_patterns:
        if re.search(pattern, content, re.MULTILINE):
            print(f"✅ {pattern_desc}")
        else:
            print(f"❌ {pattern_desc}")
            all_passed = False
    
    return all_passed

def main():
    print("="*60)
    print("板块涨幅排序修改验证")
    print("="*60)
    
    all_passed = True
    
    # 检查 evening_analysis.py
    all_passed &= check_file(
        '/home/admin/.openclaw/workspace/stock-notification/evening_analysis.py',
        [
            ("按 avg_change 排序", r"sort\(key=lambda x: x\['avg_change'\]"),
            ("板块涨幅 TOP5 输出", r"板块涨幅 TOP5"),
            ("计算 avg_change", r"avg_change = sum\(changes\) / len\(changes\)"),
        ],
        "晚间分析 - 排序逻辑"
    )
    
    # 检查 capital_fetcher.py
    all_passed &= check_file(
        '/home/admin/.openclaw/workspace/stock-notification/services/capital_fetcher.py',
        [
            ("按 avg_change 排序", r"sort\(key=lambda x: x\['avg_change'\]"),
            ("板块涨幅 TOP5 输出", r"板块涨幅 TOP5"),
            ("计算 avg_change", r"avg_change = sum\(changes\) / len\(changes\)"),
        ],
        "资金流服务 - 排序逻辑"
    )
    
    # 检查 morning_recommend.py
    all_passed &= check_file(
        '/home/admin/.openclaw/workspace/stock-notification/morning_recommend.py',
        [
            ("按涨幅排序", r"avg_change.*\*.*10"),
            ("涨幅得分", r"change_score = avg_change"),
        ],
        "早盘推荐 - 热点板块选择"
    )
    
    # 检查 stock_service.py
    all_passed &= check_file(
        '/home/admin/.openclaw/workspace/stock-notification-web/services/stock_service.py',
        [
            ("默认按 change_pct 排序", r"sort_by='change_pct'"),
            ("从 sector_flows 获取", r"sector_flows = data\.get\('sector_flows'"),
        ],
        "Web 服务 - 板块排名"
    )
    
    # 检查 web_data_service.py
    all_passed &= check_file(
        '/home/admin/.openclaw/workspace/stock-notification-web/services/web_data_service.py',
        [
            ("默认按 change_pct 排序", r"sort_by: str = 'change_pct'"),
            ("按 avg_change 排序", r"key=lambda x: x\.get\('avg_change', 0\)"),
        ],
        "Web 数据服务 - 板块资金流"
    )
    
    print(f"\n{'='*60}")
    if all_passed:
        print("✅ 所有检查通过！板块涨幅排序修改完成")
    else:
        print("❌ 部分检查未通过，请检查修改")
    print(f"{'='*60}")
    
    return 0 if all_passed else 1

if __name__ == '__main__':
    sys.exit(main())
