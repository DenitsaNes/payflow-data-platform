-- PayFlow — Seed gateway transactions for reconciliation demonstration
-- These records simulate what the three providers reported AFTER normalization.
-- Provider-specific statuses like COMPLETED/completed are normalized to SUCCESS.
-- We intentionally include:
--   - duplicates (TX003 appears twice from Provider A)
--   - an amount mismatch (TX003 from Provider B = 125.00 vs internal 120.00)
--   - a status mismatch (TX006 from Provider C = failed vs internal SUCCESS)
--   - a missing internal record (TX011 exists in gateway but not internal)

USE payflow;

TRUNCATE TABLE silver_transactions;

INSERT IGNORE INTO silver_transactions
(transaction_id, transaction_timestamp, source_system, provider, merchant_id, amount, currency, status, source_file, batch_id)
VALUES
-- Provider A (CSV format)
('TX001', '2026-09-06 10:32:11', 'provider_a', 'provider_a', 'M001', 125.50, 'EUR', 'SUCCESS', 'provider_a_2026_09_06.csv', 'sample_seed'),
('TX002', '2026-09-06 11:15:22', 'provider_a', 'provider_a', 'M001', 250.00, 'EUR', 'SUCCESS', 'provider_a_2026_09_06.csv', 'sample_seed'),
('TX003', '2026-09-06 12:01:45', 'provider_a', 'provider_a', 'M002', 120.00, 'EUR', 'SUCCESS', 'provider_a_2026_09_06.csv', 'sample_seed'),
('TX004', '2026-09-06 13:45:00', 'provider_a', 'provider_a', 'M002',  80.00, 'EUR', 'FAILED',    'provider_a_2026_09_06.csv', 'sample_seed'),
('TX005', '2026-09-06 14:20:10', 'provider_a', 'provider_a', 'M003',  90.00, 'EUR', 'SUCCESS', 'provider_a_2026_09_06.csv', 'sample_seed'),
('TX006', '2026-09-06 15:00:00', 'provider_a', 'provider_a', 'M001',  75.00, 'EUR', 'SUCCESS', 'provider_a_2026_09_06.csv', 'sample_seed'),
('TX007', '2026-09-06 16:10:00', 'provider_a', 'provider_a', 'M003',  45.00, 'EUR', 'SUCCESS', 'provider_a_2026_09_06.csv', 'sample_seed'),
('TX008', '2026-09-06 17:30:00', 'provider_a', 'provider_a', 'M002', 200.00, 'EUR', 'SUCCESS', 'provider_a_2026_09_06.csv', 'sample_seed'),
('TX009', '2026-09-06 18:00:00', 'provider_a', 'provider_a', 'M001', 100.00, 'EUR', 'SUCCESS', 'provider_a_2026_09_06.csv', 'sample_seed'),
('TX010', '2026-09-06 19:15:10', 'provider_a', 'provider_a', 'M003',  55.00, 'EUR', 'SUCCESS', 'provider_a_2026_09_06.csv', 'sample_seed'),
-- Duplicate TX003 from Provider A (will be removed by ROW_NUMBER in reconciliation)
('TX003', '2026-09-06 12:01:45', 'provider_a', 'provider_a', 'M002', 120.00, 'EUR', 'SUCCESS', 'provider_a_2026_09_06.csv', 'sample_seed'),

-- Provider B (JSON format) — note the amount mismatch on TX003
('TX001', '2026-09-06 10:32:11', 'provider_b', 'provider_b', 'M001', 125.50, 'EUR', 'SUCCESS', 'provider_b_2026_09_06.json', 'sample_seed'),
('TX002', '2026-09-06 11:15:22', 'provider_b', 'provider_b', 'M001', 250.00, 'EUR', 'SUCCESS', 'provider_b_2026_09_06.json', 'sample_seed'),
('TX003', '2026-09-06 12:05:00', 'provider_b', 'provider_b', 'M002', 125.00, 'EUR', 'SUCCESS', 'provider_b_2026_09_06.json', 'sample_seed'),
('TX004', '2026-09-06 13:45:00', 'provider_b', 'provider_b', 'M002',  80.00, 'EUR', 'FAILED',  'provider_b_2026_09_06.json', 'sample_seed'),
('TX005', '2026-09-06 14:20:10', 'provider_b', 'provider_b', 'M003',  90.00, 'EUR', 'SUCCESS', 'provider_b_2026_09_06.json', 'sample_seed'),
('TX006', '2026-09-06 15:00:00', 'provider_b', 'provider_b', 'M001',  75.00, 'EUR', 'SUCCESS', 'provider_b_2026_09_06.json', 'sample_seed'),
('TX007', '2026-09-06 16:10:00', 'provider_b', 'provider_b', 'M003',  45.00, 'EUR', 'SUCCESS', 'provider_b_2026_09_06.json', 'sample_seed'),
('TX008', '2026-09-06 17:30:00', 'provider_b', 'provider_b', 'M002', 200.00, 'EUR', 'SUCCESS', 'provider_b_2026_09_06.json', 'sample_seed'),
('TX009', '2026-09-06 18:00:00', 'provider_b', 'provider_b', 'M001', 100.00, 'EUR', 'SUCCESS', 'provider_b_2026_09_06.json', 'sample_seed'),
('TX010', '2026-09-06 19:15:10', 'provider_b', 'provider_b', 'M003',  55.00, 'EUR', 'SUCCESS', 'provider_b_2026_09_06.json', 'sample_seed'),
-- TX011 exists in gateway but not in internal records
('TX011', '2026-09-06 20:00:00', 'provider_b', 'provider_b', 'M004', 300.00, 'EUR', 'SUCCESS', 'provider_b_2026_09_06.json', 'sample_seed'),

-- Provider C (CSV with different column names)
('TX001', '2026-09-06 10:32:11', 'provider_c', 'provider_c', 'M001', 125.50, 'EUR', 'SUCCESS', 'provider_c_2026_09_06.csv', 'sample_seed'),
('TX002', '2026-09-06 11:15:22', 'provider_c', 'provider_c', 'M001', 250.00, 'EUR', 'SUCCESS', 'provider_c_2026_09_06.csv', 'sample_seed'),
('TX003', '2026-09-06 12:01:45', 'provider_c', 'provider_c', 'M002', 120.00, 'EUR', 'SUCCESS', 'provider_c_2026_09_06.csv', 'sample_seed'),
('TX006', '2026-09-06 15:00:00', 'provider_c', 'provider_c', 'M001',  75.00, 'EUR', 'FAILED', 'provider_c_2026_09_06.csv', 'sample_seed'),
('TX007', '2026-09-06 16:10:00', 'provider_c', 'provider_c', 'M003',  45.00, 'EUR', 'SUCCESS', 'provider_c_2026_09_06.csv', 'sample_seed'),
('TX008', '2026-09-06 17:30:00', 'provider_c', 'provider_c', 'M002', 200.00, 'EUR', 'SUCCESS', 'provider_c_2026_09_06.csv', 'sample_seed'),
('TX009', '2026-09-06 18:00:00', 'provider_c', 'provider_c', 'M001', 100.00, 'EUR', 'SUCCESS', 'provider_c_2026_09_06.csv', 'sample_seed'),
('TX010', '2026-09-06 19:15:10', 'provider_c', 'provider_c', 'M003',  55.00, 'EUR', 'SUCCESS', 'provider_c_2026_09_06.csv', 'sample_seed');
