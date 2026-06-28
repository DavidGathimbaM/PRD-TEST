"""
PDF report generator for the AW Client Report Portal.

Rebuilt to match the Windbrook SACS / TCC template images:
  - Page 1: SACS cashflow (block arrows, floor lines, piggy-bank + paper clip-art, white pills)
  - Page 2: Private Reserve Target (FICA <-> Investment, white pills, target box)
  - Page 3: TCC net-worth circle chart with a fully dynamic, auto-sizing
            account grid (any number of accounts) and cash sub-bubbles.

Public entry point:  build_report_pdf(data) -> (BytesIO, report_history_dict)
"""

import math
from io import BytesIO
from datetime import datetime

from reportlab.lib.pagesizes import landscape, letter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, black, white


# ----------------------------------------------------------------------------
# Small value helpers
# ----------------------------------------------------------------------------

def safe_float(value, default=0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def money(value):
    try:
        return f"${float(value):,.0f}"
    except (TypeError, ValueError):
        return "$0"


def _fit_font(pdf, text, max_width, base_size, font="Helvetica-Bold", min_size=5):
    """Return the largest font size <= base_size that fits text in max_width."""
    size = base_size
    while size > min_size and pdf.stringWidth(str(text), font, size) > max_width:
        size -= 0.5
    return size


def _wrap_name(name):
    """Split a household/person name into at most two balanced lines."""
    words = str(name).split()
    if len(words) <= 1:
        return words or [""]
    if len(words) == 2:
        return words
    # 3+ words: split roughly in half
    mid = (len(words) + 1) // 2
    return [" ".join(words[:mid]), " ".join(words[mid:])]


# ----------------------------------------------------------------------------
# Drawing primitives
# ----------------------------------------------------------------------------

def draw_block_arrow(pdf, x1, y1, x2, y2, color, thickness=14, label=None,
                     label_color=None, label_dx=0, label_dy=14):
    """Draw a chunky filled block arrow from (x1,y1) to (x2,y2)."""
    dx, dy = x2 - x1, y2 - y1
    length = math.hypot(dx, dy)
    if length == 0:
        return

    ux, uy = dx / length, dy / length          # unit vector along arrow
    px, py = -uy, ux                            # unit perpendicular

    head_len = min(length * 0.42, thickness * 2.4)
    base_x, base_y = x1 + ux * (length - head_len), y1 + uy * (length - head_len)

    hw = thickness / 2.0
    head_hw = thickness * 1.15

    points = [
        (x1 + px * hw, y1 + py * hw),
        (base_x + px * hw, base_y + py * hw),
        (base_x + px * head_hw, base_y + py * head_hw),
        (x2, y2),
        (base_x - px * head_hw, base_y - py * head_hw),
        (base_x - px * hw, base_y - py * hw),
        (x1 - px * hw, y1 - py * hw),
    ]

    pdf.setFillColor(HexColor(color))
    pdf.setStrokeColor(HexColor(color))
    pdf.setLineWidth(0.5)

    path = pdf.beginPath()
    path.moveTo(*points[0])
    for point in points[1:]:
        path.lineTo(*point)
    path.close()
    pdf.drawPath(path, fill=1, stroke=1)

    if label:
        mid_x = (x1 + x2) / 2 + label_dx
        mid_y = (y1 + y2) / 2 + label_dy
        pdf.setFillColor(HexColor(label_color or color))
        pdf.setFont("Helvetica-Bold", 9)
        pdf.drawCentredString(mid_x, mid_y, label)


def draw_double_arrow(pdf, x1, x2, y, color, thickness=12, gap=10):
    """Two stacked horizontal block arrows pointing opposite directions."""
    draw_block_arrow(pdf, x1, y + gap, x2, y + gap, color, thickness)
    draw_block_arrow(pdf, x2, y - gap, x1, y - gap, color, thickness)


def draw_pill(pdf, cx, cy, text, width=None, height=20, font_size=11,
              bg=white, fg=black, stroke="#D0D5DD"):
    """White rounded pill with centred text, anchored on its centre (cx, cy)."""
    text = str(text)
    if width is None:
        width = pdf.stringWidth(text, "Helvetica-Bold", font_size) + 20
    x = cx - width / 2
    y = cy - height / 2
    pdf.setFillColor(bg)
    pdf.setStrokeColor(HexColor(stroke))
    pdf.setLineWidth(0.8)
    pdf.roundRect(x, y, width, height, height / 2, fill=1, stroke=1)
    pdf.setFillColor(fg)
    pdf.setFont("Helvetica-Bold", font_size)
    pdf.drawCentredString(cx, cy - font_size / 2 + 1, text)


def draw_floor_line(pdf, cx, cy, radius, label, frac=0.55, color="#0B3D1E"):
    """Horizontal secant line across the lower part of a circle with a label."""
    offset = radius * frac
    y = cy - offset
    half = math.sqrt(max(radius * radius - offset * offset, 0))
    pdf.setStrokeColor(HexColor(color))
    pdf.setLineWidth(1.2)
    pdf.line(cx - half, y, cx + half, y)
    pdf.setFillColor(HexColor(color))
    pdf.setFont("Helvetica-Oblique", 7)
    pdf.drawCentredString(cx, y + 3, label)


def draw_rounded_label(pdf, cx, cy, text, color, font_size=9, pad_x=10, pad_y=5):
    """An outlined rounded box wrapping a label (e.g. the X = $/month tag)."""
    w = pdf.stringWidth(text, "Helvetica-Bold", font_size) + pad_x * 2
    h = font_size + pad_y * 2
    pdf.setFillColor(white)
    pdf.setStrokeColor(HexColor(color))
    pdf.setLineWidth(1)
    pdf.roundRect(cx - w / 2, cy - h / 2, w, h, h / 2, fill=1, stroke=1)
    pdf.setFillColor(HexColor(color))
    pdf.setFont("Helvetica-Bold", font_size)
    pdf.drawCentredString(cx, cy - font_size / 2 + 1, text)


# ----------------------------------------------------------------------------
# Clip-art (vector approximations of the template artwork)
# ----------------------------------------------------------------------------

def draw_piggy_bank(pdf, cx, cy, scale=1.0):
    """A small vector piggy bank with coins."""
    s = scale
    pink = HexColor("#EFA6C0")
    pink_dark = HexColor("#D97FA6")
    gold = HexColor("#F2C14E")

    # coins behind
    pdf.setFillColor(gold)
    pdf.setStrokeColor(HexColor("#C9991F"))
    pdf.setLineWidth(0.5)
    for i, dx in enumerate((-26, 22, 30)):
        cyy = cy - 14 * s + i * 0
        pdf.ellipse((cx + dx - 7) * 1, (cy - 20) * 1, (cx + dx + 7), (cy - 12),
                    fill=1, stroke=1)

    # legs
    pdf.setFillColor(pink_dark)
    for dx in (-16, -6, 6, 16):
        pdf.rect(cx + dx * s - 2, cy - 22 * s, 4 * s, 8 * s, fill=1, stroke=0)

    # body
    pdf.setFillColor(pink)
    pdf.setStrokeColor(pink_dark)
    pdf.setLineWidth(1)
    pdf.ellipse(cx - 26 * s, cy - 18 * s, cx + 26 * s, cy + 16 * s, fill=1, stroke=1)

    # snout
    pdf.setFillColor(pink_dark)
    pdf.ellipse(cx + 14 * s, cy - 8 * s, cx + 30 * s, cy + 4 * s, fill=1, stroke=1)
    pdf.setFillColor(HexColor("#A85C82"))
    pdf.circle(cx + 20 * s, cy - 2 * s, 1.4 * s, fill=1, stroke=0)
    pdf.circle(cx + 25 * s, cy - 2 * s, 1.4 * s, fill=1, stroke=0)

    # ear
    pdf.setFillColor(pink_dark)
    path = pdf.beginPath()
    path.moveTo(cx + 2 * s, cy + 14 * s)
    path.lineTo(cx + 10 * s, cy + 26 * s)
    path.lineTo(cx + 14 * s, cy + 12 * s)
    path.close()
    pdf.drawPath(path, fill=1, stroke=0)

    # eye
    pdf.setFillColor(black)
    pdf.circle(cx + 12 * s, cy + 4 * s, 1.6 * s, fill=1, stroke=0)

    # coin slot
    pdf.setStrokeColor(black)
    pdf.setLineWidth(1.5)
    pdf.line(cx - 6 * s, cy + 14 * s, cx + 4 * s, cy + 14 * s)

    # a dropping coin
    pdf.setFillColor(gold)
    pdf.setStrokeColor(HexColor("#C9991F"))
    pdf.setLineWidth(0.5)
    pdf.circle(cx - 1 * s, cy + 24 * s, 5 * s, fill=1, stroke=1)
    pdf.setFillColor(HexColor("#C9991F"))
    pdf.setFont("Helvetica-Bold", 6 * s)
    pdf.drawCentredString(cx - 1 * s, cy + 22 * s, "$")


def draw_paper_stack(pdf, x, y, scale=1.0):
    """A small stack of offset documents."""
    s = scale
    pdf.setLineWidth(0.8)
    for i, (dx, dy, shade) in enumerate((
        (10, -8, "#C7CCD4"),
        (5, -4, "#DDE1E7"),
        (0, 0, "#F2F4F7"),
    )):
        pdf.setFillColor(HexColor(shade))
        pdf.setStrokeColor(HexColor("#98A2B3"))
        pdf.rect(x + dx * s, y + dy * s, 34 * s, 44 * s, fill=1, stroke=1)
    # text lines on the top sheet
    pdf.setStrokeColor(HexColor("#98A2B3"))
    pdf.setLineWidth(0.6)
    for i in range(5):
        ly = y + 36 * s - i * 7 * s
        pdf.line(x + 5 * s, ly, x + 29 * s, ly)


def draw_dollar_glyph(pdf, x, y, color="#168A4A", size=34):
    pdf.setFillColor(HexColor(color))
    pdf.setFont("Helvetica-Bold", size)
    pdf.drawString(x, y, "$")


# ----------------------------------------------------------------------------
# Generic circle bubble (used on pages 1 & 2)
# ----------------------------------------------------------------------------

def draw_circle_bubble(pdf, x, y, radius, fill_color, title, subtitle=None,
                       amount=None, amount_plus=False, title_color=white,
                       text_color=white):
    pdf.setStrokeColor(black)
    pdf.setLineWidth(1.2)
    pdf.setFillColor(HexColor(fill_color))
    pdf.circle(x, y, radius, fill=1, stroke=1)

    pdf.setFillColor(title_color)
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawCentredString(x, y + radius * 0.42, str(title))

    if subtitle:
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawCentredString(x, y + radius * 0.20, str(subtitle))

    if amount is not None:
        label = money(amount) + ("+" if amount_plus else "")
        draw_pill(pdf, x, y - radius * 0.08, label, font_size=11)


# ----------------------------------------------------------------------------
# Page 3: dynamic account bubble + grid packing
# ----------------------------------------------------------------------------

def _draw_account_bubble(pdf, cx, cy, radius, account, with_cash=True):
    """A single account bubble; optionally a small cash sub-bubble lower-left."""
    pdf.setFillColor(white)
    pdf.setStrokeColor(black)
    pdf.setLineWidth(1)
    pdf.circle(cx, cy, radius, fill=1, stroke=1)

    # font sizes scale with radius
    head = max(5.5, radius * 0.22)
    body = max(5.0, radius * 0.19)
    inner_w = radius * 1.6

    pdf.setFillColor(black)
    pdf.setFont("Helvetica-Bold", head)
    pdf.drawCentredString(cx, cy + radius * 0.42, "ACCT #")

    acct_type = str(account.get("account_type", ""))
    balance = money(account.get("balance", 0))
    as_of = account.get("as_of_date", "")

    pdf.setFont("Helvetica", _fit_font(pdf, acct_type, inner_w, body, "Helvetica"))
    pdf.drawCentredString(cx, cy + radius * 0.12, acct_type)

    pdf.setFont("Helvetica-Bold", _fit_font(pdf, balance, inner_w, body))
    pdf.drawCentredString(cx, cy - radius * 0.16, balance)

    if as_of:
        pdf.setFont("Helvetica", max(4.5, body - 1))
        pdf.drawCentredString(cx, cy - radius * 0.45, f"a/o {as_of}")

    cash = safe_float(account.get("cash_balance", 0))
    if with_cash and cash > 0:
        sub_r = radius * 0.42
        sx = cx - radius * 0.95
        sy = cy - radius * 0.92
        pdf.setFillColor(HexColor("#FFF6D6"))
        pdf.setStrokeColor(HexColor("#C9991F"))
        pdf.setLineWidth(0.8)
        pdf.circle(sx, sy, sub_r, fill=1, stroke=1)
        pdf.setFillColor(black)
        pdf.setFont("Helvetica-Bold", max(4.5, sub_r * 0.42))
        pdf.drawCentredString(sx, sy + sub_r * 0.05, money(cash))
        pdf.setFont("Helvetica", max(4.0, sub_r * 0.36))
        pdf.drawCentredString(sx, sy - sub_r * 0.42, "Cash")


def _pack_bubbles(pdf, items, x0, y0, x1, y1, with_cash=True, max_radius=44):
    """Lay accounts out in an auto-sized grid filling the (x0,y0)-(x1,y1) box."""
    items = list(items)
    n = len(items)
    if n == 0:
        return

    region_w = x1 - x0
    region_h = y1 - y0

    best = None  # (cols, rows, radius)
    for cols in range(1, n + 1):
        rows = math.ceil(n / cols)
        cell_w = region_w / cols
        cell_h = region_h / rows
        radius = min(cell_w, cell_h) / 2 * 0.84
        radius = min(radius, max_radius)
        if radius < 13:
            continue
        if best is None or radius > best[2]:
            best = (cols, rows, radius)

    if best is None:
        cols, rows = n, 1
        radius = max(11, region_w / n / 2 * 0.84)
    else:
        cols, rows, radius = best

    cell_w = region_w / cols
    cell_h = region_h / rows

    for i, account in enumerate(items):
        row = i // cols
        col = i % cols
        # centre the last (possibly short) row
        items_in_row = min(cols, n - row * cols)
        row_offset = (cols - items_in_row) * cell_w / 2
        cx = x0 + row_offset + cell_w * (col + 0.5)
        cy = y1 - cell_h * (row + 0.5)
        _draw_account_bubble(pdf, cx, cy, radius, account, with_cash)


def _draw_client_circle(pdf, cx, cy, radius, name, age, dob, ssn):
    pdf.setFillColor(HexColor("#6BAA45"))
    pdf.setStrokeColor(HexColor("#2F5A1E"))
    pdf.setLineWidth(2)
    pdf.circle(cx, cy, radius, fill=1, stroke=1)

    pdf.setFillColor(white)
    name_lines = _wrap_name(name)
    max_w = radius * 1.55
    font_size = min(_fit_font(pdf, max(name_lines, key=len), max_w, 10), 10)

    top = cy + radius * 0.45
    for line in name_lines:
        pdf.setFont("Helvetica-Bold", font_size)
        pdf.drawCentredString(cx, top, line)
        top -= font_size + 1

    pdf.setFont("Helvetica", 7)
    info_y = top - 2
    for line in (f"Age {age}", f"DOB {dob}", f"SSN {ssn}"):
        pdf.drawCentredString(cx, info_y, line)
        info_y -= 9


# ----------------------------------------------------------------------------
# Main builder
# ----------------------------------------------------------------------------

def build_report_pdf(data):
    """Build the 3-page SACS/TCC PDF. Returns (BytesIO, report_history_dict)."""
    household_name = data.get("householdName", "Sample Client")
    report_date = data.get("reportDate") or datetime.now().strftime("%B %d, %Y")

    client1_name = data.get("client1Name", "Client 1")
    client1_age = data.get("client1Age", "")
    client1_dob = data.get("client1Dob", "")
    client1_ssn = data.get("client1SsnLast4", "")

    client2_name = data.get("client2Name", "")
    client2_age = data.get("client2Age", "")
    client2_dob = data.get("client2Dob", "")
    client2_ssn = data.get("client2SsnLast4", "")

    inflow = safe_float(data.get("inflow"))
    outflow = safe_float(data.get("outflow"))
    automated_transfer = inflow - outflow

    private_reserve_balance = safe_float(data.get("privateReserveBalance"))
    investment_account_balance = safe_float(data.get("investmentAccountBalance"))
    insurance_deductibles = safe_float(data.get("insuranceDeductibles"))
    floor_amount = safe_float(data.get("floorAmount"), 1000)

    private_reserve_target = (6 * outflow) + insurance_deductibles
    reserve_gap = private_reserve_balance - private_reserve_target

    client1_retirement_total = safe_float(data.get("client1RetirementTotal"))
    client2_retirement_total = safe_float(data.get("client2RetirementTotal"))
    non_retirement_total = safe_float(data.get("nonRetirementTotal"))
    trust_value = safe_float(data.get("trustValue"))
    liabilities_total = safe_float(data.get("liabilitiesTotal"))

    grand_total_net_worth = (
        client1_retirement_total
        + client2_retirement_total
        + non_retirement_total
        + trust_value
    )

    accounts = data.get("accounts", [])
    liabilities = data.get("liabilities", [])

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=landscape(letter))
    width, height = landscape(letter)
    pdf.setTitle("AW Client SACS and TCC Report")

    _page1_cashflow(pdf, width, height, household_name, report_date, inflow,
                    outflow, automated_transfer, floor_amount)
    pdf.showPage()

    _page2_reserve(pdf, width, height, household_name, report_date, outflow,
                   private_reserve_balance, investment_account_balance,
                   insurance_deductibles, private_reserve_target, reserve_gap)
    pdf.showPage()

    _page3_tcc(pdf, width, height, household_name, report_date,
               client1_name, client1_age, client1_dob, client1_ssn,
               client2_name, client2_age, client2_dob, client2_ssn,
               client1_retirement_total, client2_retirement_total,
               non_retirement_total, trust_value, grand_total_net_worth,
               liabilities_total, accounts, liabilities)

    pdf.save()
    buffer.seek(0)

    history = {
        "reportDate": report_date,
        "inflow": inflow,
        "outflow": outflow,
        "automatedTransfer": automated_transfer,
        "privateReserveTarget": private_reserve_target,
        "client1RetirementTotal": client1_retirement_total,
        "client2RetirementTotal": client2_retirement_total,
        "nonRetirementTotal": non_retirement_total,
        "trustValue": trust_value,
        "grandTotalNetWorth": grand_total_net_worth,
        "liabilitiesTotal": liabilities_total,
    }
    return buffer, history


