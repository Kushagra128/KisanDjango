# Utility Scripts

This folder contains utility and testing scripts:

## Database Analysis
- **analyze_database.py** - Comprehensive database structure analysis
- **deep_data_analysis.py** - Deep insights from all 19,970 records
- **check_database.py** - Quick database health check
- **check_table_structure.py** - Table structure comparison

## API Testing
- **check_api.py** - Test API endpoints
- **simple_test.py** - Simple API test
- **test_similarity.py** - Similarity search testing

## Database Maintenance
- **fix_database_add_embedding.py** - Add embedding column to tables
- **generate_embeddings.py** - Generate embeddings for all records
- **remove_old_tables.py** - Clean up redundant tables
- **verify_table_usage.py** - Verify correct table usage

## Usage

Activate virtual environment first:
```bash
.\.venv\Scripts\Activate.ps1   # Windows PowerShell
source .venv/bin/activate       # Linux/Mac
```

Then run any script:
```bash
python scripts/check_database.py
python scripts/check_api.py
```
