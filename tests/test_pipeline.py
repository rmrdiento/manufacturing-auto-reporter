import tempfile
import unittest
from pathlib import Path

import pandas as pd
from openpyxl import load_workbook

import generate_data
import pipeline
from reporters import excel_reporter, html_reporter


def frame(**over):
    row = dict(date="2026-01-01", line="Line A", shift="Day", planned_time_min=480,
               downtime_min=48, downtime_reason="Changeover", ideal_rate=10.0,
               total_output=3456, defects=69)
    return pd.DataFrame([{**row, **over}])


class PipelineTest(unittest.TestCase):
    def test_oee(self):
        # run 432/480 = 0.9, performance 3456/4320 = 0.8, quality 3387/3456 = 0.98
        k = pipeline.summarize(frame()).iloc[0]
        self.assertAlmostEqual(k.availability, 0.9)
        self.assertAlmostEqual(k.performance, 0.8)
        self.assertAlmostEqual(k.oee, 0.9 * 0.8 * (3456 - 69) / 3456)

    def test_validate_rejects_bad_rows(self):
        df = pd.concat([frame(), frame(), frame(line="Line B", total_output=-1),
                        frame(line="Line C", planned_time_min=0)], ignore_index=True)
        clean, issues = pipeline.validate(df)
        self.assertEqual(issues, {"duplicates": 1, "invalid": 2})
        self.assertEqual(len(clean), 1)

    def test_end_to_end_exports(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            generate_data.generate(tmp / "d.csv", days=5)
            report = pipeline.run(tmp / "d.csv", tmp / "p.db")
            self.assertEqual(report["issues"], {"duplicates": 0, "invalid": 0})
            excel_reporter.write(report, tmp / "r.xlsx")
            html_reporter.write(report, tmp / "r.html")
            wb = load_workbook(tmp / "r.xlsx")
            self.assertEqual(wb.sheetnames, ["KPI Summary", "Line x Shift", "Scrap Trend"])
            self.assertEqual(len(wb["Scrap Trend"]._charts), 1)
            self.assertEqual(wb["Line x Shift"].max_row, 7)
            self.assertNotIn("http", (tmp / "r.html").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
