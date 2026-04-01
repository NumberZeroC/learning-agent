#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
技术指标分析 - 寻找即将启动拉升的股票

注意：请使用 Python 3.11+ 运行（需要 venv311 虚拟环境）
用法：/home/admin/.openclaw/workspace/stock-notification/venv311/bin/python3 technical_analysis.py

功能：
1. 筛选全市股票（A 股）
2. 分析日线级别技术指标（MACD、KDJ、RSI、成交量等）
3. 识别特征：
   - 日线稳定运行（均线多头排列）
   - 逐渐放量（成交量温和放大）
   - 拉升试盘（小幅上涨 + 量能配合）
   - 即将启动（MACD 金叉 + 突破关键位置）
4. 推荐 10 支股票
5. 支持定时执行（开盘时间每 30 分钟）
6. QQ 消息推送

用法：
    python technical_analysis.py
"""

import os
import sys
import json
import yaml
import math
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    import akshare as ak
    import pandas as pd
    import numpy as np
    AKSHARE_AVAILABLE = True
except ImportError as e:
    print(f"[依赖] ⚠️ 缺少依赖：{e}")
    print("请安装：pip install akshare pandas numpy")
    AKSHARE_AVAILABLE = False

try:
    from talib import MACD, RSI, KDJ
    TALIB_AVAILABLE = True
    print("[TA-Lib] ✅ 已加载")
except ImportError:
    TALIB_AVAILABLE = False
    print("[TA-Lib] ⚠️ 未安装，使用自定义计算")


class TechnicalAnalyzer:
    """技术指标分析器"""
    
    def __init__(self, config_path: str = 'config.yaml'):
        self.config = self._load_config(config_path)
        self.data_dir = Path('/home/admin/.openclaw/workspace/data/stock-notification/technical')
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 缓存目录
        self.cache_dir = self.data_dir / 'cache'
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        print("=" * 70)
        print("📊 技术指标分析器 - 寻找即将启动的股票")
        print("=" * 70)
    
    def _load_config(self, config_path: str) -> dict:
        """加载配置文件"""
        try:
            config_file = Path(config_path)
            if not config_file.exists():
                config_file = Path(__file__).parent / config_file
            
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
        except:
            pass
        return {}
    
    def get_all_stocks(self) -> List[Dict]:
        """获取全 A 股股票列表"""
        print("\n📋 获取全 A 股列表...")
        
        try:
            # 使用 AKShare 获取 A 股列表
            df = ak.stock_all_a_spot_em()
            
            stocks = []
            for _, row in df.iterrows():
                code = row.get('代码', '')
                if not code:
                    continue
                
                # 过滤 ST 股票
                name = row.get('名称', '')
                if 'ST' in name or '*' in name:
                    continue
                
                # 过滤科创板（可选）
                # if code.startswith('688'):
                #     continue
                
                stocks.append({
                    'code': code,
                    'name': name,
                    'price': float(row.get('最新价', 0)),
                    'change_pct': float(row.get('涨跌幅', 0)),
                    'volume': float(row.get('成交量', 0)),
                    'amount': float(row.get('成交额', 0)),
                    'market_cap': float(row.get('总市值', 0)) if '总市值' in row else 0
                })
            
            print(f"   ✅ 获取 {len(stocks)} 只股票（已过滤 ST）")
            return stocks
            
        except Exception as e:
            print(f"   ❌ 获取失败：{e}")
            return []
    
    def get_daily_history(self, code: str, days: int = 60) -> Optional[pd.DataFrame]:
        """获取日线历史数据"""
        try:
            # AKShare 历史行情
            symbol = code.lower()
            df = ak.stock_zh_a_hist(symbol=symbol, period="daily", 
                                    start_date=(datetime.now() - timedelta(days=days*2)).strftime('%Y%m%d'),
                                    end_date=datetime.now().strftime('%Y%m%d'))
            
            if df.empty or len(df) < 20:
                return None
            
            # 重命名列
            df.columns = df.columns.str.lower()
            
            # 确保必要的列
            required_cols = ['日期', '开盘', '收盘', '最高', '最低', '成交量', '成交额', '涨跌幅']
            for col in required_cols:
                if col not in df.columns:
                    return None
            
            # 转换日期
            df['日期'] = pd.to_datetime(df['日期'])
            df = df.sort_values('日期').tail(days)
            df = df.reset_index(drop=True)
            
            return df
            
        except Exception as e:
            return None
    
    def calculate_macd(self, df: pd.DataFrame) -> Dict:
        """计算 MACD 指标"""
        try:
            close = df['收盘'].values
            
            if TALIB_AVAILABLE:
                macd, signal, hist = MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
            else:
                # 自定义 MACD 计算
                exp1 = pd.Series(close).ewm(span=12, adjust=False).mean()
                exp2 = pd.Series(close).ewm(span=26, adjust=False).mean()
                macd = exp1 - exp2
                signal = macd.ewm(span=9, adjust=False).mean()
                hist = macd - signal
                macd = macd.values
                signal = signal.values
                hist = hist.values
            
            if len(macd) < 2:
                return {}
            
            # 判断金叉/死叉
            current_macd = macd[-1]
            current_signal = signal[-1]
            prev_macd = macd[-2]
            prev_signal = signal[-2]
            
            # 金叉：MACD 从下向上穿过信号线
            golden_cross = (prev_macd <= prev_signal) and (current_macd > current_signal)
            # 死叉：MACD 从上向下穿过信号线
            death_cross = (prev_macd >= prev_signal) and (current_macd < current_signal)
            
            # MACD 在零轴上方
            above_zero = current_macd > 0
            
            # MACD 柱状线放大
            hist_increasing = hist[-1] > hist[-2] if len(hist) > 1 else False
            
            return {
                'macd': float(current_macd),
                'signal': float(current_signal),
                'hist': float(hist[-1]),
                'golden_cross': golden_cross,
                'death_cross': death_cross,
                'above_zero': above_zero,
                'hist_increasing': hist_increasing
            }
            
        except Exception as e:
            return {}
    
    def calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> float:
        """计算 RSI 指标"""
        try:
            close = df['收盘'].values
            
            if TALIB_AVAILABLE:
                rsi = RSI(close, timeperiod=period)
            else:
                # 自定义 RSI 计算
                delta = pd.Series(close).diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
            
            return float(rsi[-1]) if len(rsi) > 0 else 50
            
        except Exception:
            return 50
    
    def calculate_volume_trend(self, df: pd.DataFrame) -> Dict:
        """分析成交量趋势"""
        try:
            volume = df['成交量'].values
            
            if len(volume) < 10:
                return {}
            
            # 最近 5 日平均成交量
            recent_avg = np.mean(volume[-5:])
            # 前 5 日平均成交量
            prev_avg = np.mean(volume[-10:-5])
            
            # 成交量放大比例
            volume_ratio = recent_avg / prev_avg if prev_avg > 0 else 1
            
            # 量比（今日成交量 / 过去 5 日平均）
            today_volume = volume[-1]
            volume_rate = today_volume / recent_avg if recent_avg > 0 else 1
            
            # 逐渐放量（最近 5 日成交量递增）
            gradual_increase = all(volume[-i] >= volume[-i-1] * 0.9 for i in range(1, 5))
            
            return {
                'recent_avg': float(recent_avg),
                'prev_avg': float(prev_avg),
                'volume_ratio': float(volume_ratio),
                'volume_rate': float(volume_rate),
                'gradual_increase': gradual_increase,
                'today_volume': float(today_volume)
            }
            
        except Exception:
            return {}
    
    def check_ma_pattern(self, df: pd.DataFrame) -> Dict:
        """检查均线排列"""
        try:
            close = df['收盘'].values
            
            # 计算均线
            ma5 = pd.Series(close).rolling(5).mean().iloc[-1]
            ma10 = pd.Series(close).rolling(10).mean().iloc[-1]
            ma20 = pd.Series(close).rolling(20).mean().iloc[-1]
            ma30 = pd.Series(close).rolling(30).mean().iloc[-1]
            ma60 = pd.Series(close).rolling(60).mean().iloc[-1]
            
            current_price = close[-1]
            
            # 多头排列：5>10>20>30>60
            bull_pattern = (ma5 > ma10 > ma20 > ma30 > ma60)
            
            # 价格在均线上方
            above_ma5 = current_price > ma5
            above_ma20 = current_price > ma20
            above_ma60 = current_price > ma60
            
            # 均线向上
            ma5_up = ma5 > pd.Series(close).rolling(5).mean().iloc[-2]
            ma20_up = ma20 > pd.Series(close).rolling(20).mean().iloc[-2]
            
            return {
                'ma5': float(ma5),
                'ma10': float(ma10),
                'ma20': float(ma20),
                'ma30': float(ma30),
                'ma60': float(ma60),
                'bull_pattern': bull_pattern,
                'above_ma5': above_ma5,
                'above_ma20': above_ma20,
                'above_ma60': above_ma60,
                'ma5_up': ma5_up,
                'ma20_up': ma20_up
            }
            
        except Exception:
            return {}
    
    def check_breakout(self, df: pd.DataFrame) -> Dict:
        """检查突破形态"""
        try:
            high = df['最高'].values
            close = df['收盘'].values
            
            # 20 日新高
            high_20 = max(high[-20:])
            # 60 日新高
            high_60 = max(high[-60:]) if len(high) >= 60 else high_20
            
            current_price = close[-1]
            
            # 突破 20 日高点
            breakout_20 = current_price >= high_20 * 0.98  # 接近或突破
            
            # 突破 60 日高点
            breakout_60 = current_price >= high_60 * 0.98
            
            # 近期涨幅（5 日）
            change_5d = (close[-1] / close[-5] - 1) * 100 if len(close) >= 5 else 0
            
            # 近期涨幅（10 日）
            change_10d = (close[-1] / close[-10] - 1) * 100 if len(close) >= 10 else 0
            
            return {
                'high_20': float(high_20),
                'high_60': float(high_60),
                'breakout_20': breakout_20,
                'breakout_60': breakout_60,
                'change_5d': float(change_5d),
                'change_10d': float(change_10d)
            }
            
        except Exception:
            return {}
    
    def analyze_stock(self, code: str, name: str) -> Optional[Dict]:
        """分析单只股票"""
        try:
            # 获取历史数据
            df = self.get_daily_history(code, days=60)
            if df is None or len(df) < 30:
                return None
            
            # 计算各项指标
            macd_info = self.calculate_macd(df)
            rsi = self.calculate_rsi(df)
            volume_info = self.calculate_volume_trend(df)
            ma_info = check_ma_pattern(df)
            breakout_info = check_breakout(df)
            
            if not macd_info or not volume_info or not ma_info:
                return None
            
            # 综合评分
            score = 0
            signals = []
            
            # 1. MACD 金叉（20 分）
            if macd_info.get('golden_cross'):
                score += 20
                signals.append('MACD 金叉')
            
            # MACD 在零轴上方（10 分）
            if macd_info.get('above_zero'):
                score += 10
            
            # MACD 柱状线放大（5 分）
            if macd_info.get('hist_increasing'):
                score += 5
            
            # 2. 成交量（25 分）
            if volume_info.get('gradual_increase'):
                score += 15
                signals.append('逐渐放量')
            
            if volume_info.get('volume_ratio', 0) > 1.5:
                score += 10
                signals.append('成交量放大')
            
            # 3. 均线形态（25 分）
            if ma_info.get('bull_pattern'):
                score += 15
                signals.append('均线多头')
            
            if ma_info.get('above_ma20') and ma_info.get('above_ma60'):
                score += 10
            
            # 4. 突破形态（20 分）
            if breakout_info.get('breakout_20'):
                score += 10
                signals.append('突破 20 日高点')
            
            if breakout_info.get('breakout_60'):
                score += 10
                signals.append('突破 60 日高点')
            
            # 5. RSI 适中（10 分）
            if 40 <= rsi <= 70:
                score += 10
            
            # 6. 近期涨幅适中（10 分）- 避免已大幅拉升的
            change_5d = breakout_info.get('change_5d', 0)
            if 0 < change_5d < 15:  # 5 日涨幅在 0-15% 之间
                score += 10
                signals.append('稳步上涨')
            
            # 获取当前价格信息
            current_price = df['收盘'].iloc[-1]
            change_pct = df['涨跌幅'].iloc[-1] if '涨跌幅' in df.columns else 0
            
            return {
                'code': code,
                'name': name,
                'price': float(current_price),
                'change_pct': float(change_pct),
                'score': score,
                'signals': signals,
                'macd': macd_info,
                'rsi': rsi,
                'volume': volume_info,
                'ma': ma_info,
                'breakout': breakout_info,
                'analysis_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            return None
    
    def scan_market(self, limit: int = 10, min_score: int = 60) -> List[Dict]:
        """扫描全市场，筛选符合条件的股票"""
        print("\n🔍 开始扫描全市场...")
        
        # 获取股票列表
        stocks = self.get_all_stocks()
        if not stocks:
            return []
        
        # 初步筛选：
        # 1. 价格 > 2 元（避免垃圾股）
        # 2. 市值 < 500 亿（避免大盘股）
        # 3. 今日涨幅 -3% ~ 7%（避免已涨停或大跌）
        filtered = [
            s for s in stocks
            if s['price'] > 2
            and (s['market_cap'] == 0 or s['market_cap'] < 500e8)
            and -3 <= s['change_pct'] <= 7
        ]
        
        print(f"   初步筛选：{len(filtered)} 只股票")
        
        # 分析股票
        results = []
        for i, stock in enumerate(filtered):
            if i % 100 == 0:
                print(f"   分析进度：{i}/{len(filtered)}")
            
            result = self.analyze_stock(stock['code'], stock['name'])
            if result and result['score'] >= min_score:
                results.append(result)
        
        # 按评分排序
        results.sort(key=lambda x: x['score'], reverse=True)
        
        print(f"\n   ✅ 筛选出 {len(results)} 只符合条件的股票")
        
        # 返回前 N 只
        return results[:limit]
    
    def generate_report(self, stocks: List[Dict]) -> str:
        """生成分析报告"""
        print("\n📝 生成分析报告...")
        
        today = datetime.now().strftime('%Y-%m-%d')
        report_file = self.data_dir / f'technical_pick_{today}.md'
        
        report = f"""# 📊 技术指标选股报告

