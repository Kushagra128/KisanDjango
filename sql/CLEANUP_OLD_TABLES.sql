-- ============================================================
-- CLEANUP: Remove duplicate/old tables
-- ============================================================
-- These tables contain duplicate data that is already in pesti_comp
-- ============================================================

-- Option 1: Drop the old solutions table (recommended)
-- This table has 1,513 records that are already in pesti_comp
DROP TABLE IF EXISTS solutions CASCADE;

-- Option 2: Drop the chatbot_agriculturaladvice table (if not needed)
-- This appears to be from an old version without embeddings
-- Uncomment the line below if you want to remove it:
-- DROP TABLE IF EXISTS chatbot_agriculturaladvice CASCADE;

-- Option 3: Drop test_vectors table (empty test table)
DROP TABLE IF EXISTS test_vectors CASCADE;

-- ============================================================
-- VERIFICATION:
-- ============================================================
-- Check remaining tables:
SELECT tablename FROM pg_tables 
WHERE schemaname = 'public' 
ORDER BY tablename;

-- This should show:
-- - pesti_comp (your main data table)
-- - chatbot_unansweredproblem (useful for analytics)
-- - Django/auth system tables
