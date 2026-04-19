#!/usr/bin/env python3
"""
自定义主题生成 CLI 工具

用法：
    python generate_custom.py "微服务架构"
    python generate_custom.py "微服务架构" --agent engineering_worker
    python generate_custom.py "微服务架构" --classify
    python generate_custom.py --list
    python generate_custom.py --get custom_20260419_001
"""

import sys
import argparse
from pathlib import Path

project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

from custom_topic_generator import CustomTopicGenerator


def main():
    parser = argparse.ArgumentParser(
        description="自定义主题知识生成 CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  # 生成主题（自动分类）
  python generate_custom.py "微服务架构"
  
  # 指定 Agent 生成
  python generate_custom.py "微服务架构" --agent engineering_worker
  
  # 添加描述
  python generate_custom.py "微服务架构" --description "分布式系统设计模式"
  
  # 智能分类（不生成）
  python generate_custom.py "微服务架构" --classify
  
  # 列出已生成的主题
  python generate_custom.py --list
  
  # 查看主题详情
  python generate_custom.py --get custom_20260419_001
  
  # 跳过详情生成（加快速度）
  python generate_custom.py "微服务架构" --skip-details
  
  # 跳过关联生成
  python generate_custom.py "微服务架构" --skip-relation
        """
    )
    
    parser.add_argument("topic", nargs="?", help="主题名称")
    parser.add_argument("--agent", help="指定生成 Agent（theory_worker/tech_stack_worker/core_skill_worker/engineering_worker/interview_worker）")
    parser.add_argument("--description", help="主题补充描述")
    parser.add_argument("--classify", action="store_true", help="仅进行智能分类，不生成内容")
    parser.add_argument("--list", action="store_true", help="列出已生成的自定义主题")
    parser.add_argument("--get", metavar="TOPIC_ID", help="获取指定主题详情")
    parser.add_argument("--skip-details", action="store_true", help="跳过知识点详情生成")
    parser.add_argument("--skip-relation", action="store_true", help="跳过知识关联生成")
    parser.add_argument("--verbose", action="store_true", help="显示详细输出")
    
    args = parser.parse_args()
    
    generator = CustomTopicGenerator()
    generator.initialize()
    
    if args.list:
        topics = generator.list_custom_topics()
        if not topics:
            print("\n暂无已生成的自定义主题")
            return
        
        print(f"\n📚 已生成的自定义主题：{len(topics)} 个")
        print("=" * 60)
        
        for t in topics:
            status = "✅" if t.get("success") else "❌"
            agent_names = {
                "theory_worker": "基础理论层",
                "tech_stack_worker": "技术栈层",
                "core_skill_worker": "核心能力层",
                "engineering_worker": "工程实践层",
                "interview_worker": "面试准备层",
                "faq_worker": "FAQ",
            }
            agent_display = agent_names.get(t.get("agent"), t.get("agent"))
            
            print(f"{status} {t.get('topic_name')}")
            print(f"   Agent: {agent_display}")
            print(f"   ID: {t.get('topic_id')}")
            print(f"   时间: {t.get('created_at')}")
            if t.get("error"):
                print(f"   错误: {t.get('error')}")
            print("-" * 60)
        
        success_count = sum(1 for t in topics if t.get("success"))
        print(f"成功: {success_count}/{len(topics)}")
        return
    
    if args.get:
        import json
        topic_data = generator.get_custom_topic(args.get)
        if not topic_data:
            print(f"\n❌ 未找到主题：{args.get}")
            return
        
        print(f"\n✅ 主题详情：{args.get}")
        print("=" * 60)
        print(json.dumps(topic_data, ensure_ascii=False, indent=2))
        return
    
    if args.classify:
        if not args.topic:
            print("❌ 请提供主题名称进行分类")
            parser.print_help()
            return
        
        import asyncio
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        keyword_agent = generator._classify_by_keywords(args.topic)
        llm_agent = loop.run_until_complete(generator._classify_topic(args.topic, args.description or ""))
        
        agent_names = {
            "theory_worker": "基础理论层",
            "tech_stack_worker": "技术栈层",
            "core_skill_worker": "核心能力层",
            "engineering_worker": "工程实践层",
            "interview_worker": "面试准备层",
        }
        
        print(f"\n🔍 主题分类结果")
        print("=" * 60)
        print(f"主题: {args.topic}")
        print(f"关键词匹配: {agent_names.get(keyword_agent, keyword_agent)}")
        if llm_agent:
            print(f"LLM 智能分析: {agent_names.get(llm_agent, llm_agent)}")
        print(f"推荐 Agent: {agent_names.get(llm_agent or keyword_agent, llm_agent or keyword_agent)}")
        print("=" * 60)
        return
    
    if not args.topic:
        print("❌ 请提供主题名称")
        parser.print_help()
        return
    
    print(f"\n🚀 开始生成主题：{args.topic}")
    print("=" * 60)
    
    if args.agent:
        agent_names = {
            "theory_worker": "基础理论层",
            "tech_stack_worker": "技术栈层",
            "core_skill_worker": "核心能力层",
            "engineering_worker": "工程实践层",
            "interview_worker": "面试准备层",
        }
        print(f"指定 Agent: {agent_names.get(args.agent, args.agent)}")
    
    if args.description:
        print(f"描述: {args.description}")
    
    print(f"跳过详情: {args.skip_details}")
    print(f"跳过关联: {args.skip_relation}")
    print("=" * 60)
    
    result = generator.generate(
        topic=args.topic,
        agent=args.agent,
        description=args.description or "",
        skip_details=args.skip_details,
        skip_relation=args.skip_relation,
    )
    
    print("\n" + "=" * 60)
    if result.success:
        import json
        
        agent_names = {
            "theory_worker": "基础理论层",
            "tech_stack_worker": "技术栈层",
            "core_skill_worker": "核心能力层",
            "engineering_worker": "工程实践层",
            "interview_worker": "面试准备层",
        }
        
        print(f"✅ 生成成功！")
        print(f"主题: {result.topic_name}")
        print(f"Agent: {agent_names.get(result.agent, result.agent)}")
        print(f"知识点: {result.keypoint_count} 个")
        print(f"文件: data/custom_topics/{result.topic_id}.json")
        
        if args.verbose and result.knowledge:
            print("\n知识内容预览:")
            print("-" * 60)
            preview = {
                "topic_name": result.knowledge.get("topic_name"),
                "description": result.knowledge.get("description", "")[:200] + "...",
                "subtopics_count": len(result.knowledge.get("subtopics", [])),
                "total_hours": result.knowledge.get("total_hours"),
            }
            print(json.dumps(preview, ensure_ascii=False, indent=2))
    else:
        print(f"❌ 生成失败")
        print(f"错误: {result.error}")
    
    print("=" * 60)


if __name__ == "__main__":
    main()