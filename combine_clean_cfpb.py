#!/usr/bin/env python3
"""Combine and clean CFPB complaint CSV exports using Python's standard library."""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
import zipfile
from collections import Counter
from datetime import datetime
from pathlib import Path

OUTPUT_COLUMNS = [
    "complaint_id", "date_received", "received_year", "received_month",
    "received_month_name", "received_year_month", "product", "sub_product",
    "issue", "sub_issue", "company", "company_public_response", "state",
    "zip_code", "tags", "submitted_via", "date_sent_to_company",
    "days_to_send_to_company", "company_response_to_consumer", "timely_response",
]


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip()


def parse_date(value: str | None) -> datetime:
    value = clean_text(value)
    for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass
    raise ValueError(f"Unsupported date format: {value!r}")


def parse_optional_date(value: str | None) -> tuple[datetime | None, str]:
    """Return (date, status), where status is valid, missing, or invalid."""
    if not clean_text(value):
        return None, "missing"
    try:
        return parse_date(value), "valid"
    except ValueError:
        return None, "invalid"


def iter_csv_sources(input_path: Path):
    if input_path.suffix.lower() == ".zip":
        with zipfile.ZipFile(input_path) as archive:
            for member in sorted(archive.infolist(), key=lambda item: item.filename):
                if member.is_dir() or not member.filename.lower().endswith(".csv"):
                    continue
                with archive.open(member) as raw:
                    with io.TextIOWrapper(raw, encoding="utf-8-sig", newline="") as text:
                        yield member.filename, text
    elif input_path.is_dir():
        for csv_path in sorted(input_path.glob("*.csv")):
            with csv_path.open("r", encoding="utf-8-sig", newline="") as text:
                yield csv_path.name, text
    else:
        raise ValueError("Input must be a ZIP file or a directory containing CSV files.")


def combine_and_clean(input_path: Path, output_csv: Path, report_path: Path) -> None:
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    seen_ids: set[str] = set()
    product_counts: Counter[str] = Counter()
    year_counts: Counter[str] = Counter()
    file_counts: Counter[str] = Counter()
    missing_counts: Counter[str] = Counter()
    duplicate_rows = 0
    invalid_rows = 0
    missing_id_rows = 0
    invalid_received_date_rows = 0
    missing_sent_date_rows = 0
    invalid_sent_date_rows = 0
    sent_before_received_rows = 0
    written_rows = 0
    minimum_date: datetime | None = None
    maximum_date: datetime | None = None

    with output_csv.open("w", encoding="utf-8", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()

        for source_name, source in iter_csv_sources(input_path):
            with source:
                reader = csv.DictReader(source)
                for row in reader:
                    complaint_id = clean_text(row.get("Complaint ID"))
                    if not complaint_id:
                        invalid_rows += 1
                        missing_id_rows += 1
                        continue
                    if complaint_id in seen_ids:
                        duplicate_rows += 1
                        continue

                    try:
                        received = parse_date(row.get("Date received"))
                    except ValueError:
                        invalid_rows += 1
                        invalid_received_date_rows += 1
                        continue

                    sent, sent_status = parse_optional_date(row.get("Date sent to company"))
                    if sent_status == "missing":
                        missing_sent_date_rows += 1
                    elif sent_status == "invalid":
                        invalid_sent_date_rows += 1

                    seen_ids.add(complaint_id)
                    product = clean_text(row.get("Product"))
                    days_to_send = (sent.date() - received.date()).days if sent else ""
                    if sent and days_to_send < 0:
                        sent_before_received_rows += 1

                    cleaned = {
                        "complaint_id": complaint_id,
                        "date_received": received.strftime("%Y-%m-%d"),
                        "received_year": received.year,
                        "received_month": received.month,
                        "received_month_name": received.strftime("%b"),
                        "received_year_month": received.strftime("%Y-%m"),
                        "product": product,
                        "sub_product": clean_text(row.get("Sub-product")),
                        "issue": clean_text(row.get("Issue")),
                        "sub_issue": clean_text(row.get("Sub-issue")),
                        "company": clean_text(row.get("Company")),
                        "company_public_response": clean_text(row.get("Company public response")),
                        "state": clean_text(row.get("State")),
                        "zip_code": clean_text(row.get("ZIP code")),
                        "tags": clean_text(row.get("Tags")),
                        "submitted_via": clean_text(row.get("Submitted via")),
                        "date_sent_to_company": sent.strftime("%Y-%m-%d") if sent else "",
                        "days_to_send_to_company": days_to_send,
                        "company_response_to_consumer": clean_text(row.get("Company response to consumer")),
                        "timely_response": clean_text(row.get("Timely response?")),
                    }
                    writer.writerow(cleaned)
                    written_rows += 1
                    file_counts[source_name] += 1
                    product_counts[product] += 1
                    year_counts[str(received.year)] += 1
                    minimum_date = received if minimum_date is None or received < minimum_date else minimum_date
                    maximum_date = received if maximum_date is None or received > maximum_date else maximum_date
                    for column in OUTPUT_COLUMNS:
                        if cleaned[column] == "":
                            missing_counts[column] += 1

    report = {
        "output_file": output_csv.name,
        "rows_written": written_rows,
        "unique_complaint_ids": len(seen_ids),
        "duplicate_rows_removed": duplicate_rows,
        "invalid_rows_skipped": invalid_rows,
        "rows_skipped_missing_complaint_id": missing_id_rows,
        "rows_skipped_invalid_received_date": invalid_received_date_rows,
        "rows_retained_missing_sent_date": missing_sent_date_rows,
        "rows_retained_invalid_sent_date": invalid_sent_date_rows,
        "rows_with_sent_before_received": sent_before_received_rows,
        "date_min": minimum_date.strftime("%Y-%m-%d") if minimum_date else None,
        "date_max": maximum_date.strftime("%Y-%m-%d") if maximum_date else None,
        "rows_by_year": dict(sorted(year_counts.items())),
        "rows_by_product": dict(sorted(product_counts.items())),
        "rows_by_source_file": dict(sorted(file_counts.items())),
        "blank_values_by_column": dict(sorted(missing_counts.items())),
    }
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="CFPB ZIP file or directory of CSV files")
    parser.add_argument("--output", type=Path, default=Path("cfpb_complaints_2023_2025_clean.csv"))
    parser.add_argument("--report", type=Path, default=Path("data_quality_report.json"))
    args = parser.parse_args()
    combine_and_clean(args.input, args.output, args.report)
    print(f"Created {args.output}")
    print(f"Created {args.report}")


if __name__ == "__main__":
    main()
