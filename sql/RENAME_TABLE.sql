-- ============================================================
-- RENAME TABLE: Replace pesti_comp with solutions table
-- ============================================================
-- This will use the 1,513 records from solutions (with embeddings)
-- and replace the incomplete pesti_comp table.
-- ⚠️ WARNING: This will DELETE 19,970 records from pesti_comp!
-- ============================================================

-- Step 1: Drop the incomplete pesti_comp table
DROP TABLE pesti_comp;

-- Step 2: Rename solutions to pesti_comp
ALTER TABLE solutions RENAME TO pesti_comp;

-- Step 3: Rename indexes
ALTER INDEX IF EXISTS solutions_embedding_idx 
RENAME TO pesti_comp_embedding_idx;

ALTER INDEX IF EXISTS solutions_embedding_hnsw_idx 
RENAME TO pesti_comp_embedding_hnsw_idx;

-- Step 4: Rename sequence
ALTER SEQUENCE IF EXISTS solutions_id_seq 
RENAME TO pesti_comp_id_seq;

-- ============================================================
-- VERIFICATION QUERIES:
-- ============================================================

-- Check table exists and has embedding column
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'pesti_comp';

-- Check record count
SELECT COUNT(*) FROM pesti_comp;

-- Check embeddings
SELECT COUNT(*) FROM pesti_comp WHERE embedding IS NOT NULL;

-- Check indexes
SELECT indexname 
FROM pg_indexes 
WHERE tablename = 'pesti_comp';
