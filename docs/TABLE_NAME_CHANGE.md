# Database Table Name Change

## Date: June 8, 2026

## Change Summary
Changed database table name from **`solutions`** to **`pesti_comp`** throughout the entire codebase.

---

## Files Modified

### 1. **api/models.py**
- Updated `db_table` in Meta class: `"solutions"` → `"pesti_comp"`
- Updated docstring references

**Changes:**
```python
class Meta:
    db_table = "pesti_comp"  # Was: "solutions"
```

### 2. **api/views.py** 
Updated 4 SQL queries:

1. **Generate Embeddings** (Line ~197):
   ```sql
   SELECT id, cropname, problem FROM pesti_comp WHERE embedding IS NULL
   ```

2. **IVFFLAT Index Creation** (Line ~150):
   ```sql
   CREATE INDEX pesti_comp_embedding_idx 
   ON pesti_comp USING ivfflat (embedding vector_cosine_ops)
   ```

3. **HNSW Index Creation** (Line ~162):
   ```sql
   CREATE INDEX pesti_comp_embedding_hnsw_idx 
   ON pesti_comp USING hnsw (embedding vector_cosine_ops)
   ```

4. **Update Embeddings** (Line ~216):
   ```sql
   UPDATE pesti_comp SET embedding = %s WHERE id = %s
   ```

### 3. **services.py**
Updated 5 SQL queries:

1. **Get All Crops** (Line ~1482):
   ```sql
   SELECT id, problem, solution, cropname FROM pesti_comp ORDER BY id ASC
   ```

2. **ILIKE Fallback Search** (Line ~1558):
   ```sql
   SELECT id, problem, solution, cropname FROM pesti_comp 
   WHERE problem ILIKE %s ORDER BY id ASC LIMIT 5
   ```

3. **Crop Suggestions** (Line ~1328):
   ```sql
   SELECT DISTINCT cropname, (1 - (embedding <=> %s)) AS emb_score
   FROM pesti_comp
   WHERE embedding IS NOT NULL
   ```

4. **Semantic Search with Crop Filter** (Line ~1394):
   ```sql
   SELECT id, problem, solution, cropname, (1 - (embedding <=> %s)) AS emb_score
   FROM pesti_comp
   WHERE embedding IS NOT NULL AND cropname = %s
   ```

5. **Semantic Search without Crop Filter** (Line ~1407):
   ```sql
   SELECT id, problem, solution, cropname, (1 - (embedding <=> %s)) AS emb_score
   FROM pesti_comp
   WHERE embedding IS NOT NULL
   ```

### 4. **api/admin.py**
- Updated CSV export filename: `solutions.csv` → `pesti_comp.csv`
- Updated docstring reference

---

## Database Migration Required

### Option 1: Rename Existing Table (Recommended if keeping data)
```sql
-- Rename the table
ALTER TABLE solutions RENAME TO pesti_comp;

-- Rename the indexes
ALTER INDEX solutions_embedding_idx RENAME TO pesti_comp_embedding_idx;
ALTER INDEX solutions_embedding_hnsw_idx RENAME TO pesti_comp_embedding_hnsw_idx;

-- Update any sequences (if using SERIAL)
ALTER SEQUENCE solutions_id_seq RENAME TO pesti_comp_id_seq;
```

### Option 2: Create New Table (If starting fresh)
```sql
CREATE TABLE pesti_comp (
    id SERIAL PRIMARY KEY,
    cropname VARCHAR(200),
    problem TEXT,
    solution TEXT,
    embedding vector(768)
);

-- Create indexes
CREATE INDEX pesti_comp_embedding_idx 
ON pesti_comp USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);

CREATE INDEX pesti_comp_embedding_hnsw_idx 
ON pesti_comp USING hnsw (embedding vector_cosine_ops) 
WITH (m = 16, ef_construction = 200);
```

---

## Verification Checklist

After making database changes, verify:

- [ ] Django model loads correctly: `python manage.py check`
- [ ] Database connection works: `python manage.py shell` → `from api.models import Solution` → `Solution.objects.count()`
- [ ] Indexes exist: 
  ```sql
  SELECT indexname FROM pg_indexes WHERE tablename = 'pesti_comp';
  ```
- [ ] API endpoints work:
  - [ ] `GET /health` returns 200
  - [ ] `POST /init-db` creates indexes successfully
  - [ ] `POST /search` returns results
  - [ ] `GET /all` returns all records
  - [ ] `POST /generate-embeddings` works (if needed)

---

## Testing Commands

```bash
# Check database connection
python manage.py dbshell

# In psql:
\dt pesti_comp              # Verify table exists
\d pesti_comp               # Show table structure
SELECT COUNT(*) FROM pesti_comp;  # Count records

# Test API
curl http://localhost:8000/health
curl -X POST http://localhost:8000/search -H "Content-Type: application/json" -d '{"q":"टमाटर में कीड़े"}'
```

---

## Rollback Instructions

If you need to revert:

1. **Database:**
   ```sql
   ALTER TABLE pesti_comp RENAME TO solutions;
   ALTER INDEX pesti_comp_embedding_idx RENAME TO solutions_embedding_idx;
   ALTER INDEX pesti_comp_embedding_hnsw_idx RENAME TO solutions_embedding_hnsw_idx;
   ALTER SEQUENCE pesti_comp_id_seq RENAME TO solutions_id_seq;
   ```

2. **Code:** Revert the changes in:
   - api/models.py
   - api/views.py
   - services.py
   - api/admin.py

---

## Notes

- **Model class name remains `Solution`** (unchanged) - only the database table name changed
- **No API endpoint URLs changed** - all endpoints work exactly the same
- **No data loss** - this is purely a rename operation
- **Backward compatible** - as long as the database table is renamed, everything works

---

## Environment Variables

No changes required to `.env` file. The table name is hardcoded in the application code.

---

## Impact Analysis

### No Impact On:
- ✅ API endpoint URLs
- ✅ Request/response formats
- ✅ Authentication/authorization
- ✅ Frontend integration
- ✅ Embedding model
- ✅ Search algorithm

### Requires Update:
- ⚠️ **Database schema** (rename table)
- ⚠️ **Any external scripts** that directly query the `solutions` table
- ⚠️ **Database backups/exports** (will use new table name)
- ⚠️ **Database documentation** (update table name references)

---

## Related Files

### Code Files Changed
- `api/models.py` - Django ORM model
- `api/views.py` - REST API endpoints
- `services.py` - Core search logic
- `api/admin.py` - Django admin panel

### Documentation Files
- This file: `TABLE_NAME_CHANGE.md`
- Project summary: `PROJECT_SUMMARY.md` (should be updated)

---

## Next Steps

1. **Backup your database** before making any changes
2. **Run the SQL migration** (Option 1 or Option 2 above)
3. **Restart Django server**
4. **Run verification tests**
5. **Update any monitoring/logging** that references the old table name
6. **Update database documentation**

---

## Contact

If you encounter issues:
1. Check Django logs for errors
2. Verify table name in database: `\dt pesti_comp`
3. Check if indexes exist: `\di pesti_comp*`
4. Test direct database query: `SELECT COUNT(*) FROM pesti_comp;`
