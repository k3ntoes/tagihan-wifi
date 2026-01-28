-- Migration: Drop sqid column from customers table
-- Date: 2026-01-28
-- Reason: Sqid is now generated on-the-fly, not stored in database (like Laravel Sqids)

-- Drop the sqid column and its index
DROP INDEX IF EXISTS idx_customers_sqid;

ALTER TABLE customers DROP COLUMN IF EXISTS sqid;

-- Verify the migration
SELECT 'Migration completed: sqid column dropped' as status;
