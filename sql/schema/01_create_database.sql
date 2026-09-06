-- PayFlow — Initial MySQL schema setup
-- This runs automatically when the MySQL container starts because it lives in /docker-entrypoint-initdb.d.
-- It creates the payflow database and all tables.

CREATE DATABASE IF NOT EXISTS payflow CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE payflow;

-- Temporarily disable foreign key checks so we can drop and recreate tables in any order.
SET FOREIGN_KEY_CHECKS = 0;

-- ---------------------------------------------------------------------------
-- Staging tables
-- ---------------------------------------------------------------------------

DROP TABLE IF EXISTS staging_transactions;

CREATE TABLE staging_transactions (
    transaction_id          VARCHAR(64) NOT NULL,
    transaction_timestamp     DATETIME NOT NULL,
    provider                  VARCHAR(32) NOT NULL,
    merchant_id               VARCHAR(32) NOT NULL,
    amount                    DECIMAL(18, 4) NOT NULL,
    currency                  CHAR(3) NOT NULL,
    status                    VARCHAR(32) NOT NULL,
    loaded_at                 DATETIME DEFAULT CURRENT_TIMESTAMP,
    source_file               VARCHAR(512),
    is_valid                  BOOLEAN DEFAULT TRUE,
    rejection_reason          TEXT,
    PRIMARY KEY (transaction_id, provider)
);

-- ---------------------------------------------------------------------------
-- Bronze layer — raw provider files and records
-- ---------------------------------------------------------------------------

DROP TABLE IF EXISTS bronze_provider_transactions;
DROP TABLE IF EXISTS bronze_raw_provider_files;

CREATE TABLE bronze_raw_provider_files (
    file_id INT AUTO_INCREMENT PRIMARY KEY,
    source_file VARCHAR(512) NOT NULL,
    provider VARCHAR(32) NOT NULL,
    file_format VARCHAR(16),
    batch_id VARCHAR(64) NOT NULL,
    loaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    record_count INT,
    status VARCHAR(32) DEFAULT 'loaded',
    UNIQUE KEY uq_bronze_file (source_file, provider)
);

CREATE TABLE bronze_provider_transactions (
    bronze_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    file_id INT,
    transaction_id VARCHAR(64),
    transaction_timestamp VARCHAR(255),
    provider VARCHAR(32) NOT NULL,
    merchant_id VARCHAR(64),
    amount VARCHAR(255),
    currency VARCHAR(16),
    status VARCHAR(64),
    source_file VARCHAR(512),
    source_system VARCHAR(32) GENERATED ALWAYS AS (provider) STORED,
    batch_id VARCHAR(64) NOT NULL,
    loaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    raw_record JSON,
    FOREIGN KEY (file_id) REFERENCES bronze_raw_provider_files(file_id),
    INDEX idx_bronze_batch (batch_id),
    INDEX idx_bronze_txn (transaction_id, provider)
);

-- ---------------------------------------------------------------------------
-- Silver layer — cleaned, validated, deduplicated canonical transactions
-- ---------------------------------------------------------------------------

DROP TABLE IF EXISTS silver_transactions;
DROP TABLE IF EXISTS silver_rejected_transactions;

CREATE TABLE silver_transactions (
    silver_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    transaction_id VARCHAR(64) NOT NULL,
    transaction_timestamp DATETIME NOT NULL,
    source_system VARCHAR(32) NOT NULL,
    provider VARCHAR(32),
    merchant_id VARCHAR(32) NOT NULL,
    amount DECIMAL(18, 4) NOT NULL,
    currency CHAR(3) NOT NULL,
    status VARCHAR(32) NOT NULL,
    source_file VARCHAR(512),
    batch_id VARCHAR(64) NOT NULL,
    loaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    cleaned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_silver_txn_provider (transaction_id, provider),
    INDEX idx_silver_merchant (merchant_id),
    INDEX idx_silver_status (status),
    INDEX idx_silver_provider (provider),
    INDEX idx_silver_batch (batch_id)
);

CREATE TABLE silver_rejected_transactions (
    rejected_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    transaction_id VARCHAR(64),
    transaction_timestamp VARCHAR(255),
    source_system VARCHAR(32),
    provider VARCHAR(32),
    merchant_id VARCHAR(64),
    amount VARCHAR(255),
    currency VARCHAR(16),
    status VARCHAR(64),
    source_file VARCHAR(512),
    batch_id VARCHAR(64) NOT NULL,
    rejection_reason TEXT,
    rejection_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    raw_json JSON,
    INDEX idx_rejected_batch (batch_id),
    INDEX idx_rejected_reason (rejection_reason(64))
);

-- ---------------------------------------------------------------------------
-- Pipeline idempotency log
-- ---------------------------------------------------------------------------

DROP TABLE IF EXISTS pipeline_processed_files;

