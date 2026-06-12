"""
Add embedding column to pesti_comp table
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kisan.settings')
django.setup()

from django.db import connection

def fix_database():
    print("=" * 60)
    print("FIXING DATABASE: Adding embedding column to pesti_comp")
    print("=" * 60)
    
    with connection.cursor() as cursor:
        # Step 1: Check current state
        print("\n1. Checking current table structure...")
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'pesti_comp'
        """)
        columns = [row[0] for row in cursor.fetchall()]
        print(f"   Current columns: {columns}")
        
        if 'embedding' in columns:
            print("   ✓ Embedding column already exists!")
            return
        
        # Step 2: Add embedding column
        print("\n2. Adding embedding column (vector 768)...")
        try:
            cursor.execute("ALTER TABLE pesti_comp ADD COLUMN embedding vector(768);")
            print("   ✓ Embedding column added successfully")
        except Exception as e:
            print(f"   ✗ Error: {e}")
            return
        
        # Step 3: Check pgvector extension
        print("\n3. Checking pgvector extension...")
        cursor.execute("""
            SELECT EXISTS(
                SELECT 1 FROM pg_extension WHERE extname = 'vector'
            );
        """)
        has_vector = cursor.fetchone()[0]
        if not has_vector:
            print("   ⚠ pgvector extension not installed. Installing...")
            try:
                cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                print("   ✓ pgvector extension installed")
            except Exception as e:
                print(f"   ✗ Error: {e}")
                print("   You may need to run: CREATE EXTENSION vector; manually with superuser")
        else:
            print("   ✓ pgvector extension already installed")
        
        # Step 4: Create IVFFLAT index (may take time with 19K records)
        print("\n4. Creating IVFFLAT index (this may take a few minutes)...")
        try:
            cursor.execute("DROP INDEX IF EXISTS pesti_comp_embedding_idx;")
            cursor.execute("""
                CREATE INDEX pesti_comp_embedding_idx 
                ON pesti_comp USING ivfflat (embedding vector_cosine_ops) 
                WITH (lists = 100);
            """)
            print("   ✓ IVFFLAT index created")
        except Exception as e:
            print(f"   ⚠ Could not create IVFFLAT index: {e}")
            print("   This is OK - index will be created when data has embeddings")
        
        # Step 5: Create HNSW index
        print("\n5. Creating HNSW index...")
        try:
            cursor.execute("DROP INDEX IF EXISTS pesti_comp_embedding_hnsw_idx;")
            cursor.execute("""
                CREATE INDEX pesti_comp_embedding_hnsw_idx 
                ON pesti_comp USING hnsw (embedding vector_cosine_ops) 
                WITH (m = 16, ef_construction = 200);
            """)
            print("   ✓ HNSW index created")
        except Exception as e:
            print(f"   ⚠ Could not create HNSW index: {e}")
            print("   This is OK - index will be created when data has embeddings")
        
        # Step 6: Verify
        print("\n6. Verifying changes...")
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'pesti_comp'
            ORDER BY ordinal_position
        """)
        columns = cursor.fetchall()
        print("   Table structure:")
        for col, dtype in columns:
            print(f"      - {col}: {dtype}")
        
        cursor.execute("SELECT COUNT(*) FROM pesti_comp")
        total = cursor.fetchone()[0]
        print(f"\n   ✓ Total records: {total}")
        
        cursor.execute("SELECT COUNT(*) FROM pesti_comp WHERE embedding IS NULL")
        null_embeddings = cursor.fetchone()[0]
        print(f"   Records without embeddings: {null_embeddings}")
        
        cursor.execute("SELECT COUNT(*) FROM pesti_comp WHERE embedding IS NOT NULL")
        with_embeddings = cursor.fetchone()[0]
        print(f"   Records with embeddings: {with_embeddings}")
        
        # Step 7: Check indexes
        print("\n7. Checking indexes...")
        cursor.execute("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE tablename = 'pesti_comp'
        """)
        indexes = [row[0] for row in cursor.fetchall()]
        if indexes:
            print(f"   Indexes: {indexes}")
        else:
            print("   No indexes found")
        
        print("\n" + "=" * 60)
        print("✓ DATABASE FIX COMPLETE!")
        print("=" * 60)
        print("\nNEXT STEPS:")
        print("1. Restart your Django server")
        print("2. Generate embeddings by calling: POST /generate-embeddings")
        print("   Or run: python manage.py shell")
        print("           from api.views import GenerateEmbeddingsView")
        print("3. Test the search with: POST /search")
        print("=" * 60)

if __name__ == "__main__":
    try:
        fix_database()
    except Exception as e:
        print(f"\n✗ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
