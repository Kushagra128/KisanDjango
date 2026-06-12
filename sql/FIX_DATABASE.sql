-- ============================================================
-- FIX DATABASE: Add embedding column to pesti_comp table
-- ============================================================
-- This will keep your 19,970 records in pesti_comp and add
-- the missing embedding column so Django can work properly.
-- ============================================================

-- Step 1: Add embedding column to pesti_comp
ALTER TABLE pesti_comp ADD COLUMN embedding vector(768);

-- Step 2: Create indexes on pesti_comp (if they don't exist)
CREATE INDEX IF NOT EXISTS pesti_comp_embedding_idx 
ON pesti_comp USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);

CREATE INDEX IF NOT EXISTS pesti_comp_embedding_hnsw_idx 
ON pesti_comp USING hnsw (embedding vector_cosine_ops) 
WITH (m = 16, ef_construction = 200);

-- Step 3: (Optional) Drop the old solutions table if not needed
-- Uncomment this line if you want to remove the old table:
-- DROP TABLE solutions;

-- ============================================================
-- VERIFICATION QUERIES:
-- ============================================================
-- Run these to verify the fix worked:

-- Check table structure
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'pesti_comp';

-- Check record count
SELECT COUNT(*) FROM pesti_comp;

-- Check how many have embeddings
SELECT COUNT(*) FROM pesti_comp WHERE embedding IS NOT NULL;
SELECT COUNT(*) FROM pesti_comp WHERE embedding IS NULL;

-- After adding the column, you need to generate embeddings
-- by calling: POST /generate-embeddings from your Django API
