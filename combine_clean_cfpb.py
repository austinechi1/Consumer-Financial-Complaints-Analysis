#!/usr/bin/env python3
"""Combine and clean CFPB complaint CSV exports using Python's standard library."""

from __future__ import annotations

import argparse
import csv
import json
import re
import zipfile
from collections import Counter
from datetime import datetime
from pathlib import Path


OUTPUT_COLUMNS = [
    "complaint_id",
    "date_received",
    "received_year",
    "received_month",
    "received_month_name",
    "received_year_month",
    "product",
    "sub_product",
    "issue",
    "sub_issue",
    "company",
    "company_public_response",
    "state",
    "zip_code",
    "tags",
    "submitted_via",
    "date_sent_to_company",
    "days_to_send_to_company",
    "company_response_to_consumer",
    "timely_response",
]


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip()


def parse_date(value: str) -> datetime:
    value = value.strip()
    for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass
    raise ValueError(f"Unsupported date format: {value!r}")


def iter_csv_sources(input_path: Path):
    if input_path.suffix.lower() == ".zip":
        archive = zipfile.ZipFile(input_path)
        try:
            for member in sorted(archive.infolist(), key=lambda item: item.filename):
                if member.is_dir() or not member.filename.lower().endswith(".csv"):
                    continue
                raw = archive.open(member)
                text = __import__("io").TextIOWrapper(raw, encoding="utf-8-sig", newline="")
                yield member.filename, text
                text.close()
        finally:
            archive.close()
    elif input_path.is_dir():
        for csv_path in sorted(input_path.glob("*.csv")):
            with csv_path.open("r", encoding="utf-8-sig", newline="") as text:
                yield csv_path.name, text
    else:
        raise ValueError("Input must be a ZIP file or a directory containing CSV files.")


def combine_and_clean(input_path: Path, output_csv: Path, report_path: Path) -> None:
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    seen_ids: set[str] = set()
    product_counts: Counter[str] = Counter()
    year_counts: Counter[str] = Counter()
    file_counts: Counter[str] = Counter()
    missing_counts: Counter[str] = Counter()
    duplicate_rows = 0
    invalid_rows = 0
    written_rows = 0
    minimum_date: datetime | None = None
    maximum_date: datetime | None = None

    with output_csv.open("w", encoding="utf-8", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()

        for source_name, source in iter_csv_sources(input_path):
            reader = csv.DictReader(source)
            for row in reader:
                complaint_id = clean_text(row.get("Complaint ID"))
                if not complaint_id:
                    invalid_rows += 1
                    continue
                if complaint_id in seen_ids:
                    duplicate_rows += 1
                    continue

                try:
                    received = parse_date(row.get("Date received", ""))
                    sent = parse_date(row.get("Date sent to company", ""))
                except ValueError:
                    invalid_rows += 1
                    continue

                seen_ids.add(complaint_id)
                product = clean_text(row.get("Product"))
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
                    "date_sent_to_company": sent.strftime("%Y-%m-%d"),
                    "days_to_send_to_company": (sent.date() - received.date()).days,
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
