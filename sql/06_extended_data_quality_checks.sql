-- Extended validation checks for the complaints table.
-- Run after loading the cleaned CSV and creating the complaints table.
-- Each query returns exceptions or reconciliation figures; investigate exceptions
-- rather than assuming that every non-zero count is automatically an error.

-- 1. Check blank strings in key categorical fields.
SELECT
    COUNT(*) FILTER (WHERE product IS NULL OR TRIM(product) = '') AS blank_product,
    COUNT(*) FILTER (WHERE company IS NULL OR TRIM(company) = '') AS blank_company,
    COUNT(*) FILTER (WHERE issue IS NULL OR TRIM(issue) = '') AS blank_issue,
    COUNT(*) FILTER (WHERE state IS NULL OR TRIM(state) = '') AS blank_state,
    COUNT(*) FILTER (WHERE timely_response IS NULL OR TRIM(timely_response) = '') AS blank_timely_response
FROM complaints;

-- 2. Check dates and derived elapsed-day values for inconsistencies.
SELECT
    COUNT(*) FILTER (WHERE date_sent_to_company < date_received)
        AS sent_before_received,
    COUNT(*) FILTER (
        WHERE days_to_send_to_company IS DISTINCT FROM
              CASE WHEN date_sent_to_company IS NOT NULL
                   THEN (date_sent_to_company - date_received)
                   ELSE NULL
              END
    ) AS elapsed_days_mismatch,
    COUNT(*) FILTER (
        WHERE received_year <> EXTRACT(YEAR FROM date_received)::INTEGER
    ) AS received_year_mismatch,
    COUNT(*) FILTER (
        WHERE received_month <> EXTRACT(MONTH FROM date_received)::INTEGER
    ) AS received_month_mismatch,
    COUNT(*) FILTER (
        WHERE received_year_month <>
              TO_CHAR(date_received, 'YYYY-MM')
    ) AS received_year_month_mismatch
FROM complaints;

-- 3. Inspect response values outside the expected Yes/No categories.
-- Review returned values before recoding; do not silently discard them.
SELECT
    COALESCE(NULLIF(TRIM(timely_response), ''), '[blank/null]') AS response_value,
    COUNT(*) AS row_count
FROM complaints
GROUP BY 1
ORDER BY row_count DESC;

-- 4. Reconcile total rows by year against the full table.
SELECT
    received_year,
    COUNT(*) AS rows_in_table,
    COUNT(DISTINCT complaint_id) AS distinct_complaint_ids,
    COUNT(*) - COUNT(DISTINCT complaint_id) AS duplicate_id_difference
FROM complaints
GROUP BY received_year
ORDER BY received_year;

-- 5. Check that monthly counts reconcile to the table total.
WITH monthly AS (
    SELECT
        DATE_TRUNC('month', date_received)::DATE AS complaint_month,
        COUNT(*) AS monthly_rows
    FROM complaints
    GROUP BY 1
)
SELECT
    SUM(monthly_rows) AS rows_across_months,
    (SELECT COUNT(*) FROM complaints) AS rows_in_table,
    SUM(monthly_rows) - (SELECT COUNT(*) FROM complaints) AS difference
FROM monthly;

-- 6. Check response-count consistency by product.
SELECT
    product,
    COUNT(*) AS total_complaints,
    COUNT(*) FILTER (WHERE timely_response = 'Yes') AS timely_responses,
    COUNT(*) FILTER (WHERE timely_response = 'No') AS late_responses,
    COUNT(*) FILTER (
        WHERE timely_response IS NULL
           OR TRIM(timely_response) NOT IN ('Yes', 'No')
    ) AS unclassified_response_rows,
    COUNT(*) -
        COUNT(*) FILTER (WHERE timely_response = 'Yes') -
        COUNT(*) FILTER (WHERE timely_response = 'No') AS response_count_difference
FROM complaints
GROUP BY product
ORDER BY product;
