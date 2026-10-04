SELECT
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (WHERE state = 'None') AS state_none_text,
    COUNT(*) FILTER (WHERE state IS NULL) AS state_nulls,
    COUNT(*) FILTER (WHERE sub_product = 'None') AS sub_product_none_text,
    COUNT(*) FILTER (WHERE sub_product IS NULL) AS sub_product_nulls,
    COUNT(*) FILTER (
        WHERE company_public_response = 'None'
    ) AS public_response_none_text,
    COUNT(*) FILTER (
        WHERE company_public_response IS NULL
    ) AS public_response_nulls
FROM complaints;