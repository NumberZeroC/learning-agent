#!/usr/bin/env python3
"""
AI 新闻每日推送 - 专为 AI 应用创业者定制
功能：获取 AI 新闻 + 生成个人建议 + QQ 推送
目标用户：6 年开发经验，华为云背景，AI 应用创业
"""

import os
import sys
import json
import requests
from datetime import datetime
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# ============== 配置区 ==============
USER_PROFILE = {
    "name": "老板",
    "experience": "6 年开发",
    "background": "华为云计算 5 年",
    "current": "AI 应用创业",
    "goal": "抓住 AI 风口",
    "strengths": [
        "云计算架构经验",
        "大规模系统开发",
        "技术深度",
        "华为方法论"
    ],
    "focus_areas": [
        "AI 应用落地",
        "产品化能力",
        "商业敏感度",
        "快速迭代"
    ]
}

# QQ 推送配置
QQ_TARGET = "qqbot:c2c:6BD7A1BCF3F92369D0580647287C0D52"

# 新闻源配置
NEWS_SOURCES = [
    {
        "name": "The Verge AI",
        "url": "https://www.theverge.com/ai-artificial-intelligence",
        "weight": 1.0
    },
    {
        "name": "TechCrunch AI",
        "url": "https://techcrunch.com/category/artificial-intelligence/",
        "weight": 0.9
    },
    {
        "name": "OpenAI News",
        "url": "https://openai.com/news/",
        "weight": 0.8
    },
]

# ============== 新闻获取 ==============

def fetch_news_source(source: dict) -> list:
    """从单个源获取新闻"""
    try:
        # 使用 web_fetch 工具（通过 OpenClaw Gateway）
        from openclaw.tools import web_fetch
        result = web_fetch(url=source["url"], maxChars=8000)
        
        if result.get("status") == "error":
            print(f"[{source['name']}] 获取失败：{result.get('error')}")
            return []
        
        # 解析新闻内容（简化版，实际需要根据 HTML 结构解析）
        news_items = parse_news_content(result.get("text", ""))
        return news_items
    except Exception as e:
        print(f"[{source['name']}] 异常：{e}")
        return []


def parse_news_content(content: str) -> list:
    """解析新闻内容，提取关键信息"""
    news_items = []
    
    # 简化解析逻辑（实际应该用 BeautifulSoup 等）
    # 这里返回示例结构
    lines = content.split('\n')
    current_item = {}
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # 检测标题
        if line.startswith('#') or (len(line) < 100 and line.endswith('.')):
            if current_item:
                news_items.append(current_item)
            current_item = {
                "title": line,
                "summary": "",
                "source": "",
                "category": "general"
            }
        elif current_item and not current_item.get("summary"):
            current_item["summary"] = line[:200]
    
    if current_item:
        news_items.append(current_item)
    
    return news_items[:10]  # 限制数量


def get_today_ai_news() -> list:
    """获取今日 AI 新闻"""
    all_news = []
    
    for source in NEWS_SOURCES:
        print(f"📰 获取 [{source['name']}] 新闻...")
        news = fetch_news_source(source)
        all_news.extend(news)
    
    # 去重和排序
    return deduplicate_news(all_news)


def deduplicate_news(news: list) -> list:
    """去重新闻"""
    seen = set()
    unique = []
    
    for item in news:
        title = item.get("title", "")[:50]
        if title not in seen:
            seen.add(title)
            unique.append(item)
    
    return unique


# ============== 建议生成 ==============

