"""
Generates a fee voucher PDF containing TWO copies on one A4 page:
  - Top half:    OFFICE COPY
  - Bottom half: STUDENT COPY
Built with reportlab only (no external binaries required).
"""
from io import BytesIO
import html
from datetime import datetime
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


def _draw_slip(c, x, y, width, height, payment, student, dev, college_name, copy_label, student_total_due):
    """Draw a single voucher slip with its top-left corner at (x, y - height)."""
    top = y
    left = x
    right = x + width

    # Outer border
    c.setLineWidth(1.2)
    c.rect(left, top - height, width, height)

    cursor = top - 7 * mm

    # Copy label (top right, small)
    c.setFont("Helvetica-Bold", 7)
    c.drawRightString(right - 4 * mm, top - 5 * mm, copy_label)

    # Header
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(left + width / 2, cursor, college_name)
    cursor -= 4.5 * mm
    if dev.get("affiliation"):
        c.setFont("Helvetica", 7)
        c.drawCentredString(left + width / 2, cursor, dev["affiliation"])
        cursor -= 3 * mm
    c.setLineWidth(0.8)
    c.line(left + 4 * mm, cursor, right - 4 * mm, cursor)
    cursor -= 4.5 * mm

    # Meta row: date / candidate no
    c.setFont("Helvetica", 8)
    today_str = payment["due_date"] or ""
    c.drawString(left + 4 * mm, cursor, f"Date: {payment['due_date'] or '-'}")
    c.drawRightString(right - 4 * mm, cursor, f"Candidate No: {student['candidate_no'] or '-'}")
    cursor -= 4.5 * mm

    # Student info
    c.setFont("Helvetica-Bold", 8)
    c.drawString(left + 4 * mm, cursor, f"Student Name: {student['name']}")
    cursor -= 4 * mm
    c.drawString(left + 4 * mm, cursor, f"Father Name: {student['father_name'] or '-'}")
    cursor -= 4 * mm
    course_line = f"Program: {student['course_name'] or '-'}   |   Duration: {student['course_duration'] or '-'}"
    c.drawString(left + 4 * mm, cursor, course_line)
    cursor -= 5 * mm

    # Table
    col_widths = [12 * mm, width - 12 * mm - 30 * mm - 8 * mm, 30 * mm]
    row_h = 5.4 * mm
    table_top = cursor
    table_left = left + 4 * mm

    rows = [
        ("S.No", "Particulars", "Amount (Rs.)"),
        ("1", "ID Card Fee", f"{payment['id_card_fee']:.0f}" if payment["id_card_fee"] else "---"),
        ("2", f"Tuition Fee (Installment {payment['installment_no']} of {student['installment_count']})",
         f"{payment['tuition_amount']:.0f}"),
        ("3", "DMC", f"{payment['dmc_fee']:.0f}" if payment["dmc_fee"] else "---"),
        ("4", "Exam Fee", f"{payment['exam_fee']:.0f}" if payment["exam_fee"] else "---"),
        ("5", "Fund Fee", f"{payment['fund_fee']:.0f}" if payment["fund_fee"] else "---"),
    ]
    total = (payment["tuition_amount"] + payment["id_card_fee"] + payment["dmc_fee"]
             + payment["exam_fee"] + payment["fund_fee"])
    paid_amount = float(payment["paid_amount"] or 0)
    remaining_amount = max(total - paid_amount, 0)
    rows.append(("6", "Total", f"{total:.0f}"))
    rows.append(("7", "Paid Amount", f"{paid_amount:.0f}"))
    rows.append(("8", "Remaining Dues", f"{remaining_amount:.0f}"))

    c.setLineWidth(0.7)
    y_cursor = table_top
    for i, row in enumerate(rows):
        is_header = i == 0
        is_total = i == len(rows) - 1
        # row background for header
        if is_header:
            c.setFillColor(colors.whitesmoke)
            c.rect(table_left, y_cursor - row_h, sum(col_widths), row_h, fill=1, stroke=0)
            c.setFillColor(colors.black)

        xpos = table_left
        c.setFont("Helvetica-Bold" if (is_header or is_total) else "Helvetica", 7.5)
        for ci, (text, cw) in enumerate(zip(row, col_widths)):
            c.rect(xpos, y_cursor - row_h, cw, row_h, fill=0, stroke=1)
            if ci == 1:
                c.drawString(xpos + 1.5 * mm, y_cursor - row_h + 2 * mm, str(text)[:48])
            else:
                c.drawCentredString(xpos + cw / 2, y_cursor - row_h + 2 * mm, str(text))
            xpos += cw
        y_cursor -= row_h

    cursor = y_cursor - 4 * mm

    # Footer info
    c.setFont("Helvetica", 7.5)
    paid_status = "PAID" if payment["paid"] else ("PARTIAL" if paid_amount > 0 else "UNPAID")
    c.drawString(left + 4 * mm, cursor,
                 f"Installment: {payment['installment_no']} of {student['installment_count']}   "
                 f"Status: {paid_status}")
    c.drawRightString(right - 4 * mm, cursor, f"Due Date: {payment['due_date'] or '-'}")
    cursor -= 4 * mm
    c.drawString(left + 4 * mm, cursor, f"Student Remaining Dues: Rs. {student_total_due:.0f}")
    cursor -= 6 * mm

    # Signature area
    c.setLineWidth(0.6)
    c.line(left + 8 * mm, cursor, left + 38 * mm, cursor)
    c.line(right - 38 * mm, cursor, right - 8 * mm, cursor)
    cursor -= 3 * mm
    c.setFont("Helvetica", 6.5)
    c.drawCentredString(left + 23 * mm, cursor, "Student Sign")
    c.drawCentredString(right - 23 * mm, cursor, "Accountant Stamp")
    cursor -= 4 * mm

    c.setFont("Helvetica-Bold", 6.5)
    c.drawCentredString(left + width / 2, cursor, "FEE ONCE PAID WILL NOT BE RETURNED IN ANY CASE")
    cursor -= 3.5 * mm

    c.setFont("Helvetica-Bold", 6.5)
    admin_display = dev.get("admin_display") or (" / ".join(dev.get("admin_contacts") or [])) or "Rashid Zada (0347-0983567)"
    c.drawCentredString(left + width / 2, cursor, f"Admin Contact: {admin_display}")
    cursor -= 3.5 * mm

    c.setFont("Helvetica-Oblique", 6.5)
    c.drawCentredString(
        left + width / 2, cursor,
        f"Need software like this? Contact {dev['name']} ({dev['title']}) - WhatsApp: {dev['whatsapp_display']}"
    )


