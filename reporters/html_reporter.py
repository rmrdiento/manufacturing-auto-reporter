from jinja2 import Template

from pipeline import status

TEMPLATE = Template("""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Production Dashboard</title>
<style>
:root{--navy:#1f3a5f;--bg:#f4f6f9;--card:#fff;--ink:#1b2430;--mute:#6b7785;
--good:#1e8e5a;--warn:#d99a00;--bad:#c93c3c;--line:#e1e6ec}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,Segoe UI,Arial,sans-serif}
header{background:var(--navy);color:#fff;padding:20px 5vw}
header h1{margin:0;font-size:22px}header p{margin:2px 0 0;opacity:.8}
main{padding:20px 5vw;display:grid;gap:20px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:14px}
.card{background:var(--card);border-radius:8px;padding:14px 16px;border-top:4px solid var(--mute);box-shadow:0 1px 3px #0001}
.card.good{border-color:var(--good)}.card.warn{border-color:var(--warn)}.card.bad{border-color:var(--bad)}
.card small{color:var(--mute);text-transform:uppercase;letter-spacing:.05em}
.card b{display:block;font-size:30px}
section{background:var(--card);border-radius:8px;padding:16px;box-shadow:0 1px 3px #0001;overflow-x:auto}
h2{margin:0 0 12px;font-size:16px;color:var(--navy)}
table{width:100%;border-collapse:collapse}
th,td{padding:8px 10px;text-align:right;border-bottom:1px solid var(--line);white-space:nowrap}
th:first-child,td:first-child,th:nth-child(2),td:nth-child(2){text-align:left}
th{background:var(--navy);color:#fff;font-weight:600}
td.good{background:#d8f1e4}td.warn{background:#fff1c2}td.bad{background:#fbd5d5}
.grid2{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:20px}
.hbar{display:grid;grid-template-columns:140px 1fr 90px;gap:10px;align-items:center;margin:8px 0}
.track{background:var(--line);border-radius:4px;height:16px}
.fill{background:var(--navy);height:100%;border-radius:4px}
.cols{display:flex;align-items:flex-end;gap:3px;height:160px;border-bottom:1px solid var(--mute)}
.cols div{flex:1;background:var(--navy);border-radius:2px 2px 0 0;min-height:2px}
.cols div.bad{background:var(--bad)}
.axis{display:flex;justify-content:space-between;color:var(--mute);font-size:12px;margin-top:4px}
footer{padding:0 5vw 24px;color:var(--mute);font-size:12px}
</style></head><body>
<header><h1>Manufacturing &amp; Sales Dashboard</h1><p>{{ period[0] }} &rarr; {{ period[1] }}</p></header>
<main>
<div class="cards">
{% for name, key, value in kpis %}
<div class="card {{ status(key, value) }}"><small>{{ name }}</small><b>{{ '%.1f%%' % (value * 100) }}</b></div>
{% endfor %}
<div class="card"><small>Total output</small><b>{{ '{:,}'.format(kpi.total_output | int) }}</b></div>
</div>
<section><h2>Line &times; Shift</h2>
<table><tr><th>Line</th><th>Shift</th><th>Output</th><th>Downtime, min</th><th>Availability</th><th>Performance</th><th>Quality</th><th>OEE</th><th>Scrap</th></tr>
{% for (line, shift), r in matrix.iterrows() %}
<tr><td>{{ line }}</td><td>{{ shift }}</td><td>{{ '{:,}'.format(r.total_output | int) }}</td><td>{{ '{:,}'.format(r.downtime_min | int) }}</td>
<td>{{ '%.1f%%' % (r.availability * 100) }}</td><td>{{ '%.1f%%' % (r.performance * 100) }}</td><td>{{ '%.1f%%' % (r.quality * 100) }}</td>
<td class="{{ status('oee', r.oee) }}">{{ '%.1f%%' % (r.oee * 100) }}</td>
<td class="{{ status('scrap_rate', r.scrap_rate) }}">{{ '%.2f%%' % (r.scrap_rate * 100) }}</td></tr>
{% endfor %}</table></section>
<div class="grid2">
<section><h2>Downtime Pareto</h2>
{% for reason, r in pareto.iterrows() %}
<div class="hbar"><span>{{ reason }}</span><div class="track"><div class="fill" style="width:{{ '%.1f' % (r.share * 100) }}%"></div></div>
<span>{{ '{:,}'.format(r.minutes | int) }} min</span></div>
{% endfor %}</section>
<section><h2>Daily scrap rate (plant)</h2>
<div class="cols">
{% for day, v in daily_scrap.items() %}
<div class="{{ 'bad' if status('scrap_rate', v) == 'bad' else '' }}" style="height:{{ '%.1f' % (v / scrap_max * 100) }}%" title="{{ day }}: {{ '%.2f%%' % (v * 100) }}"></div>
{% endfor %}</div>
<div class="axis"><span>{{ period[0] }}</span><span>max {{ '%.2f%%' % (scrap_max * 100) }}</span><span>{{ period[1] }}</span></div>
</section></div>
</main>
<footer>Rows rejected by validation: {{ issues.invalid }} invalid, {{ issues.duplicates }} duplicates.</footer>
</body></html>
""")


def write(report, path):
    kpi, daily = report["kpi"], report["daily"].scrap_rate
    names = [("OEE", "oee"), ("Availability", "availability"), ("Performance", "performance"),
             ("Quality", "quality"), ("Scrap rate", "scrap_rate")]
    html = TEMPLATE.render(
        status=status, kpi=kpi, kpis=[(n, k, kpi[k]) for n, k in names],
        period=report["period"], issues=report["issues"], matrix=report["matrix"],
        pareto=report["pareto"], daily_scrap=daily, scrap_max=daily.max() or 1,
    )
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
