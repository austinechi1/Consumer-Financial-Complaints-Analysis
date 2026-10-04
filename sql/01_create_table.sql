CREATE TABLE complaints (
    complaint_id BIGINT PRIMARY KEY,
    date_received DATE NOT NULL,
    received_year INTEGER NOT NULL,
    received_month INTEGER NOT NULL,
    received_month_name VARCHAR(3) NOT NULL,
    received_year_month VARCHAR(7) NOT NULL,
    product VARCHAR(100) NOT NULL,
    sub_product TEXT,
    issue TEXT,
    sub_issue TEXT,
    company TEXT NOT NULL,
    company_public_response TEXT,
    state VARCHAR(2),
    zip_code VARCHAR(10),
    tags TEXT,
    submitted_via VARCHAR(50),
    date_sent_to_company DATE,
    days_to_send_to_company INTEGER,
    company_response_to_consumer TEXT,
    timely_response VARCHAR(3)
);



