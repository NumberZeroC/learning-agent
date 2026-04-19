#!/usr/bin/env python3
"""
知识内容生成工具（重构版）

功能：
- 列出所有主题/指定层主题
- 生成单个主题
- 生成整个层级

用法：
    python regenerate_topic.py --list                # 列出所有主题
    python regenerate_topic.py --list-layer 1        # 列出第1层主题
    python regenerate_topic.py "机器学习"            # 生成单个主题
    python regenerate_topic.py --layer-only 1        # 生成第1层所有主题
    python regenerate_topic.py --layer-only 1 --skip-details  # 只生成结构
"""

import sys
import argparse
from pathlib import Path

project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))


def main():
    parser = argparse.ArgumentParser(description="知识内容生成工具（调用 WorkflowOrchestrator）")
    parser.add_argument("topic", nargs="?", help="主题名称")
    parser.add_argument("--layer", type=int, help="指定层级（配合主题名称使用）")
    parser.add_argument("--layer-only", type=int, help="生成整个层级")
    parser.add_argument("--list", action="store_true", help="列出所有主题")
    parser.add_argument("--list-layer", type=int, help="列出指定层级的主题")
    parser.add_argument("--skip-details", action="store_true", help="跳过知识点详情生成")
    parser.add_argument("--skip-relation", action="store_true", help="跳过知识关联生成")

    args = parser.parse_args()

    # 导入 WorkflowOrchestrator
    from workflow_orchestrator import WorkflowOrchestrator

    orchestrator = WorkflowOrchestrator()
    orchestrator.initialize()

    # 列出所有主题
    if args.list:
        topics = orchestrator.list_all_topics()
        print("\n📚 所有主题列表：")
        print("-" * 60)
        for t in topics:
            marker = "★" if t['priority'] == 'high' else "○"
            print(f"  [{t['layer']}] {t['layer_name']} - {marker} {t['topic_name']}")
            print(f"      Agent: {t['agent']}")
        print("-" * 60)
        print(f"共 {len(topics)} 个主题")
        return

    # 列出指定层级主题
    if args.list_layer:
        layer_topics = orchestrator.list_layer_topics(args.list_layer)
        if not layer_topics:
            print(f"❌ 第{args.list_layer}层不存在")
            return
        layer_name = layer_topics[0]['layer_name']
        agent = layer_topics[0]['agent']
        print(f"\n📚 第{args.list_layer}层主题列表：{layer_name}")
        print(f"   Agent: {agent}")
        print("-" * 40)
        for t in layer_topics:
            marker = "★" if t['priority'] == 'high' else "○"
            print(f"  {marker} {t['topic_name']}")
        print("-" * 40)
        print(f"共 {len(layer_topics)} 个主题")
        return

    # 生成整个层级
    if args.layer_only:
        print(f"\n🔄 开始生成第{args.layer_only}层...")
        
        result = orchestrator.execute_layer(
            args.layer_only, args.skip_details, args.skip_relation
        )

        if result.get("success"):
            print(f"\n✅ 第{result['layer']}层生成完成！")
            print(f"   层级名称：{result['layer_name']}")
            print(f"   Agent：{result['agent']}")
            print(f"   ✅ 成功：{result['success_count']}/{result['total_topics']}")
            print(f"   ❌ 失败：{result['failed_count']}/{result['total_topics']}")
            
            if result['failed_count'] > 0:
                print("\n失败的主题：")
                layer_result = result.get('layer_result', {})
                topics = layer_result.get('topics', [])
                for topic in topics:
                    if topic.get('error'):
                        print(f"   - {topic.get('topic_name', '未知')}: {topic.get('error', '未知错误')}")
        else:
            print(f"\n❌ 生成失败：{result.get('error')}")
        return

    # 生成单个主题
    if not args.topic:
        parser.print_help()
        return

    # 🔒 安全验证：检查主题名称是否有效
    all_topics = orchestrator.list_all_topics()
    valid_topic_names = [t['topic_name'] for t in all_topics]
    
    if args.topic not in valid_topic_names:
        print(f"\n❌ 错误：无效的主题名称 '{args.topic}'")
        print(f"\n✅ 有效的主题列表：")
        print("-" * 60)
        for t in all_topics:
            marker = "★" if t['priority'] == 'high' else "○"
            print(f"  [{t['layer']}] {t['layer_name']} - {marker} {t['topic_name']}")
        print("-" * 60)
        print(f"\n💡 提示：使用 --list 查看所有主题，使用 --layer-only 生成整个层级")
        return

    print(f"\n🔄 开始生成主题：{args.topic}")
    
    result = orchestrator.execute_single_topic(
        args.topic, args.layer, args.skip_details, args.skip_relation
    )

    if result.get("success"):
        print(f"\n✅ 成功生成主题：{result['topic_name']}")
        print(f"   层级：第{result['layer']}层")
        print(f"   Agent：{result['agent']}")
        print(f"   知识点详情数：{result['keypoint_count']}")
        print(f"   实践项目：{'有' if result.get('has_practice_project') else '无'}")
        print(f"   面试亮点：{'有' if result.get('has_interview_highlights') else '无'}")
    else:
        print(f"\n❌ 生成失败：{result.get('error')}")


if __name__ == "__main__":
    main()