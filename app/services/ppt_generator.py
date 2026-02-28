"""PPT generation service using python-pptx."""
import os
from typing import List, Dict, Any
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN

# Ensure output directories exist
os.makedirs("output/ppts", exist_ok=True)
os.makedirs("output/previews", exist_ok=True)


def generate_ppt_from_lesson_plan(
    plan_data: Dict[str, Any],
    template: str = "lesson_default",
    ppt_id: str = ""
) -> str:
    """Generate PPT file from lesson plan data.

    Returns: file_path of generated PPT
    """
    # Load template or create new
    template_path = f"templates/{template}.pptx"
    if os.path.exists(template_path):
        prs = Presentation(template_path)
    else:
        prs = Presentation()

    # Clear existing slides (keep first as template)
    while len(prs.slides) > 1:
        rId = prs.slides._sldIdLst[1].rId
        prs.part.drop_rel(rId)
        del prs.slides._sldIdLst[1]

    # Title slide
    if len(prs.slides) == 0:
        title_slide = prs.slides.add_slide(prs.slide_layouts[6])  # Blank
    else:
        title_slide = prs.slides[0]

    # Add title
    title_box = title_slide.shapes.add_textbox(Inches(1), Inches(2), Inches(8), Inches(1.5))
    title_frame = title_box.text_frame
    title_frame.text = plan_data.get("title", "教案")
    title_frame.paragraphs[0].font.size = Pt(44)
    title_frame.paragraphs[0].font.bold = True
    title_frame.paragraphs[0].alignment = PP_ALIGN.CENTER

    # Add objective
    obj_box = title_slide.shapes.add_textbox(Inches(1), Inches(4), Inches(8), Inches(1))
    obj_frame = obj_box.text_frame
    obj_frame.text = f"教学目标：{plan_data.get('objective', '')}"
    obj_frame.paragraphs[0].font.size = Pt(20)
    obj_frame.paragraphs[0].alignment = PP_ALIGN.CENTER

    # Content slides for each section
    sections = plan_data.get("sections", [])
    for section in sections:
        slide = prs.slides.add_slide(prs.slide_layouts[6])  # Blank layout

        # Section title
        title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.5), Inches(9), Inches(1))
        title_frame = title_box.text_frame
        title_frame.text = section.get("title", "")
        title_frame.paragraphs[0].font.size = Pt(36)
        title_frame.paragraphs[0].font.bold = True

        # Duration
        duration_box = slide.shapes.add_textbox(Inches(0.5), Inches(1.5), Inches(2), Inches(0.5))
        duration_frame = duration_box.text_frame
        duration_frame.text = f"⏱ {section.get('duration_minutes', 0)}分钟"
        duration_frame.paragraphs[0].font.size = Pt(14)

        # Activity content
        content_box = slide.shapes.add_textbox(Inches(0.5), Inches(2.2), Inches(9), Inches(3))
        content_frame = content_box.text_frame
        content_frame.word_wrap = True
        content_frame.text = f"【活动】{section.get('activity', '')}\n\n"
        content_frame.text += f"【方法】{section.get('teaching_method', '')}\n\n"
        content_frame.text += f"【预期成果】{section.get('expected_outcome', '')}"

        # Format content
        for paragraph in content_frame.paragraphs:
            paragraph.font.size = Pt(16)

    # End slide
    end_slide = prs.slides.add_slide(prs.slide_layouts[6])
    end_box = end_slide.shapes.add_textbox(Inches(1), Inches(3), Inches(8), Inches(2))
    end_frame = end_box.text_frame
    end_frame.text = "谢谢聆听！\nQuestions & Discussion"
    end_frame.paragraphs[0].font.size = Pt(40)
    end_frame.paragraphs[0].font.bold = True
    end_frame.paragraphs[0].alignment = PP_ALIGN.CENTER

    # Save PPT
    file_path = f"output/ppts/{ppt_id}.pptx"
    prs.save(file_path)

    return file_path


def get_slide_count(file_path: str) -> int:
    """Get number of slides in PPT."""
    prs = Presentation(file_path)
    return len(prs.slides)
