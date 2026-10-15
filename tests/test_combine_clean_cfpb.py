import csv
import json
import tempfile
import unittest
from pathlib import Path

from combine_clean_cfpb import OUTPUT_COLUMNS, combine_and_clean


SOURCE_COLUMNS = [
    "Complaint ID", "Date received", "Product", "Sub-product", "Issue",
    "Sub-issue", "Company", "Company public response", "State", "ZIP code",
    "Tags", "Submitted via", "Date sent to company",
    "Company response to consumer", "Timely response?",
]


def source_row(complaint_id, received, sent, product="Credit card"):
    return {
        "Complaint ID": complaint_id,
        "Date received": received,
        "Product": product,
        "Sub-product": "",
        "Issue": "Billing dispute",
        "Sub-issue": "",
        "Company": "Example Bank",
        "Company public response": "",
        "State": "CA",
        "ZIP code": "90001",
        "Tags": "",
        "Submitted via": "Web",
        "Date sent to company": sent,
        "Company response to consumer": "Closed with explanation",
        "Timely response?": "Yes",
    }


class CombineAndCleanTests(unittest.TestCase):
    def test_retains_missing_or_invalid_sent_dates_and_reports_them(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            input_dir = root / "input"
            input_dir.mkdir()
            source = input_dir / "complaints.csv"
            rows = [
                source_row("1001", "2025-01-02", ""),
                source_row("1002", "2025-01-03", "not-a-date"),
                source_row("1003", "2025-01-04", "2025-01-06"),
            ]
            with source.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=SOURCE_COLUMNS)
                writer.writeheader()
                writer.writerows(rows)

            output = root / "clean.csv"
            report_path = root / "report.json"
            combine_and_clean(input_dir, output, report_path)

            with output.open("r", encoding="utf-8", newline="") as handle:
                cleaned = list(csv.DictReader(handle))
            report = json.loads(report_path.read_text(encoding="utf-8"))

            self.assertEqual(len(cleaned), 3)
            self.assertEqual(cleaned[0]["date_sent_to_company"], "")
            self.assertEqual(cleaned[0]["days_to_send_to_company"], "")
            self.assertEqual(cleaned[1]["date_sent_to_company"], "")
            self.assertEqual(cleaned[2]["days_to_send_to_company"], "2")
            self.assertEqual(report["rows_written"], 3)
            self.assertEqual(report["rows_retained_missing_sent_date"], 1)
            self.assertEqual(report["rows_retained_invalid_sent_date"], 1)
            self.assertEqual(report["invalid_rows_skipped"], 0)
            self.assertEqual(report["blank_values_by_column"]["date_sent_to_company"], 2)

    def test_skips_invalid_received_date_and_deduplicates_valid_ids(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            input_dir = root / "input"
            input_dir.mkdir()
            source = input_dir / "complaints.csv"
            rows = [
                source_row("2001", "bad-date", "2025-01-05"),
                source_row("2002", "2025-01-03", "2025-01-04"),
                source_row("2002", "2025-01-03", "2025-01-06"),
                source_row("", "2025-01-04", "2025-01-05"),
            ]
            with source.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=SOURCE_COLUMNS)
                writer.writeheader()
                writer.writerows(rows)

            output = root / "clean.csv"
            report_path = root / "report.json"
            combine_and_clean(input_dir, output, report_path)

            with output.open("r", encoding="utf-8", newline="") as handle:
                cleaned = list(csv.DictReader(handle))
            report = json.loads(report_path.read_text(encoding="utf-8"))

            self.assertEqual([row["complaint_id"] for row in cleaned], ["2002"])
            self.assertEqual(report["rows_written"], 1)
            self.assertEqual(report["duplicate_rows_removed"], 1)
            self.assertEqual(report["rows_skipped_invalid_received_date"], 1)
            self.assertEqual(report["rows_skipped_missing_complaint_id"], 1)
            self.assertEqual(report["invalid_rows_skipped"], 2)

    def test_output_columns_remain_stable(self):
        self.assertIn("date_sent_to_company", OUTPUT_COLUMNS)
        self.assertIn("days_to_send_to_company", OUTPUT_COLUMNS)
        self.assertEqual(len(OUTPUT_COLUMNS), len(set(OUTPUT_COLUMNS)))


if __name__ == "__main__":
    unittest.main()
