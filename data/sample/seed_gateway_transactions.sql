-- PayFlow — Seed gateway transactions for reconciliation demonstration
-- These records simulate what the three providers reported AFTER normalization.
-- Provider-specific statuses like COMPLETED/completed are normalized to SUCCESS.
-- We intentionally include:
--   - duplicates (TX003 appears twice from Provider A)
--   - an amount mismatch (TX003 from Provider B = 125.00 vs internal 120.00)
--   - a status mismatch (TX006 from Provider C = failed vs internal SUCCESS)
--   - a missing internal record (TX011 exists in gateway but not internal)

USE payflow;

TRUNCATE TABLE reconciliation_gateway_transactions;

INSERT INTO reconciliation_gateway_transactions
(transaction_id, provider, transaction_timestamp, merchant_id, amount, currency, status, source_file)
VALUES
-- Provider A (CSV format)
('TX001', 'provider_a', '2026-09-06 10:32:11', 'M001', 125.50, 'EUR', 'SUCCESS', 'provider_a_2026_09_06.csv'),
('TX002', 'provider_a', '2026-09-06 11:15:22', 'M001', 250.00, 'EUR', 'SUCCESS', 'provider_a_2026_09_06.csv'),
('TX003', 'provider_a', '2026-09-06 12:01:45', 'M002', 120.00, 'EUR', 'SUCCESS', 'provider_a_2026_09_06.csv'),
('TX004', 'provider_a', '2026-09-06 13:45:00', 'M002',  80.00, 'EUR', 'FAILED',    'provider_a_2026_09_06.csv'),
('TX005', 'provider_a', '2026-09-06 14:20:10', 'M003',  90.00, 'EUR', 'SUCCESS', 'provider_a_2026_09_06.csv'),
('TX006', 'provider_a', '2026-09-06 15:00:00', 'M001',  75.00, 'EUR', 'SUCCESS', 'provider_a_2026_09_06.csv'),
('TX007', 'provider_a', '2026-09-06 16:10:00', 'M003',  45.00, 'EUR', 'SUCCESS', 'provider_a_2026_09_06.csv'),
('TX008', 'provider_a', '2026-09-06 17:30:00', 'M002', 200.00, 'EUR', 'SUCCESS', 'provider_a_2026_09_06.csv'),
('TX009', 'provider_a', '2026-09-06 18:00:00', 'M001', 100.00, 'EUR', 'SUCCESS', 'provider_a_2026_09_06.csv'),
('TX010', 'provider_a', '2026-09-06 19:15:10', 'M003',  55.00, 'EUR', 'SUCCESS', 'provider_a_2026_09_06.csv'),
-- Duplicate TX003 from Provider A (will be removed by ROW_NUMBER in reconciliation)
('TX003', 'provider_a', '2026-09-06 12:01:45', 'M002', 120.00, 'EUR', 'SUCCESS', 'provider_a_2026_09_06.csv'),

-- Provider B (JSON format) — note the amount mismatch on TX003
('TX001', 'provider_b', '2026-09-06 10:32:11', 'M001', 125.50, 'EUR', 'SUCCESS', 'provider_b_2026_09_06.json'),
('TX002', 'provider_b', '2026-09-06 11:15:22', 'M001', 250.00, 'EUR', 'SUCCESS', 'provider_b_2026_09_06.json'),
('TX003', 'provider_b', '2026-09-06 12:05:00', 'M002', 125.00, 'EUR', 'SUCCESS', 'provider_b_2026_09_06.json'),
('TX004', 'provider_b', '2026-09-06 13:45:00', 'M002',  80.00, 'EUR', 'FAILED',  'provider_b_2026_09_06.json'),
('TX005', 'provider_b', '2026-09-06 14:20:10', 'M003',  90.00, 'EUR', 'SUCCESS', 'provider_b_2026_09_06.json'),
('TX006', 'provider_b', '2026-09-06 15:00:00', 'M001',  75.00, 'EUR', 'SUCCESS', 'provider_b_2026_09_06.json'),
('TX007', 'provider_b', '2026-09-06 16:10:00', 'M003',  45.00, 'EUR', 'SUCCESS', 'provider_b_2026_09_06.json'),
('TX008', 'provider_b', '2026-09-06 17:30:00', 'M002', 200.00, 'EUR', 'SUCCESS', 'provider_b_2026_09_06.json'),
('TX009', 'provider_b', '2026-09-06 18:00:00', 'M001', 100.00, 'EUR', 'SUCCESS', 'provider_b_2026_09_06.json'),
('TX010', 'provider_b', '2026-09-06 19:15:10', 'M003',  55.00, 'EUR', 'SUCCESS', 'provider_b_2026_09_06.json'),
-- TX011 exists in gateway but not in internal records
('TX011', 'provider_b', '2026-09-06 20:00:00', 'M004', 300.00, 'EUR', 'SUCCESS', 'provider_b_2026_09_06.json'),

-- Provider C (CSV with different column names)
('TX001', 'provider_c', '2026-09-06 10:32:11', 'M001', 125.50, 'EUR', 'SUCCESS', 'provider_c_2026_09_06.csv'),
('TX002', 'provider_c', '2026-09-06 11:15:22', 'M001', 250.00, 'EUR', 'SUCCESS', 'provider_c_2026_09_06.csv'),
('TX003', 'provider_c', '2026-09-06 12:01:45', 'M002', 120.00, 'EUR', 'SUCCESS', 'provider_c_2026_09_06.csv'),
('TX006', 'provider_c', '2026-09-06 15:00:00', 'M001',  75.00, 'EUR', 'FAILED', 'provider_c_2026_09_06.csv'),
('TX007', 'provider_c', '2026-09-06 16:10:00', 'M003',  45.00, 'EUR', 'SUCCESS', 'provider_c_2026_09_06.csv'),
('TX008', 'provider_c', '2026-09-06 17:30:00', 'M002', 200.00, 'EUR', 'SUCCESS', 'provider_c_2026_09_06.csv'),
('TX009', 'provider_c', '2026-09-06 18:00:00', 'M001', 100.00, 'EUR', 'SUCCESS', 'provider_c_2026_09_06.csv'),
('TX010', 'provider_c', '2026-09-06 19:15:10', 'M003',  55.00, 'EUR', 'SUCCESS', 'provider_c_2026_09_06.csv');
