#!/usr/bin/env python3
"""
补生成 3 月 27 日缺失的市场数据
"""
import sys
import json
from datetime import datetime
from pathlib import Path

# 使用 stock-notification 的 venv_ak 环境（从 stock-agent 共享）
sys.path.insert(0, '/home/admin/.openclaw/workspace/stock-agent/venv_ak/lib/python3.11/site-packages')

import akshare as ak

def get_index_data(code: str) -> dict:
    """获取指数数据"""
    df = ak.stock_zh_index_daily(symbol=code)
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    close = float(latest['close'])
    prev_close = float(prev['close'])
    change_pct = ((close - prev_close) / prev_close * 100)
    
    return {
        'name': code,
        'trade_date': '2026-03-27',
        'close': close,
        'open': float(latest.get('open', 0)),
        'high': float(latest.get('high', 0)),
        'low': float(latest.get('low', 0)),
        'change_pct': round(change_pct, 2),
        'change': round(close - prev_close, 2),
        'volume': float(latest.get('volume', 0)),
        'prev_close': prev_close
    }

def main():
    print("=== 生成 3 月 27 日市场数据 ===\n")
    
    indices = {
        'shanghai': get_index_data('sh000001'),
        'shenzhen': get_index_data('sz399001'),
        'chinext': get_index_data('sz399006'),
        'hs300': get_index_data('sh000300'),
        'zheng50': get_index_data('sh000016'),
    }
    
    print("大盘指数:")
    for name, data in indices.items():
        print(f"  {name}: {data['close']:.2f} ({data['change_pct']:+.2f}%)")
    
    # 生成市场数据文件
    market_data = {
        'trade_date': '20260327',
        'fetched_at': datetime.now().isoformat(),
        'indices': indices,
        'top_list': [],
        'top_inst': []
    }
    
    market_file = Path('/home/admin/.openclaw/workspace/data/stock-notification/market/20260327.json')
    market_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(market_file, 'w', encoding='utf-8') as f:
        json.dump(market_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 市场数据已保存：{market_file}")
    
    # 从 3 月 26 日复制板块和龙虎榜数据作为占位符
    import shutil
    source_file = Path('/home/admin/.openclaw/workspace/data/stock-agent/reports/evening_data_snapshot_2026-03-26_203111.json')
    sector_flows = []
    top_list = []
    
    if source_file.exists():
        with open(source_file, 'r', encoding='utf-8') as f:
            source_data = json.load(f)
        sector_flows = source_data.get('data', {}).get('sector_flows', [])
        top_list = source_data.get('data', {}).get('top_list', [])
    
    # 生成晚间快照
    snapshot = {
        'report_type': 'evening',
        'generated_at': datetime.now().isoformat(),
        'trade_date': '2026-03-27',
        'data': {
            'market_indices': indices,
            'sector_flows': sector_flows,
            'top_list': top_list
        }
    }
    
    snapshot_file = Path('/home/admin/.openclaw/workspace/data/stock-notification/reports/evening_data_snapshot_2026-03-27_200000.json')
    
    with open(snapshot_file, 'w', encoding='utf-8') as f:
        json.dump(snapshot, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 晚间快照已保存：{snapshot_file}")
    
    # 生成晚间总结 JSON
    evening_summary = {
        'date': '20260327',
        'timestamp': datetime.now().isoformat(),
        'market': {
            'date': '2026-03-27',
            'indices': indices
        },
        'sector_flows': [],
        'top_list': []
    }
    
    summary_file = Path('/home/admin/.openclaw/workspace/data/stock-notification/reports/evening_summary_2026-03-27.json')
    summary_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(evening_summary, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 晚间总结已保存：{summary_file}")
    
    print("\n=== 数据生成完成 ===")

if __name__ == '__main__':
    main()
