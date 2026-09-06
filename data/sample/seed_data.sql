-- PayFlow — Seed dimension data and sample internal transactions for MySQL
-- Run after sql/schema/01_create_database.sql has created the database and tables.

USE payflow;

-- ---------------------------------------------------------------------------
-- Seed merchants
-- ---------------------------------------------------------------------------

INSERT IGNORE INTO warehouse_dim_merchant (merchant_id, merchant_name, country, contract_start_date, fee_variable_pct, fee_fixed_amount)
VALUES
('M001', 'Merchant One', 'BG', '2025-01-15', 0.0150, 0.25),
('M002', 'Merchant Two', 'DE', '2025-03-01', 0.0150, 0.25),
('M003', 'Merchant Three', 'GB', '2025-06-20', 0.0150, 0.25),
('M004', 'Merchant Four', 'FR', '2025-01-01', 0.0150, 0.25);

-- ---------------------------------------------------------------------------
-- Seed dates for September 2026
-- ---------------------------------------------------------------------------
-- We insert every day of September 2026. The values are hardcoded here to avoid
-- MySQL recursive CTE syntax issues and to make the data easy to see.
-- MySQL WEEKDAY() returns 0 for Monday and 6 for Sunday.

INSERT IGNORE INTO warehouse_dim_date (date_key, full_date, year, month, day, quarter, day_of_week, is_weekend)
VALUES
(20260901, '2026-09-01', 2026, 9, 1, 3, 1, FALSE),
(20260902, '2026-09-02', 2026, 9, 2, 3, 2, FALSE),
(20260903, '2026-09-03', 2026, 9, 3, 3, 3, FALSE),
(20260904, '2026-09-04', 2026, 9, 4, 3, 4, FALSE),
(20260905, '2026-09-05', 2026, 9, 5, 3, 5, TRUE),
(20260906, '2026-09-06', 2026, 9, 6, 3, 6, TRUE),
(20260907, '2026-09-07', 2026, 9, 7, 3, 0, FALSE),
(20260908, '2026-09-08', 2026, 9, 8, 3, 1, FALSE),
(20260909, '2026-09-09', 2026, 9, 9, 3, 2, FALSE),
(20260910, '2026-09-10', 2026, 9, 10, 3, 3, FALSE),
(20260911, '2026-09-11', 2026, 9, 11, 3, 4, FALSE),
(20260912, '2026-09-12', 2026, 9, 12, 3, 5, TRUE),
(20260913, '2026-09-13', 2026, 9, 13, 3, 6, TRUE),
(20260914, '2026-09-14', 2026, 9, 14, 3, 0, FALSE),
(20260915, '2026-09-15', 2026, 9, 15, 3, 1, FALSE),
(20260916, '2026-09-16', 2026, 9, 16, 3, 2, FALSE),
(20260917, '2026-09-17', 2026, 9, 17, 3, 3, FALSE),
(20260918, '2026-09-18', 2026, 9, 18, 3, 4, FALSE),
(20260919, '2026-09-19', 2026, 9, 19, 3, 5, TRUE),
(20260920, '2026-09-20', 2026, 9, 20, 3, 6, TRUE),
(20260921, '2026-09-21', 2026, 9, 21, 3, 0, FALSE),
(20260922, '2026-09-22', 2026, 9, 22, 3, 1, FALSE),
(20260923, '2026-09-23', 2026, 9, 23, 3, 2, FALSE),
(20260924, '2026-09-24', 2026, 9, 24, 3, 3, FALSE),
(20260925, '2026-09-25', 2026, 9, 25, 3, 4, FALSE),
(20260926, '2026-09-26', 2026, 9, 26, 3, 5, TRUE),
(20260927, '2026-09-27', 2026, 9, 27, 3, 6, TRUE),
(20260928, '2026-09-28', 2026, 9, 28, 3, 0, FALSE),
(20260929, '2026-09-29', 2026, 9, 29, 3, 1, FALSE),
(20260930, '2026-09-30', 2026, 9, 30, 3, 2, FALSE);

-- ---------------------------------------------------------------------------
-- Seed internal transactions
-- ---------------------------------------------------------------------------

TRUNCATE TABLE reconciliation_internal_transactions;

INSERT INTO reconciliation_internal_transactions (transaction_id, transaction_timestamp, merchant_id, amount, currency, status)
VALUES
('TX001', '2026-09-06 10:32:11', 'M001', 125.50, 'EUR', 'SUCCESS'),
('TX002', '2026-09-06 11:15:22', 'M001', 250.00, 'EUR', 'SUCCESS'),
('TX003', '2026-09-06 12:01:45', 'M002', 120.00, 'EUR', 'SUCCESS'),
('TX004', '2026-09-06 13:45:00', 'M002', 80.00, 'EUR', 'FAILED'),
('TX005', '2026-09-06 14:20:10', 'M003', 90.00, 'EUR', 'SUCCESS'),
('TX006', '2026-09-06 15:00:00', 'M001', 75.00, 'EUR', 'SUCCESS'),
('TX007', '2026-09-06 16:10:00', 'M003', 45.00, 'EUR', 'SUCCESS'),
('TX008', '2026-09-06 17:30:00', 'M002', 200.00, 'EUR', 'SUCCESS'),
('TX009', '2026-09-06 18:00:00', 'M001', 100.00, 'EUR', 'SUCCESS'),
('TX010', '2026-09-06 19:15:10', 'M003', 55.00, 'EUR', 'SUCCESS'),
('TX016', '2026-09-06 20:00:00', 'M002', 67.00, 'EUR', 'SUCCESS');
