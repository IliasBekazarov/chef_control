"""
PDF отчет генератору — fpdf2 аркылуу.

Эки режим:
  • Сессия боюнча: build_session_report(session, records)
  • Дата диапазону боюнча: build_range_report(records_qs, date_from, date_to, stats)
"""
from datetime import date
from fpdf import FPDF, XPos, YPos

# Arial Unicode.ttf — Cyrillic + Latin + спецсимволдорду колдойт
FONT_PATH = "/Library/Fonts/Arial Unicode.ttf"


# ─── Түстөр ─────────────────────────────────────────────────────────────────
C_PRIMARY  = (251, 146,  60)
C_GREEN    = ( 16, 185, 129)
C_RED      = (239,  68,  68)
C_DARK     = ( 30,  41,  59)
C_MUTED    = (100, 116, 139)
C_SURFACE  = (248, 250, 252)
C_BORDER   = (226, 232, 240)


class ChefPDF(FPDF):
    def __init__(self, title: str):
        super().__init__()
        self._title = title
        self.add_font("uni", "", FONT_PATH)
        self.add_font("uni", "B", FONT_PATH)
        self.set_auto_page_break(auto=True, margin=18)
        self.set_margins(18, 18, 18)

    def _f(self, style="", size=10):
        self.set_font("uni", style, size)

    # ── Header / Footer ──────────────────────────────────────────────────────
    def header(self):
        self.set_fill_color(*C_DARK)
        self.rect(0, 0, 210, 14, "F")
        self.set_y(3)
        self._f("B", 9)
        self.set_text_color(255, 255, 255)
        self.cell(0, 8, "  Chef Control — Compliance Report", align="L")
        self.set_y(18)
        self.set_text_color(*C_DARK)

    def footer(self):
        self.set_y(-12)
        self._f("", 8)
        self.set_text_color(*C_MUTED)
        self.cell(0, 6, f"  Chef Control  ·  Бет {self.page_no()}", align="L")
        self.cell(0, 6, f"Генерацияланды: {date.today().strftime('%d.%m.%Y')}  ", align="R")

    # ── Section heading ──────────────────────────────────────────────────────
    def section(self, text: str):
        self.ln(4)
        self._f("B", 11)
        self.set_text_color(*C_PRIMARY)
        self.cell(0, 8, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        # Separator line
        self.set_draw_color(*C_PRIMARY)
        self.set_line_width(0.5)
        self.line(self.get_x(), self.get_y(), 192, self.get_y())
        self.ln(3)
        self.set_text_color(*C_DARK)
        self.set_draw_color(*C_BORDER)

    # ── Summary KPI box ──────────────────────────────────────────────────────
    def kpi_row(self, items: list[tuple]):
        """items: [(label, value, color), ...]"""
        w = (210 - 36) / len(items)
        for label, value, color in items:
            x = self.get_x(); y = self.get_y()
            self.set_fill_color(*C_SURFACE)
            self.set_draw_color(*C_BORDER)
            self.set_line_width(0.3)
            self.rect(x, y, w - 2, 22, "FD")
            self._f("B", 14)
            self.set_text_color(*color)
            self.set_xy(x + 1, y + 3)
            self.cell(w - 4, 9, str(value), align="C")
            self._f("", 7)
            self.set_text_color(*C_MUTED)
            self.set_xy(x + 1, y + 13)
            self.cell(w - 4, 6, label, align="C")
            self.set_xy(x + w, y)
        self.ln(26)

    # ── Table ────────────────────────────────────────────────────────────────
    def table(self, headers: list, rows: list, col_widths: list, aligns: list = None):
        aligns = aligns or ["L"] * len(headers)
        # Header row
        self.set_fill_color(*C_DARK)
        self.set_text_color(255, 255, 255)
        self._f("B", 8)
        self.set_draw_color(*C_BORDER)
        self.set_line_width(0.2)
        for h, w, a in zip(headers, col_widths, aligns):
            self.cell(w, 7, f"  {h}", border=1, fill=True, align=a)
        self.ln()
        # Data rows
        self.set_text_color(*C_DARK)
        self._f("", 8)
        for idx, row in enumerate(rows):
            self.set_fill_color(248, 250, 252) if idx % 2 == 0 else self.set_fill_color(255, 255, 255)
            for cell, w, a in zip(row, col_widths, aligns):
                self.cell(w, 6, f"  {cell}", border=1, fill=True, align=a)
            self.ln()
        self.ln(2)


# ─── Пайдалуу жардамчы ──────────────────────────────────────────────────────
def _pct_color(rate: float):
    if rate >= 90: return C_GREEN
    if rate >= 70: return C_PRIMARY
    return C_RED


def _compliance_bar(pdf: ChefPDF, rate: float, width: float = 174):
    """Горизонталдык прогресс бар"""
    h   = 6
    y   = pdf.get_y()
    x   = pdf.get_x()
    # Background
    pdf.set_fill_color(*C_BORDER)
    pdf.rect(x, y, width, h, "F")
    # Fill
    filled = width * rate / 100
    color  = _pct_color(rate)
    pdf.set_fill_color(*color)
    if filled > 0:
        pdf.rect(x, y, filled, h, "F")
    # Label
    pdf._f("B", 7)
    pdf.set_text_color(255, 255, 255)
    pdf.set_xy(x + 2, y + 0.8)
    pdf.cell(filled - 4 if filled > 20 else 0, h - 1.5, f"{rate:.1f}%")
    pdf.ln(h + 3)
    pdf.set_text_color(*C_DARK)


# ─── Сессия отчету ──────────────────────────────────────────────────────────
def build_session_report(session, records) -> bytes:
    pdf = ChefPDF(f"Сессия: {session.session_id}")
    pdf.add_page()

    # Title
    pdf._f("B", 18)
    pdf.set_text_color(*C_DARK)
    pdf.cell(0, 10, "Chef Control", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf._f("", 11)
    pdf.set_text_color(*C_MUTED)
    pdf.cell(0, 6, "Ашпозчу жабдыктарын текшерүү — Сессия отчету",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)

    # Session meta
    started = session.started_at.strftime("%d.%m.%Y %H:%M") if session.started_at else "—"
    ended   = session.ended_at.strftime("%d.%m.%Y %H:%M") if session.ended_at else "Жүрүп жатат"
    pdf._f("", 9)
    pdf.set_text_color(*C_MUTED)
    pdf.cell(0, 5, f"Сессия ID: {session.session_id}   |   Баштоо: {started}   |   Аяктоо: {ended}",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)

    # KPI
    rate = session.compliance_rate
    pdf.section("Жыйынтык")
    pdf.kpi_row([
        ("Жалпы текшерүү",  session.total_checks,  C_DARK),
        ("Шарт аткарылды",  session.total_checks - session.violations, C_GREEN),
        ("Бузуулар",        session.violations,    C_RED),
        ("Compliance %",    f"{rate:.1f}%",         _pct_color(rate)),
    ])

    # Progress bar
    pdf._f("", 8)
    pdf.set_text_color(*C_MUTED)
    pdf.cell(0, 5, "Compliance деңгээли:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    _compliance_bar(pdf, rate)

    # Records table
    if records:
        pdf.section("Текшерүүлөр")
        headers   = ["Убакыт", "Адам", "Шляпа", "Шляпа%", "Фартук", "Фартук%", "Статус", "Бузуулар"]
        col_w     = [30, 14, 16, 16, 16, 16, 20, 46]
        aligns    = ["L","C","C","R","C","R","C","L"]

        rows = []
        for r in records:
            ts     = r.timestamp.strftime("%d.%m %H:%M:%S") if r.timestamp else "—"
            status = "OK" if r.is_compliant else "БУЗУУ"
            viols  = (r.violations or "").replace("|", ", ")[:38]
            rows.append([
                ts,
                str(r.person_count),
                "ИЙЕ" if r.has_hat else "ЖОК",
                f"{r.hat_confidence:.0%}",
                "ИЙЕ" if r.has_apron else "ЖОК",
                f"{r.apron_confidence:.0%}",
                status,
                viols or "—",
            ])
        pdf.table(headers, rows, col_w, aligns)

    return bytes(pdf.output())


# ─── Дата диапазону отчету ──────────────────────────────────────────────────
def build_range_report(records_qs, sessions_qs, date_from, date_to, weekly_trend, top_violations) -> bytes:
    pdf = ChefPDF("Жалпы отчет")
    pdf.add_page()

    # Title
    pdf._f("B", 18)
    pdf.set_text_color(*C_DARK)
    pdf.cell(0, 10, "Chef Control", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf._f("", 11)
    pdf.set_text_color(*C_MUTED)
    pdf.cell(0, 6, "Ашпозчу жабдыктарын текшерүү — Жалпы отчет",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)

    d_from = date_from.strftime("%d.%m.%Y") if date_from else "—"
    d_to   = date_to.strftime("%d.%m.%Y")   if date_to   else "—"
    pdf._f("", 9)
    pdf.set_text_color(*C_MUTED)
    pdf.cell(0, 5, f"Мезгил: {d_from} — {d_to}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)

    # KPI
    total   = records_qs.count()
    viols   = records_qs.filter(is_compliant=False).count()
    rate    = round((total - viols) / total * 100, 1) if total else 0.0
    sessions_cnt = sessions_qs.count()

    pdf.section("Жыйынтык")
    pdf.kpi_row([
        ("Жалпы текшерүү",  total,        C_DARK),
        ("Шарт аткарылды",  total - viols, C_GREEN),
        ("Бузуулар",        viols,         C_RED),
        ("Compliance %",    f"{rate:.1f}%", _pct_color(rate)),
    ])
    _compliance_bar(pdf, rate)

    pdf._f("", 9)
    pdf.set_text_color(*C_MUTED)
    pdf.cell(0, 5, f"Жалпы сессиялар: {sessions_cnt}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(3)

    # Weekly trend table
    if weekly_trend:
        pdf.section("7 Күндүк Тренд")
        headers = ["Дата", "Текшерүү", "Шарт аткарылды", "Бузуулар", "Compliance %"]
        col_w   = [30, 30, 40, 30, 44]
        aligns  = ["L", "R", "R", "R", "R"]
        rows = []
        for d in weekly_trend:
            c   = d.get("checks", 0)
            v   = d.get("violations", 0)
            ok  = d.get("compliant",  c - v)
            r   = round(ok / c * 100, 1) if c else 0.0
            rows.append([d["date"], str(c), str(ok), str(v), f"{r:.1f}%"])
        pdf.table(headers, rows, col_w, aligns)

    # Top violations
    if top_violations:
        pdf.section("Эң Кеп Кездешкен Бузуулар")
        headers = ["Бузуу", "Жолу"]
        col_w   = [140, 34]
        aligns  = ["L", "R"]
        rows    = [[v["name"], str(v["count"])] for v in top_violations]
        pdf.table(headers, rows, col_w, aligns)

    # Sessions summary
    sessions_list = list(sessions_qs.order_by("-started_at")[:30])
    if sessions_list:
        pdf.section("Сессиялар")
        headers = ["Сессия ID", "Баштоо", "Текшерүү", "Бузуу", "Compliance %"]
        col_w   = [52, 36, 24, 20, 42]
        aligns  = ["L", "L", "R", "R", "R"]
        rows = []
        for s in sessions_list:
            started = s.started_at.strftime("%d.%m.%Y %H:%M") if s.started_at else "—"
            rows.append([
                s.session_id[:22],
                started,
                str(s.total_checks),
                str(s.violations),
                f"{s.compliance_rate:.1f}%",
            ])
        pdf.table(headers, rows, col_w, aligns)

    return bytes(pdf.output())