def build_voucher_pdf(payment, student, dev, college_name, student_total_due=0):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    page_w, page_h = A4

    margin = 10 * mm
    slip_w = page_w - 2 * margin
    slip_h = (page_h - 3 * margin) / 2

    # Office copy (top)
    _draw_slip(c, margin, page_h - margin, slip_w, slip_h, payment, student, dev, college_name, "OFFICE COPY", student_total_due)
    # dashed cut line
    c.setDash(3, 3)
    c.setLineWidth(0.5)
    mid_y = page_h - margin - slip_h - (margin / 2)
    c.line(margin, mid_y, page_w - margin, mid_y)
    c.setDash()

    # Student copy (bottom)
    _draw_slip(c, margin, page_h - margin - slip_h - margin, slip_w, slip_h, payment, student, dev, college_name, "STUDENT COPY", student_total_due)

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer


def _get_row_value(row, key, default=""):
    try:
        if isinstance(row, dict):
            return row.get(key, default)
        return row[key] if row[key] is not None else default
    except Exception:
        return default


def build_clearance_pdf(student, payments, total_payable, total_paid, total_due, dev, college_name):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    page_w, page_h = A4
    margin = 18 * mm
    y = page_h - margin

    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(page_w / 2, y, college_name)
    y -= 8 * mm

    c.setFont("Helvetica", 9)
    affiliation = dev.get("affiliation") or ""
    c.drawCentredString(page_w / 2, y, f"{affiliation}")
    y -= 6 * mm
    c.line(margin, y, page_w - margin, y)
    y -= 8 * mm

    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin, y, "Fee Clearance Slip")
    c.setFont("Helvetica", 9)
    status = "CLEARED" if float(total_due or 0) <= 0 else "DUES REMAINING"
    c.drawRightString(page_w - margin, y, f"Status: {status}")
    y -= 10 * mm

    student_info = [
        ("Student Name", _get_row_value(student, "name", "-")),
        ("Candidate No", _get_row_value(student, "candidate_no", "-")),
        ("Father Name", _get_row_value(student, "father_name", "-")),
        ("Program", _get_row_value(student, "course_name", "-")),
        ("Duration", _get_row_value(student, "course_duration", "-")),
        ("Teacher", _get_row_value(student, "teacher_name", "-")),
    ]
    c.setFont("Helvetica", 8.5)
    for label, value in student_info:
        c.drawString(margin, y, f"{label}: {value}")
        y -= 5.5 * mm

    y -= 2 * mm
    c.setFont("Helvetica-Bold", 9)
    c.drawString(margin, y, "Payment Summary")
    y -= 6 * mm
    c.setFont("Helvetica", 8.5)
    c.drawString(margin, y, f"Total Payable: PKR {float(total_payable or 0):.0f}")
    c.drawString(page_w / 2 + 10 * mm, y, f"Total Paid: PKR {float(total_paid or 0):.0f}")
    c.drawRightString(page_w - margin, y, f"Total Due: PKR {float(total_due or 0):.0f}")
    y -= 10 * mm

    # Table header
    col_widths = [18 * mm, 22 * mm, 18 * mm, 18 * mm, 18 * mm, 18 * mm, 18 * mm, 20 * mm]
    table_x = margin
    row_h = 7 * mm
    c.setLineWidth(0.6)
    c.setFont("Helvetica-Bold", 8)

    headers = ["Inst", "Due Date", "Tuition", "ID Card", "DMC", "Exam", "Fund", "Remaining"]
    x = table_x
    for hdr, width in zip(headers, col_widths):
        c.rect(x, y - row_h, width, row_h, stroke=1, fill=1)
        c.setFillColor(colors.black)
        c.drawCentredString(x + width / 2, y - 5 * mm, hdr)
        x += width
    y -= row_h

    c.setFont("Helvetica", 8)
    for payment in payments:
        if y < margin + row_h * 3:
            c.showPage()
            y = page_h - margin
            c.setFont("Helvetica-Bold", 8)
            x = table_x
            for hdr, width in zip(headers, col_widths):
                c.rect(x, y - row_h, width, row_h, stroke=1, fill=1)
                c.setFillColor(colors.black)
                c.drawCentredString(x + width / 2, y - 5 * mm, hdr)
                x += width
            y -= row_h
            c.setFont("Helvetica", 8)

        tuition = float(_get_row_value(payment, "tuition_amount", 0) or 0)
        id_card = float(_get_row_value(payment, "id_card_fee", 0) or 0)
        dmc = float(_get_row_value(payment, "dmc_fee", 0) or 0)
        exam = float(_get_row_value(payment, "exam_fee", 0) or 0)
        fund = float(_get_row_value(payment, "fund_fee", 0) or 0)
        paid = float(_get_row_value(payment, "paid_amount", 0) or 0)
        total = tuition + id_card + dmc + exam + fund
        remaining = max(total - paid, 0)
        row_values = [
            str(_get_row_value(payment, "installment_no", "-")),
            _get_row_value(payment, "due_date", "-"),
            f"{tuition:.0f}",
            f"{id_card:.0f}",
            f"{dmc:.0f}",
            f"{exam:.0f}",
            f"{fund:.0f}",
            f"{remaining:.0f}",
        ]
        x = table_x
        for text, width in zip(row_values, col_widths):
            c.rect(x, y - row_h, width, row_h, stroke=1, fill=0)
            c.drawCentredString(x + width / 2, y - 5 * mm, text)
            x += width
        y -= row_h

    y -= 10 * mm
    c.setFont("Helvetica-Bold", 8)
    c.drawString(margin, y, "Notes:")
    y -= 5 * mm
    c.setFont("Helvetica", 7.5)
    c.drawString(margin, y, "This document is issued for clearance verification purposes only.")
    y -= 5.5 * mm
    c.drawString(margin, y, "Please keep this slip safe and present it at the office if requested.")
    y -= 12 * mm

    c.setFont("Helvetica", 7)
    c.drawString(margin, y, f"Generated by: {dev.get('name') or '-'}")
    c.drawString(page_w / 2, y, f"Contact: {dev.get('whatsapp_display') or dev.get('whatsapp') or '-'}")
    y -= 5.5 * mm
    admin_display = dev.get("admin_display") or (", ".join(dev.get("admin_contacts") or [])) or "Rashid Zada (0347-0983567)"
    c.drawString(margin, y, f"Admin Contact: {admin_display}")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to compute and render total page numbers and running footer/header."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            page_w, page_h = landscape(A4)
            self.saveState()

            # Running footer rule
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.6)
            self.line(10 * mm, 12 * mm, page_w - 10 * mm, 12 * mm)

            # Running footer text
            self.setFont("Helvetica", 7.5)
            self.setFillColor(colors.HexColor("#64748b"))
            self.drawString(10 * mm, 7 * mm, "The Smart Skills Academy Qalagay — Fee Voucher & Student Management System")
            self.drawRightString(page_w - 10 * mm, 7 * mm, f"Page {self._pageNumber} of {num_pages}")

            self.restoreState()
            super().showPage()
        super().save()


