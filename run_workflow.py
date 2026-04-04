#!/usr/bin/env python3
"""
🚀 运行知识生成工作流

用法：
    python3 run_workflow.py

输出：
    - data/workflow_results/workflow_YYYYMMDD_HHMMSS.json (完整结果)
    - data/workflow_results/layer_X_workflow.json (按层级分类)
    - data/workflow_results/workflow_summary.json (汇总)
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from workflow_orchestrator import WorkflowOrchestrator


def main():
    """主函数"""
    print("="*70)
    print("🤖 Learning Agent - 知识生成工作流")
    print("="*70)
    print()
    print("📚 学习架构图：")
    print("   第 1 层：基础理论层 (AI 基础、LLM 原理、Agent 概念、架构模式)")
    print("   第 2 层：技术栈层 (Python、Agent 框架、向量数据库)")
    print("   第 3 层：核心能力层 (任务规划、工具调用、记忆管理、多 Agent)")
    print("   第 4 层：工程实践层 (项目经验、性能优化、部署运维)")
    print("   第 5 层：面试准备层 (算法题、系统设计、行为面试)")
    print()
    print("🎯 工作流说明：")
    print("   1. 根据架构图创建 17 个知识生成任务")
    print("   2. 5 个子 Agent 并发执行（每个 Agent 负责一个层级）")
    print("   3. 每个 Agent 调用 Qwen3.5-Plus 大模型生成知识")
    print("   4. 工作流记录所有回答并保存为 JSON")
    print()
    print("="*70)
    print()
    
    # 创建工作流编排器
    orchestrator = WorkflowOrchestrator()
    
    # 初始化
    print("⚙️  初始化工作流...")
    orchestrator.initialize()
    print()
    
    # 执行工作流
    result = orchestrator.execute_workflow()
    
    # 打印详细总结
    print()
    print("="*70)
    print("📊 工作流执行总结")
    print("="*70)
    print(f"   工作流 ID:    {result.workflow_id}")
    print(f"   开始时间：    {result.started_at}")
    print(f"   完成时间：    {result.completed_at}")
    print(f"   总任务数：    {result.total_tasks}")
    print(f"   ✅ 成功：     {result.success_count}")
    print(f"   ❌ 失败：     {result.failed_count}")
    print(f"   ⏱️  总耗时：   {result.duration_seconds:.2f}秒")
    print()
    
    # 各层级详情
    print("📚 各层级详情:")
    for layer_num, layer_data in result.layer_results.items():
        topics_count = len(layer_data.get('topics', []))
        agent_name = layer_data.get('agent', 'unknown')
        layer_name = layer_data.get('layer_name', f'第{layer_num}层')
        print(f"   第{layer_num}层 ({layer_name}):")
        print(f"      Agent: {agent_name}")
        print(f"      生成主题数：{topics_count}")
    print()
    print("="*70)
    print()
    print("✅ 工作流完成！结果已保存到 data/workflow_results/ 目录")
    print()
    print("📄 输出文件:")
    print(f"   - data/workflow_results/workflow_{result.workflow_id}.json")
    print(f"   - data/workflow_results/layer_X_workflow.json (各层级)")
    print(f"   - data/workflow_results/workflow_summary.json (汇总)")
    print()


if __name__ == "__main__":
    main()
