"""
AgriSpark 2.0 — PDF Farm Plan Generator
Builds a professional, branded PDF using ReportLab.
"""

import os
import uuid
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT

import config

# ─── Brand Colours ────────────────────────────────────────────────────────────
GREEN_DARK  = colors.HexColor("#1B4332")
GREEN_MID   = colors.HexColor("#40916C")
GREEN_LIGHT = colors.HexColor("#D8F3DC")
GOLD        = colors.HexColor("#F4A261")
WHITE       = colors.white
GREY_TEXT   = colors.HexColor("#4A4A4A")


def _styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("title", fontName="Helvetica-Bold",
                                fontSize=24, textColor=WHITE,
                                spaceAfter=8, alignment=TA_CENTER),
        "subtitle": ParagraphStyle("subtitle", fontName="Helvetica-Bold",
                                   fontSize=14, textColor=GOLD,
                                   spaceAfter=6, alignment=TA_CENTER),
        "section": ParagraphStyle("section", fontName="Helvetica-Bold",
                                  fontSize=15, textColor=colors.HexColor("#0D3B16"),
                                  spaceBefore=16, spaceAfter=6),
        "body": ParagraphStyle("body", fontName="Helvetica",
                               fontSize=11, textColor=GREY_TEXT,
                               spaceAfter=6, leading=16),
        "small": ParagraphStyle("small", fontName="Helvetica",
                                fontSize=9, textColor=GREY_TEXT,
                                alignment=TA_CENTER),
    }


