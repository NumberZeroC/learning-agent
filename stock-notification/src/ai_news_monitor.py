#!/usr/bin/env python3
"""
AI 新闻监控模块 - 专为 AI 应用创业者定制
功能：获取 AI 领域新闻、生成洞察、推送到 QQ
集成到 stock-notification 项目，作为信息源补充

目标用户：6 年开发经验，华为云背景，AI 应用创业
"""

import os
import sys
import json
import time
import hashlib
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
import requests

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False


class AINewsMonitor:
    """AI 新闻监控器"""
    
    def __init__(self, cache_dir: str = None, cache_ttl: int = 600):
        """
        初始化 AI 新闻监控器
        
        Args:
            cache_dir: 缓存目录
            cache_ttl: 缓存有效期（秒）
        """
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            self.cache_dir = Path(__file__).parent.parent / 'data' / 'cache' / 'ai_news'
        
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_ttl = cache_ttl
        
        # 用户画像
        self.user_profile = {
            "name": "老板",
            "experience": "6 年开发",
            "background": "华为云计算 5 年",
            "current": "AI 应用创业",
            "goal": "抓住 AI 风口"
        }
        
        # 新闻源配置 - 优化版（仅保留可用源）
        self.news_sources = [
            # ===== 国际科技媒体（英文）=====
            {
                "name": "The Verge AI",
                "url": "https://www.theverge.com/ai-artificial-intelligence",
                "type": "rss",
                "language": "en",
                "priority": 1,
                "focus": ["产品发布", "行业动态", "监管政策"]
            },
            {
                "name": "TechCrunch AI",
                "url": "https://techcrunch.com/category/artificial-intelligence/",
                "type": "rss",
                "language": "en",
                "priority": 1,
                "focus": ["创业融资", "产品发布", "并购"]
            },
            {
                "name": "Anthropic News",
                "url": "https://www.anthropic.com/news",
                "type": "official",
                "language": "en",
                "priority": 1,
                "focus": ["官方动态", "研究突破"]
            },
            
            # ===== 中文媒体 =====
            {
                "name": "机器之心",
                "url": "https://www.jiqizhixin.com/",
                "type": "news",
                "language": "zh",
                "priority": 1,
                "focus": ["技术突破", "研究论文", "行业动态"]
            },
            {
                "name": "量子位",
                "url": "https://www.qbitai.com/",
                "type": "news",
                "language": "zh",
                "priority": 1,
                "focus": ["前沿技术", "融资新闻", "产品发布"]
            },
            
            # ===== 社区热度 =====
            {
                "name": "Hacker News AI",
                "url": "https://news.ycombinator.com/front",
                "type": "community",
                "language": "en",
                "priority": 2,
                "focus": ["社区讨论", "技术趋势"],
                "filter": "AI|Machine Learning|LLM"
            },
            {
                "name": "Reddit ML",
                "url": "https://www.reddit.com/r/MachineLearning/",
                "type": "community",
                "language": "en",
                "priority": 2,
                "focus": ["社区讨论", "研究论文", "开源项目"]
            },
            
            # ===== 专业资讯 =====
            {
                "name": "Import AI",
                "url": "https://jack-clark.net/",
                "type": "newsletter",
                "language": "en",
                "priority": 2,
                "focus": ["周报汇总", "政策解读"]
            },
            {
                "name": "The Batch (DeepLearning.AI)",
                "url": "https://www.deeplearning.ai/the-batch/",
                "type": "newsletter",
                "language": "en",
                "priority": 2,
                "focus": ["周报汇总", "技术解读"]
            },
        ]
        
        # 请求头
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }
        
        # 是否启用全文抓取（会增加请求时间）
        self.fetch_full_content = os.environ.get('AI_NEWS_FULL_CONTENT', 'false').lower() == 'true'
    
    def fetch_article_content(self, url: str, timeout: int = 10) -> str:
        """获取文章全文内容"""
        try:
            time.sleep(0.5)  # 礼貌延迟
            response = requests.get(url, headers=self.headers, timeout=timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 移除不需要的元素
            for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                tag.decompose()
            
            # 找主要内容区域
            main = soup.find('main') or soup.find('article') or soup.find('div', class_=lambda x: x and isinstance(x, str) and ('content' in x.lower() or 'article' in x.lower() or 'post' in x.lower()))
            
            if main:
                # 提取段落
                paragraphs = main.find_all(['p', 'h1', 'h2', 'h3', 'h4'])
                content = '\n'.join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 20])
                return content[:3000]  # 限制长度
            
            # 备用方案：提取所有段落
            paragraphs = soup.find_all('p')
            content = '\n'.join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 30])
            return content[:3000]
            
        except Exception as e:
            return f"无法获取全文：{str(e)[:50]}"
    
    def translate_simple(self, text: str) -> str:
        """简单的英文到中文翻译（基于短语匹配）"""
        
        # 常见短语翻译（按长度排序，长的优先匹配）
        phrases = [
            ("Responsible Scaling Policy", "负责任扩展政策"),
            ("Build and Learn", "构建与学习"),
            ("Economic Index", "经济指数"),
            ("Core views on AI safety", "AI 安全核心观点"),
            ("largest study ever done on AI", "有史以来最大规模的 AI 研究"),
            ("how it's shaping lives around the world", "如何塑造全球人们的生活"),
            ("AI-assisted drive on another planet", "外星球上的 AI 辅助驾驶"),
            ("Claude helped NASA's Perseverance rover travel four hundred meters on Mars", "Claude 帮助 NASA 毅力号火星车在火星上行驶了 400 米"),
            ("Introducing Claude Sonnet", "推出 Claude Sonnet"),
            ("Introducing Claude Opus", "推出 Claude Opus"),
            ("Claude is a space to think", "Claude 是一个思考的空间"),
            ("No ads", "无广告"),
            ("delivers frontier performance", "提供前沿性能"),
            ("across coding, agents, and professional work", "涵盖编程、智能体和专业工作"),
            ("at scale", "规模化"),
            ("upgrading our smartest model", "升级我们最智能的模型"),
            ("Across agentic coding, computer use, tool use, search, and financial analysis", "涵盖智能体编程、电脑使用、工具使用、搜索和金融分析"),
            ("We've made a choice", "我们做出了一个选择"),
            ("Claude will remain ad-free", "Claude 将保持无广告"),
            ("We explain why advertising incentives are incompatible with safety", "我们解释为什么广告激励与安全不兼容"),
            ("The first AI-assisted drive on another planet", "首次在外星球上进行 AI 辅助驾驶"),
            ("What 81,000 people want from AI", "81,000 人对 AI 的期望"),
            ("Anthropic's", "Anthropic 的"),
            ("Claude's", "Claude 的"),
            ("NASA's", "NASA 的"),
            ("Perseverance rover", "毅力号火星车"),
            ("four hundred meters", "400 米"),
            ("on Mars", "在火星上"),
            ("another planet", "外星球"),
        ]
        
        result = text
        
        # 按顺序替换短语
        for en, zh in phrases:
            result = result.replace(en, zh)
        
        # 处理剩余的数字 + 名词组合
        import re
        result = re.sub(r'(\d+) people', r'\1 人', result)
        result = re.sub(r'(\d+) meters', r'\1 米', result)
        
        # 清理多余的英文
        cleanup = {
            " and ": " 和 ",
            " on ": " 在 ",
            " in ": " 在 ",
            " from ": " 从 ",
            " with ": " 使用 ",
            " for ": " 为了 ",
            " about ": " 关于 ",
        }
        for en, zh in cleanup.items():
            result = result.replace(en, zh)
        
        return result.strip()
    
    def generate_detailed_summary(self, title: str, content: str) -> str:
        """根据文章内容生成详细总结"""
        if not content or len(content) < 50:
            return ""
        
        # 检测是否为英文
        is_english = sum(1 for c in content if c.isalpha() and ord(c) < 128) > len(content) * 0.5
        
        # 检查是否是网站通用内容（导航、页脚等）
        generic_patterns = [
            "skip to main", "skip to footer", "navigation", "menu",
            "Core views on", "Anthropic's", "Claude's", "Academy",
            "Responsible Scaling", "Economic Index", "Constitution"
        ]
        is_generic = any(pattern.lower() in content.lower() for pattern in generic_patterns)
        
        # 如果是网站通用内容，返回空（让调用方显示分类标签）
        if is_generic:
            return ""
        
        # 提取关键句子（简单算法：找包含关键词的句子）
        keywords = ['发布', '推出', '新功能', '升级', '融资', '投资', '合作', '技术', '突破', '模型', 'AI', 'Claude', 'GPT', 'launch', 'release', 'new', 'feature', 'update', 'fund', 'invest']
        
        sentences = re.split(r'[.!?。！？]', content)
        key_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 20 or len(sentence) > 300:
                continue
            
            # 检查是否包含关键词
            score = sum(1 for kw in keywords if kw.lower() in sentence.lower())
            if score >= 1:
                key_sentences.append((score, sentence))
        
        # 排序并取前 3 句（减少数量提高质量）
        key_sentences.sort(key=lambda x: x[0], reverse=True)
        top_sentences = [s[1] for s in key_sentences[:3]]
        
        if not top_sentences:
            # 如果没找到关键句，不返回摘要
            return ""
        
        # 生成总结
        summary = "📌 **重点摘要**"
        if is_english:
            summary += " (已翻译):\n"
        else:
            summary += ":\n"
        
        for i, sent in enumerate(top_sentences, 1):
            if is_english:
                translated = self.translate_simple(sent)
                # 如果翻译后还是很多英文，说明翻译效果不好，直接显示原文
                if sum(1 for c in translated if c.isalpha() and ord(c) < 128) > len(translated) * 0.5:
                    summary += f"   {i}. {sent}\n"
                else:
                    summary += f"   {i}. {translated}\n"
            else:
                summary += f"   {i}. {sent}\n"
        
        return summary
    
    def _get_cache_key(self, source_name: str) -> str:
        """生成缓存键"""
        date_str = datetime.now().strftime('%Y-%m-%d')
        return f"{source_name}_{date_str}"
    
    def _get_cache_file(self, key: str) -> Path:
        """获取缓存文件路径"""
        return self.cache_dir / f"{key}.json"
    
    def get_cached_news(self, source_name: str) -> Optional[List[Dict]]:
        """获取缓存的新闻"""
        key = self._get_cache_key(source_name)
        cache_file = self._get_cache_file(key)
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 检查缓存是否过期
            if time.time() - data.get('cached_at', 0) > self.cache_ttl:
                return None
            
            return data.get('news', [])
        except:
            return None
    
    def save_cache(self, source_name: str, news: List[Dict]):
        """保存新闻到缓存"""
        key = self._get_cache_key(source_name)
        cache_file = self._get_cache_file(key)
        
        try:
            data = {
                'news': news,
                'cached_at': time.time(),
                'source': source_name
            }
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[缓存] 写入失败：{e}")
    
    def fetch_news_from_source(self, source: Dict) -> List[Dict]:
        """从指定源获取新闻"""
        # 检查缓存
        cached = self.get_cached_news(source['name'])
        if cached:
            print(f"[{source['name']}] ✅ 使用缓存")
            return cached
        
        print(f"[{source['name']}] 📡 获取新闻中...")
        
        try:
            # 添加随机延迟，避免被封
            time.sleep(1 + hash(source['name']) % 3)
            
            response = requests.get(
                source['url'],
                headers=self.headers,
                timeout=15
            )
            response.raise_for_status()
            
            # 解析新闻
            if BS4_AVAILABLE:
                news = self._parse_news_bs4(response.text, source)
            else:
                news = self._parse_news_simple(response.text, source)
            
            # 保存缓存
            if news:
                self.save_cache(source['name'], news)
                print(f"[{source['name']}] ✅ 获取 {len(news)} 条")
            
            return news
            
        except Exception as e:
            print(f"[{source['name']}] ❌ 错误：{e}")
            return []
    
    def _parse_news_bs4(self, html: str, source: Dict) -> List[Dict]:
        """使用 BeautifulSoup 解析新闻"""
        news_items = []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # 根据不同类型的源使用不同的解析策略
            if source['type'] == 'official' and 'anthropic.com' in source['url']:
                # Anthropic 官网专用解析 - 找新闻列表项
                # 尝试多种选择器
                selectors = [
                    ('a', {'href': lambda x: x and '/news/' in x and len(x) < 200}),
                    ('article', {}),
                    ('div', {'class': lambda x: x and isinstance(x, str) and ('news-item' in x.lower() or 'post-item' in x.lower())}),
                    ('li', {'class': lambda x: x and isinstance(x, str) and ('news' in x.lower() or 'post' in x.lower())}),
                ]
                
                articles = []
                for tag, attrs in selectors:
                    found = soup.find_all(tag, attrs)
                    if found:
                        articles = found
                        break
                
                # 如果还是没找到，尝试找所有带 /news/ 链接的 a 标签
                if not articles:
                    articles = soup.find_all('a', href=lambda x: x and '/news/' in x and len(x) < 200)[:10]
                
                for article in articles[:10]:
                    # 找标题
                    title_tag = None
                    for t in ['h1', 'h2', 'h3', 'h4']:
                        title_tag = article.find(t)
                        if title_tag:
                            break
                    
                    if not title_tag:
                        title_tag = article.find('a', href=lambda x: x and '/news/' in x) if hasattr(article, 'find') else None
                    
                    if title_tag:
                        title = title_tag.get_text(strip=True)
                        
                        # 获取 URL
                        url = ''
                        if title_tag.name == 'a':
                            url = title_tag.get('href', '')
                        else:
                            link_tag = article.find('a', href=True)
                            if link_tag:
                                url = link_tag.get('href', '')
                        
                        # 找摘要/描述 - 尝试多个选择器
                        summary = ""
                        for desc_class in ['description', 'desc', 'excerpt', 'summary', 'preview', 'subtitle']:
                            desc_tag = article.find(['p', 'div'], class_=lambda x: x and isinstance(x, str) and desc_class in x.lower())
                            if desc_tag:
                                summary = desc_tag.get_text(strip=True)
                                break
                        
                        # 如果没有找到摘要，尝试找第一个 p 标签
                        if not summary:
                            p_tag = article.find('p')
                            if p_tag:
                                summary = p_tag.get_text(strip=True)
                        
                        # 过滤无效标题
                        if len(title) < 5 or len(title) > 200:
                            continue
                        if any(kw in title.lower() for kw in ['skip', 'main content', 'footer', 'navigation', 'menu']):
                            continue
                        
                        news_items.append({
                            'title': title,
                            'summary': summary[:100] if summary else '',
                            'url': url if url.startswith('http') else 'https://www.anthropic.com' + url,
                            'source': source['name'],
                            'language': source['language'],
                            'focus': source['focus'],
                            'fetched_at': datetime.now().isoformat()
                        })
            
            elif source['type'] == 'news' and 'jiqizhixin.com' in source['url']:
                # 机器之心专用解析
                articles = soup.find_all(['article', 'div'], class_=lambda x: x and isinstance(x, str) and ('news-item' in x.lower() or 'post' in x.lower() or 'article' in x.lower()))
                if not articles:
                    articles = soup.find_all('li', class_=lambda x: x and isinstance(x, str) and ('news' in x.lower() or 'item' in x.lower()))
                
                for article in articles[:10]:
                    # 找标题
                    title_tag = article.find(['h2', 'h3', 'a'], class_=lambda x: x and isinstance(x, str) and ('title' in x.lower() or 'heading' in x.lower()))
                    if not title_tag:
                        title_tag = article.find('a', href=True)
                    
                    if title_tag:
                        title = title_tag.get_text(strip=True)
                        url = title_tag.get('href', '')
                        
                        # 找摘要
                        summary = ""
                        desc_tag = article.find('p', class_=lambda x: x and isinstance(x, str) and ('desc' in x.lower() or 'summary' in x.lower() or 'abstract' in x.lower()))
                        if desc_tag:
                            summary = desc_tag.get_text(strip=True)[:100]
                        
                        # 过滤
                        if len(title) < 5 or len(title) > 150:
                            continue
                        
                        news_items.append({
                            'title': title,
                            'summary': summary,
                            'url': url if url.startswith('http') else source['url'].rsplit('/', 1)[0] + '/' + url.lstrip('/'),
                            'source': source['name'],
                            'language': source['language'],
                            'focus': source['focus'],
                            'fetched_at': datetime.now().isoformat()
                        })
            
            elif source['type'] in ['official', 'news']:
                # 通用解析
                articles = soup.find_all('a', href=True)
                
                for article in articles[:20]:
                    title = article.get_text(strip=True)
                    url = article['href']
                    
                    if len(title) < 10 or len(title) > 200:
                        continue
                    
                    if any(kw in url.lower() for kw in ['login', 'signup', 'about', 'contact']):
                        continue
                    
                    if any(kw in title.lower() for kw in ['skip to', 'main content', 'footer', 'navigation', 'menu', '广告', '会员', '推广']):
                        continue
                    
                    news_items.append({
                        'title': title,
                        'summary': '',
                        'url': url if url.startswith('http') else source['url'].rsplit('/', 1)[0] + '/' + url,
                        'source': source['name'],
                        'language': source['language'],
                        'focus': source['focus'],
                        'fetched_at': datetime.now().isoformat()
                    })
            
            elif source['type'] == 'community':
                # 社区类解析
                titles = soup.find_all(['h3', 'h4', 'span'], class_=lambda x: x and ('title' in x.lower() or 'story' in x.lower()))
                
                for title_tag in titles[:15]:
                    title = title_tag.get_text(strip=True)
                    
                    # 检查是否包含 AI 相关关键词
                    if not any(kw.lower() in title.lower() for kw in ['ai', 'ml', 'llm', 'model', 'gpt', 'claude']):
                        continue
                    
                    news_items.append({
                        'title': title,
                        'url': source['url'],
                        'source': source['name'],
                        'language': source['language'],
                        'focus': source['focus'],
                        'fetched_at': datetime.now().isoformat()
                    })
            
            # 去重
            seen = set()
            unique = []
            for item in news_items:
                title_hash = hashlib.md5(item['title'].encode()).hexdigest()
                if title_hash not in seen:
                    seen.add(title_hash)
                    unique.append(item)
            
            return unique[:10]  # 限制每个源最多 10 条
            
        except Exception as e:
            print(f"[{source['name']}] 解析失败：{e}")
            return []
    
    def _parse_news_simple(self, html: str, source: Dict) -> List[Dict]:
        """简单解析（无 BeautifulSoup 时）"""
        news_items = []
        
        # 简单提取标题
        import re
        titles = re.findall(r'<title>([^<]+)</title>', html)
        
        for title in titles[:5]:
            if len(title) > 10:
                news_items.append({
                    'title': title.strip(),
                    'url': source['url'],
                    'source': source['name'],
                    'language': source['language'],
                    'focus': source['focus'],
                    'fetched_at': datetime.now().isoformat()
                })
        
        return news_items
    
    def fetch_all_news(self, limit_sources: int = None) -> List[Dict]:
        """从所有源获取新闻"""
        all_news = []
        
        # 按优先级排序
        sorted_sources = sorted(self.news_sources, key=lambda x: x['priority'])
        
        if limit_sources:
            sorted_sources = sorted_sources[:limit_sources]
        
        for source in sorted_sources:
            news = self.fetch_news_from_source(source)
            all_news.extend(news)
        
        # 去重和排序
        return self._deduplicate_and_sort(all_news)
    
    def _deduplicate_and_sort(self, news: List[Dict]) -> List[Dict]:
        """去重并排序"""
        seen = set()
        unique = []
        
        for item in news:
            title_hash = hashlib.md5(item['title'][:50].encode()).hexdigest()
            if title_hash not in seen:
                seen.add(title_hash)
                unique.append(item)
        
        # 按优先级排序（优先显示高优先级源的新闻）
        source_priority = {s['name']: s['priority'] for s in self.news_sources}
        unique.sort(key=lambda x: source_priority.get(x['source'], 99))
        
        return unique
    
    def _generate_hot_news_summary(self, news: List[Dict]) -> str:
        """生成热点新闻摘要"""
        if not news:
            return ""
        
        # 统计各来源新闻数量
        source_count = {}
        for item in news:
            source = item.get("source", "未知")
            source_count[source] = source_count.get(source, 0) + 1
        
        # 提取标题列表用于关键词统计
        titles = [item.get("title", "") for item in news]
        
        # 统计热点话题（关键词频率）
        keywords = self._extract_hot_topics(titles)
        
        # 生成摘要
        summary_lines = ["🔥 **热点新闻摘要**"]
        
        # 来源统计
        if source_count:
            summary_lines.append("📊 **新闻来源**")
            for source, count in sorted(source_count.items(), key=lambda x: x[1], reverse=True)[:5]:
                summary_lines.append(f"   • {source}: {count}条")
        
        # 热点话题
        if keywords:
            summary_lines.append("\n🎯 **热点话题**")
            hot_topics = [kw for kw in keywords[:5]]
            summary_lines.append(f"   {' · '.join(hot_topics)}")
        
        # 情感分析
        sentiment = self.analyze_news_sentiment(news)
        overall_level = sentiment.get("overall_level", "neutral")
        level_map = {"positive": "🟢 积极", "neutral": "🟡 中性", "negative": "🔴 消极"}
        summary_lines.append(f"\n💭 **整体情绪**: {level_map.get(overall_level, '🟡 中性')} (得分：{sentiment.get('overall_score', 50):.1f})")
        
        return "\n".join(summary_lines)
    
    def generate_personal_advice(self, news: List[Dict]) -> Dict:
        """根据新闻生成个人建议"""
        
        # 分类新闻
        categories = {
            "product": [],      # 产品发布
            "funding": [],      # 融资新闻
            "tech": [],         # 技术突破
            "policy": [],       # 政策法规
            "market": [],       # 市场动态
            "risk": []          # 风险警示
        }
        
        for item in news:
            title = item.get("title", "").lower()
            
            # 简单分类
            if any(kw in title for kw in ["launch", "release", "new", "product", "发布", "上线"]):
                categories["product"].append(item)
            elif any(kw in title for kw in ["fund", "invest", "acquisition", "buy", "融资", "投资", "收购"]):
                categories["funding"].append(item)
            elif any(kw in title for kw in ["agi", "model", "ai", "llm", "technology", "技术", "突破"]):
                categories["tech"].append(item)
            elif any(kw in title for kw in ["regulation", "policy", "law", "guilty", "监管", "政策", "法案"]):
                categories["policy"].append(item)
            elif any(kw in title for kw in ["fraud", "scam", "risk", "fraud", "欺诈", "风险"]):
                categories["risk"].append(item)
            else:
                categories["market"].append(item)
        
        # 生成建议
        advice = {
            "opportunities": [],
            "risks": [],
            "learning": [],
            "actions": []
        }
        
        # 机会分析
        if categories["funding"]:
            advice["opportunities"].append({
                "type": "💰 资本动向",
                "content": "关注融资热点领域，可能是下一个风口",
                "items": [n['title'] for n in categories["funding"][:3]]
            })
        
        if categories["product"]:
            advice["opportunities"].append({
                "type": "🚀 产品趋势",
                "content": "分析新产品功能，寻找差异化机会",
                "items": [n['title'] for n in categories["product"][:3]]
            })
        
        if categories["tech"]:
            advice["learning"].append({
                "type": "📚 技术跟进",
                "content": "保持对新技术的敏感度",
                "items": [n['title'] for n in categories["tech"][:3]]
            })
        
        # 风险分析
        if categories["policy"]:
            advice["risks"].append({
                "type": "⚠️ 政策监管",
                "content": "注意 AI 监管动态，避免踩红线",
                "items": [n['title'] for n in categories["policy"][:3]]
            })
        
        if categories["risk"]:
            advice["risks"].append({
                "type": "🛡️ 风险警示",
                "content": "关注 AI 滥用案例，加强产品风控",
                "items": [n['title'] for n in categories["risk"][:3]]
            })
        
        # 行动建议（结合用户背景）
        advice["actions"] = self._generate_action_items(categories)
        
        return advice
    
    def _generate_action_items(self, categories: Dict) -> List[Dict]:
        """生成具体行动项"""
        actions = []
        
        # 基于华为云背景的建议
        if categories["funding"]:
            actions.append({
                "priority": "🔥 高",
                "item": "研究融资新闻中的公司，评估是否有合作/投资机会",
                "reason": "华为云人脉 + 行业理解 = 独特优势"
            })
        
        # 基于 AI 应用创业的建议
        if categories["product"]:
            actions.append({
                "priority": "🔥 高",
                "item": "分析竞品新功能，思考如何差异化",
                "reason": "快速迭代是创业公司的核心竞争力"
            })
        
        # 技术跟进
        if categories["tech"]:
            actions.append({
                "priority": "📅 中",
                "item": "记录技术突破到知识库，评估是否可应用到产品",
                "reason": "技术深度是华为系创业者的优势"
            })
        
        # 通用建议
        actions.append({
            "priority": "📅 中",
            "item": "记录今日新闻到知识库，周末复盘",
            "reason": "建立行业认知体系"
        })
        
        actions.append({
            "priority": "💡 低",
            "item": "在社交媒体分享一条洞察",
            "reason": "建立个人品牌影响力"
        })
        
        return actions
    
    def analyze_news_sentiment(self, news: List[Dict]) -> Dict:
        """
        分析 AI 新闻情感
        
        返回：
        {
            "overall_score": 75.5,  # 整体情感得分 (0-100)
            "overall_level": "positive",  # positive/neutral/negative
            "categories": {
                "product": {"score": 80, "level": "positive"},
                "funding": {"score": 70, "level": "positive"},
                ...
            },
            "hot_topics": [...],  # 热点话题
            "risk_signals": [...]  # 风险信号
        }
        """
        
        # 情感关键词
        positive_keywords = [
            "突破", "发布", "上线", "成功", "增长", "创新", "领先",
            "fund", "invest", "launch", "release", "breakthrough", "success",
            "融资", "收购", "合作", "战略", "升级", "优化"
        ]
        
        negative_keywords = [
            "风险", "欺诈", "监管", "处罚", "下跌", "失败", "裁员",
            "risk", "fraud", "regulation", "penalty", "layoff", "failure",
            "监管", "调查", "诉讼", "暴雷", "亏损"
        ]
        
        # 分类统计
        category_stats = {}
        all_titles = []
        
        for item in news:
            title = item.get("title", "").lower()
            all_titles.append(title)
            
            # 分类
            category = item.get("category", "general")
            if category not in category_stats:
                category_stats[category] = {
                    "positive": 0,
                    "negative": 0,
                    "neutral": 0,
                    "titles": []
                }
            
            # 情感分析
            pos_count = sum(1 for kw in positive_keywords if kw in title)
            neg_count = sum(1 for kw in negative_keywords if kw in title)
            
            if pos_count > neg_count:
                category_stats[category]["positive"] += 1
            elif neg_count > pos_count:
                category_stats[category]["negative"] += 1
            else:
                category_stats[category]["neutral"] += 1
            
            category_stats[category]["titles"].append(title)
        
        # 计算整体情感得分
        total_positive = sum(s["positive"] for s in category_stats.values())
        total_negative = sum(s["negative"] for s in category_stats.values())
        total_news = len(news)
        
        if total_news > 0:
            overall_score = 50 + (total_positive - total_negative) / total_news * 25
            overall_score = max(0, min(100, overall_score))
        else:
            overall_score = 50
        
        # 确定整体情感级别
        if overall_score >= 60:
            overall_level = "positive"
            overall_emoji = "🟢"
        elif overall_score >= 40:
            overall_level = "neutral"
            overall_emoji = "🟡"
        else:
            overall_level = "negative"
            overall_emoji = "🔴"
        
        # 计算各类别情感
        categories_sentiment = {}
        for cat, stats in category_stats.items():
            cat_total = stats["positive"] + stats["negative"] + stats["neutral"]
            if cat_total > 0:
                cat_score = 50 + (stats["positive"] - stats["negative"]) / cat_total * 25
                cat_score = max(0, min(100, cat_score))
            else:
                cat_score = 50
            
            if cat_score >= 60:
                cat_level = "positive"
            elif cat_score >= 40:
                cat_level = "neutral"
            else:
                cat_level = "negative"
            
            categories_sentiment[cat] = {
                "score": round(cat_score, 1),
                "level": cat_level,
                "count": cat_total
            }
        
        # 提取热点话题（高频词）
        hot_topics = self._extract_hot_topics(all_titles)
        
        # 提取风险信号
        risk_signals = []
        for item in news:
            title = item.get("title", "").lower()
            if any(kw in title for kw in negative_keywords):
                risk_signals.append({
                    "title": item.get("title", ""),
                    "source": item.get("source", ""),
                    "severity": "high" if any(kw in title for kw in ["欺诈", "fraud", "处罚", "penalty"]) else "medium"
                })
        
        return {
            "overall_score": round(overall_score, 1),
            "overall_level": overall_level,
            "overall_emoji": overall_emoji,
            "categories": categories_sentiment,
            "hot_topics": hot_topics[:5],
            "risk_signals": risk_signals[:5],
            "total_news": total_news,
            "positive_ratio": round(total_positive / total_news * 100, 1) if total_news > 0 else 0,
            "negative_ratio": round(total_negative / total_news * 100, 1) if total_news > 0 else 0
        }
    
    def _extract_hot_topics(self, titles: List[str]) -> List[str]:
        """提取热点话题"""
        # 关键词频率统计
        keywords = [
            "AGI", "GPT", "Claude", "LLM", "模型", "大模型",
            "OpenAI", "Anthropic", "Google", "Microsoft", "Meta",
            "融资", "投资", "收购", "发布", "上线",
            "监管", "政策", "法案", "安全", "欺诈"
        ]
        
        keyword_count = {}
        for title in titles:
            for kw in keywords:
                if kw.lower() in title.lower():
                    keyword_count[kw] = keyword_count.get(kw, 0) + 1
        
        # 按频率排序
        sorted_keywords = sorted(keyword_count.items(), key=lambda x: x[1], reverse=True)
        
        return [f"{kw} ({count})" for kw, count in sorted_keywords]
    
    def _generate_news_summary(self, item: Dict) -> str:
        """为单条新闻生成摘要"""
        title = item.get("title", "")
        summary = item.get("summary", "")
        detailed_summary = item.get("detailed_summary", "")
        source = item.get("source", "")
        category = item.get("category", "")
        
        # 优先显示详细总结（全文抓取后生成）
        if detailed_summary and len(detailed_summary) > 20:
            return detailed_summary
        
        # 其次显示短摘要
        if summary and len(summary) > 10:
            # 检测是否为英文
            is_english = sum(1 for c in summary if c.isalpha() and ord(c) < 128) > len(summary) * 0.5
            
            # 截断过长的摘要
            if len(summary) > 80:
                summary = summary[:77] + "..."
            
            # 翻译英文摘要
            if is_english:
                translated = self.translate_simple(summary)
                # 如果翻译效果好（英文少），使用翻译版本
                if sum(1 for c in translated if c.isalpha() and ord(c) < 128) < len(translated) * 0.5:
                    return f"   ↳ {translated}"
            
            return f"   ↳ {summary}"
        
        # 否则显示分类标签
        # 来源标识
        source_map = {
            "Anthropic News": "🏢 官方",
            "The Verge AI": "📰 媒体",
            "TechCrunch AI": "💰 创投",
            "机器之心": "🔬 技术",
            "量子位": "🤖 产业",
            "Import AI": "📧 通讯"
        }
        source_tag = source_map.get(source, "📄")
        
        # 分类标识
        category_map = {
            "product": "🚀 产品",
            "funding": "💰 融资",
            "tech": "🔬 技术",
            "policy": "📜 政策",
            "market": "📊 市场",
            "risk": "⚠️ 风险"
        }
        category_tag = category_map.get(category, "📰 资讯")
        
        # 从标题提取关键信息
        title_lower = title.lower()
        key_points = []
        
        if any(kw in title_lower for kw in ["claude", "anthropic"]):
            key_points.append("Anthropic 官方动态")
        if any(kw in title_lower for kw in ["launch", "release", "发布", "上线"]):
            key_points.append("新产品/功能发布")
        if any(kw in title_lower for kw in ["fund", "invest", "融资", "投资"]):
            key_points.append("融资/投资相关")
        if any(kw in title_lower for kw in ["model", "llm", "agi", "模型"]):
            key_points.append("大模型技术")
        if any(kw in title_lower for kw in ["regulation", "policy", "监管", "政策"]):
            key_points.append("监管政策")
        
        # 生成摘要
        if key_points:
            summary_text = f"   ↳ {source_tag} {category_tag} · {' | '.join(key_points)}"
        else:
            summary_text = f"   ↳ {source_tag} {category_tag} · 行业动态"
        
        return summary_text
    
    def format_message(self, news: List[Dict], advice: Dict) -> str:
        """格式化推送消息"""
        
        today = datetime.now().strftime("%Y-%m-%d %A")
        
        message = f"""🤖 AI 应用新闻 | {today}

━━━━━━━━━━━━━━━━━━

📰 今日热点（精选）

"""
        
        # 添加新闻及摘要
        for i, item in enumerate(news[:5], 1):
            title = item.get("title", "无标题")
            # 截断过长的标题
            if len(title) > 60:
                title = title[:57] + "..."
            message += f"{i}. {title}\n"
            
            # 添加该新闻的摘要
            summary = self._generate_news_summary(item)
            message += f"{summary}\n\n"
        
        message += """━━━━━━━━━━━━━━━━━━

💡 个人建议（基于你的背景）

"""
        
        # 机会
        if advice["opportunities"]:
            message += "【机会】\n"
            for opp in advice["opportunities"]:
                message += f"• {opp['type']}: {opp['content']}\n"
            message += "\n"
        
        # 风险
        if advice["risks"]:
            message += "【风险】\n"
            for risk in advice["risks"]:
                message += f"• {risk['type']}: {risk['content']}\n"
            message += "\n"
        
        # 行动项
        if advice["actions"]:
            message += "【行动项】\n"
            for action in advice["actions"]:
                message += f"{action['priority']} {action['item']}\n"
                message += f"   → {action['reason']}\n"
        
        message += """
━━━━━━━━━━━━━━━━━━

🎯 今日金句
"2026 年不是 AI 取代程序员，而是会用 AI 的程序员取代不会用的。"

---
📬 如需调整推送内容或频率，请回复"配置"
"""
        
        return message
    
    def run_once(self, export_report: bool = True, send_qq: bool = True, fetch_full_content: bool = False) -> Dict:
        """执行一次新闻获取和推送"""
        print(f"\n{'='*60}")
        print(f"🤖 AI 新闻监控 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        
        # 1. 获取新闻
        print("📰 获取新闻中...")
        news = self.fetch_all_news(limit_sources=8)  # 限制源数量，加快速度
        print(f"✅ 获取到 {len(news)} 条新闻\n")
        
        if not news:
            print("⚠️ 未获取到新闻")
            return {'success': False, 'message': '未获取到新闻'}
        
        # 1.5 获取全文内容并生成详细总结（可选）
        if fetch_full_content or self.fetch_full_content:
            print("📖 获取文章全文并生成详细总结...\n")
            for i, item in enumerate(news[:5], 1):  # 只处理前 5 条
                url = item.get('url', '')
                if url and url.startswith('http'):
                    print(f"   [{i}/5] 抓取：{item.get('title', '')[:40]}...")
                    content = self.fetch_article_content(url)
                    if content and len(content) > 50:
                        detailed_summary = self.generate_detailed_summary(item.get('title', ''), content)
                        item['detailed_summary'] = detailed_summary
                        print(f"       ✅ 已生成详细总结")
                    else:
                        item['detailed_summary'] = "无法获取详细内容"
                        print(f"       ⚠️ 无法获取全文")
            print()
        
        # 2. 生成建议
        print("💡 生成建议中...")
        advice = self.generate_personal_advice(news)
        
        # 3. 格式化消息
        message = self.format_message(news, advice)
        
        # 4. 导出报告
        if export_report:
            self._export_report(message, news, advice)
        
        # 5. 推送到 QQ
        if send_qq:
            self._send_to_qq(message)
        
        print(f"\n✅ AI 新闻监控完成\n")
        
        return {
            'success': True,
            'count': len(news),
            'news': news,
            'advice': advice
        }
    
    def _export_report(self, message: str, news: List[Dict], advice: Dict):
        """导出报告"""
        today = datetime.now().strftime('%Y-%m-%d')
        reports_dir = Path(__file__).parent.parent / 'data' / 'reports' / 'ai_news'
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存 Markdown
        md_file = reports_dir / f'ai_news_{today}.md'
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(message)
        print(f"📄 报告已保存：{md_file}")
        
        # 保存 JSON
        json_file = reports_dir / f'ai_news_{today}.json'
        data = {
            'date': today,
            'update_time': datetime.now().isoformat(),
            'news': news,
            'advice': advice
        }
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"📄 数据已保存：{json_file}")
    
    def _send_to_qq(self, message: str):
        """推送到 QQ"""
        try:
            # 使用 OpenClaw message 工具
            import subprocess
            
            qq_target = "qqbot:c2c:6BD7A1BCF3F92369D0580647287C0D52"
            
            # 通过 openclaw CLI 发送
            cmd = [
                'openclaw', 'message', 'send',
                '--target', qq_target,
                '--message', message
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print("📬 QQ 推送成功")
            else:
                print(f"📬 QQ 推送失败：{result.stderr}")
                
        except Exception as e:
            print(f"📬 推送异常：{e}")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='AI 新闻监控')
    parser.add_argument('--once', action='store_true', help='执行一次')
    parser.add_argument('--no-export', action='store_true', help='不导出报告')
    parser.add_argument('--no-qq', action='store_true', help='不推送 QQ')
    parser.add_argument('--full-content', action='store_true', help='获取文章全文并生成详细总结')
    
    args = parser.parse_args()
    
    monitor = AINewsMonitor()
    
    if args.once:
        result = monitor.run_once(
            export_report=not args.no_export,
            send_qq=not args.no_qq,
            fetch_full_content=args.full_content
        )
        sys.exit(0 if result.get('success') else 1)
    else:
        parser.print_help()
