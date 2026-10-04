-- Indexes for faster complaint analysis

CREATE INDEX IF NOT EXISTS idx_complaints_date_received
ON complaints (date_received);

CREATE INDEX IF NOT EXISTS idx_complaints_product
ON complaints (product);

CREATE INDEX IF NOT EXISTS idx_complaints_company
ON complaints (company);

CREATE INDEX IF NOT EXISTS idx_complaints_state
ON complaints (state);

CREATE INDEX IF NOT EXISTS idx_complaints_year_product
ON complaints (received_year, product);

CREATE INDEX IF NOT EXISTS idx_complaints_year_month
ON complaints (received_year, received_month);