def generate_personal_advice(news: list) -> dict:
    """根据新闻生成个人建议"""
    
    # 分析新闻类别
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
        if any(kw in title for kw in ["launch", "release", "new", "product"]):
            categories["product"].append(item)
        elif any(kw in title for kw in ["fund", "invest", "acquisition", "buy"]):
            categories["funding"].append(item)
        elif any(kw in title for kw in ["agi", "model", "ai", "llm", "technology"]):
            categories["tech"].append(item)
        elif any(kw in title for kw in ["regulation", "policy", "law", "guilty"]):
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
        advice["opportunities"].append(
            "💰 资本动向：关注融资热点领域，可能是下一个风口"
        )
    
    if categories["product"]:
        advice["opportunities"].append(
            "🚀 产品趋势：分析新产品功能，寻找差异化机会"
        )
    
    # 风险分析
    if categories["risk"]:
        advice["risks"].append(
            "⚠️ 合规警示：注意 AI 监管动态，避免踩红线"
        )
    
    # 学习建议
    if categories["tech"]:
        advice["learning"].append(
            "📚 技术跟进：保持对新技术的敏感度"
        )
    
    # 行动建议（结合用户背景）
    advice["actions"] = generate_action_items(categories, USER_PROFILE)
    
    return advice


def generate_action_items(categories: dict, profile: dict) -> list:
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


# ============== 消息格式化 ==============

def format_message(news: list, advice: dict) -> str:
    """格式化推送消息"""
    
    today = datetime.now().strftime("%Y-%m-%d %A")
    
    message = f"""🤖 AI 应用创业日报 | {today}

━━━━━━━━━━━━━━━━━━

📰 今日热点（精选）

"""
    
    # 添加新闻
    for i, item in enumerate(news[:5], 1):
        title = item.get("title", "无标题")
        source = item.get("source", "未知来源")
        message += f"{i}. {title}\n"
    
    message += """
━━━━━━━━━━━━━━━━━━

💡 个人建议（基于你的背景）

"""
    
    # 机会
    if advice["opportunities"]:
        message += "【机会】\n"
        for opp in advice["opportunities"]:
            message += f"• {opp}\n"
        message += "\n"
    
    # 风险
    if advice["risks"]:
        message += "【风险】\n"
        for risk in advice["risks"]:
            message += f"• {risk}\n"
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


# ============== QQ 推送 ==============

def send_to_qq(message: str) -> bool:
    """发送到 QQ"""
    try:
        # 使用 OpenClaw message 工具
        # 这里通过调用 OpenClaw CLI 或 API 实现
        cmd = f'''
        openclaw message send --target "{QQ_TARGET}" --message "{message}"
        '''
        
        # 或者使用 requests 调用 Gateway API
        gateway_url = os.getenv("OPENCLAW_GATEWAY_URL", "http://localhost:17078")
        token = os.getenv("OPENCLAW_TOKEN", "")
        
        payload = {
            "action": "send",
            "target": QQ_TARGET,
            "message": message
        }
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            f"{gateway_url}/api/message",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            print("✅ QQ 推送成功")
            return True
        else:
            print(f"❌ QQ 推送失败：{response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 推送异常：{e}")
        return False


# ============== 主流程 ==============

def main():
    """主执行流程"""
    print(f"🚀 开始执行 AI 新闻推送 - {datetime.now()}")
    
    # 1. 获取新闻
    print("\n📰 获取新闻中...")
    news = get_today_ai_news()
    print(f"✅ 获取到 {len(news)} 条新闻")
    
    if not news:
        print("⚠️ 未获取到新闻，使用备用方案")
        news = get_fallback_news()
    
    # 2. 生成建议
    print("\n💡 生成建议中...")
    advice = generate_personal_advice(news)
    
    # 3. 格式化消息
    print("\n📝 格式化消息...")
    message = format_message(news, advice)
    
    # 4. 保存到本地（备份）
    save_to_file(message)
    
    # 5. 推送到 QQ
    print("\n📬 推送中...")
    success = send_to_qq(message)
    
    if success:
        print("\n✅ 推送完成！")
    else:
        print("\n❌ 推送失败，请检查配置")
    
    return success


def get_fallback_news() -> list:
    """备用新闻（当抓取失败时）"""
    return [
        {
            "title": "AI 行业持续高速发展，建议保持关注",
            "summary": "今日暂无具体新闻，建议主动查看新闻源",
            "source": "系统",
            "category": "general"
        }
    ]


def save_to_file(message: str):
    """保存到本地文件"""
    today = datetime.now().strftime("%Y-%m-%d")
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / f"ai_news_{today}.md"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(message)
    
    print(f"📄 已保存到：{output_file}")


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