CREATE TABLE pipeline_processed_files (
    processed_id INT AUTO_INCREMENT PRIMARY KEY,
    source_file VARCHAR(512) NOT NULL,
    provider VARCHAR(32) NOT NULL,
    batch_id VARCHAR(64) NOT NULL,
    loaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    records_loaded INT,
    records_rejected INT,
    status VARCHAR(32) DEFAULT 'success',
    UNIQUE KEY uq_processed_file (source_file, provider, batch_id)
);

-- ---------------------------------------------------------------------------
-- Dimension tables
-- ---------------------------------------------------------------------------

DROP TABLE IF EXISTS warehouse_dim_date;
CREATE TABLE warehouse_dim_date (
    date_key          INT PRIMARY KEY,
    full_date         DATE NOT NULL UNIQUE,
    year              INT NOT NULL,
    month             INT NOT NULL,
    day               INT NOT NULL,
    quarter           INT NOT NULL,
    day_of_week       INT NOT NULL,
    is_weekend        BOOLEAN NOT NULL
);

DROP TABLE IF EXISTS warehouse_dim_merchant;
CREATE TABLE warehouse_dim_merchant (
    merchant_key      INT AUTO_INCREMENT PRIMARY KEY,
    merchant_id       VARCHAR(32) NOT NULL UNIQUE,
    merchant_name     VARCHAR(128) NOT NULL,
    country           CHAR(2),
    contract_start_date DATE,
    fee_variable_pct  DECIMAL(5, 4) DEFAULT 0.0150,
    fee_fixed_amount  DECIMAL(18, 4) DEFAULT 0.25,
    is_active         BOOLEAN DEFAULT TRUE
);

DROP TABLE IF EXISTS warehouse_dim_provider;
CREATE TABLE warehouse_dim_provider (
    provider_key      INT AUTO_INCREMENT PRIMARY KEY,
    provider_id       VARCHAR(32) NOT NULL UNIQUE,
    provider_name     VARCHAR(128) NOT NULL,
    file_format       VARCHAR(16) NOT NULL
);

DROP TABLE IF EXISTS warehouse_dim_currency;
CREATE TABLE warehouse_dim_currency (
    currency_key      INT AUTO_INCREMENT PRIMARY KEY,
    currency_code     CHAR(3) NOT NULL UNIQUE,
    currency_name     VARCHAR(64) NOT NULL
);

DROP TABLE IF EXISTS warehouse_dim_transaction_status;
CREATE TABLE warehouse_dim_transaction_status (
    status_key        INT AUTO_INCREMENT PRIMARY KEY,
    status_code       VARCHAR(32) NOT NULL UNIQUE,
    status_category   VARCHAR(32) NOT NULL,
    description       VARCHAR(256)
);

-- ---------------------------------------------------------------------------
-- Fact tables
-- ---------------------------------------------------------------------------

DROP TABLE IF EXISTS warehouse_fact_transaction;
CREATE TABLE warehouse_fact_transaction (
    fact_transaction_id   BIGINT AUTO_INCREMENT PRIMARY KEY,
    transaction_id        VARCHAR(64) NOT NULL,
    transaction_timestamp DATETIME NOT NULL,
    date_key              INT NOT NULL,
    merchant_key          INT NOT NULL,
    provider_key          INT NOT NULL,
    currency_key          INT NOT NULL,
    status_key            INT NOT NULL,
    amount                DECIMAL(18, 4) NOT NULL,
    source_file           VARCHAR(512),
    loaded_at             DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (transaction_id, provider_key),
    FOREIGN KEY (date_key) REFERENCES warehouse_dim_date(date_key),
    FOREIGN KEY (merchant_key) REFERENCES warehouse_dim_merchant(merchant_key),
    FOREIGN KEY (provider_key) REFERENCES warehouse_dim_provider(provider_key),
    FOREIGN KEY (currency_key) REFERENCES warehouse_dim_currency(currency_key),
    FOREIGN KEY (status_key) REFERENCES warehouse_dim_transaction_status(status_key)
);

DROP TABLE IF EXISTS warehouse_fact_reconciliation;
CREATE TABLE warehouse_fact_reconciliation (
    reconciliation_id         BIGINT AUTO_INCREMENT PRIMARY KEY,
    transaction_id            VARCHAR(64) NOT NULL,
    date_key                  INT NOT NULL,
    merchant_key              INT NOT NULL,
    provider_key              INT NOT NULL,
    internal_amount           DECIMAL(18, 4),
    gateway_amount            DECIMAL(18, 4),
    amount_difference         DECIMAL(18, 4),
    internal_status_key       INT,
    gateway_status_key        INT,
    reconciliation_status     VARCHAR(32) NOT NULL,
    reconciled_at             DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (date_key) REFERENCES warehouse_dim_date(date_key),
    FOREIGN KEY (merchant_key) REFERENCES warehouse_dim_merchant(merchant_key),
    FOREIGN KEY (provider_key) REFERENCES warehouse_dim_provider(provider_key),
    FOREIGN KEY (internal_status_key) REFERENCES warehouse_dim_transaction_status(status_key),
    FOREIGN KEY (gateway_status_key) REFERENCES warehouse_dim_transaction_status(status_key)
);