def build_students_list_pdf(students, totals, dev, college_name, course_name=None, show_amounts=True):
    """
    Builds a professional, print-ready PDF containing either:
      - Full Fee Register (show_amounts=True): course fees, paid amounts, remaining dues, payment status, and dates.
      - Nominal / Attendance Roll (show_amounts=False): roll no, student name, father name, phone, course, teacher,
        admission date, and attendance / remarks column (hides all prices and fees).
    Can be filtered for a specific course or for all courses.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=10 * mm,
        rightMargin=10 * mm,
        topMargin=8 * mm,
        bottomMargin=15 * mm,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=17,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=2,
    )

    subtitle_style = ParagraphStyle(
        "DocSubTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=13,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#1e40af"),
        spaceAfter=3,
    )

    meta_style = ParagraphStyle(
        "DocMeta",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=10,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#475569"),
        spaceAfter=6,
    )

    story = []
    # 1. Academy Name on top
    c_name = html.escape(college_name or "The Smart Skills Academy Qalagay").upper()
    story.append(Paragraph(c_name, title_style))

    course_suffix = f" — {html.escape(course_name).upper()}" if course_name else ""
    if show_amounts:
        sub_text = f"STUDENTS REGISTER &amp; FEE PAYMENT STATUS REPORT{course_suffix}"
    else:
        sub_text = f"STUDENTS REGISTER &amp; NOMINAL ATTENDANCE ROLL (NO PRICES){course_suffix}"
    story.append(Paragraph(sub_text, subtitle_style))

    gen_time = datetime.now().strftime("%d-%b-%Y %I:%M %p")
    admin_display = html.escape(dev.get("admin_display") or "Rashid Zada (0347-0983567)")
    doc_type_label = "Official Student Fee Ledger" if show_amounts else "Official Class & Attendance Roll"
    story.append(Paragraph(
        f"Admin Contact: {admin_display} &nbsp;|&nbsp; Report Date: {gen_time} &nbsp;|&nbsp; {doc_type_label}",
        meta_style
    ))

    # 2. KPI / Summary Bar
    student_count = len(students)
    kpi_pstyle = lambda align=TA_CENTER: ParagraphStyle("kpi", fontName="Helvetica", alignment=align, fontSize=7, leading=9.5)

    if show_amounts:
        tot_pay = float(totals.get("total_payable") or 0)
        tot_paid = float(totals.get("total_paid") or 0)
        tot_dues = float(totals.get("dues_amount") or 0)
        recovery = (tot_paid / tot_pay * 100) if tot_pay > 0 else 0

        kpi_data = [
            [
                Paragraph(f"<b>Total Students</b><br/><font size=\"10\" color=\"#0f172a\"><b>{student_count} Enrolled</b></font>", kpi_pstyle()),
                Paragraph(f"<b>Total Course Payable</b><br/><font size=\"10\" color=\"#0f172a\"><b>Rs. {tot_pay:,.0f}</b></font>", kpi_pstyle()),
                Paragraph(f"<b>Total Amount Collected</b><br/><font size=\"10\" color=\"#15803d\"><b>Rs. {tot_paid:,.0f}</b></font>", kpi_pstyle()),
                Paragraph(f"<b>Total Outstanding Dues</b><br/><font size=\"10\" color=\"#b91c1c\"><b>Rs. {tot_dues:,.0f}</b></font>", kpi_pstyle()),
                Paragraph(f"<b>Recovery / Cleared Rate</b><br/><font size=\"10\" color=\"#1e40af\"><b>{recovery:.1f}% Collected</b></font>", kpi_pstyle()),
            ]
        ]
        kpi_col_widths = [55*mm, 55*mm, 55*mm, 55*mm, 57*mm]
    else:
        scope_text = html.escape(course_name) if course_name else "All Registered Courses"
        kpi_data = [
            [
                Paragraph(f"<b>Total Students</b><br/><font size=\"10\" color=\"#0f172a\"><b>{student_count} Enrolled</b></font>", kpi_pstyle()),
                Paragraph(f"<b>Course Scope</b><br/><font size=\"9.5\" color=\"#0f172a\"><b>{scope_text}</b></font>", kpi_pstyle()),
                Paragraph("<b>Report Type</b><br/><font size=\"9.5\" color=\"#1e40af\"><b>Attendance / Nominal Roll</b></font>", kpi_pstyle()),
                Paragraph("<b>Price Status</b><br/><font size=\"9.5\" color=\"#15803d\"><b>Fees Hidden (General Safe)</b></font>", kpi_pstyle()),
            ]
        ]
        kpi_col_widths = [60*mm, 85*mm, 70*mm, 62*mm]

    kpi_table = Table(kpi_data, colWidths=kpi_col_widths)
    kpi_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#cbd5e1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 3.5 * mm))

    # 3. Main Data Table (Printable width: 277 mm)
    th_style = ParagraphStyle("TH", fontName="Helvetica-Bold", fontSize=7.5, leading=9, textColor=colors.white, alignment=TA_CENTER)
    td_c = ParagraphStyle("TDC", fontName="Helvetica", fontSize=7, leading=8.5, alignment=TA_CENTER)
    td_l = ParagraphStyle("TDL", fontName="Helvetica", fontSize=7, leading=8.5, alignment=TA_LEFT)
    td_r = ParagraphStyle("TDR", fontName="Helvetica", fontSize=7, leading=8.5, alignment=TA_RIGHT)

    if show_amounts:
        col_widths = [8*mm, 22*mm, 36*mm, 34*mm, 46*mm, 21*mm, 24*mm, 24*mm, 25*mm, 37*mm]
        headers = ["#", "Candidate #", "Student Name", "Father Name", "Course / Program", "Date", "Payable", "Paid", "Remaining Dues", "Payment Status"]
        table_data = [[Paragraph(f"<b>{h}</b>", th_style) for h in headers]]

        if not students:
            empty_p = Paragraph("<i>No student records found for this selection.</i>", td_c)
            table_data.append([empty_p] + [Paragraph("", td_c) for _ in range(len(headers) - 1)])
        else:
            for idx, s in enumerate(students, 1):
                c_no = html.escape(str(_get_row_value(s, "candidate_no") or "-"))
                s_name = f"<b>{html.escape(str(_get_row_value(s, 'name', '-')))}</b>"
                f_name = html.escape(str(_get_row_value(s, "father_name") or "-"))
                c_name = html.escape(str(_get_row_value(s, "course_name") or "Unassigned"))

                adm_date = html.escape(str(_get_row_value(s, "admission_date") or "-"))
                last_paid = _get_row_value(s, "last_paid_date")
                next_due = _get_row_value(s, "next_due_date")

                pay = float(_get_row_value(s, "total_payable", 0) or 0)
                paid = float(_get_row_value(s, "total_paid", 0) or 0)
                dues = float(_get_row_value(s, "dues_amount", 0) or 0)

                date_str = adm_date
                if dues > 0 and next_due:
                    date_str = f"{adm_date}<br/><font size=\"6\" color=\"#b91c1c\">Due: {html.escape(str(next_due))}</font>"
                elif dues <= 0 and last_paid:
                    date_str = f"{adm_date}<br/><font size=\"6\" color=\"#15803d\">Paid: {html.escape(str(last_paid))}</font>"

                pending_inst = _get_row_value(s, "pending_installments", 0)
                paid_inst = _get_row_value(s, "paid_installments", 0)
                inst_count = _get_row_value(s, "installment_count", 1)

                paid_detail = f"Rs. {paid:,.0f}"
                if inst_count and inst_count > 1:
                    paid_detail += f"<br/><font size=\"6\" color=\"#64748b\">({paid_inst}/{inst_count} paid)</font>"

                dues_color = "#b91c1c" if dues > 0 else "#64748b"
                dues_detail = f"Rs. {dues:,.0f}"
                if dues > 0 and pending_inst:
                    dues_detail += f"<br/><font size=\"6\" color=\"#b91c1c\">({pending_inst} pending)</font>"

                if dues <= 0:
                    status_html = "<font color=\"#15803d\"><b>CLEARED</b></font><br/><font size=\"6\" color=\"#15803d\">Fully Paid</font>"
                elif paid > 0:
                    status_html = "<font color=\"#b45309\"><b>PARTIAL</b></font><br/><font size=\"6\" color=\"#b45309\">Installment Due</font>"
                else:
                    status_html = "<font color=\"#b91c1c\"><b>UNPAID</b></font><br/><font size=\"6\" color=\"#b91c1c\">No Payment</font>"

                table_data.append([
                    Paragraph(str(idx), td_c),
                    Paragraph(c_no, td_c),
                    Paragraph(s_name, td_l),
                    Paragraph(f_name, td_l),
                    Paragraph(c_name, td_l),
                    Paragraph(date_str, td_c),
                    Paragraph(f"Rs. {pay:,.0f}", td_r),
                    Paragraph(f"<font color=\"#15803d\"><b>{paid_detail}</b></font>", td_r),
                    Paragraph(f"<font color=\"{dues_color}\"><b>{dues_detail}</b></font>", td_r),
                    Paragraph(status_html, td_c),
                ])

            # Grand total row
            table_data.append([
                Paragraph("<b>TOTAL</b>", td_c),
                Paragraph(f"<b>{student_count} Students</b>", td_c),
                Paragraph("", td_l),
                Paragraph("", td_l),
                Paragraph("", td_l),
                Paragraph("", td_c),
                Paragraph(f"<b>Rs. {tot_pay:,.0f}</b>", td_r),
                Paragraph(f"<font color=\"#15803d\"><b>Rs. {tot_paid:,.0f}</b></font>", td_r),
                Paragraph(f"<font color=\"#b91c1c\"><b>Rs. {tot_dues:,.0f}</b></font>", td_r),
                Paragraph(f"<b>{recovery:.1f}% Recovery</b>", td_c),
            ])
    else:
        # WITHOUT PAYMENT (Nominal / Attendance List, No Prices)
        col_widths = [8*mm, 24*mm, 44*mm, 40*mm, 32*mm, 46*mm, 32*mm, 23*mm, 28*mm]
        headers = ["#", "Candidate #", "Student Name", "Father Name", "Phone / WhatsApp", "Course / Program", "Teacher", "Adm Date", "Attendance / Remarks"]
        table_data = [[Paragraph(f"<b>{h}</b>", th_style) for h in headers]]

        if not students:
            empty_p = Paragraph("<i>No student records found for this selection.</i>", td_c)
            table_data.append([empty_p] + [Paragraph("", td_c) for _ in range(len(headers) - 1)])
        else:
            for idx, s in enumerate(students, 1):
                c_no = html.escape(str(_get_row_value(s, "candidate_no") or "-"))
                s_name = f"<b>{html.escape(str(_get_row_value(s, 'name', '-')))}</b>"
                f_name = html.escape(str(_get_row_value(s, "father_name") or "-"))
                phone = html.escape(str(_get_row_value(s, "phone") or "-"))
                c_name = html.escape(str(_get_row_value(s, "course_name") or "Unassigned"))
                t_name = html.escape(str(_get_row_value(s, "teacher_name") or "-"))
                adm_date = html.escape(str(_get_row_value(s, "admission_date") or "-"))

                table_data.append([
                    Paragraph(str(idx), td_c),
                    Paragraph(c_no, td_c),
                    Paragraph(s_name, td_l),
                    Paragraph(f_name, td_l),
                    Paragraph(phone, td_c),
                    Paragraph(c_name, td_l),
                    Paragraph(t_name, td_l),
                    Paragraph(adm_date, td_c),
                    Paragraph("", td_c),  # Blank space for marking attendance or teacher remarks
                ])

            table_data.append([
                Paragraph("<b>TOTAL</b>", td_c),
                Paragraph(f"<b>{student_count} Students</b>", td_c),
                Paragraph("", td_l),
                Paragraph("", td_l),
                Paragraph("", td_c),
                Paragraph("", td_l),
                Paragraph("", td_l),
                Paragraph("", td_c),
                Paragraph("<b>Nominal Roll</b>", td_c),
            ])

    main_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    t_style = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a8a")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 2.2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.2),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#e2e8f0")),
    ]

    for r_idx in range(1, len(table_data) - 1):
        if r_idx % 2 == 0:
            t_style.append(("BACKGROUND", (0, r_idx), (-1, r_idx), colors.HexColor("#f8fafc")))

    main_table.setStyle(TableStyle(t_style))
    story.append(main_table)
    story.append(Spacer(1, 6 * mm))

    # 4. Signatures / Verification row
    sig_style = lambda: ParagraphStyle("sig", fontName="Helvetica", alignment=TA_CENTER, fontSize=7.5, leading=10)
    if show_amounts:
        sig_data = [
            [
                Paragraph("__________________________<br/><b>Prepared By (Accountant)</b>", sig_style()),
                Paragraph("__________________________<br/><b>Checked By (Admin / Incharge)</b>", sig_style()),
                Paragraph("__________________________<br/><b>Principal / Director Seal & Sign</b>", sig_style()),
            ]
        ]
    else:
        sig_data = [
            [
                Paragraph("__________________________<br/><b>Instructor / Teacher Sign</b>", sig_style()),
                Paragraph("__________________________<br/><b>Checked By (Admin / Incharge)</b>", sig_style()),
                Paragraph("__________________________<br/><b>Principal / Director Seal & Sign</b>", sig_style()),
            ]
        ]
    sig_table = Table(sig_data, colWidths=[90*mm, 95*mm, 92*mm])
    sig_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))
    story.append(KeepTogether([sig_table]))

    doc.build(story, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    return buffer
