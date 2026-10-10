from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

SOURCE = "DermTrack_Project_Review_Intro_Problem.pptx"
OUT = "DermTrack_Project_Review_With_Literature.pptx"
prs = Presentation(SOURCE)

navy = RGBColor(10, 25, 47)
navy2 = RGBColor(16, 42, 67)
teal = RGBColor(35, 194, 176)
coral = RGBColor(255, 126, 103)
white = RGBColor(246, 250, 252)
muted = RGBColor(181, 204, 213)
line = RGBColor(52, 91, 111)
soft = RGBColor(222, 237, 240)


def textbox(slide, text, x, y, w, h, size=16, color=white, bold=False,
            font="Aptos", align=PP_ALIGN.LEFT, valign=MSO_ANCHOR.TOP, margin=0):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame; tf.clear(); tf.margin = margin; tf.vertical_anchor = valign; tf.word_wrap = True
    p = tf.paragraphs[0]; p.text = text; p.alignment = align
    p.font.name = font; p.font.size = Pt(size); p.font.color.rgb = color; p.font.bold = bold
    return box


def header(slide, section, title, number):
    slide.background.fill.solid(); slide.background.fill.fore_color.rgb = navy
    textbox(slide, section.upper(), 0.72, 0.46, 4.5, 0.25, 10, teal, True)
    textbox(slide, title, 0.72, 0.78, 9.4, 0.6, 28, white, True, "Aptos Display")
    textbox(slide, f"0{number}  /  DERMTRACK AGENT", 10.1, 0.52, 2.5, 0.25, 9, muted, True, align=PP_ALIGN.RIGHT)
    a = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.72), Inches(1.53), Inches(0.72), Inches(0.06))
    a.fill.solid(); a.fill.fore_color.rgb = coral; a.line.fill.background()


def card(slide, x, y, w, h, title, body, accent=teal):
    shp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    shp.fill.solid(); shp.fill.fore_color.rgb = navy2; shp.line.color.rgb = line; shp.line.width = Pt(1)
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(0.08), Inches(h))
    bar.fill.solid(); bar.fill.fore_color.rgb = accent; bar.line.fill.background()
    textbox(slide, title, x+0.28, y+0.24, w-0.48, 0.25, 11, accent, True)
    textbox(slide, body, x+0.28, y+0.62, w-0.48, h-0.80, 14, white, True)


def add_table_slide(slide, table_title, subtitle, rows, slide_no):
    header(slide, "Literature review", table_title, slide_no)
    textbox(slide, subtitle, 0.72, 1.69, 11.85, 0.34, 10.5, muted)
    x, y, w, h = 0.55, 2.18, 12.23, 3.95
    cols = [1.62, 1.75, 1.95, 2.48, 1.92, 2.51]
    table = slide.shapes.add_table(len(rows)+1, 6, Inches(x), Inches(y), Inches(w), Inches(h)).table
    for i, cw in enumerate(cols): table.columns[i].width = Inches(cw)
    headers = ["Paper", "Method", "Dataset / evaluation", "Major findings", "Performance / evidence", "Limitations"]
    for c, text in enumerate(headers):
        cell = table.cell(0,c); cell.text = text; cell.fill.solid(); cell.fill.fore_color.rgb = RGBColor(20, 67, 80)
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        for p in cell.text_frame.paragraphs:
            p.font.name='Aptos'; p.font.size=Pt(10); p.font.bold=True; p.font.color.rgb=white
            p.alignment=PP_ALIGN.LEFT
        cell.margin_left=Inches(0.08); cell.margin_right=Inches(0.06); cell.margin_top=Inches(0.04); cell.margin_bottom=Inches(0.04)
    for r, row in enumerate(rows,1):
        for c, text in enumerate(row):
            cell=table.cell(r,c); cell.text=text; cell.vertical_anchor=MSO_ANCHOR.TOP
            cell.fill.solid(); cell.fill.fore_color.rgb = navy2 if r%2 else RGBColor(19, 51, 76)
            cell.margin_left=Inches(0.08); cell.margin_right=Inches(0.06); cell.margin_top=Inches(0.06); cell.margin_bottom=Inches(0.04)
            for p in cell.text_frame.paragraphs:
                p.font.name='Aptos'; p.font.size=Pt(8.4); p.font.color.rgb=white; p.alignment=PP_ALIGN.LEFT
                p.space_after=Pt(0)
    # table borders
    for row in table.rows:
        for cell in row.cells:
            for border in ('top','bottom','left','right'):
                ln = getattr(cell, f'_tc').get_or_add_tcPr()
            
    textbox(slide, "Comparison is based on the selected source's stated task and evaluation setting; benchmark success is not equivalent to clinical validation.", 0.72, 6.43, 11.85, 0.30, 9.5, muted, False, align=PP_ALIGN.CENTER)

# Slide 4: review strategy
slide = prs.slides.add_slide(prs.slide_layouts[6])
header(slide, "Literature review", "How the evidence was selected", 4)
textbox(slide, "The review connects DermTrack's implementation choices to research on dermatology AI, evidence grounding, fairness, and safe deployment.", 0.72, 1.70, 11.7, 0.40, 14, muted)

