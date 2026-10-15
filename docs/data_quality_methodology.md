# Data Quality and Reproducibility Notes

## Purpose

These checks make the Consumer Financial Complaints analysis easier to inspect and reproduce. They are intended to surface exceptions for review, not to make every non-zero result an automatic failure.

## Cleaning decisions currently implemented

The Python script `combine_clean_cfpb.py`:

- accepts a ZIP archive or a directory containing CSV files;
- reads CSVs with UTF-8 BOM support;
- standardizes whitespace in text values;
- requires a complaint ID and parseable received and sent-to-company dates;
- skips rows with missing complaint IDs or dates that cannot be parsed;
- keeps the first valid occurrence of each complaint ID encountered in sorted input-file order;
- derives year, month, month name and year-month from the received date;
- derives `days_to_send_to_company` as sent date minus received date;
- writes the cleaned CSV and a JSON report with row counts, date coverage, counts by year/product/source file, skipped rows and blank values.

**Important behavior to know:** a row with an unparseable or missing sent-to-company date is currently counted as invalid and skipped, even though the database schema allows that date to be nullable. This is a conservative limitation of the current script and should be reconsidered before refreshing the dataset. The duplicate rule is first-valid-row-wins, so source-file ordering can affect which copy is retained when duplicate IDs have conflicting values.

## Existing evidence

- [Python cleaning script](../combine_clean_cfpb.py)
- [Recorded quality report](../data_quality_report.json)
- [SQL table definition](../sql/01_create_table.sql)
- [Initial SQL quality checks](../sql/03_data_quality_checks.sql)
- [Extended SQL validation checks](../sql/06_extended_data_quality_checks.sql)
- [Dashboard screenshots](../screenshots/)
- [Business case and limitations](business_case.md)

The committed JSON is a record of a prior run. It is not proof that a future refresh produces the same results. Re-run the script on the same source extracts to reproduce the report.

## How to reproduce

1. Download the required public complaint extracts from the [CFPB Consumer Complaint Database](https://www.consumerfinance.gov/data-research/consumer-complaints/).
2. Put the ZIP archive or CSV files in a local input directory. The script scans only the top level of a directory; it does not recursively scan subdirectories.
3. Run the cleaning script, for example:

   ```bash
   python combine_clean_cfpb.py path/to/cfpb_csvs \
     --output cfpb_complaints_2023_2025_clean.csv \
     --report data_quality_report.json
   ```

4. Create the PostgreSQL table using `sql/01_create_table.sql`, then load the cleaned CSV using your PostgreSQL import method.
5. Run `sql/03_data_quality_checks.sql` and `sql/06_extended_data_quality_checks.sql`.
6. Run `sql/05_business_analysis.sql` and compare the outputs with the key findings and the processed dashboard summaries.
7. For a dashboard check, run `python -m streamlit run app.py` after installing `requirements.txt`.

## Recorded baseline from the committed report

The currently committed `data_quality_report.json` records these results for its prior run:

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

Use these as comparison values only when reproducing the same source extracts and filtering rules. If the source data or cleaning logic changes, investigate and document any differences rather than forcing the output to match these numbers.

## What to inspect in the validation output

- **Row counts:** compare loaded rows with the JSON report's `rows_written`.
- **Unique IDs:** complaint IDs should be unique; the table's primary key also enforces this at load time.
- **Date logic:** investigate sent-before-received rows and mismatches between dates and derived day/year/month columns.
- **Categorical values:** inspect unexpected response values before recoding.
- **Reconciliation:** monthly totals should reconcile to the table total. Product totals should reconcile if the product summary includes every product in the table. State/company/issue summaries may differ when they intentionally filter missing values or show only top entries.
- **Missingness:** distinguish expected missing values from accidental blanks; do not fill missing categories without documenting the rule.

## Interpretation limitations

- These records measure complaints submitted to the CFPB, not all customer experiences.
- Raw complaint counts are not rates adjusted for customer base, account volume or state population.
- A complaint is not, by itself, proof of wrongdoing.
- A timely response is not the same as a satisfactory resolution.
- The January 2025 increase is a descriptive change. Product/issue breakdowns can identify where the increase appears, but do not establish why it happened.