# ----------------------------------------------------------------------------
# Page builders
# ----------------------------------------------------------------------------

def _page1_cashflow(pdf, width, height, household_name, report_date, inflow,
                    outflow, automated_transfer, floor_amount):
    pdf.setFillColor(black)
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawCentredString(width / 2, height - 42, "Simple Automated Cashflow System (SACS)")
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawCentredString(width / 2, height - 66, household_name)

    # top-left dollar glyph + salary split
    draw_dollar_glyph(pdf, 34, height - 70, "#168A4A", 34)
    pdf.setFillColor(HexColor("#168A4A"))
    pdf.setFont("Helvetica", 8)
    pdf.drawString(30, height - 92, f"{money(inflow * 0.53)} - Client 1")
    pdf.drawString(30, height - 106, f"{money(inflow * 0.47)} - Client 2")

    # top-right paper stack + expense bracket
    draw_paper_stack(pdf, width - 110, height - 95, 1.0)
    pdf.setFillColor(HexColor("#475467"))
    pdf.setFont("Helvetica", 9)
    pdf.drawString(width - 132, height - 112, "X = Monthly")
    pdf.drawString(width - 132, height - 124, "Expenses")
    pdf.setStrokeColor(HexColor("#475467"))
    pdf.setLineWidth(1)
    pdf.line(width - 107, height - 130, width - 107, 350)
    pdf.line(width - 107, 350, 638, 350)

    inflow_c = (165, 350, 78)
    outflow_c = (560, 350, 78)
    reserve_c = (365, 165, 75)

    # salary -> inflow block arrow
    draw_block_arrow(pdf, 78, height - 118, 120, 412, "#168A4A", 13)

    # inflow circle
    draw_circle_bubble(pdf, *inflow_c[:2], inflow_c[2], "#39C96B", "INFLOW",
                       amount=inflow)
    draw_floor_line(pdf, inflow_c[0], inflow_c[1], inflow_c[2],
                    f"{money(floor_amount)} Floor")

    # outflow circle
    draw_circle_bubble(pdf, *outflow_c[:2], outflow_c[2], "#F04438", "OUTFLOW",
                       amount=outflow)
    draw_floor_line(pdf, outflow_c[0], outflow_c[1], outflow_c[2],
                    f"{money(floor_amount)} Floor")

    # private reserve circle (with piggy bank)
    pdf.setFillColor(HexColor("#3A8DCC"))
    pdf.setStrokeColor(black)
    pdf.setLineWidth(1.2)
    pdf.circle(reserve_c[0], reserve_c[1], reserve_c[2], fill=1, stroke=1)
    pdf.setFillColor(white)
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawCentredString(reserve_c[0], reserve_c[1] + 46, "PRIVATE")
    pdf.drawCentredString(reserve_c[0], reserve_c[1] + 32, "RESERVE")
    draw_piggy_bank(pdf, reserve_c[0], reserve_c[1] - 6, 0.95)
    draw_pill(pdf, reserve_c[0], reserve_c[1] - 50, money(automated_transfer),
              font_size=10)

    # inflow -> outflow red block arrow + rounded label
    draw_block_arrow(pdf, 250, 360, 470, 360, "#D92D20", 12)
    draw_rounded_label(pdf, 360, 392, f"X = {money(outflow)}/month", "#D92D20", 9)
    pdf.setFillColor(black)
    pdf.setFont("Helvetica", 8)
    pdf.drawCentredString(360, 340, "Automated transfer on the 28th")

    # inflow -> reserve blue block arrow (label clear of the circle)
    draw_block_arrow(pdf, 150, 285, 285, 200, "#6EA8D9", 12)
    pdf.setFillColor(HexColor("#3A8DCC"))
    pdf.setFont("Helvetica-Bold", 9)
    pdf.drawCentredString(178, 232, f"{money(automated_transfer)}/mo*")

    # monthly cashflow label + dashed line
    pdf.setFillColor(black)
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawCentredString(reserve_c[0], 72, "MONTHLY CASHFLOW")
    pdf.setDash(3, 3)
    pdf.setStrokeColor(black)
    pdf.line(reserve_c[0], 66, reserve_c[0], 28)
    pdf.setDash()

    pdf.setFillColor(HexColor("#667085"))
    pdf.setFont("Helvetica", 8)
    pdf.drawRightString(width - 35, 30, f"Report Date: {report_date}")