def generate_pdf(profile: dict, plan_text: str, lang: str = "EN") -> str:
    """
    Generate a PDF farm plan and return the absolute file path.
    profile: dict with farmer fields
    plan_text: full AI-generated advisory text
    lang: 'EN' or 'TH'
    """
    os.makedirs(config.PDF_DIR, exist_ok=True)
    farmer_id = str(uuid.uuid4())[:8]
    filename  = f"agrispark_plan_{farmer_id}.pdf"
    filepath  = os.path.join(config.PDF_DIR, filename)

    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
    )

    st  = _styles()
    story = []

    # ── Header Banner ────────────────────────────────────────────────────────
    header_data = [[
        Paragraph("🌾 AGRISPARK MASTER ADVISORY", st["title"]),
    ]]
    header_table = Table(header_data, colWidths=[17*cm])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#0D361F")), # High-Authority Dark Green
        ("TOPPADDING",    (0, 0), (-1, -1), 22),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 18),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("ROUNDEDCORNERS", [8]),
    ]))
    story.append(header_table)

    subtitle = ("MISSION-CRITICAL FARM COMMANDS" if lang == "EN"
                else "คำสั่งการทำฟาร์มที่สำคัญยิ่ง")
    story.append(Paragraph(subtitle, st["subtitle"]))
    story.append(Spacer(1, 0.4*cm))

    # ── Date & ID ────────────────────────────────────────────────────────────
    date_str = datetime.now().strftime("%d %B %Y")
    story.append(Paragraph(f"GENRATED: {date_str}  |  ARCHIVE ID: {farmer_id}", st["small"]))
    story.append(HRFlowable(width="100%", thickness=2.5, color=GREEN_DARK, spaceAfter=12))

    # ── Farmer Profile Table ──────────────────────────────────────────────────
    heading = "FARMER PROFILE" if lang == "EN" else "ข้อมูลเกษตรกร"
    story.append(Paragraph(heading, st["section"]))

    labels_en = ["Name", "Location", "Past Crop", "Planned Crop", "Soil Type", "Terrain"]
    labels_th = ["ชื่อ", "ที่ตั้ง", "พืชที่ผ่านมา", "พืชที่วางแผน", "ประเภทดิน", "สภาพพื้นที่"]
    labels = labels_th if lang == "TH" else labels_en
    fields = ["name", "location", "past_crop", "current_crop", "soil_type", "terrain"]

    table_data = [[
        Paragraph(f"<b>{lbl}</b>", st["body"]),
        Paragraph(str(profile.get(f, "—")), st["body"])
    ] for lbl, f in zip(labels, fields)]

    profile_table = Table(table_data, colWidths=[5*cm, 12*cm])
    profile_table.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (0, -1), GREEN_LIGHT),
        ("GRID",         (0, 0), (-1, -1), 0.5, GREEN_MID),
        ("TOPPADDING",   (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 6),
        ("LEFTPADDING",  (0, 0), (-1, -1), 8),
    ]))
    story.append(profile_table)
    story.append(Spacer(1, 0.4*cm))

    # ── AI Plan Content ───────────────────────────────────────────────────────
    plan_heading = "YOUR FARM ADVISORY PLAN" if lang == "EN" else "แผนการเกษตรของคุณ"
    story.append(HRFlowable(width="100%", thickness=1, color=GREEN_MID, spaceAfter=6))
    story.append(Paragraph(plan_heading, st["section"]))

    # 🧩 ADVANCED PARSER: Handle Tables & Paragraphs
    lines = plan_text.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            story.append(Spacer(1, 0.2*cm))
            i += 1
            continue
            
        # 🧪 TABLE DETECTOR: Detect Markdown Tables (starts with |)
        if line.startswith("|") and i + 1 < len(lines) and lines[i+1].strip().replace(" ", "").startswith("|-"):
            table_data = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                # Clean row and split by |
                row = [Paragraph(cell.strip().replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"), st["body"]) 
                       for cell in lines[i].strip().strip("|").split("|")]
                
                # Skip the separator line (e.g., |---|---|)
                if not all(c.strip().startswith("-") for c in lines[i].strip().strip("|").split("|")):
                    table_data.append(row)
                i += 1
            
            if table_data:
                # Create a professional looking table
                grid_table = Table(table_data, colWidths=[2.5*cm, 4*cm, 10.5*cm])
                grid_table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), GREEN_LIGHT),
                    ("TEXTCOLOR", (0, 0), (-1, 0), GREEN_DARK),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 0.5, GREEN_MID),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]))
                story.append(grid_table)
            continue

        # Clear Markdown syntax and clean para
        # 1. Escape HTML basics
        clean_para = (line.replace("&", "&amp;")
                         .replace("<", "&lt;")
                         .replace(">", "&gt;"))
                         
        # 2. Convert Bold **Text** to <b>Text</b>
        import re
        clean_para = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', clean_para)
        
        # 3. Preserve Indents
        clean_para = clean_para.replace("  ", "&nbsp;&nbsp;")
                         
        if clean_para.startswith("#"):
            # Header handling
            level = clean_para.count("#")
            text = clean_para.replace("#", "").strip()
            story.append(Paragraph(f"<b>{text}</b>", st["section"]))
        elif clean_para.isupper() and len(clean_para) > 3:
            story.append(Paragraph(clean_para, st["section"]))
        else:
            story.append(Paragraph(clean_para, st["body"]))
        i += 1

    # ── Footer ───────────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.6*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=GREEN_MID, spaceAfter=6))
    footer_text = ("AgriSpark 2.0 — AI Agricultural Advisory for Southeast Asia | "
                   "WhatsApp your questions anytime for ongoing support.")
    story.append(Paragraph(footer_text, st["small"]))

    doc.build(story)
    return filepath


def get_pdf_url(filepath: str) -> str:
    """Convert local path to public URL for WhatsApp delivery."""
    filename = os.path.basename(filepath)
    base = config.BASE_URL.strip("/")
    
    # 🕵️‍♂️ SMART PROTOCOL: Ensure the URL has http/https
    if base and not (base.startswith("http://") or base.startswith("https://")):
        # Default to https for security unless it's localhost
        if "localhost" in base or "127.0.0.1" in base:
            base = f"http://{base}"
        else:
            base = f"https://{base}"
            
    return f"{base}/static/pdf/{filename}"
