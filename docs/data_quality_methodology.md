# Data Quality and Reproducibility Notes

## Purpose

These checks make the Consumer Financial Complaints analysis easier to inspect and reproduce. They surface exceptions for review; a non-zero result is not automatically a failure.

## Cleaning decisions

The Python script \`combine_clean_cfpb.py\`:

- accepts a ZIP archive or a directory containing top-level CSV files;
- reads CSVs with UTF-8 BOM support and normalizes whitespace in text values;
- requires a complaint ID and a parseable received date;
- retains a complaint when its received date is valid even if the sent-to-company date is missing or malformed;
- leaves the sent date and elapsed days blank when the sent date is missing or malformed, and reports these cases separately;
- skips rows with a missing complaint ID or an unparseable received date;
- keeps the first valid occurrence of a complaint ID encountered in sorted input-file order;
- derives year, month, month name and year-month from the received date;
- derives \`days_to_send_to_company\` only when the sent date is parseable;
- reports rows written, duplicate IDs removed, skipped rows, sent-date exceptions, date coverage, counts by year/product/source file and blank values.

A parseable sent date earlier than the received date is retained but counted in \`rows_with_sent_before_received\` for investigation. The extended SQL checks also flag this condition. The duplicate rule is first-valid-row-wins, so source-file ordering can affect which copy is retained when duplicate IDs have conflicting values. Directory input is not recursive.

## Evidence files

- [Python cleaning script](../combine_clean_cfpb.py)
- [Automated regression tests](../tests/test_combine_clean_cfpb.py)
- [Recorded quality report](../data_quality_report.json)
- [SQL table definition](../sql/01_create_table.sql)
- [Initial SQL quality checks](../sql/03_data_quality_checks.sql)
- [Extended SQL validation checks](../sql/06_extended_data_quality_checks.sql)
- [Dashboard screenshots](../screenshots/)
- [Business case and limitations](business_case.md)

The committed JSON is a record of a prior run, not proof that a future refresh will produce the same counts. Re-run the script on the same source extracts to reproduce the report.

## How to reproduce

1. Download the required public complaint extracts from the [CFPB Consumer Complaint Database](https://www.consumerfinance.gov/data-research/consumer-complaints/).
2. Put the ZIP archive or CSV files in a local input directory. The script scans only the top level of a directory; it does not recursively scan subdirectories.
3. Run the cleaning script, for example:

   \`\`\`bash
   python combine_clean_cfpb.py path/to/cfpb_csvs \\
     --output cfpb_complaints_2023_2025_clean.csv \\
     --report data_quality_report.json
   \`\`\`

4. Run the standard-library regression tests from the repository root:

   \`\`\`bash
   python -m unittest discover -s tests -v
   \`\`\`

5. Create the PostgreSQL table using \`sql/01_create_table.sql\`, then load the cleaned CSV using your PostgreSQL import method.
6. Run \`sql/03_data_quality_checks.sql\` and \`sql/06_extended_data_quality_checks.sql\`.
7. Run \`sql/05_business_analysis.sql\` and compare the outputs with the key findings and the processed dashboard summaries.
8. For a dashboard check, install \`requirements.txt\` and run \`python -m streamlit run app.py\`.

## Recorded baseline from the committed report

The currently committed \`data_quality_report.json\` records these results for its prior run:

| Check | Recorded value |
|---|---:|
| Rows written | 490,639 |
| Unique complaint IDs | 490,639 |
| Duplicate rows removed | 0 |
| Invalid rows skipped | 0 |
| Earliest received date | 2023-01-01 |
| Latest received date | 2025-12-31 |
| 2023 rows | 107,392 |
| 2024 rows | 163,608 |
| 2025 rows | 219,639 |

Use these as comparison values only when reproducing the same source extracts and filtering rules. The new script distinguishes missing/invalid sent dates from skipped rows; differences from the historical report should be investigated rather than forced to match.

## What to inspect in validation output

- **Row counts:** compare loaded rows with the report's \`rows_written\`.
- **Unique IDs:** complaint IDs should be unique; the table primary key also enforces this at load time.
- **Sent dates:** inspect \`rows_retained_missing_sent_date\`, \`rows_retained_invalid_sent_date\`, and \`rows_with_sent_before_received\`. Missing dates are retained, not imputed.
- **Date logic:** investigate sent-before-received rows and mismatches between dates and derived day/year/month columns.
- **Categorical values:** inspect unexpected response values before recoding.
- **Reconciliation:** monthly totals should reconcile to the table total. Product totals should reconcile if every product is included. State/company/issue summaries may differ when they intentionally filter missing values or show only top entries.
- **Missingness:** distinguish expected missing values from accidental blanks; do not fill missing categories without documenting the rule.

## Interpretation limitations

- These records measure complaints submitted to the CFPB, not all customer experiences.
- Raw complaint counts are not rates adjusted for customer base, account volume or state population.
- A complaint is not, by itself, proof of wrongdoing.
- A timely response is not the same as a satisfactory resolution.
- The January 2025 increase is descriptive. Product/issue breakdowns can identify where the increase appears, but do not establish why it happened.
