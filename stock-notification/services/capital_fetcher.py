#!/usr/bin/env python3
"""
资金流数据获取服务
功能：获取板块资金流、个股资金流、融资融券等数据
存储：data/capital/YYYY-MM-DD.json
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.capital_flow import CapitalFlowAnalyzer


class CapitalFlowFetcher:
    """资金流数据获取器"""
    
    def __init__(self, config_path: str = 'config.yaml'):
        self.config = self._load_config(config_path)
        self.data_dir = Path('/home/admin/.openclaw/workspace/data/stock-notification') / 'capital'
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化分析器
        akshare_config = self.config.get('akshare', {})
        self.analyzer = CapitalFlowAnalyzer(
            cache_dir=akshare_config.get('cache_dir'),
            cache_ttl=akshare_config.get('cache_ttl', 300)
        )
    
    def _load_config(self, config_path: str) -> dict:
        """加载配置文件"""
        import yaml
        config_file = Path(config_path)
        if not config_file.exists():
            config_file = Path(__file__).parent.parent / config_file
        
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return {}
    
    def fetch_sector_flow(self, trade_date: str = None) -> list:
        """获取板块资金流数据 - 按板块涨幅排序"""
        if not trade_date:
            trade_date = datetime.now().strftime('%Y%m%d')
        
        print(f"\n💰 获取板块资金流 ({trade_date})...")
        
        sector_flows = []
        
        # 配置的板块列表
        sectors = self.config.get('sectors', [
            '半导体', '人工智能', '新能源', '医药生物',
            '消费电子', '汽车', '金融', '消费',
            '化工', '机械', '军工', '通信'
        ])
        
        # 获取全市场资金流
        market_flow = self.analyzer.get_market_moneyflow(trade_date=trade_date)
        
        for sector in sectors:
            try:
                stocks = self.analyzer._get_sector_with_market_flow(sector, market_flow)
                
                if stocks:
                    total_inflow = sum(s.get('main_force_in', 0) for s in stocks if s.get('main_force_in', 0) > 0)
                    total_outflow = abs(sum(s.get('main_force_in', 0) for s in stocks if s.get('main_force_in', 0) < 0))
                    net_flow = total_inflow - total_outflow
                    inst_net = sum(s.get('inst_net', 0) for s in stocks)
                    financing_net = sum(s.get('financing_net', 0) for s in stocks)
                    
                    # 计算板块平均涨幅
                    changes = [s.get('change_pct', 0) for s in stocks if s.get('change_pct') is not None]
                    avg_change = sum(changes) / len(changes) if changes else 0
                    
                    sector_flows.append({
                        'sector': sector,
                        'main_force_in': total_inflow,
                        'main_force_out': total_outflow,
                        'net_flow': net_flow,
                        'inst_net': inst_net,
                        'financing_net': financing_net,
                        'stock_count': len(stocks),
                        'avg_change': avg_change,  # 板块平均涨幅
                        'top_stocks': [s for s in stocks if s.get('top_reason', '')]
                    })
                    
            except Exception as e:
                print(f"   ⚠️ {sector} 获取失败：{e}")
        
        # 🔥 修改：按板块涨幅排序（而不是按资金净流入）
        sector_flows.sort(key=lambda x: x['avg_change'], reverse=True)
        
        # 显示涨幅前五
        print("\n   板块涨幅 TOP5:")
        for i, s in enumerate(sector_flows[:5], 1):
            net_text = f" (净流入 {s['net_flow']/10000:.1f}万)" if s['net_flow'] != 0 else ""
            print(f"   {i}. {s['sector']}: {s['avg_change']:+.2f}%{net_text}")
        
        print(f"\n   ✅ 获取 {len(sector_flows)} 个板块")
        
        return sector_flows
    
    def fetch_market_flow(self, trade_date: str = None) -> list:
        """获取全市场资金流数据"""
        if not trade_date:
            trade_date = datetime.now().strftime('%Y%m%d')
        
        print(f"\n📊 获取全市场资金流 ({trade_date})...")
        
        market_flow = []
        
        if self.analyzer.tushare_pro:
            try:
                market_flow = self.analyzer.get_market_moneyflow(trade_date=trade_date)
                print(f"   ✅ 获取 {len(market_flow)} 只股票")
            except Exception as e:
                print(f"   ⚠️ 获取失败：{e}")
        
        return market_flow
    
    def fetch_all(self, trade_date: str = None) -> dict:
        """获取所有资金流数据"""
        if not trade_date:
            trade_date = datetime.now().strftime('%Y%m%d')
        
        print(f"\n{'='*60}")
        print(f"💰 资金流数据获取 - {trade_date}")
        print(f"{'='*60}")
        
        data = {
            'trade_date': trade_date,
            'fetched_at': datetime.now().isoformat(),
            'sector_flows': self.fetch_sector_flow(trade_date),
            'market_flow': self.fetch_market_flow(trade_date)
        }
        
        # 保存到文件
        self._save_data(trade_date, data)
        
        print(f"\n✅ 资金流数据获取完成")
        print(f"📄 已保存：{self._get_data_file(trade_date)}")
        
        return data
    
    def _get_data_file(self, trade_date: str) -> Path:
        """获取数据文件路径"""
        date_str = trade_date if len(trade_date) == 8 else trade_date.replace('-', '')
        return self.data_dir / f'{date_str}.json'
    
    def _save_data(self, trade_date: str, data: dict):
        """保存数据到文件"""
        data_file = self._get_data_file(trade_date)
        
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load_data(self, trade_date: str = None) -> dict:
        """加载已存储的数据"""
        if not trade_date:
            trade_date = datetime.now().strftime('%Y%m%d')
        
        data_file = self._get_data_file(trade_date)
        
        if data_file.exists():
            with open(data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return {}


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='资金流数据获取服务')
    parser.add_argument('--date', '-d', help='交易日期 (YYYYMMDD)')
    parser.add_argument('--config', '-c', default='config.yaml', help='配置文件')
    
    args = parser.parse_args()
    
    fetcher = CapitalFlowFetcher(config_path=args.config)
    data = fetcher.fetch_all(args.date)
    
    print(f"\n💰 数据摘要:")
    print(f"   板块数量：{len(data.get('sector_flows', []))}")
    print(f"   个股资金流：{len(data.get('market_flow', []))} 只")
    
    if data.get('sector_flows'):
        print(f"\n   资金净流入 TOP3:")
        for i, s in enumerate(data['sector_flows'][:3], 1):
            print(f"   {i}. {s['sector']}: {s['net_flow']/10000:.1f}万")


if __name__ == '__main__':
    main()