def _page2_reserve(pdf, width, height, household_name, report_date, outflow,
                   private_reserve_balance, investment_account_balance,
                   insurance_deductibles, private_reserve_target, reserve_gap):
    pdf.setFillColor(black)
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawCentredString(width / 2, height - 46, "Simple Automated Cashflow System (SACS)")
    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawCentredString(width / 2, height - 70, "Private Reserve Target")
    pdf.setFont("Helvetica", 9)
    pdf.drawCentredString(width / 2, height - 86, f"{household_name}  |  {report_date}")

    # dashed centre divider
    pdf.setDash(3, 3)
    pdf.setStrokeColor(HexColor("#98A2B3"))
    pdf.line(width / 2, height - 110, width / 2, 175)
    pdf.setDash()

    fica = (260, 330, 78)
    invest = (535, 330, 78)

    # FICA circle (light blue)
    pdf.setFillColor(HexColor("#A8C8E6"))
    pdf.setStrokeColor(black)
    pdf.setLineWidth(1.2)
    pdf.circle(*fica[:2], fica[2], fill=1, stroke=1)
    pdf.setFillColor(HexColor("#1F3D5C"))
    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawCentredString(fica[0], fica[1] + 30, "FICA")
    pdf.drawCentredString(fica[0], fica[1] + 14, "ACCOUNT")
    draw_pill(pdf, fica[0], fica[1] - 14, money(private_reserve_balance), font_size=12)

    # Investment circle (dark navy)
    pdf.setFillColor(HexColor("#152B4F"))
    pdf.setStrokeColor(black)
    pdf.circle(*invest[:2], invest[2], fill=1, stroke=1)
    pdf.setFillColor(white)
    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawCentredString(invest[0], invest[1] + 30, "INVESTMENT")
    pdf.drawCentredString(invest[0], invest[1] + 14, "ACCOUNT")
    draw_pill(pdf, invest[0], invest[1] - 14, money(investment_account_balance) + "+",
              font_size=12)

    # bidirectional block arrows
    draw_double_arrow(pdf, 345, 455, 320, "#1F4E79", 11, gap=11)

    pdf.setFillColor(black)
    pdf.setFont("Helvetica", 9)
    pdf.drawCentredString(fica[0], 232, "6X Monthly Expenses + Deductibles")
    pdf.drawCentredString(invest[0], 232, "Remainder")

    # target calculation box
    pdf.setFillColor(HexColor("#F7F9FC"))
    pdf.setStrokeColor(HexColor("#D0D5DD"))
    pdf.setLineWidth(1)
    pdf.rect(145, 80, 510, 86, fill=1, stroke=1)
    pdf.setFillColor(black)
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(165, 142, "Target Calculation")
    pdf.setFont("Helvetica", 9)
    pdf.drawString(165, 122, f"Monthly Outflow: {money(outflow)}")
    pdf.drawString(360, 122, f"Insurance Deductibles: {money(insurance_deductibles)}")
    pdf.drawString(165, 104, "Formula: 6 x Outflow + Deductibles")
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(165, 88, f"Private Reserve Target: {money(private_reserve_target)}")
    pdf.drawString(430, 88, f"Reserve Gap / Surplus: {money(reserve_gap)}")

    pdf.setFillColor(HexColor("#667085"))
    pdf.setFont("Helvetica", 8)
    pdf.drawRightString(width - 35, 30, f"Report Date: {report_date}")


