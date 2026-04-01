"""
新闻监控模块 - 抓取和分析财经新闻
支持多数据源、自动重试、故障转移
"""
import requests
import re
import time
import random
from datetime import datetime
from typing import List, Dict, Optional
from bs4 import BeautifulSoup


class NewsMonitor:
    """财经新闻监控器"""
    
    def __init__(self, keywords: Dict[str, List[str]]):
        self.positive_keywords = keywords.get('positive', [])
        self.negative_keywords = keywords.get('negative', [])
        
        # 请求头
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
        }
        
        # 扩展新闻源 - 多个备选源
        # 注：东方财富已移除 (2026-03-16 连接不稳定)
        self.news_sources = [
            # 主流财经门户（优先级 1）
            {
                'name': '同花顺财经',
                'url': 'http://news.10jqka.com.cn/',
                'encoding': 'gbk',
                'selector': '.list-content ul li a',
                'priority': 1
            },
            {
                'name': '金融界',
                'url': 'https://www.jrj.com.cn/',
                'encoding': 'utf-8',
                'selector': '.news-list a',
                'priority': 1
            },
            # 官方媒体（优先级 2）
            {
                'name': '证券时报',
                'url': 'http://www.stcn.com/article/list/',
                'encoding': 'utf-8',
                'selector': '.list-content a, .article-list a',
                'priority': 2
            },
            {
                'name': '上海证券报',
                'url': 'https://www.cnstock.com/',
                'encoding': 'utf-8',
                'selector': '.news-list a, .article a',
                'priority': 2
            },
            # 其他备选（优先级 3）
            {
                'name': '和讯财经',
                'url': 'http://stock.hexun.com/',
                'encoding': 'utf-8',
                'selector': '.main-content a',
                'priority': 3
            }
        ]
    
    def fetch_news(self, source: Dict, retries: int = 3) -> List[Dict]:
        """从指定源抓取新闻（带重试机制）"""
        url = source['url']
        encoding = source['encoding']
        name = source['name']
        
        for attempt in range(retries):
            try:
                # 随机延迟，避免被封
                if attempt > 0:
                    delay = random.uniform(1, 3) * attempt
                    time.sleep(delay)
                
                response = requests.get(
                    url, 
                    headers=self.headers, 
                    timeout=15, 
                    verify=False,
                    allow_redirects=True
                )
                response.encoding = encoding
                response.raise_for_status()
                
                news_list = []
                soup = BeautifulSoup(response.text, 'lxml')
                
                # 尝试多种选择器
                selectors = [
                    source.get('selector', 'a'),
                    'li a', 'ul a', '.news-list a', '.list a', 
                    '[class*="news"] a', '[class*="list"] a',
                    'article a', '.title a', '[class*="item"] a'
                ]
                
                seen_titles = set()
                for selector in selectors:
                    try:
                        for link in soup.select(selector)[:30]:
                            title = link.get_text(strip=True)
                            href = link.get('href', '')
                            
                            # 过滤无效链接和重复标题
                            if len(title) > 8 and len(title) < 100 and href and title not in seen_titles:
                                if href.startswith('http') or href.startswith('/'):
                                    news_list.append({
                                        'title': title,
                                        'url': href if href.startswith('http') else url.split('/')[2] + href,
                                        'source': name,
                                        'time': datetime.now().isoformat()
                                    })
                                    seen_titles.add(title)
                            
                            if len(news_list) >= 20:
                                break
                    except Exception:
                        continue
                    
                    if len(news_list) >= 20:
                        break
                
                if news_list:
                    return news_list
                    
            except requests.exceptions.Timeout:
                print(f"[新闻抓取] {name} 超时 (尝试 {attempt + 1}/{retries})")
            except requests.exceptions.ConnectionError:
                print(f"[新闻抓取] {name} 连接失败 (尝试 {attempt + 1}/{retries})")
            except requests.exceptions.RequestException as e:
                print(f"[新闻抓取] {name} 请求失败：{e}")
            except Exception as e:
                print(f"[新闻抓取] {name} 解析失败：{e}")
        
        return []
    
    def fetch_news_from_api(self, api_name: str) -> List[Dict]:
        """从 API 获取新闻（备选方案）"""
        try:
            if api_name == 'thousend':
                # 同花顺 API
                url = 'http://search.10jqka.com.cn/gateway/urp/v7/landing/getDataList'
                params = {
                    'query': '股票',
                    'condition': '[{"type":"type","value":"news"}]',
                    'perpage': 20,
                    'page': 1,
                    'source': 'ths_mobile'
                }
                response = requests.get(url, params=params, headers=self.headers, timeout=10)
                data = response.json()
                
                news_list = []
                if data.get('data') and data['data'].get('data'):
                    for item in data['data']['data']:
                        news_list.append({
                            'title': item.get('title', ''),
                            'url': item.get('url', ''),
                            'source': '同花顺 API',
                            'time': item.get('time', datetime.now().isoformat())
                        })
                return news_list
                
        except Exception as e:
            print(f"[API 新闻] {api_name} 获取失败：{e}")
        
        return []
    
    def analyze_sentiment(self, text: str) -> Dict:
        """分析文本情感（关键词匹配 + 权重）"""
        text_lower = text.lower()
        
        # 强权重关键词
        strong_positive = ['涨停', '暴涨', '重大利好', '突破新高', '业绩暴增']
        strong_negative = ['跌停', '暴跌', '重大利空', '业绩亏损', '被立案']
        
        positive_count = sum(1 for kw in self.positive_keywords if kw in text_lower)
        negative_count = sum(1 for kw in self.negative_keywords if kw in text_lower)
        strong_pos = sum(2 for kw in strong_positive if kw in text_lower)
        strong_neg = sum(2 for kw in strong_negative if kw in text_lower)
        
        total_positive = positive_count + strong_pos
        total_negative = negative_count + strong_neg
        
        if total_positive > total_negative:
            sentiment = 'positive'
            score = total_positive - total_negative
        elif total_negative > total_positive:
            sentiment = 'negative'
            score = total_negative - total_positive
        else:
            sentiment = 'neutral'
            score = 0
        
        return {
            'sentiment': sentiment,
            'score': score,
            'positive_hits': total_positive,
            'negative_hits': total_negative
        }
    
    def extract_sectors(self, news_list: List[Dict]) -> Dict[str, List[Dict]]:
        """从新闻中提取板块信息"""
        sector_news = {}
        
        # 扩展板块关键词
        sector_keywords = {
            '半导体': ['半导体', '芯片', '集成电路', '中芯', '华虹', '晶圆', '光刻'],
            '人工智能': ['AI', '人工智能', '大模型', '算力', 'GPT', '深度学习', '神经网络'],
            '新能源': ['新能源', '光伏', '风电', '锂电', '储能', '宁德时代', '比亚迪', '氢能'],
            '医药生物': ['医药', '生物', '疫苗', '创新药', '医疗', 'CXO', '集采'],
            '消费电子': ['消费电子', '苹果', '华为', '手机', 'VR', 'AR', '元宇宙'],
            '券商': ['券商', '证券', '投行', '经纪', '中信证券', '东方财富'],
            '银行': ['银行', '信贷', '利率', '央行', '降准', '加息'],
            '房地产': ['房地产', '楼市', '房产', '万科', '保利', '恒大', '碧桂园'],
            '汽车': ['汽车', '新能源車', '特斯拉', '蔚来', '小鹏', '理想'],
            '白酒': ['白酒', '茅台', '五粮液', '泸州老窖', '汾酒'],
            '军工': ['军工', '航天', '国防', '中航', '导弹', '战机'],
            '化工': ['化工', '石化', '化纤', '农药', '化肥']
        }
        
        for news in news_list:
            title = news['title']
            sentiment = self.analyze_sentiment(title)
            
            for sector, keywords in sector_keywords.items():
                if any(kw.lower() in title.lower() for kw in keywords):
                    if sector not in sector_news:
                        sector_news[sector] = []
                    news_copy = news.copy()
                    news_copy['sentiment'] = sentiment
                    sector_news[sector].append(news_copy)
        
        return sector_news
    
    def get_sector_sentiment(self, sector_news: Dict[str, List[Dict]]) -> Dict[str, Dict]:
        """计算各板块整体情感"""
        result = {}
        
        for sector, news_list in sector_news.items():
            total_score = sum(n['sentiment']['score'] for n in news_list)
            positive_count = sum(1 for n in news_list if n['sentiment']['sentiment'] == 'positive')
            negative_count = sum(1 for n in news_list if n['sentiment']['sentiment'] == 'negative')
            
            if total_score > 2:
                trend = '利好'
            elif total_score < -2:
                trend = '利空'
            else:
                trend = '中性'
            
            result[sector] = {
                'trend': trend,
                'score': total_score,
                'news_count': len(news_list),
                'positive_news': positive_count,
                'negative_news': negative_count,
                'latest_news': news_list[:5]  # 最新 5 条
            }
        
        return result
    
    def run(self) -> Dict[str, Dict]:
        """执行完整新闻分析流程"""
        print("[新闻监控] 开始抓取新闻...")
        
        all_news = []
        successful_sources = []
        
        # 按优先级抓取
        for priority in [1, 2, 3]:
            sources = [s for s in self.news_sources if s.get('priority', 2) == priority]
            
            for source in sources:
                news = self.fetch_news(source)
                if news:
                    all_news.extend(news)
                    successful_sources.append(source['name'])
                    print(f"[新闻监控] 从 {source['name']} 获取 {len(news)} 条新闻")
                    
                    # 如果已有足够新闻，跳过低优先级源
                    if len(all_news) >= 50 and priority == 1:
                        break
            
            if len(all_news) >= 50:
                break
        
        # 如果网页抓取失败，尝试 API
        if len(all_news) < 20:
            print("[新闻监控] 网页抓取不足，尝试 API...")
            api_news = self.fetch_news_from_api('thousend')
            if api_news:
                all_news.extend(api_news)
                print(f"[新闻监控] 从 API 获取 {len(api_news)} 条新闻")
        
        if not all_news:
            print("[新闻监控] 未获取到新闻")
            return {}
        
        # 去重
        seen = set()
        unique_news = []
        for n in all_news:
            if n['title'] not in seen:
                seen.add(n['title'])
                unique_news.append(n)
        
        print(f"[新闻监控] 去重后共 {len(unique_news)} 条新闻")
        
        # 分析板块
        sector_news = self.extract_sectors(unique_news)
        result = self.get_sector_sentiment(sector_news)
        
        print(f"[新闻监控] 分析完成，覆盖 {len(result)} 个板块")
        print(f"[新闻监控] 成功数据源：{', '.join(successful_sources)}")
        
        return result


if __name__ == '__main__':
    # 测试
    keywords = {
        'positive': ['利好', '突破', '增长', '订单', '签约', '上涨', '创新高'],
        'negative': ['利空', '下跌', '亏损', '处罚', '风险', '下滑', '减持']
    }
    monitor = NewsMonitor(keywords)
    result = monitor.run()
    
    for sector, info in result.items():
        print(f"\n{sector}: {info['trend']} (分数：{info['score']}, 新闻数：{info['news_count']})")
