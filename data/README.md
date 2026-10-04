# Data Directory

The full cleaned complaint-level CSV contains 490,639 records and is not stored in this repository because it exceeds GitHub's individual file-size limit.

The small files in `processed/` are included because they power the Streamlit dashboard.

To reproduce the complete analysis:

1. Download the relevant complaint data from the [CFPB Consumer Complaint Database](https://www.consumerfinance.gov/data-research/consumer-complaints/).
2. Save the downloaded source files locally.
3. Run `combine_clean_cfpb.py` to create `cfpb_complaints_2023_2025_clean.csv`.
4. Import the cleaned CSV into PostgreSQL using the table definition in `sql/01_create_table.sql`.

The large cleaned CSV is intentionally listed in `.gitignore`.
