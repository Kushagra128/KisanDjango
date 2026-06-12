# Database Complete Analysis - KisanDjango

**Date:** June 12, 2026  
**Database:** Kisan_AI (PostgreSQL 17.7)  
**Size:** 235 MB

---

## 📊 ACTIVE TABLES

### 1. **pesti_comp** (PRIMARY TABLE) ✅

- **Purpose**: Main agricultural advice database
- **Records**: 19,970
- **Size**: 214 MB
- **Embeddings**: 19,970 (100% complete) ✅
- **Structure**:
  - `id` (integer) - Primary key
  - `problem` (text) - Farmer's problem description
  - `solution` (text) - Recommended solution
  - `cropname` (text) - Crop name (Hindi)
  - `embedding` (vector[768]) - AI embedding for semantic search

**Indexes**:

- `pesti_comp_pkey` - Primary key
- `pesti_comp_embedding_idx` - IVFFLAT vector index
- `pesti_comp_embedding_hnsw_idx` - HNSW vector index

**Top Crops by Record Count**:

1. आलू (Potato): 2,033 records
2. आम (Mango): 1,701 records
3. अरहर (Pigeon pea): 407 records
4. अमरुद (Guava): 288 records
5. धान (Rice): Multiple records

**Total Unique Crops**: 80+

---

### 2. **chatbot_unansweredproblem**

- **Purpose**: Track queries that couldn't be answered
- **Records**: 15
- **Size**: 32 KB
- **Structure**:
  - `id` (bigint) - Primary key
  - `query` (text) - User's query
  - `detected_intent` (varchar) - Classified intent
  - `detected_crop` (varchar) - Detected crop (nullable)
  - `timestamp` (timestamp) - When query was made

**Use Case**: Analytics and system improvement

---

## 🗑️ OLD/DUPLICATE TABLES (Can be removed)

### 3. **solutions** ⚠️

- **Status**: OLD TABLE - Should be dropped
- **Records**: 1,513
- **Size**: 11 MB
- **Note**: Subset of pesti_comp data (duplicate)

### 4. **chatbot_agriculturaladvice** ⚠️

- **Status**: OLD TABLE (no embeddings)
- **Records**: 1,513
- **Size**: 1 MB
- **Note**: Same data as solutions but without embedding column

### 5. **test_vectors**

- **Status**: Empty test table
- **Records**: 0
- **Note**: Can be safely dropped

---

## 🔐 DJANGO SYSTEM TABLES

### Authentication & Authorization

- `auth_user` - 1 superuser (username: kisanai)
- `auth_group` - 0 groups
- `auth_permission` - 36 permissions
- `auth_group_permissions` - Empty
- `auth_user_groups` - Empty
- `auth_user_user_permissions` - Empty

### Django Admin

- `django_admin_log` - 0 admin actions logged
- `django_content_type` - 9 content types
- `django_migrations` - 19 migrations applied
- `django_session` - 0 active sessions

---

## 🔧 DATABASE CONFIGURATION

### Extensions Installed

- **plpgsql** v1.0 (PostgreSQL procedural language)
- **vector** v0.8.2 (pgvector for semantic search) ✅

### Connection Details (from .env)

- **Host**: localhost
- **Port**: 5050
- **Database**: Kisan_AI
- **User**: querymind

---

## ✅ HEALTH STATUS

| Metric                  | Status       | Details                 |
| ----------------------- | ------------ | ----------------------- |
| Database Connection     | ✅ Healthy   | PostgreSQL 17.7 running |
| Main Table (pesti_comp) | ✅ Healthy   | 19,970 records          |
| Embeddings Generated    | ✅ Complete  | 100% (19,970/19,970)    |
| Vector Indexes          | ✅ Active    | IVFFLAT + HNSW          |
| pgvector Extension      | ✅ Installed | v0.8.2                  |
| Total Size              | ✅ Normal    | 235 MB                  |

---

## 📈 DATA STATISTICS

### Record Distribution

```
Total records in pesti_comp: 19,970
- With embeddings: 19,970 (100%)
- Without embeddings: 0 (0%)

Old tables (duplicate data):
- solutions: 1,513 records
- chatbot_agriculturaladvice: 1,513 records
```

### Crop Coverage

```
Top 5 crops by record count:
1. आलू (Potato) - 2,033 records (10.2%)
2. आम (Mango) - 1,701 records (8.5%)
3. अरहर (Pigeon pea) - 407 records (2.0%)
4. अमरुद (Guava) - 288 records (1.4%)
5. धान (Rice) - Multiple records

Total unique crops: 80+
```

### Sample Problems (from pesti_comp)

1. "धान की बालिया काली हो रही है कृपया समाधान बताने का कष्ट करें"
2. "धान की पत्तियाँ पीली हो रही है कृपया समाधान बताने का कष्ट करें"
3. "अमरुद के पेड़ सूख रहे है और फल झड़ रहे है कृपया समाधान बताने का कष्ट करें"

---

## 🔄 MIGRATION HISTORY

### Previous Changes

1. ✅ Renamed table from `solutions` to `pesti_comp` (code level)
2. ✅ Added `embedding` column to `pesti_comp`
3. ✅ Created vector indexes (IVFFLAT + HNSW)
4. ✅ Generated embeddings for all 19,970 records

### Pending Cleanup (Optional)

- Drop old `solutions` table (duplicate data)
- Drop `test_vectors` table (empty)
- Consider dropping `chatbot_agriculturaladvice` if not needed

---

## 🎯 RECOMMENDATIONS

### Immediate Actions

1. ✅ **No action needed** - Database is fully operational
2. ✅ **Embeddings complete** - Search ready to use
3. ✅ **Indexes active** - Performance optimized

### Optional Cleanup

Run `CLEANUP_OLD_TABLES.sql` to remove duplicate tables:

```sql
DROP TABLE IF EXISTS solutions CASCADE;
DROP TABLE IF EXISTS test_vectors CASCADE;
```

This will free up ~11 MB of space and reduce confusion.

### Monitoring

- Track queries in `chatbot_unansweredproblem` table
- Add more problem-solution pairs as farmers use the system
- Regenerate embeddings if adding bulk data

---

## 🚀 NEXT STEPS

1. **Test Search Functionality**:
   - Server is running on port 8000
   - Use POST /search endpoint
   - Example: `{"q": "टमाटर के पत्ते पीले हो रहे हैं"}`

2. **Monitor Performance**:
   - Check search response times
   - Review unanswered queries
   - Adjust MIN_RETURN_SCORE if needed (currently 0.45)

3. **Data Management**:
   - Regular backups recommended
   - Add new solutions as needed
   - Update embeddings when adding data

---

## 📞 SUPPORT

For database issues:

1. Check connection: `python check_database.py`
2. Analyze structure: `python analyze_database.py`
3. Test API: `python check_api.py`
4. Generate embeddings: `python generate_embeddings.py`

---

**Last Updated**: June 12, 2026  
**Database Version**: PostgreSQL 17.7  
**Application**: KisanDjango Agricultural Advisory System
