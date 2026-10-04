-- Business Question 1:
-- How has complaint volume changed each year?

WITH yearly_complaints AS (
    SELECT
        received_year,
        COUNT(*) AS total_complaints
    FROM complaints
    GROUP BY received_year
),
yearly_growth AS (
    SELECT
        received_year,
        total_complaints,
        LAG(total_complaints) OVER (
            ORDER BY received_year
        ) AS previous_year_complaints
    FROM yearly_complaints
)
SELECT
    received_year,
    total_complaints,
    previous_year_complaints,
    ROUND(
        100.0 * (
            total_complaints - previous_year_complaints
        ) / NULLIF(previous_year_complaints, 0),
        2
    ) AS year_over_year_growth_pct
FROM yearly_growth
ORDER BY received_year;



-- Business Question 2:
-- Which financial products generate the most complaints?

WITH product_summary AS (
    SELECT
        product,
        COUNT(*) AS total_complaints
    FROM complaints
    GROUP BY product
)
SELECT
    product,
    total_complaints,
    ROUND(
        100.0 * total_complaints
        / SUM(total_complaints) OVER (),
        2
    ) AS percentage_of_all_complaints,
    RANK() OVER (
        ORDER BY total_complaints DESC
    ) AS complaint_rank
FROM product_summary
ORDER BY total_complaints DESC;



-- Business Question 3:
-- What are the top five complaint issues within each product?

WITH issue_counts AS (
    SELECT
        product,
        issue,
        COUNT(*) AS total_complaints
    FROM complaints
    WHERE issue IS NOT NULL
    GROUP BY product, issue
),
ranked_issues AS (
    SELECT
        product,
        issue,
        total_complaints,
        ROW_NUMBER() OVER (
            PARTITION BY product
            ORDER BY total_complaints DESC
        ) AS issue_rank
    FROM issue_counts
)
SELECT
    product,
    issue,
    total_complaints,
    issue_rank
FROM ranked_issues
WHERE issue_rank <= 5
ORDER BY product, issue_rank;



-- Business Question 4:
-- How effectively are companies responding to complaints?

SELECT
    product,
    COUNT(*) AS total_complaints,
    COUNT(*) FILTER (
        WHERE timely_response = 'Yes'
    ) AS timely_responses,
    COUNT(*) FILTER (
        WHERE timely_response = 'No'
    ) AS late_responses,
    ROUND(
        100.0 * COUNT(*) FILTER (
            WHERE timely_response = 'Yes'
        ) / COUNT(*),
        2
    ) AS timely_response_rate_pct,
    ROUND(
        AVG(days_to_send_to_company),
        2
    ) AS average_days_to_send
FROM complaints
GROUP BY product
ORDER BY timely_response_rate_pct DESC;




-- Business Question 5:
-- Which high-volume companies have the highest late-response rates?

WITH company_performance AS (
    SELECT
        company,
        COUNT(*) AS total_complaints,
        COUNT(*) FILTER (
            WHERE timely_response = 'No'
        ) AS late_responses
    FROM complaints
    GROUP BY company
    HAVING COUNT(*) >= 500
)
SELECT
    company,
    total_complaints,
    late_responses,
    ROUND(
        100.0 * late_responses
        / total_complaints,
        2
    ) AS late_response_rate_pct
FROM company_performance
ORDER BY late_response_rate_pct DESC,
         total_complaints DESC
LIMIT 15;



-- Business Question 6:
-- How did complaint volume change year over year for each product?

WITH annual_product_complaints AS (
    SELECT
        received_year,
        product,
        COUNT(*) AS total_complaints
    FROM complaints
    GROUP BY received_year, product
)
SELECT
    current_year.received_year,
    current_year.product,
    current_year.total_complaints,
    previous_year.total_complaints
        AS previous_year_complaints,
    ROUND(
        100.0 * (
            current_year.total_complaints
            - previous_year.total_complaints
        ) / NULLIF(previous_year.total_complaints, 0),
        2
    ) AS year_over_year_growth_pct
FROM annual_product_complaints AS current_year
LEFT JOIN annual_product_complaints AS previous_year
    ON current_year.product = previous_year.product
    AND current_year.received_year =
        previous_year.received_year + 1
ORDER BY
    current_year.product,
    current_year.received_year;




    -- Business Question 7:
-- What is the monthly complaint trend and three-month moving average?

WITH monthly_complaints AS (
    SELECT
        DATE_TRUNC('month', date_received)::DATE
            AS complaint_month,
        COUNT(*) AS total_complaints
    FROM complaints
    GROUP BY DATE_TRUNC('month', date_received)
)
SELECT
    complaint_month,
    total_complaints,
    ROUND(
        AVG(total_complaints) OVER (
            ORDER BY complaint_month
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ),
        2
    ) AS three_month_moving_average
FROM monthly_complaints
ORDER BY complaint_month;



-- Business Question 8:
-- Which states generate the highest complaint volumes?

WITH state_summary AS (
    SELECT
        state,
        COUNT(*) AS total_complaints,
        COUNT(*) FILTER (
            WHERE timely_response = 'No'
        ) AS late_responses
    FROM complaints
    WHERE state IS NOT NULL
      AND LENGTH(state) = 2
    GROUP BY state
)
SELECT
    state,
    total_complaints,
    ROUND(
        100.0 * total_complaints
        / SUM(total_complaints) OVER (),
        2
    ) AS percentage_of_state_complaints,
    late_responses,
    ROUND(
        100.0 * late_responses
        / total_complaints,
        2
    ) AS late_response_rate_pct
FROM state_summary
ORDER BY total_complaints DESC
LIMIT 10;


-- Business Question 9:
-- Which products and issues drove the January 2025 complaint spike?

WITH january_2025_summary AS (
    SELECT
        product,
        issue,
        COUNT(*) AS total_complaints
    FROM complaints
    WHERE date_received >= DATE '2025-01-01'
      AND date_received < DATE '2025-02-01'
      AND issue IS NOT NULL
    GROUP BY product, issue
),
ranked_drivers AS (
    SELECT
        product,
        issue,
        total_complaints,
        ROW_NUMBER() OVER (
            PARTITION BY product
            ORDER BY total_complaints DESC
        ) AS issue_rank
    FROM january_2025_summary
)
SELECT
    product,
    issue,
    total_complaints,
    issue_rank
FROM ranked_drivers
WHERE issue_rank <= 3
ORDER BY product, issue_rank;