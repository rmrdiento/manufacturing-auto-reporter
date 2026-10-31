from openpyxl import Workbook
from openpyxl.chart import LineChart, Reference
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

from pipeline import TARGETS, status

NAVY, WHITE = "1F3A5F", "FFFFFF"
FILL = {"good": "C6EFCE", "warn": "FFEB9C", "bad": "FFC7CE"}
INK = {"good": "006100", "warn": "9C5700", "bad": "9C0006"}
THIN = Side(style="thin", color="D0D7DE")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
PCT, INT = "0.0%", "#,##0"

KPIS = [("OEE", "oee"), ("Availability", "availability"), ("Performance", "performance"),
        ("Quality", "quality"), ("Scrap Rate", "scrap_rate")]


def _header(ws, row, titles):
    for col, t in enumerate(titles, 1):
        c = ws.cell(row, col, t)
        c.font = Font(bold=True, color=WHITE)
        c.fill = PatternFill("solid", fgColor=NAVY)
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.border = BORDER


def _row(ws, row, values, formats):
    for col, (v, fmt) in enumerate(zip(values, formats), 1):
        c = ws.cell(row, col, v)
        c.number_format = fmt
        c.border = BORDER


def _flag(cell, metric, value):
    s = status(metric, value)
    cell.fill = PatternFill("solid", fgColor=FILL[s])
    cell.font = Font(bold=True, color=INK[s])


def _widths(ws, widths):
    for col, w in enumerate(widths, 1):
        ws.column_dimensions[chr(64 + col)].width = w


def write(report, path):
    wb = Workbook()

    ws = wb.active
    ws.title = "KPI Summary"
    ws["A1"] = "Manufacturing KPI Summary"
    ws["A1"].font = Font(bold=True, size=16, color=NAVY)
    ws["A2"] = "Period: {} to {}".format(*report["period"])
    _header(ws, 4, ["Metric", "Value", "Target", "Status"])
    for i, (name, key) in enumerate(KPIS, 5):
        value = report["kpi"][key]
        target = "≤ {:.0%}" if key == "scrap_rate" else "≥ {:.0%}"
        _row(ws, i, [name, value, target.format(TARGETS[key][0]),
                     status(key, value).upper()], ["@", PCT, "@", "@"])
        _flag(ws.cell(i, 2), key, value)
        _flag(ws.cell(i, 4), key, value)
    top = 5 + len(KPIS) + 1
    ws.cell(top, 1, "Downtime Pareto").font = Font(bold=True, size=12, color=NAVY)
    _header(ws, top + 1, ["Reason", "Minutes", "Share", "Cumulative"])
    for i, (reason, r) in enumerate(report["pareto"].iterrows(), top + 2):
        _row(ws, i, [reason, int(r.minutes), r.share, r.cumulative], ["@", INT, PCT, PCT])
    ws.freeze_panes = "A5"
    _widths(ws, [22, 14, 12, 14])

    ws = wb.create_sheet("Line x Shift")
    _header(ws, 1, ["Line", "Shift", "Output", "Defects", "Downtime (min)",
                    "Availability", "Performance", "Quality", "OEE", "Scrap Rate"])
    for i, ((line, shift), r) in enumerate(report["matrix"].iterrows(), 2):
        _row(ws, i, [line, shift, int(r.total_output), int(r.defects), int(r.downtime_min),
                     r.availability, r.performance, r.quality, r.oee, r.scrap_rate],
             ["@", "@", INT, INT, INT, PCT, PCT, PCT, PCT, PCT])
        _flag(ws.cell(i, 9), "oee", r.oee)
        _flag(ws.cell(i, 10), "scrap_rate", r.scrap_rate)
    ws.freeze_panes = "C2"
    _widths(ws, [12, 10, 12, 10, 16, 14, 14, 12, 10, 12])

    ws = wb.create_sheet("Scrap Trend")
    trend = report["trend"]
    _header(ws, 1, ["Date", *trend.columns])
    for i, (day, r) in enumerate(trend.iterrows(), 2):
        _row(ws, i, [day, *r], ["@"] + [PCT] * len(r))
    ws.freeze_panes = "B2"
    _widths(ws, [14, 12, 12, 12])
    chart = LineChart()
    chart.title, chart.height, chart.width = "Scrap Rate by Line", 9, 22
    chart.y_axis.title, chart.y_axis.number_format = "Scrap rate", "0%"
    chart.add_data(Reference(ws, min_col=2, max_col=1 + len(trend.columns), min_row=1, max_row=1 + len(trend)),
                   titles_from_data=True)
    chart.set_categories(Reference(ws, min_col=1, min_row=2, max_row=1 + len(trend)))
    chart.x_axis.delete = chart.y_axis.delete = False
    ws.add_chart(chart, "F2")

    wb.save(path)
