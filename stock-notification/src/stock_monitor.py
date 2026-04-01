#!/usr/bin/env python3
"""
股票监控模块 - 对指定股票清单进行重点监控

功能：
1. 日 K 线技术分析（MA、MACD、KDJ、RSI 等）
2. 分时图监控（实时价格、成交量）
3. 实时新闻监控（个股相关新闻）
4. 市场情绪分析
5. 资金博弈分析（主力、北向、散户）
6. 综合买卖建议

⚠️ 免责声明：仅供学习研究，不构成投资建议
"""
import os
import json
import time
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import numpy as np

try:
    import akshare as ak
    AKSHARE_AVAILABLE = True
except ImportError:
    AKSHARE_AVAILABLE = False

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class CacheManager:
    """轻量级缓存管理器"""
    
    def __init__(self, cache_dir: str = None, ttl_seconds: int = 300):
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            script_dir = Path(__file__).parent
            self.cache_dir = script_dir.parent / 'data' / 'cache' / 'stock_monitor'
        
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl_seconds = ttl_seconds
    
    def _get_key(self, func_name: str, **kwargs) -> str:
        key_str = f"{func_name}:{json.dumps(kwargs, sort_keys=True, default=str)}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, func_name: str, **kwargs) -> Optional[Dict]:
        key = self._get_key(func_name, **kwargs)
        cache_path = self.cache_dir / f"{key}.json"
        
        if not cache_path.exists():
            return None
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if time.time() - data.get('_cached_at', 0) > self.ttl_seconds:
                cache_path.unlink()
                return None
            
            return data.get('value')
        except:
            return None
    
    def set(self, func_name: str, value: Dict, **kwargs):
        key = self._get_key(func_name, **kwargs)
        cache_path = self.cache_dir / f"{key}.json"
        
        try:
            data = {'value': value, '_cached_at': time.time()}
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, default=str)
        except Exception as e:
            print(f"[缓存] 写入失败：{e}")


