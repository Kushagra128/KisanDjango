"""
Check the structure of both tables
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kisan.settings')
django.setup()

from django.db import connection

def check_tables():
    print("=" * 60)
    print("TABLE STRUCTURE CHECK")
    print("=" * 60)
    
    with connection.cursor() as cursor:
        # Check solutions table
        print("\n1. SOLUTIONS TABLE:")
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'solutions'
            ORDER BY ordinal_position
        """)
        solutions_cols = cursor.fetchall()
        if solutions_cols:
            for col, dtype in solutions_cols:
                print(f"   - {col}: {dtype}")
        else:
            print("   ✗ Table does not exist")
        
        # Check pesti_comp table
        print("\n2. PESTI_COMP TABLE:")
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'pesti_comp'
            ORDER BY ordinal_position
        """)
        pesti_comp_cols = cursor.fetchall()
        if pesti_comp_cols:
            for col, dtype in pesti_comp_cols:
                print(f"   - {col}: {dtype}")
        else:
            print("   ✗ Table does not exist")
        
        # Check record counts
        print("\n3. RECORD COUNTS:")
        cursor.execute("SELECT COUNT(*) FROM solutions")
        print(f"   solutions: {cursor.fetchone()[0]} records")
        
        cursor.execute("SELECT COUNT(*) FROM pesti_comp")
        print(f"   pesti_comp: {cursor.fetchone()[0]} records")
        
        print("\n" + "=" * 60)
        print("RECOMMENDATION:")
        print("=" * 60)
        
        if solutions_cols and pesti_comp_cols:
            solutions_dict = {col: dtype for col, dtype in solutions_cols}
            pesti_comp_dict = {col: dtype for col, dtype in pesti_comp_cols}
            
            # Check if solutions has embedding but pesti_comp doesn't
            if 'embedding' in solutions_dict and 'embedding' not in pesti_comp_dict:
                print("\n⚠ ISSUE FOUND:")
                print("  - 'solutions' table has 'embedding' column")
                print("  - 'pesti_comp' table is MISSING 'embedding' column")
                print("\n✓ SOLUTION:")
                print("  You should DROP the incomplete 'pesti_comp' table")
                print("  and RENAME 'solutions' to 'pesti_comp' instead.")
                print("\n  SQL Commands:")
                print("  --------------")
                print("  DROP TABLE pesti_comp;")
                print("  ALTER TABLE solutions RENAME TO pesti_comp;")
                print("  ALTER INDEX solutions_embedding_idx RENAME TO pesti_comp_embedding_idx;")
                print("  ALTER INDEX solutions_embedding_hnsw_idx RENAME TO pesti_comp_embedding_hnsw_idx;")
                print("  ALTER SEQUENCE solutions_id_seq RENAME TO pesti_comp_id_seq;")
            elif not solutions_cols:
                print("\n✓ Good: Only pesti_comp exists, but it's missing embedding column")
                print("  Add the embedding column to pesti_comp")
            else:
                print("\nBoth tables exist with similar structure.")

if __name__ == "__main__":
    check_tables()
