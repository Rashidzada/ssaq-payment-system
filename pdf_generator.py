"""
Generates a fee voucher PDF containing TWO copies on one A4 page:
  - Top half:    OFFICE COPY
  - Bottom half: STUDENT COPY
Built with reportlab only (no external binaries required).
"""
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib import colors


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