DROP TABLE IF EXISTS warehouse_fact_billing;
CREATE TABLE warehouse_fact_billing (
    billing_id                BIGINT AUTO_INCREMENT PRIMARY KEY,
    merchant_key              INT NOT NULL,
    billing_period            VARCHAR(7) NOT NULL, -- YYYY-MM
    successful_transactions   INT NOT NULL DEFAULT 0,
    gross_volume              DECIMAL(18, 4) NOT NULL DEFAULT 0,
    refunds_volume            DECIMAL(18, 4) NOT NULL DEFAULT 0,
    net_volume                DECIMAL(18, 4) NOT NULL DEFAULT 0,
    variable_fees             DECIMAL(18, 4) NOT NULL DEFAULT 0,
    fixed_fees                DECIMAL(18, 4) NOT NULL DEFAULT 0,
    total_fees                DECIMAL(18, 4) NOT NULL DEFAULT 0,
    amount_due                DECIMAL(18, 4) NOT NULL DEFAULT 0,
    calculated_at             DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (merchant_key, billing_period),
    FOREIGN KEY (merchant_key) REFERENCES warehouse_dim_merchant(merchant_key)
);

-- ---------------------------------------------------------------------------
-- Reconciliation helper tables
-- ---------------------------------------------------------------------------

DROP TABLE IF EXISTS reconciliation_internal_transactions;
CREATE TABLE reconciliation_internal_transactions (
    transaction_id          VARCHAR(64) PRIMARY KEY,
    transaction_timestamp   DATETIME NOT NULL,
    merchant_id             VARCHAR(32) NOT NULL,
    amount                  DECIMAL(18, 4) NOT NULL,
    currency                CHAR(3) NOT NULL,
    status                  VARCHAR(32) NOT NULL,
    source_system           VARCHAR(32) DEFAULT 'internal',
    source_file             VARCHAR(512) DEFAULT 'internal_transactions.csv',
    loaded_at               DATETIME DEFAULT CURRENT_TIMESTAMP
);

DROP TABLE IF EXISTS reconciliation_gateway_transactions;
CREATE TABLE reconciliation_gateway_transactions (
    internal_id             BIGINT AUTO_INCREMENT PRIMARY KEY,
    transaction_id            VARCHAR(64) NOT NULL,
    provider                  VARCHAR(32) NOT NULL,
    transaction_timestamp     DATETIME NOT NULL,
    merchant_id               VARCHAR(32) NOT NULL,
    amount                    DECIMAL(18, 4) NOT NULL,
    currency                  CHAR(3) NOT NULL,
    status                    VARCHAR(32) NOT NULL,
    source_file               VARCHAR(512),
    loaded_at                 DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ---------------------------------------------------------------------------
-- Indexes
-- ---------------------------------------------------------------------------

CREATE INDEX idx_staging_transactions_merchant ON staging_transactions(merchant_id);
CREATE INDEX idx_staging_transactions_status   ON staging_transactions(status);
CREATE INDEX idx_fact_transaction_date         ON warehouse_fact_transaction(date_key);
CREATE INDEX idx_fact_transaction_merchant     ON warehouse_fact_transaction(merchant_key);
CREATE INDEX idx_fact_reconciliation_status    ON warehouse_fact_reconciliation(reconciliation_status);
CREATE INDEX idx_fact_billing_period           ON warehouse_fact_billing(billing_period);
CREATE INDEX idx_gateway_transactions_id       ON reconciliation_gateway_transactions(transaction_id);

-- Re-enable foreign key checks now that all tables are created.
SET FOREIGN_KEY_CHECKS = 1;

-- ---------------------------------------------------------------------------
-- Seed dimension data
-- ---------------------------------------------------------------------------

INSERT IGNORE INTO warehouse_dim_currency (currency_code, currency_name) VALUES
('EUR', 'Euro'),
('USD', 'United States Dollar'),
('GBP', 'British Pound');

INSERT IGNORE INTO warehouse_dim_provider (provider_id, provider_name, file_format) VALUES
('provider_a', 'Provider A', 'csv'),
('provider_b', 'Provider B', 'json'),
('provider_c', 'Provider C', 'csv'),
('unknown', 'Unknown Provider', 'unknown');

INSERT IGNORE INTO warehouse_dim_transaction_status (status_code, status_category, description) VALUES
('SUCCESS', 'completed', 'Transaction completed successfully'),
('COMPLETED', 'completed', 'Transaction completed successfully'),
('FAILED', 'failed', 'Transaction failed'),
('DECLINED', 'failed', 'Transaction was declined'),
('REFUNDED', 'refund', 'Transaction was refunded'),
('PENDING', 'pending', 'Transaction is pending');