class StockMonitor:
    """股票监控器 - 对指定股票进行全方位监控"""
    
    def __init__(self, cache_dir: str = None, cache_ttl: int = 300):
        self.cache = CacheManager(cache_dir, cache_ttl)
        
        # 技术指标权重
        self.weights = {
            'ma_trend': 0.15,       # 均线趋势
            'macd': 0.20,           # MACD
            'kdj': 0.15,            # KDJ
            'rsi': 0.15,            # RSI
            'volume': 0.15,         # 成交量
            'capital_flow': 0.20    # 资金流
        }
        
        # 买卖信号阈值
        self.thresholds = {
            'strong_buy': 8.0,      # 强烈买入
            'buy': 6.5,             # 买入
            'hold': 4.5,            # 持有
            'sell': 3.0,            # 卖出
            'strong_sell': 1.5      # 强烈卖出
        }
    
    def get_stock_info(self, stock_code: str, retry: int = 3) -> Optional[Dict]:
        """获取股票基本信息（支持重试和备用数据源）"""
        cache_key = f"stock_info_{stock_code}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached
        
        # 尝试 AKShare
        if AKSHARE_AVAILABLE:
            for attempt in range(retry):
                try:
                    # 使用 AKShare 获取实时行情
                    data = ak.stock_zh_a_spot_em()
                    if data is not None and not data.empty:
                        stock_data = data[data['代码'] == stock_code]
                        if not stock_data.empty:
                            row = stock_data.iloc[0]
                            info = {
                                'code': stock_code,
                                'name': row.get('名称', ''),
                                'price': float(row.get('最新价', 0)),
                                'change_pct': float(row.get('涨跌幅', 0)),
                                'change': float(row.get('涨跌额', 0)),
                                'volume': float(row.get('成交量', 0)),
                                'amount': float(row.get('成交额', 0)),
                                'high': float(row.get('最高', 0)),
                                'low': float(row.get('最低', 0)),
                                'open': float(row.get('今开', 0)),
                                'prev_close': float(row.get('昨收', 0)),
                                'pe': float(row.get('市盈率 - 动态', 0)),
                                'pb': float(row.get('市净率', 0)),
                                'market_cap': float(row.get('总市值', 0)),
                                'update_time': datetime.now().isoformat()
                            }
                            self.cache.set(cache_key, info)
                            return info
                except Exception as e:
                    if attempt < retry - 1:
                        time.sleep(1)
                        continue
                    print(f"[{stock_code}] AKShare 失败：{e}")
        
        # AKShare 失败，尝试新浪财经备用
        if REQUESTS_AVAILABLE:
            for attempt in range(retry):
                try:
                    info = self._get_from_sina(stock_code)
                    if info:
                        self.cache.set(cache_key, info)
                        print(f"[{stock_code}] ✅ 新浪财经获取成功")
                        return info
                except Exception as e:
                    if attempt < retry - 1:
                        time.sleep(1)
                        continue
                    print(f"[{stock_code}] 新浪财经失败：{e}")
        
        return None
    
    def _get_from_sina(self, stock_code: str) -> Optional[Dict]:
        """从新浪财经获取行情（备用数据源）"""
        try:
            # 确定市场
            if stock_code.startswith('6'):
                symbol = f'sh{stock_code}'
            else:
                symbol = f'sz{stock_code}'
            
            url = f'https://hq.sinajs.cn/list={symbol}'
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://finance.sina.com.cn/'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                return None
            
            # 解析：var hq_str_sh600000="名称，开盘，昨收，当前，最高，最低，..."
            text = response.text.strip()
            if '=' not in text:
                return None
            
            data_str = text.split('=')[1].strip().strip('"').strip(';')
            fields = data_str.split(',')
            
            if len(fields) < 32:
                return None
            
            name = fields[0]
            price = float(fields[3]) if fields[3] else 0
            prev_close = float(fields[2]) if fields[2] else price
            change = price - prev_close
            change_pct = (change / prev_close * 100) if prev_close > 0 else 0
            high = float(fields[4]) if fields[4] else 0
            low = float(fields[5]) if fields[5] else 0
            open_price = float(fields[1]) if fields[1] else 0
            volume = float(fields[8]) if fields[8] else 0
            amount = float(fields[9]) if fields[9] else 0
            
            return {
                'code': stock_code,
                'name': name,
                'price': round(price, 2),
                'change_pct': round(change_pct, 2),
                'change': round(change, 2),
                'volume': int(volume),
                'amount': float(amount),
                'high': round(high, 2),
                'low': round(low, 2),
                'open': round(open_price, 2),
                'prev_close': round(prev_close, 2),
                'pe': 0,
                'pb': 0,
                'market_cap': 0,
                'update_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"[{stock_code}] 新浪接口异常：{e}")
            return None
    
    def get_daily_k_data(self, stock_code: str, period: str = 'daily', 
                         start_date: str = None, end_date: str = None) -> Optional[pd.DataFrame]:
        """获取日 K 线数据"""
        if not AKSHARE_AVAILABLE or not PANDAS_AVAILABLE:
            print("[AKShare/Pandas] 未安装，跳过 K 线分析")
            return None
        
        cache_key = f"daily_k_{stock_code}_{period}_{start_date}_{end_date}"
        cached = self.cache.get(cache_key)
        if cached and PANDAS_AVAILABLE:
            return pd.DataFrame(cached)
        
        try:
            # 默认获取最近 60 天数据
            if not end_date:
                end_date = datetime.now().strftime('%Y%m%d')
            if not start_date:
                start_date = (datetime.now() - timedelta(days=60)).strftime('%Y%m%d')
            
            # 获取日 K 数据
            df = ak.stock_zh_a_hist(
                symbol=stock_code,
                period=period,
                start_date=start_date,
                end_date=end_date,
                adjust="qfq"  # 前复权
            )
            
            if df is not None and not df.empty:
                # 缓存为字典格式
                self.cache.set(cache_key, df.to_dict('records'))
                return df
            
        except Exception as e:
            print(f"[{stock_code}] 获取 K 线数据失败：{e}")
        
        return None
    
    def calculate_ma(self, df: pd.DataFrame, periods: List[int] = [5, 10, 20, 60]) -> Dict:
        """计算均线"""
        if df is None or df.empty:
            return {}
        
        result = {}
        close = df['收盘'] if '收盘' in df.columns else df['Close']
        
        for period in periods:
            ma_name = f'MA{period}'
            ma_value = close.rolling(window=period).mean().iloc[-1]
            prev_ma = close.rolling(window=period).mean().iloc[-2] if len(close) > period else ma_value
            
            result[ma_name] = {
                'value': round(ma_value, 2),
                'prev_value': round(prev_ma, 2),
                'trend': 'up' if ma_value > prev_ma else 'down'
            }
        
        # 判断均线排列
        current_price = close.iloc[-1]
        ma_values = [result[f'MA{p}']['value'] for p in periods if f'MA{p}' in result]
        
        if all(current_price > ma for ma in ma_values):
            result['pattern'] = '多头排列'
            result['pattern_score'] = 10
        elif all(current_price < ma for ma in ma_values):
            result['pattern'] = '空头排列'
            result['pattern_score'] = 0
        else:
            result['pattern'] = '震荡'
            result['pattern_score'] = 5
        
        return result
    
    def calculate_macd(self, df: pd.DataFrame) -> Dict:
        """计算 MACD 指标"""
        if df is None or df.empty:
            return {}
        
        try:
            close = df['收盘'] if '收盘' in df.columns else df['Close']
            
            # 计算 EMA
            ema12 = close.ewm(span=12, adjust=False).mean()
            ema26 = close.ewm(span=26, adjust=False).mean()
            
            # DIF
            dif = ema12 - ema26
            
            # DEA
            dea = dif.ewm(span=9, adjust=False).mean()
            
            # MACD 柱
            macd_bar = (dif - dea) * 2
            
            # 当前值
            current_dif = dif.iloc[-1]
            current_dea = dea.iloc[-1]
            current_macd = macd_bar.iloc[-1]
            
            # 前一日值（判断金叉死叉）
            prev_dif = dif.iloc[-2] if len(dif) > 1 else current_dif
            prev_dea = dea.iloc[-2] if len(dea) > 1 else current_dea
            prev_macd = macd_bar.iloc[-2] if len(macd_bar) > 1 else current_macd
            
            # 判断信号
            signal = 'hold'
            if prev_dif <= prev_dea and current_dif > current_dea:
                signal = 'golden_cross'  # 金叉
            elif prev_dif >= prev_dea and current_dif < current_dea:
                signal = 'death_cross'   # 死叉
            
            # 评分
            score = 5.0
            if signal == 'golden_cross':
                score = 8.0
            elif signal == 'death_cross':
                score = 2.0
            elif current_dif > 0 and current_macd > 0:
                score = 6.5
            elif current_dif < 0 and current_macd < 0:
                score = 3.5
            
            return {
                'dif': round(current_dif, 4),
                'dea': round(current_dea, 4),
                'macd': round(current_macd, 4),
                'signal': signal,
                'score': score
            }
            
        except Exception as e:
            print(f"MACD 计算失败：{e}")
            return {}
    
    def calculate_kdj(self, df: pd.DataFrame, n: int = 9) -> Dict:
        """计算 KDJ 指标"""
        if df is None or df.empty:
            return {}
        
        try:
            high = df['最高'] if '最高' in df.columns else df['High']
            low = df['最低'] if '最低' in df.columns else df['Low']
            close = df['收盘'] if '收盘' in df.columns else df['Close']
            
            # 计算 RSV
            lowest_low = low.rolling(window=n).min()
            highest_high = high.rolling(window=n).max()
            
            rsv = (close - lowest_low) / (highest_high - lowest_low) * 100
            rsv = rsv.fillna(50)
            
            # 计算 K、D、J
            k = rsv.ewm(com=2, adjust=False).mean()
            d = k.ewm(com=2, adjust=False).mean()
            j = 3 * k - 2 * d
            
            current_k = k.iloc[-1]
            current_d = d.iloc[-1]
            current_j = j.iloc[-1]
            
            # 判断超买超卖
            if current_k > 80 and current_d > 80:
                signal = 'overbought'
                score = 2.0
            elif current_k < 20 and current_d < 20:
                signal = 'oversold'
                score = 8.0
            elif current_k > current_d:
                signal = 'bullish'
                score = 6.5
            else:
                signal = 'bearish'
                score = 3.5
            
            return {
                'k': round(current_k, 2),
                'd': round(current_d, 2),
                'j': round(current_j, 2),
                'signal': signal,
                'score': score
            }
            
        except Exception as e:
            print(f"KDJ 计算失败：{e}")
            return {}
    
    def calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> Dict:
        """计算 RSI 指标"""
        if df is None or df.empty:
            return {}
        
        try:
            close = df['收盘'] if '收盘' in df.columns else df['Close']
            
            # 计算价格变化
            delta = close.diff()
            
            # 分离涨跌
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            
            # 计算平均涨跌幅
            avg_gain = gain.rolling(window=period).mean()
            avg_loss = loss.rolling(window=period).mean()
            
            # 计算 RS 和 RSI
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            rsi = rsi.fillna(50)
            
            current_rsi = rsi.iloc[-1]
            
            # 判断信号
            if current_rsi > 70:
                signal = 'overbought'
                score = 2.5
            elif current_rsi < 30:
                signal = 'oversold'
                score = 7.5
            elif current_rsi > 50:
                signal = 'bullish'
                score = 6.0
            else:
                signal = 'bearish'
                score = 4.0
            
            return {
                'rsi': round(current_rsi, 2),
                'signal': signal,
                'score': score
            }
            
        except Exception as e:
            print(f"RSI 计算失败：{e}")
            return {}
    
    def analyze_volume(self, df: pd.DataFrame) -> Dict:
        """分析成交量"""
        if df is None or df.empty:
            return {}
        
        try:
            volume = df['成交量'] if '成交量' in df.columns else df['Volume']
            
            # 计算均量线
            ma5_vol = volume.rolling(window=5).mean()
            ma10_vol = volume.rolling(window=10).mean()
            
            current_vol = volume.iloc[-1]
            avg_vol = ma5_vol.iloc[-1]
            
            # 量比
            volume_ratio = current_vol / avg_vol if avg_vol > 0 else 1
            
            # 判断
            if volume_ratio > 2:
                signal = '放量'
                score = 7.0
            elif volume_ratio > 1.5:
                signal = '温和放量'
                score = 6.0
            elif volume_ratio < 0.5:
                signal = '缩量'
                score = 4.0
            else:
                signal = '正常'
                score = 5.0
            
            return {
                'current_volume': int(current_vol),
                'avg_volume': int(avg_vol),
                'volume_ratio': round(volume_ratio, 2),
                'signal': signal,
                'score': score
            }
            
        except Exception as e:
            print(f"成交量分析失败：{e}")
            return {}
    
    def get_capital_flow(self, stock_code: str) -> Dict:
        """获取资金流数据"""
        cache_key = f"capital_flow_{stock_code}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached
        
        result = {
            'main_force_net': 0,
            'north_flow': 0,
            'retail_flow': 0,
            'signal': 'neutral',
            'score': 5.0
        }
        
        try:
            # 获取个股资金流
            if AKSHARE_AVAILABLE:
                flow_data = ak.stock_individual_fund_flow(symbol=stock_code)
                if flow_data is not None and not flow_data.empty:
                    # 解析资金流数据
                    # 注意：AKShare 返回格式可能变化，需要适配
                    pass
            
            # 简化处理：从行情数据推断
            stock_info = self.get_stock_info(stock_code)
            if stock_info:
                change_pct = stock_info.get('change_pct', 0)
                amount = stock_info.get('amount', 0)
                
                # 根据涨跌幅和成交额估算资金流向
                if change_pct > 3 and amount > 1e9:
                    result['main_force_net'] = amount * 0.1  # 估算 10% 为主力
                    result['signal'] = 'inflow'
                    result['score'] = 7.5
                elif change_pct > 0:
                    result['main_force_net'] = amount * 0.05
                    result['signal'] = 'slight_inflow'
                    result['score'] = 6.0
                elif change_pct < -3:
                    result['main_force_net'] = -amount * 0.1
                    result['signal'] = 'outflow'
                    result['score'] = 2.5
                else:
                    result['signal'] = 'neutral'
                    result['score'] = 5.0
            
            self.cache.set(cache_key, result)
            
        except Exception as e:
            print(f"[{stock_code}] 资金流分析失败：{e}")
        
        return result
    
    def get_stock_news(self, stock_code: str, stock_name: str = '') -> List[Dict]:
        """获取个股相关新闻"""
        cache_key = f"stock_news_{stock_code}"
        cached = self.cache.get(cache_key, ttl_seconds=600)  # 新闻缓存 10 分钟
        if cached:
            return cached
        
        news_list = []
        
        try:
            if AKSHARE_AVAILABLE:
                # 获取个股新闻
                news_df = ak.stock_news_em(symbol=stock_code)
                if news_df is not None and not news_df.empty:
                    for _, row in news_df.head(10).iterrows():
                        news_list.append({
                            'title': row.get('新闻标题', ''),
                            'content': row.get('新闻内容', '')[:200],
                            'source': row.get('信息来源', ''),
                            'publish_time': row.get('发布时间', ''),
                            'url': row.get('新闻链接', '')
                        })
            
            # 如果没有新闻，返回空列表
            if not news_list:
                news_list.append({
                    'title': f'{stock_name}暂无最新新闻',
                    'content': '',
                    'source': '系统',
                    'publish_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'url': ''
                })
            
            self.cache.set(cache_key, news_list)
            
        except Exception as e:
            print(f"[{stock_code}] 获取新闻失败：{e}")
            news_list.append({
                'title': '新闻获取失败',
                'content': str(e),
                'source': '系统',
                'publish_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'url': ''
            })
        
        return news_list
    
    def analyze_sentiment(self, news_list: List[Dict]) -> Dict:
        """分析新闻情绪"""
        if not news_list:
            return {'score': 0, 'trend': 'neutral', 'keywords': []}
        
        # 简单关键词匹配
        positive_words = ['利好', '增长', '突破', '创新高', '业绩', '中标', '重组', '增持']
        negative_words = ['利空', '下跌', '亏损', '违规', '减持', '诉讼', '风险', '警告']
        
        positive_count = 0
        negative_count = 0
        keywords = []
        
        for news in news_list:
            title = news.get('title', '') + ' ' + news.get('content', '')
            
            for word in positive_words:
                if word in title:
                    positive_count += 1
                    keywords.append(word)
            
            for word in negative_words:
                if word in title:
                    negative_count += 1
                    keywords.append(word)
        
        total = positive_count + negative_count
        if total == 0:
            score = 0
            trend = 'neutral'
        else:
            score = (positive_count - negative_count) / total * 10
            if score > 2:
                trend = 'bullish'
            elif score < -2:
                trend = 'bearish'
            else:
                trend = 'neutral'
        
        return {
            'score': round(score, 2),
            'trend': trend,
            'positive_count': positive_count,
            'negative_count': negative_count,
            'keywords': list(set(keywords))[:5]
        }
    
    def generate_trading_signal(self, stock_code: str, stock_name: str = '') -> Dict:
        """生成综合买卖信号"""
        print(f"[监控] 分析 {stock_name}({stock_code})...")
        
        # 1. 获取基本信息
        stock_info = self.get_stock_info(stock_code)
        if not stock_info:
            return {
                'code': stock_code,
                'name': stock_name,
                'status': 'error',
                'message': '无法获取股票信息'
            }
        
        # 2. 获取 K 线数据
        k_data = self.get_daily_k_data(stock_code)
        
        # 3. 技术指标分析
        ma_result = self.calculate_ma(k_data) if k_data is not None else {}
        macd_result = self.calculate_macd(k_data) if k_data is not None else {}
        kdj_result = self.calculate_kdj(k_data) if k_data is not None else {}
        rsi_result = self.calculate_rsi(k_data) if k_data is not None else {}
        volume_result = self.analyze_volume(k_data) if k_data is not None else {}
        
        # 4. 资金流分析
        capital_result = self.get_capital_flow(stock_code)
        
        # 5. 新闻和情绪分析
        news_list = self.get_stock_news(stock_code, stock_name)
        sentiment_result = self.analyze_sentiment(news_list)
        
        # 6. 综合评分
        scores = []
        signals = []
        
        # 均线趋势
        if ma_result:
            scores.append(ma_result.get('pattern_score', 5) * self.weights['ma_trend'])
            signals.append(f"均线：{ma_result.get('pattern', 'N/A')}")
        
        # MACD
        if macd_result:
            scores.append(macd_result.get('score', 5) * self.weights['macd'])
            macd_signal = macd_result.get('signal', 'hold')
            if macd_signal == 'golden_cross':
                signals.append("MACD: 金叉✅")
            elif macd_signal == 'death_cross':
                signals.append("MACD: 死叉❌")
            else:
                signals.append(f"MACD: {macd_signal}")
        
        # KDJ
        if kdj_result:
            scores.append(kdj_result.get('score', 5) * self.weights['kdj'])
            signals.append(f"KDJ: {kdj_result.get('signal', 'N/A')}")
        
        # RSI
        if rsi_result:
            scores.append(rsi_result.get('score', 5) * self.weights['rsi'])
            signals.append(f"RSI: {rsi_result.get('rsi', 'N/A')}")
        
        # 成交量
        if volume_result:
            scores.append(volume_result.get('score', 5) * self.weights['volume'])
            signals.append(f"成交量：{volume_result.get('signal', 'N/A')}")
        
        # 资金流
        scores.append(capital_result.get('score', 5) * self.weights['capital_flow'])
        signals.append(f"资金：{capital_result.get('signal', 'N/A')}")
        
        # 计算总分
        total_score = sum(scores)
        
        # 新闻情绪调整
        if sentiment_result['trend'] == 'bullish':
            total_score += 0.5
        elif sentiment_result['trend'] == 'bearish':
            total_score -= 0.5
        
        # 7. 生成买卖建议
        if total_score >= self.thresholds['strong_buy']:
            action = '强烈买入'
            action_code = 'STRONG_BUY'
            confidence = '高'
        elif total_score >= self.thresholds['buy']:
            action = '买入'
            action_code = 'BUY'
            confidence = '中高'
        elif total_score >= self.thresholds['hold']:
            action = '持有'
            action_code = 'HOLD'
            confidence = '中'
        elif total_score >= self.thresholds['sell']:
            action = '卖出'
            action_code = 'SELL'
            confidence = '中高'
        else:
            action = '强烈卖出'
            action_code = 'STRONG_SELL'
            confidence = '高'
        
        # 8. 生成风险提示
        risks = []
        if kdj_result and kdj_result.get('signal') == 'overbought':
            risks.append('KDJ 超买，注意回调')
        if rsi_result and rsi_result.get('signal') == 'overbought':
            risks.append('RSI 超买，警惕反转')
        if capital_result.get('signal') == 'outflow':
            risks.append('主力资金流出')
        if sentiment_result['trend'] == 'bearish':
            risks.append('新闻情绪偏空')
        
        # 9. 目标价位（简单估算）
        current_price = stock_info.get('price', 0)
        if action_code in ['STRONG_BUY', 'BUY']:
            target_price = round(current_price * 1.05, 2)  # 5% 目标
            stop_loss = round(current_price * 0.95, 2)     # 5% 止损
        elif action_code in ['STRONG_SELL', 'SELL']:
            target_price = round(current_price * 0.95, 2)
            stop_loss = round(current_price * 1.05, 2)
        else:
            target_price = round(current_price * 1.02, 2)
            stop_loss = round(current_price * 0.98, 2)
        
        result = {
            'code': stock_code,
            'name': stock_name,
            'status': 'success',
            'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            
            # 基本信息
            'stock_info': stock_info,
            
            # 技术指标
            'technical': {
                'ma': ma_result,
                'macd': macd_result,
                'kdj': kdj_result,
                'rsi': rsi_result,
                'volume': volume_result
            },
            
            # 资金流
            'capital_flow': capital_result,
            
            # 新闻情绪
            'sentiment': {
                'score': sentiment_result['score'],
                'trend': sentiment_result['trend'],
                'keywords': sentiment_result['keywords'],
                'news_count': len(news_list)
            },
            
            # 买卖信号
            'signal': {
                'action': action,
                'action_code': action_code,
                'score': round(total_score, 2),
                'confidence': confidence,
                'signals': signals,
                'risks': risks,
                'target_price': target_price,
                'stop_loss': stop_loss
            },
            
            # 最新新闻
            'news': news_list[:3]
        }
        
        print(f"  → {action} (得分：{total_score:.1f}, 置信度：{confidence})")
        
        return result
    
    def monitor_stocks(self, stock_list: List[Dict]) -> List[Dict]:
        """批量监控股票清单
        
        Args:
            stock_list: 股票列表，格式 [{'code': '000001', 'name': '平安银行'}, ...]
        
        Returns:
            监控结果列表
        """
        print(f"\n{'='*60}")
        print(f"📊 开始监控 {len(stock_list)} 只股票")
        print(f"{'='*60}\n")
        
        results = []
        
        for stock in stock_list:
            code = stock.get('code', '')
            name = stock.get('name', '')
            
            if not code:
                print(f"⚠️ 跳过无效股票：{stock}")
                continue
            
            result = self.generate_trading_signal(code, name)
            results.append(result)
            
            # 避免请求过快
            time.sleep(0.5)
        
        # 统计
        buy_count = sum(1 for r in results if r.get('signal', {}).get('action_code') in ['BUY', 'STRONG_BUY'])
        sell_count = sum(1 for r in results if r.get('signal', {}).get('action_code') in ['SELL', 'STRONG_SELL'])
        hold_count = len(results) - buy_count - sell_count
        
        print(f"\n{'='*60}")
        print(f"✅ 监控完成")
        print(f"{'='*60}")
        print(f"买入信号：{buy_count} 只 | 持有：{hold_count} 只 | 卖出：{sell_count} 只")
        
        return results
    
    def export_report(self, results: List[Dict], output_dir: str = None) -> str:
        """导出监控报告"""
        if not output_dir:
            script_dir = Path(__file__).parent
            output_dir = script_dir.parent / 'data' / 'reports' / 'monitor'
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = output_dir / f'stock_monitor_{timestamp}.md'
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(f"# 股票监控报告\n\n")
            f.write(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"{'='*60}\n\n")
            
            for result in results:
                if result.get('status') != 'success':
                    continue
                
                stock = result.get('stock_info', {})
                signal = result.get('signal', {})
                
                f.write(f"## {result.get('name', '')}({result.get('code', '')})\n\n")
                f.write(f"**当前价格**: {stock.get('price', 'N/A')} ")
                f.write(f"({stock.get('change_pct', 0):+.2f}%)\n\n")
                
                f.write(f"**操作建议**: {signal.get('action', 'N/A')} ")
                f.write(f"(置信度：{signal.get('confidence', 'N/A')})\n\n")
                
                f.write(f"**目标价**: {signal.get('target_price', 'N/A')} | ")
                f.write(f"**止损价**: {signal.get('stop_loss', 'N/A')}\n\n")
                
                f.write(f"**综合得分**: {signal.get('score', 'N/A')}/10\n\n")
                
                f.write(f"**技术信号**:\n")
                for s in signal.get('signals', []):
                    f.write(f"- {s}\n")
                f.write("\n")
                
                if signal.get('risks'):
                    f.write(f"**风险提示**:\n")
                    for r in signal.get('risks', []):
                        f.write(f"- ⚠️ {r}\n")
                    f.write("\n")
                
                f.write(f"{'-'*40}\n\n")
        
        print(f"📄 报告已保存：{report_path}")
        return str(report_path)


if __name__ == '__main__':
    # 测试
    monitor = StockMonitor()
    
    # 测试股票清单
    test_stocks = [
        {'code': '000001', 'name': '平安银行'},
        {'code': '600519', 'name': '贵州茅台'},
        {'code': '300750', 'name': '宁德时代'}
    ]
    
    results = monitor.monitor_stocks(test_stocks)
    
    # 导出报告
    report_path = monitor.export_report(results)
    print(f"\n报告路径：{report_path}")
