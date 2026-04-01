#!/usr/bin/env python3
"""
市场数据获取服务
功能：获取大盘指数、个股行情、龙虎榜等市场数据
存储：data/market/YYYY-MM-DD.json
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tushare_pro_source import TushareProSource
from src.enhanced_data_source import EnhancedDataSource
from src.reliable_data_source import ReliableDataSource


class MarketDataFetcher:
    """市场数据获取器"""
    
    def __init__(self, config_path: str = 'config.yaml'):
        self.config = self._load_config(config_path)
        # 使用公共数据目录
        self.data_dir = Path('/home/admin/.openclaw/workspace/data/stock-notification/market')
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化数据源
        self._init_data_sources()
    
    def _load_config(self, config_path: str) -> dict:
        """加载配置文件"""
        import yaml
        config_file = Path(config_path)
        if not config_file.exists():
            config_file = Path(__file__).parent.parent / config_path
        
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return {}
    
    def _init_data_sources(self):
        """初始化数据源"""
        akshare_config = self.config.get('akshare', {})
        cache_dir = akshare_config.get('cache_dir')
        
        # Tushare Pro
        self.tushare_pro = None
        try:
            token = self.config.get('tushare', {}).get('token')
            if token:
                self.tushare_pro = TushareProSource(
                    token=token,
                    cache_dir=cache_dir,
                    cache_ttl=600
                )
                print("[Tushare Pro] ✅ 已连接")
        except Exception as e:
            print(f"[Tushare Pro] ⚠️ 未连接：{e}")
        
        # 可靠数据源
        self.reliable_data = None
        try:
            self.reliable_data = ReliableDataSource(
                cache_dir=cache_dir,
                cache_ttl=300,
                tushare_token=self.config.get('tushare', {}).get('token')
            )
            print("[可靠数据源] ✅ 已初始化")
        except Exception as e:
            print(f"[可靠数据源] ⚠️ 初始化失败：{e}")
    
    def fetch_index_data(self) -> dict:
        """获取大盘指数数据"""
        print("\n📊 获取大盘指数...")
        
        indices_data = {}
        
        if self.reliable_data:
            try:
                indices_data = self.reliable_data.get_index_data()
                print(f"   ✅ 成功获取 {len(indices_data)} 个指数")
            except Exception as e:
                print(f"   ⚠️ 获取失败：{e}")
        
        return indices_data
    
    def fetch_top_list(self, trade_date: str = None) -> list:
        """获取龙虎榜数据"""
        if not trade_date:
            trade_date = datetime.now().strftime('%Y%m%d')
        
        print(f"\n📋 获取龙虎榜 ({trade_date})...")
        
        top_list = []
        
        if self.tushare_pro:
            try:
                top_list = self.tushare_pro.get_top_list(trade_date=trade_date)
                print(f"   ✅ 获取 {len(top_list)} 只股票")
            except Exception as e:
                print(f"   ⚠️ 获取失败：{e}")
        
        return top_list
    
    def fetch_top_inst(self, trade_date: str = None) -> list:
        """获取机构交易数据"""
        if not trade_date:
            trade_date = datetime.now().strftime('%Y%m%d')
        
        print(f"\n🏢 获取机构交易 ({trade_date})...")
        
        top_inst = []
        
        if self.tushare_pro:
            try:
                top_inst = self.tushare_pro.get_top_inst(trade_date=trade_date)
                print(f"   ✅ 获取 {len(top_inst)} 条记录")
            except Exception as e:
                print(f"   ⚠️ 获取失败：{e}")
        
        return top_inst
    
    def fetch_all(self, trade_date: str = None) -> dict:
        """获取所有市场数据"""
        if not trade_date:
            trade_date = datetime.now().strftime('%Y%m%d')
        
        print(f"\n{'='*60}")
        print(f"📊 市场数据获取 - {trade_date}")
        print(f"{'='*60}")
        
        data = {
            'trade_date': trade_date,
            'fetched_at': datetime.now().isoformat(),
            'indices': self.fetch_index_data(),
            'top_list': self.fetch_top_list(trade_date),
            'top_inst': self.fetch_top_inst(trade_date)
        }
        
        # 保存到文件
        self._save_data(trade_date, data)
        
        print(f"\n✅ 市场数据获取完成")
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
    
    parser = argparse.ArgumentParser(description='市场数据获取服务')
    parser.add_argument('--date', '-d', help='交易日期 (YYYYMMDD)')
    parser.add_argument('--config', '-c', default='config.yaml', help='配置文件')
    
    args = parser.parse_args()
    
    fetcher = MarketDataFetcher(config_path=args.config)
    data = fetcher.fetch_all(args.date)
    
    print(f"\n📊 数据摘要:")
    print(f"   指数数量：{len(data.get('indices', {}))}")
    print(f"   龙虎榜：{len(data.get('top_list', []))} 只")
    print(f"   机构交易：{len(data.get('top_inst', []))} 条")


if __name__ == '__main__':
    main()