def _page3_tcc(pdf, width, height, household_name, report_date,
               client1_name, client1_age, client1_dob, client1_ssn,
               client2_name, client2_age, client2_dob, client2_ssn,
               client1_retirement_total, client2_retirement_total,
               non_retirement_total, trust_value, grand_total_net_worth,
               liabilities_total, accounts, liabilities):

    cx_center = width / 2

    # outer olive border
    pdf.setStrokeColor(HexColor("#7A8F3A"))
    pdf.setLineWidth(2)
    pdf.rect(18, 18, width - 36, height - 36, fill=0, stroke=1)

    # quadrant cross
    pdf.setStrokeColor(HexColor("#D0D5DD"))
    pdf.setLineWidth(1)
    pdf.line(cx_center, 45, cx_center, height - 45)
    pdf.line(20, height / 2, width - 20, height / 2)

    # NAME / DATE
    pdf.setFillColor(black)
    pdf.setFont("Helvetica", 8)
    pdf.drawString(30, height - 50, "NAME")
    pdf.line(72, height - 52, 200, height - 52)
    pdf.drawString(80, height - 50, household_name)
    pdf.drawString(30, height - 68, "DATE")
    pdf.line(72, height - 70, 200, height - 70)
    pdf.drawString(80, height - 68, report_date)

    # GRAND TOTAL + Liabilities boxes (center top)
    _filled_box(pdf, cx_center - 60, height - 84, 120, 46, "#344054",
                "GRAND TOTAL", money(grand_total_net_worth))
    _filled_box(pdf, cx_center - 60, height - 132, 120, 38, "#E4E7EC",
                "Liabilities", money(liabilities_total), fg=black, border=True)

    # client circles
    _draw_client_circle(pdf, 235, height - 100, 40, client1_name,
                        client1_age, client1_dob, client1_ssn)
    if client2_name:
        _draw_client_circle(pdf, width - 235, height - 100, 40, client2_name,
                            client2_age, client2_dob, client2_ssn)

    # "... Retirement Only" boxes
    _filled_box(pdf, 40, height - 120, 130, 34, "#344054",
                "Client 1 Retirement Only", money(client1_retirement_total))
    _filled_box(pdf, width - 170, height - 120, 130, 34, "#344054",
                "Client 2 Retirement Only", money(client2_retirement_total))

    # split accounts
    c1_ret = [a for a in accounts if a.get("owner") == "client1" and a.get("category") == "retirement"]
    c2_ret = [a for a in accounts if a.get("owner") == "client2" and a.get("category") == "retirement"]
    non_ret = [a for a in accounts if a.get("category") == "non_retirement"]

    divider_y = height / 2

    # retirement bubbles (top quadrants)
    _pack_bubbles(pdf, c1_ret, 30, divider_y + 12, 360, height - 150, with_cash=True)
    _pack_bubbles(pdf, c2_ret, width - 360, divider_y + 12, width - 30, height - 150, with_cash=True)

    # RETIREMENT labels + divider band
    pdf.setFillColor(HexColor("#98A250"))
    pdf.setFont("Helvetica", 8)
    pdf.drawString(45, divider_y + 6, "RETIREMENT")
    pdf.drawRightString(width - 45, divider_y + 6, "RETIREMENT")
    pdf.setStrokeColor(black)
    pdf.setLineWidth(1)
    pdf.line(20, divider_y, width - 20, divider_y)

    # non-retirement: fill left region, overflow into right region
    left_cap = 4
    left_items = non_ret[:left_cap]
    right_items = non_ret[left_cap:]
    _pack_bubbles(pdf, left_items, 30, 70, 320, divider_y - 12, with_cash=True)
    _pack_bubbles(pdf, right_items, width - 320, 70, width - 30, divider_y - 12, with_cash=True)

    # family trust bubble (upper center)
    pdf.setFillColor(white)
    pdf.setStrokeColor(black)
    pdf.setLineWidth(1)
    pdf.circle(cx_center, divider_y - 56, 52, fill=1, stroke=1)
    pdf.setFillColor(black)
    pdf.setFont("Helvetica-Bold", 9)
    pdf.drawCentredString(cx_center, divider_y - 38, "Client 1 and")
    pdf.setFont("Helvetica", 8)
    pdf.drawCentredString(cx_center, divider_y - 52, "Client 2 Family")
    pdf.drawCentredString(cx_center, divider_y - 64, "Trust")
    pdf.setFont("Helvetica-Bold", 9)
    pdf.drawCentredString(cx_center, divider_y - 80, money(trust_value))

    # liabilities detail box (center)
    pdf.setFillColor(HexColor("#E4E7EC"))
    pdf.setStrokeColor(HexColor("#98A2B3"))
    pdf.setLineWidth(1)
    box_top = 175
    box_bottom = 100
    pdf.rect(cx_center - 65, box_bottom, 130, box_top - box_bottom, fill=1, stroke=1)
    pdf.setFillColor(black)
    pdf.setFont("Helvetica-Bold", 8)
    pdf.drawCentredString(cx_center, box_top - 13, "Liabilities")
    pdf.setFont("Helvetica", 6.5)
    line_y = box_top - 26
    if liabilities:
        for liability in liabilities[:6]:
            label = str(liability.get("liability_type", "Liability"))
            rate = str(liability.get("interest_rate", ""))
            bal = money(liability.get("remaining_balance", 0))
            left_label = f"{label} {rate}".strip()
            left_label = (left_label[:20] + "…") if len(left_label) > 21 else left_label
            pdf.drawString(cx_center - 60, line_y, left_label)
            pdf.drawRightString(cx_center + 60, line_y, bal)
            line_y -= 10
    else:
        pdf.drawCentredString(cx_center, box_top - 40, "No liabilities entered")

    # NON RETIREMENT TOTAL box
    _filled_box(pdf, cx_center - 60, 58, 120, 34, "#344054",
                "NON RETIREMENT TOTAL", money(non_retirement_total))

    # asterisk note
    pdf.setFillColor(HexColor("#D92D20"))
    pdf.setFont("Helvetica", 7)
    pdf.drawRightString(width - 35, 40, "* Indicates we do not have up to date information")
    pdf.setFillColor(black)
    pdf.setFont("Helvetica", 7)
    pdf.drawRightString(width - 35, 28, "Liabilities shown separately; not subtracted from net worth.")


def _filled_box(pdf, x, y, w, h, color, title, value, fg=white, border=False):
    pdf.setFillColor(HexColor(color))
    if border:
        pdf.setStrokeColor(HexColor("#98A2B3"))
        pdf.setLineWidth(1)
        pdf.rect(x, y, w, h, fill=1, stroke=1)
    else:
        pdf.rect(x, y, w, h, fill=1, stroke=0)
    pdf.setFillColor(fg)
    pdf.setFont("Helvetica-Bold", _fit_font(pdf, title, w - 8, 7.5))
    pdf.drawCentredString(x + w / 2, y + h - 13, title)
    pdf.setFont("Helvetica-Bold", 9)
    pdf.drawCentredString(x + w / 2, y + 8, value)
