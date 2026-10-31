import argparse
import sys
from pathlib import Path

import generate_data
import pipeline
from reporters import excel_reporter, html_reporter


def main():
    ap = argparse.ArgumentParser(description="Manufacturing & Sales reporting pipeline")
    ap.add_argument("--generate-mock", action="store_true", help="generate 30 days of mock data first")
    ap.add_argument("--csv", default="production_data.csv")
    ap.add_argument("--db", default="production.db")
    ap.add_argument("--out", default="reports")
    args = ap.parse_args()

    if args.generate_mock:
        print(f"Generated {generate_data.generate(args.csv)} rows -> {args.csv}")
    if not Path(args.csv).exists():
        sys.exit(f"{args.csv} not found; run with --generate-mock or pass --csv")

    report = pipeline.run(args.csv, args.db)
    print("Validation:", report["issues"])
    out = Path(args.out)
    out.mkdir(exist_ok=True)
    excel_reporter.write(report, out / "executive_report.xlsx")
    html_reporter.write(report, out / "dashboard.html")
    print(f"OEE {report['kpi'].oee:.1%} | reports -> {out}/")


if __name__ == "__main__":
    main()