**日期：** {today}  
**生成时间：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**筛选条件：** 日线稳定 + 逐渐放量 + 突破形态 + MACD 金叉

---

## 🏆 推荐股票 TOP10

| 排名 | 股票 | 代码 | 价格 | 涨幅 | 得分 | 信号 |
|------|------|------|------|------|------|------|
"""
        
        for i, stock in enumerate(stocks, 1):
            signals = '、'.join(stock['signals'][:3])
            report += f"| {i} | **{stock['name']}** | {stock['code']} | {stock['price']:.2f} | {stock['change_pct']:+.1f}% | {stock['score']} | {signals} |\n"
        
        report += f"""
---

## 📈 详细分析

"""
        
        for i, stock in enumerate(stocks, 1):
            report += f"### {i}. {stock['name']} ({stock['code']})\n\n"
            report += f"- **当前价格**: ¥{stock['price']:.2f} ({stock['change_pct']:+.1f}%)\n"
            report += f"- **综合得分**: {stock['score']} 分\n"
            report += f"- **技术信号**: {'、'.join(stock['signals'])}\n"
            
            # MACD
            macd = stock.get('macd', {})
            report += f"- **MACD**: {'金叉' if macd.get('golden_cross') else '死叉' if macd.get('death_cross') else '延续'} "
            report += f"(零轴{'上' if macd.get('above_zero') else '下'})\n"
            
            # RSI
            report += f"- **RSI**: {stock.get('rsi', 50):.1f}\n"
            
            # 成交量
            vol = stock.get('volume', {})
            report += f"- **成交量**: {'逐渐放量' if vol.get('gradual_increase') else '正常'} "
            report += f"(量比 {vol.get('volume_rate', 1):.2f})\n"
            
            # 均线
            ma = stock.get('ma', {})
            report += f"- **均线**: {'多头排列' if ma.get('bull_pattern') else '震荡'}\n"
            
            # 突破
            bo = stock.get('breakout', {})
            if bo.get('breakout_20'):
                report += f"- **突破**: 20 日高点 (5 日涨幅 {bo.get('change_5d', 0):.1f}%)\n"
            
            report += "\n"
        
        report += f"""
