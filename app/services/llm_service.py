"""LLM service for AI lesson plan generation."""
import json
from typing import List, Dict, Any
from anthropic import Anthropic
from config import SETTINGS

# Initialize Anthropic client
_client = None


def get_client() -> Anthropic:
    global _client
    if _client is None:
        if not SETTINGS.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY not configured")
        _client = Anthropic(api_key=SETTINGS.anthropic_api_key)
    return _client


def generate_lesson_plan_content(
    title: str,
    objective: str,
    material_ids: List[str],
    topics: List[str]
) -> List[Dict[str, Any]]:
    """Generate lesson plan sections using Claude."""
    client = get_client()

    topics_str = ", ".join(topics) if topics else "根据教学目标自动生成"
    materials_str = ", ".join(material_ids) if material_ids else "未指定"

    prompt = f"""作为资深教师，请为以下课程生成详细教案：

课程标题：{title}
教学目标：{objective}
关联教材：{materials_str}
主题：{topics_str}

请生成4-6个教学阶段，总时长45分钟。每个阶段包含：
- title: 阶段标题（简短，5-10字）
- duration_minutes: 时长（分钟）
- activity: 具体教学活动描述（50-100字）
- teaching_method: 教学方法（如：讲授法、讨论法、练习法）
- expected_outcome: 预期学习成果（30-50字）

请以JSON数组格式返回：
[{{"title": "...", "duration_minutes": 10, "activity": "...", "teaching_method": "...", "expected_outcome": "..."}}]

确保内容紧密围绕教学目标和主题，不要返回通用模板。"""

    try:
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )

        content = response.content[0].text
        # Extract JSON from response
        json_start = content.find("[")
        json_end = content.rfind("]") + 1
        if json_start >= 0 and json_end > json_start:
            json_str = content[json_start:json_end]
            sections = json.loads(json_str)
            return sections
        else:
            # Fallback: return default if parsing fails
            return _get_default_sections(topics)
    except Exception as e:
        print(f"LLM generation failed: {e}")
        return _get_default_sections(topics)


def _get_default_sections(topics: List[str]) -> List[Dict[str, Any]]:
    """Fallback default sections."""
    topic = topics[0] if topics else "concept-review"
    return [
        {"title": f"导入：{topic}", "duration_minutes": 10, "activity": "通过问题引导学生回顾前置知识", "teaching_method": "启发式提问", "expected_outcome": "激活已有知识，建立学习动机"},
        {"title": "核心概念讲解", "duration_minutes": 20, "activity": "系统讲解核心概念，配合示例说明", "teaching_method": "讲授法+示例法", "expected_outcome": "理解并掌握核心知识点"},
        {"title": "练习巩固", "duration_minutes": 20, "activity": "学生分组完成练习题，教师巡视指导", "teaching_method": "练习法+小组合作", "expected_outcome": "能够独立运用所学知识解决问题"},
        {"title": "总结与反思", "duration_minutes": 10, "activity": "师生共同总结，学生自我评价学习效果", "teaching_method": "讨论法", "expected_outcome": "形成完整的知识结构"},
    ]
