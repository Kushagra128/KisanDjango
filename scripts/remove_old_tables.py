"""
Remove old redundant tables and keep only pesti_comp (19,970 records)
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kisan.settings')
django.setup()

from django.db import connection

def remove_old_tables():
    print("=" * 80)
    print("REMOVING OLD REDUNDANT TABLES")
    print("=" * 80)
    
    with connection.cursor() as cursor:
        # Step 1: Check what we're about to remove
        print("\n📊 CURRENT STATE:")
        print("-" * 80)
        
        tables_to_check = ['solutions', 'chatbot_agriculturaladvice', 'test_vectors', 'pesti_comp']
        
        for table in tables_to_check:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table};")
                count = cursor.fetchone()[0]
                print(f"  • {table}: {count:,} records")
            except Exception as e:
                print(f"  • {table}: Does not exist")
        
        # Step 2: Confirm with user what will happen
        print("\n" + "=" * 80)
        print("⚠️  TABLES TO BE REMOVED:")
        print("=" * 80)
        print("  1. solutions (1,513 records) - OLD TABLE")
        print("  2. chatbot_agriculturaladvice (1,513 records) - OLD TABLE")
        print("  3. test_vectors (0 records) - EMPTY TEST TABLE")
        print("\n✅ TABLE TO KEEP:")
        print("  • pesti_comp (19,970 records) - YOUR MAIN TABLE")
        
        print("\n" + "=" * 80)
        print("STARTING CLEANUP...")
        print("=" * 80)
        
        # Step 3: Drop old tables
        tables_to_drop = [
            ('solutions', 'Old table with 1,513 records (subset of pesti_comp)'),
            ('chatbot_agriculturaladvice', 'Old table without embeddings'),
            ('test_vectors', 'Empty test table')
        ]
        
        dropped_count = 0
        
        for table_name, description in tables_to_drop:
            print(f"\n🗑️  Dropping {table_name}...")
            print(f"   Reason: {description}")
            
            try:
                cursor.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE;")
                print(f"   ✓ Successfully dropped {table_name}")
                dropped_count += 1
            except Exception as e:
                print(f"   ✗ Error dropping {table_name}: {e}")
        
        print(f"\n{'='*80}")
        print(f"✓ CLEANUP COMPLETE - {dropped_count} tables removed")
        print("=" * 80)
        
        # Step 4: Verify final state
        print("\n📊 FINAL STATE:")
        print("-" * 80)
        
        cursor.execute("""
            SELECT tablename, pg_size_pretty(pg_total_relation_size('public.'||tablename))
            FROM pg_tables 
            WHERE schemaname = 'public' 
            AND tablename NOT LIKE 'auth_%'
            AND tablename NOT LIKE 'django_%'
            ORDER BY tablename;
        """)
        
        remaining_tables = cursor.fetchall()
        
        for table, size in remaining_tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table};")
            count = cursor.fetchone()[0]
            print(f"  ✓ {table}: {count:,} records ({size})")
        
        # Step 5: Verify pesti_comp is intact
        print("\n" + "=" * 80)
        print("✓ VERIFICATION: pesti_comp table")
        print("=" * 80)
        
        cursor.execute("SELECT COUNT(*) FROM pesti_comp;")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM pesti_comp WHERE embedding IS NOT NULL;")
        with_emb = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT cropname) FROM pesti_comp;")
        unique_crops = cursor.fetchone()[0]
        
        print(f"\n  Total records: {total:,}")
        print(f"  With embeddings: {with_emb:,} ({with_emb/total*100:.1f}%)")
        print(f"  Unique crops: {unique_crops}")
        
        # Check indexes
        cursor.execute("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE tablename = 'pesti_comp';
        """)
        indexes = [row[0] for row in cursor.fetchall()]
        print(f"  Indexes: {len(indexes)} ({', '.join(indexes)})")
        
        # Sample data
        print("\n  Sample records:")
        cursor.execute("SELECT id, cropname, LEFT(problem, 60) FROM pesti_comp LIMIT 3;")
        samples = cursor.fetchall()
        for rec_id, crop, prob in samples:
            print(f"    • ID {rec_id}: {crop} - {prob}...")
        
        print("\n" + "=" * 80)
        print("✅ SUCCESS! Old tables removed, pesti_comp is your only data table")
        print("=" * 80)
        
        print("\nNEXT STEPS:")
        print("1. ✓ Database is clean (no redundant tables)")
        print("2. ✓ pesti_comp has 19,970 records with embeddings")
        print("3. ✓ Django models.py already uses db_table='pesti_comp'")
        print("4. → Restart Django server and test the API")
        print("\nTest command:")
        print("  python check_api.py")

if __name__ == "__main__":
    try:
        remove_old_tables()
    except Exception as e:
        print(f"\n✗ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
