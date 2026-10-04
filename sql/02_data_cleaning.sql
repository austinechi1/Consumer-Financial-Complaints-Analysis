UPDATE complaints
SET
    sub_product = NULLIF(TRIM(sub_product), 'None'),
    issue = NULLIF(TRIM(issue), 'None'),
    sub_issue = NULLIF(TRIM(sub_issue), 'None'),
    company_public_response =
        NULLIF(TRIM(company_public_response), 'None'),
    state = NULLIF(TRIM(state), 'None'),
    zip_code = NULLIF(TRIM(zip_code), 'None'),
    tags = NULLIF(TRIM(tags), 'None'),
    submitted_via = NULLIF(TRIM(submitted_via), 'None'),
    company_response_to_consumer =
        NULLIF(TRIM(company_response_to_consumer), 'None'),
    timely_response =
        NULLIF(TRIM(timely_response), 'None');