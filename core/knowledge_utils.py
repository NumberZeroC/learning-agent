#!/usr/bin/env python3
"""
Knowledge Utils - 玥识统计工具

提供知识内容的统计和辅助函数。
"""

from typing import Dict, List


def count_keypoints(knowledge: Dict) -> int:
    """
    统计已生成的知识点详情数量

    Args:
        knowledge: 知识内容字典

    Returns:
        int: 知识点数量
    """
    # 如果是 terms 格式（名词解释）
    if "terms" in knowledge:
        return len(knowledge.get("terms", []))

    # 如果是 subtopics 格式（知识体系）
    count = 0
    for subtopic in knowledge.get("subtopics", []):
        # 优先统计已生成的详细知识点
        count += len(subtopic.get("detailed_keypoints", []))
        # 如果没有详细知识点，统计基础知识点
        if count == 0:
            count += len(subtopic.get("key_points", []))

    return count


def count_subtopics(knowledge: Dict) -> int:
    """
    统计子主题数量

    Args:
        knowledge: 知识内容字典

    Returns:
        int: 子主题数量
    """
    if "terms" in knowledge:
        return 0  # 名词解释格式没有子主题
    return len(knowledge.get("subtopics", []))


def count_total_hours(knowledge: Dict) -> int:
    """
    统计总学习时长

    Args:
        knowledge: 知识内容字典

    Returns:
        int: 总学习时长（小时）
    """
    return knowledge.get("total_hours", 0)


def get_all_keypoints(knowledge: Dict) -> List[str]:
    """
    获取所有知识点名称列表

    Args:
        knowledge: 知识内容字典

    Returns:
        List[str]: 知识点名称列表
    """
    keypoints = []

    # 名词解释格式
    if "terms" in knowledge:
        for term in knowledge.get("terms", []):
            keypoints.append(term.get("name", ""))
        return keypoints

    # 知识体系格式
    for subtopic in knowledge.get("subtopics", []):
        subtopic_name = subtopic.get("name", "")
        for kp in subtopic.get("key_points", []):
            keypoints.append(f"[{subtopic_name}] {kp}")

    return keypoints


def has_practice_project(knowledge: Dict) -> bool:
    """
    检查是否包含实践项目

    Args:
        knowledge: 知识内容字典

    Returns:
        bool: 是否包含实践项目
    """
    return "practice_project" in knowledge


def has_interview_highlights(knowledge: Dict) -> bool:
    """
    检查是否包含面试亮点

    Args:
        knowledge: 知识内容字典

    Returns:
        bool: 是否包含面试亮点
    """
    return "interview_highlights" in knowledge


def has_knowledge_graph(knowledge: Dict) -> bool:
    """
    检查是否包含知识图谱

    Args:
        knowledge: 知识内容字典

    Returns:
        bool: 是否包含知识图谱
    """
    return "knowledge_graph" in knowledge


def get_knowledge_summary(knowledge: Dict) -> Dict:
    """
    获取知识内容的摘要统计

    Args:
        knowledge: 知识内容字典

    Returns:
        Dict: 摘要统计信息
    """
    return {
        "topic_name": knowledge.get("topic_name", "未知"),
        "keypoint_count": count_keypoints(knowledge),
        "subtopic_count": count_subtopics(knowledge),
        "total_hours": count_total_hours(knowledge),
        "has_practice_project": has_practice_project(knowledge),
        "has_interview_highlights": has_interview_highlights(knowledge),
        "has_knowledge_graph": has_knowledge_graph(knowledge),
    }