card(slide, 0.72, 2.35, 3.72, 1.65, "01  DOMAIN EVIDENCE", "Dermatology image AI and multimodal models\n\nQuestion: How well do image-based systems generalize?", teal)
card(slide, 4.80, 2.35, 3.72, 1.65, "02  SYSTEM METHOD", "RAG and medical language models\n\nQuestion: How can responses be grounded in external knowledge?", coral)
card(slide, 8.88, 2.35, 3.72, 1.65, "03  SAFETY + FAIRNESS", "Bias, explainability, and governance\n\nQuestion: What must the system avoid claiming?", teal)

textbox(slide, "SELECTED SOURCE SET", 0.72, 4.48, 2.3, 0.25, 10, coral, True)
textbox(slide, "Liu 2020  ·  Daneshjou 2022  ·  Yan 2025  ·  Zhou 2024\nLewis 2020  ·  Xiong 2024  ·  Zakka 2024  ·  WHO 2021", 0.72, 4.82, 8.8, 0.70, 19, white, True)

rounded = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(9.75), Inches(4.45), Inches(2.85), Inches(1.18))
rounded.fill.solid(); rounded.fill.fore_color.rgb = RGBColor(54, 49, 64); rounded.line.color.rgb = RGBColor(111,82,91)
textbox(slide, "LITERATURE RUBRIC", 10.05, 4.70, 2.2, 0.22, 10, coral, True)
textbox(slide, "Paper → Method → Dataset → Findings → Performance → Limitations", 10.05, 5.05, 2.25, 0.42, 11.5, white, True)
textbox(slide, "Peer-reviewed research is separated from surveys and organizational guidance.", 0.72, 6.44, 11.85, 0.25, 9.5, muted, False, align=PP_ALIGN.CENTER)

# Slide 5: dermatology table
slide = prs.slides.add_slide(prs.slide_layouts[6])
rows_a = [
    ["Liu et al.\nNature Medicine (2020)", "Deep-learning differential diagnosis from clinical skin images.", "Clinical dermatology image datasets; internal and external evaluation.", "Shows the feasibility of automated differential diagnosis across multiple skin conditions.", "Strong reported image-classification results; clinician comparison included.", "Dataset shift, image quality, subgroup coverage, and diagnosis-risk concerns."],
    ["Daneshjou et al.\nScience Advances (2022)", "Evaluates dermatology AI across skin-tone groups using a curated clinical set.", "DDI: Diverse Dermatology Images dataset; subgroup evaluation.", "Performance disparities were observed across skin-tone groups.", "Demonstrates that aggregate performance can hide subgroup underperformance.", "Limited dataset size and representativeness; benchmark fairness ≠ clinical fairness."],
    ["Yan et al.\nNature Medicine (2025)", "Multimodal vision foundation model for clinical dermatology.", "Multi-source dermatology image–text evaluations; model and clinician tasks.", "Shows the promise of foundation-model transfer across dermatology tasks.", "Reports benchmark and clinician-oriented evaluations; exact metrics require full-text extraction.", "Foundation-model opacity, dataset bias, hallucination, and prospective validation needs."],
    ["Zhou et al.\nNature Communications (2024)", "Pre-trained multimodal LLM, SkinGPT-4, for dermatology image–text reasoning.", "Dermatology image–text data and diagnostic evaluation tasks.", "Demonstrates multimodal generation for dermatological descriptions and predictions.", "Reports diagnostic and generation evaluations; not evidence of autonomous clinical safety.", "Possible hallucinations, limited generalization, and diagnosis may overstate capability."],
]
add_table_slide(slide, "Dermatology AI: methods and evidence", "These papers establish the opportunity while highlighting generalization, skin-tone fairness, and diagnostic-risk concerns.", rows_a, 5)

# Slide 6: RAG and safety table
slide = prs.slides.add_slide(prs.slide_layouts[6])
rows_b = [
    ["Lewis et al.\nNeurIPS (2020)", "Retrieval-Augmented Generation combines a retriever with a generator.", "Knowledge-intensive NLP benchmarks including open-domain QA tasks.", "External evidence can complement parametric model knowledge.", "RAG improved results on several knowledge-intensive tasks in the original study.", "Retrieval quality, stale sources, irrelevant context, and unsupported synthesis."],
    ["Xiong et al.\nFindings of ACL (2024)", "Medical RAG with domain retrievers, knowledge bases, and context construction.", "MedQA, MedMCQA, PubMedQA, and other medical QA benchmarks.", "Medical retrieval often improves QA, but configuration and corpus choice matter.", "Benchmark accuracy improves in many RAG settings; not a clinical-safety metric.", "Multiple-choice benchmarks do not measure triage, calibration, or patient harm."],
    ["Zakka et al.\nNEJM AI (2024)", "Almanac: LLM connected to retrieved medical references and clinical tools.", "Medical QA benchmarks plus expert assessment.", "Grounding can improve factual support and clinical answer quality.", "Reported gains over standalone generation in evaluated medical tasks.", "Corpus coverage, retrieval errors, limited expert evaluation, and no deployment validation."],
    ["WHO (2021)\nGovernance report", "Ethical and governance framework for AI in health.", "No experimental dataset; evidence synthesis and expert consultation.", "Calls for human control, transparency, privacy, equity, and accountability.", "No numerical performance; provides safety and governance requirements.", "Normative guidance must be translated into concrete product controls and audits."],
]
add_table_slide(slide, "RAG, clinical AI, and governance", "These sources support DermTrack's grounded, privacy-conscious, non-diagnostic and human-supervised design.", rows_b, 6)

prs.core_properties.title = "DermTrack Agent — Literature Review"
prs.core_properties.subject = "Literature review comparison slides"
prs.save(OUT)
print(OUT)