---

## ⚠️ 风险提示

1. 技术分析仅供参考，不构成投资建议
2. 请结合基本面、消息面综合判断
3. 注意设置止损位，控制风险
4. 市场有风险，投资需谨慎

---

*报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        # 保存报告
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        # 保存 JSON 数据
        json_file = self.data_dir / f'technical_pick_{today}.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump({'stocks': stocks, 'generated_at': datetime.now().isoformat()}, f, ensure_ascii=False, indent=2)
        
        print(f"   报告已保存：{report_file}")
        
        return str(report_file)
    
    def format_qq_message(self, stocks: List[Dict]) -> str:
        """格式化 QQ 消息"""
        today = datetime.now().strftime('%m-%d %H:%M')
        
        message = f"📊 **技术选股推送** ({today})\n\n"
        message += "🔍 筛选条件：日线稳定 + 逐渐放量 + MACD 金叉 + 突破形态\n\n"
        message += "🏆 **推荐 TOP10**\n\n"
        
        for i, stock in enumerate(stocks, 1):
            signals = '、'.join(stock['signals'][:2])
            message += f"{i}. **{stock['name']}** ({stock['code']})\n"
            message += f"   价格：¥{stock['price']:.2f} ({stock['change_pct']:+.1f}%) | 得分：{stock['score']}分\n"
            message += f"   信号：{signals}\n\n"
        
        message += "⚠️ 风险提示：技术分析仅供参考，请结合基本面判断，注意设置止损！"
        
        return message
    
    def run_analysis(self, limit: int = 10, min_score: int = 60) -> Dict:
        """执行完整分析"""
        print(f"\n{'='*70}")
        print(f"📊 技术指标分析 - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"{'='*70}\n")
        
        try:
            # 扫描市场
            stocks = self.scan_market(limit=limit, min_score=min_score)
            
            if not stocks:
                print("\n⚠️ 未找到符合条件的股票")
                return {'success': False, 'stocks': []}
            
            # 生成报告
            report_file = self.generate_report(stocks)
            
            # 生成 QQ 消息
            qq_message = self.format_qq_message(stocks)
            
            print(f"\n{'='*70}")
            print("✅ 技术分析完成")
            print(f"{'='*70}")
            print(f"📄 报告：{report_file}")
            print(f"📱 推荐 {len(stocks)} 只股票")
            
            return {
                'success': True,
                'stocks': stocks,
                'report_file': report_file,
                'qq_message': qq_message
            }
            
        except Exception as e:
            print(f"\n❌ 分析失败：{e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}


# 兼容导入
def check_ma_pattern(df):
    """独立函数版本"""
    try:
        close = df['收盘'].values
        ma5 = pd.Series(close).rolling(5).mean().iloc[-1]
        ma10 = pd.Series(close).rolling(10).mean().iloc[-1]
        ma20 = pd.Series(close).rolling(20).mean().iloc[-1]
        ma30 = pd.Series(close).rolling(30).mean().iloc[-1]
        ma60 = pd.Series(close).rolling(60).mean().iloc[-1]
        current_price = close[-1]
        bull_pattern = (ma5 > ma10 > ma20 > ma30 > ma60)
        return {
            'ma5': float(ma5), 'ma10': float(ma10), 'ma20': float(ma20),
            'ma30': float(ma30), 'ma60': float(ma60),
            'bull_pattern': bull_pattern,
            'above_ma5': current_price > ma5,
            'above_ma20': current_price > ma20,
            'above_ma60': current_price > ma60
        }
    except:
        return {}

def check_breakout(df):
    """独立函数版本"""
    try:
        high = df['最高'].values
        close = df['收盘'].values
        high_20 = max(high[-20:])
        high_60 = max(high[-60:]) if len(high) >= 60 else high_20
        current_price = close[-1]
        breakout_20 = current_price >= high_20 * 0.98
        breakout_60 = current_price >= high_60 * 0.98
        change_5d = (close[-1] / close[-5] - 1) * 100 if len(close) >= 5 else 0
        change_10d = (close[-1] / close[-10] - 1) * 100 if len(close) >= 10 else 0
        return {
            'high_20': float(high_20), 'high_60': float(high_60),
            'breakout_20': breakout_20, 'breakout_60': breakout_60,
            'change_5d': float(change_5d), 'change_10d': float(change_10d)
        }
    except:
        return {}


def main():
    parser = argparse.ArgumentParser(description='📊 技术指标分析')
    parser.add_argument('--limit', '-l', type=int, default=10, help='推荐股票数量')
    parser.add_argument('--min-score', '-s', type=int, default=60, help='最低分数')
    parser.add_argument('--config', '-c', default='config.yaml', help='配置文件')
    parser.add_argument('--qq', action='store_true', help='发送 QQ 消息')
    
    args = parser.parse_args()
    
    analyzer = TechnicalAnalyzer(config_path=args.config)
    result = analyzer.run_analysis(limit=args.limit, min_score=args.min_score)
    
    if result.get('success') and result.get('qq_message'):
        print(f"\n📱 QQ 消息预览:\n{result['qq_message']}")
    
    sys.exit(0 if result.get('success') else 1)


if __name__ == '__main__':
    import argparse
    main()
