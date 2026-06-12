"""
Quick script to check if database data is accessible
"""
import os
import django
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kisan.settings')
django.setup()

from django.db import connection
from api.models import Solution

def check_database():
    print("=" * 60)
    print("DATABASE CONNECTION CHECK")
    print("=" * 60)
    
    try:
        # Test 1: Check database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            print(f"✓ PostgreSQL Connected: {version[0][:50]}...")
            
        # Test 2: Check if table exists (try both old and new names)
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT tablename FROM pg_tables 
                WHERE tablename IN ('solutions', 'pesti_comp')
            """)
            tables = cursor.fetchall()
            if tables:
                print(f"✓ Tables found: {[t[0] for t in tables]}")
            else:
                print("✗ ERROR: Neither 'solutions' nor 'pesti_comp' table exists!")
                return
        
        # Test 3: Count total records
        try:
            count = Solution.objects.count()
            print(f"✓ Total records in database: {count}")
        except Exception as e:
            print(f"✗ ERROR counting records: {e}")
            print("\nNote: If table 'solutions' doesn't exist, you need to rename it to 'pesti_comp'")
            print("Run: ALTER TABLE solutions RENAME TO pesti_comp;")
            return
        
        if count == 0:
            print("⚠ WARNING: Database is empty! No data to query.")
            return
        
        # Test 4: Sample 5 records
        print("\n" + "=" * 60)
        print("SAMPLE DATA (First 5 records)")
        print("=" * 60)
        samples = Solution.objects.all()[:5]
        for sol in samples:
            print(f"\nID: {sol.id}")
            print(f"Crop: {sol.cropname}")
            print(f"Problem: {sol.problem[:80]}...")
            print(f"Solution: {sol.solution[:80]}...")
            print(f"Has Embedding: {sol.embedding is not None}")
        
        # Test 5: Check specific ID 120 (the problematic one from context)
        print("\n" + "=" * 60)
        print("CHECKING ID 120 (Problem Case)")
        print("=" * 60)
        try:
            sol_120 = Solution.objects.get(id=120)
            print(f"✓ ID 120 exists")
            print(f"Crop: {sol_120.cropname}")
            print(f"Problem: {sol_120.problem}")
            print(f"Solution: {sol_120.solution[:100]}...")
            print(f"Has Embedding: {sol_120.embedding is not None}")
            
            # Check for the specific Hindi characters
            if "सड़" in sol_120.problem:
                print(f"✓ Contains 'सड़' character")
            if "सड" in sol_120.problem:
                print(f"✓ Contains 'सड' character")
                
        except Solution.DoesNotExist:
            print("✗ ID 120 not found in database")
        
        # Test 6: Check embeddings
        print("\n" + "=" * 60)
        print("EMBEDDING STATUS")
        print("=" * 60)
        with_embeddings = Solution.objects.filter(embedding__isnull=False).count()
        without_embeddings = Solution.objects.filter(embedding__isnull=True).count()
        print(f"With embeddings: {with_embeddings}")
        print(f"Without embeddings: {without_embeddings}")
        
        if without_embeddings > 0:
            print(f"⚠ WARNING: {without_embeddings} records missing embeddings")
            print("Run: POST /generate-embeddings to fix")
        
        # Test 7: Check pgvector extension
        print("\n" + "=" * 60)
        print("PGVECTOR EXTENSION")
        print("=" * 60)
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT extname, extversion 
                FROM pg_extension 
                WHERE extname = 'vector'
            """)
            result = cursor.fetchone()
            if result:
                print(f"✓ pgvector extension installed: v{result[1]}")
            else:
                print("✗ pgvector extension NOT installed!")
                print("Run: POST /init-db to install")
        
        # Test 8: Check indexes
        print("\n" + "=" * 60)
        print("INDEXES")
        print("=" * 60)
        with connection.cursor() as cursor:
            # Try both table names
            for table_name in ['pesti_comp', 'solutions']:
                cursor.execute("""
                    SELECT indexname 
                    FROM pg_indexes 
                    WHERE tablename = %s
                """, [table_name])
                indexes = cursor.fetchall()
                if indexes:
                    print(f"✓ Indexes on '{table_name}': {[i[0] for i in indexes]}")
                    break
            else:
                print("⚠ No indexes found")
        
        print("\n" + "=" * 60)
        print("✓ DATABASE CHECK COMPLETE")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_database()
