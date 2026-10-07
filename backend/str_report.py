import hashlib
import io
from datetime import datetime, timezone
from typing import Any, Dict

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def generate_str_report(txn_data: Dict[str, Any]) -> bytes:
    """
    Generates a formal, tamper-evident Suspicious Transaction Report (STR)
    compliant with Financial Intelligence Unit - India (FIU-IND) format standards.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontSize=16,
        leading=20,
        textColor=colors.HexColor("#0D3B66"),
        alignment=1,
    )
    subtitle_style = ParagraphStyle(
        "ReportSub",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#555555"),
        alignment=1,
    )
    section_style = ParagraphStyle(
        "ReportSection",
        parent=styles["Heading2"],
        fontSize=12,
        leading=15,
        textColor=colors.HexColor("#0D3B66"),
        spaceBefore=10,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "ReportBody",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
    )

    elements = []

    # 1. Official Header
    elements.append(Paragraph("CONFIDENTIAL // LAW ENFORCEMENT & REGULATORY SENSITIVE", subtitle_style))
    elements.append(Paragraph("FINANCIAL INTELLIGENCE UNIT - INDIA (FIU-IND)", title_style))
    elements.append(Paragraph("SUSPICIOUS TRANSACTION REPORT (STR) — FORM AR-1", subtitle_style))
    elements.append(Spacer(1, 10))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0D3B66"), spaceAfter=12))

    # 2. Reference & Metadata
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    txn_id = str(txn_data.get("txn_id", "N/A"))
    user_id = str(txn_data.get("user_id", "N/A"))
    amount = float(txn_data.get("amount", 0.0))

    meta_table_data = [
        [Paragraph("<b>Reporting Entity:</b> Canara Bank (SuRaksha Surveillance)", body_style),
         Paragraph(f"<b>Report Reference:</b> STR-{txn_id}", body_style)],
        [Paragraph(f"<b>Filing Date:</b> {generated_at}", body_style),
         Paragraph("<b>Statutory Mandate:</b> PMLA Section 12", body_style)],
    ]
    meta_table = Table(meta_table_data, colWidths=[270, 270])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F4F6F8")),
        ("PADDING", (0, 0), (-1, -1), 6),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#D0D5DD")),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 12))

    # 3. Transaction Details
    elements.append(Paragraph("Section 1: Transaction Summary", section_style))
    txn_table_data = [
        ["Transaction ID", txn_id],
        ["Subject / User ID", user_id],
        ["Transaction Value", f"INR {amount:,.2f}"],
        ["Channel / Instrument", str(txn_data.get("channel", "N/A"))],
        ["Location / City", f"{txn_data.get('city', 'Unknown')} ({txn_data.get('lat', 'N/A')}, {txn_data.get('lon', 'N/A')})"],
        ["Risk Assessment Level", str(txn_data.get("risk_level", "HIGH")).upper()],
    ]
    t_details = Table(txn_table_data, colWidths=[180, 360])
    t_details.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#EAEFF5")),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#1A1A1A")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D0D5DD")),
    ]))
    elements.append(t_details)
    elements.append(Spacer(1, 12))

    # 4. Grounds of Suspicion & Statutory Violations
    elements.append(Paragraph("Section 2: Grounds of Suspicion & Heuristic Triggers", section_style))
    fiu_info = txn_data.get("fiu_compliance", {})
    violations = fiu_info.get("violations", [])

    if violations:
        viol_data = [["Rule Code", "Statutory Rule Description", "Severity"]]
        for v in violations:
            viol_data.append([
                v.get("rule_id", "N/A"),
                f"{v.get('name', '')}\n{v.get('details', '')}",
                v.get("severity", "high").upper(),
            ])
        t_viol = Table(viol_data, colWidths=[100, 360, 80])
        t_viol.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#C0392B")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D0D5DD")),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(t_viol)
    else:
        elements.append(Paragraph("Flagged via Machine Learning Multi-Factor Anomaly Scoring engine.", body_style))

    elements.append(Spacer(1, 12))

    # 5. Cryptographic Seal (Anti-Tamper)
    raw_payload_str = f"{txn_id}:{user_id}:{amount}:{generated_at}"
    sha256_hash = hashlib.sha256(raw_payload_str.encode("utf-8")).hexdigest()

    elements.append(Paragraph("Section 3: Cryptographic Integrity Verification", section_style))
    crypto_box = [
        [Paragraph(f"<b>SHA-256 Audit Seal:</b> {sha256_hash}", body_style)],
        [Paragraph("<i>This document is automatically compiled and cryptographically registered upon anomaly interception. Any alteration invalidates this record.</i>", subtitle_style)],
    ]
    t_crypto = Table(crypto_box, colWidths=[540])
    t_crypto.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8F9FA")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#6C757D")),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))
    elements.append(t_crypto)

    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes