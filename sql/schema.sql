CREATE TABLE IF NOT EXISTS clean_sales (
    sale_id BIGSERIAL PRIMARY KEY,
    invoice_no VARCHAR(20) NOT NULL,
    stock_code VARCHAR(30) NOT NULL,
    description TEXT NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    invoice_date TIMESTAMP NOT NULL,
    unit_price NUMERIC(18,6) NOT NULL CHECK (unit_price > 0),
    customer_id VARCHAR(30) NOT NULL,
    country VARCHAR(100) NOT NULL,
    transaction_type VARCHAR(30) NOT NULL
        CHECK (transaction_type = 'sale'),
    total_amount NUMERIC(20,6) NOT NULL
        CHECK (total_amount > 0),
    loaded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS rejected_sales (
    rejected_id BIGSERIAL PRIMARY KEY,
    invoice_no VARCHAR(20),
    stock_code VARCHAR(30),
    description TEXT,
    quantity INTEGER,
    invoice_date TIMESTAMP,
    unit_price NUMERIC(18,6),
    customer_id VARCHAR(30),
    country VARCHAR(100),
    transaction_type VARCHAR(30),
    exclusion_reason VARCHAR(50) NOT NULL,
    is_duplicate BOOLEAN NOT NULL DEFAULT FALSE,
    rejected_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_clean_sales_invoice_no
    ON clean_sales(invoice_no);

CREATE INDEX IF NOT EXISTS idx_clean_sales_customer_id
    ON clean_sales(customer_id);

CREATE INDEX IF NOT EXISTS idx_clean_sales_invoice_date
    ON clean_sales(invoice_date);

CREATE INDEX IF NOT EXISTS idx_clean_sales_country
    ON clean_sales(country);

CREATE INDEX IF NOT EXISTS idx_rejected_sales_reason
    ON rejected_sales(exclusion_reason);