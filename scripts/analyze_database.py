"""
Comprehensive database analysis - get full picture of all tables and entities
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kisan.settings')
django.setup()

from django.db import connection
import json

def analyze_database():
    print("=" * 80)
    print("COMPREHENSIVE DATABASE ANALYSIS")
    print("=" * 80)
    
    with connection.cursor() as cursor:
        # 1. List all tables in the database
        print("\n📊 ALL TABLES IN DATABASE:")
        print("-" * 80)
        cursor.execute("""
            SELECT 
                schemaname,
                tablename,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
            FROM pg_tables 
            WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
            ORDER BY tablename;
        """)
        tables = cursor.fetchall()
        
        all_tables = []
        for schema, table, size in tables:
            print(f"  📋 {schema}.{table} (Size: {size})")
            all_tables.append(table)
        
        print(f"\nTotal tables found: {len(all_tables)}")
        
        # 2. Detailed analysis of each table
        print("\n" + "=" * 80)
        print("DETAILED TABLE ANALYSIS")
        print("=" * 80)
        
        for table_name in all_tables:
            print(f"\n{'='*80}")
            print(f"TABLE: {table_name}")
            print(f"{'='*80}")
            
            # Get column information
            print("\n📝 COLUMNS:")
            cursor.execute("""
                SELECT 
                    column_name,
                    data_type,
                    character_maximum_length,
                    is_nullable,
                    column_default
                FROM information_schema.columns 
                WHERE table_name = %s
                ORDER BY ordinal_position;
            """, [table_name])
            columns = cursor.fetchall()
            
            for col_name, dtype, max_len, nullable, default in columns:
                len_info = f"({max_len})" if max_len else ""
                null_info = "NULL" if nullable == "YES" else "NOT NULL"
                default_info = f" DEFAULT {default}" if default else ""
                print(f"  • {col_name}: {dtype}{len_info} {null_info}{default_info}")
            
            # Get row count
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                count = cursor.fetchone()[0]
                print(f"\n📈 RECORD COUNT: {count:,} records")
            except Exception as e:
                print(f"\n⚠ Could not count records: {e}")
            
            # Get indexes
            print("\n🔍 INDEXES:")
            cursor.execute("""
                SELECT 
                    indexname,
                    indexdef
                FROM pg_indexes 
                WHERE tablename = %s;
            """, [table_name])
            indexes = cursor.fetchall()
            
            if indexes:
                for idx_name, idx_def in indexes:
                    print(f"  • {idx_name}")
                    print(f"    {idx_def[:100]}...")
            else:
                print("  No indexes")
            
            # Get primary key
            print("\n🔑 PRIMARY KEY:")
            cursor.execute("""
                SELECT a.attname
                FROM pg_index i
                JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
                WHERE i.indrelid = %s::regclass AND i.indisprimary;
            """, [table_name])
            pk = cursor.fetchall()
            if pk:
                print(f"  {', '.join([col[0] for col in pk])}")
            else:
                print("  No primary key")
            
            # Get foreign keys
            print("\n🔗 FOREIGN KEYS:")
            cursor.execute("""
                SELECT
                    tc.constraint_name,
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_name = %s;
            """, [table_name])
            fks = cursor.fetchall()
            
            if fks:
                for fk_name, col, ref_table, ref_col in fks:
                    print(f"  • {col} → {ref_table}.{ref_col}")
            else:
                print("  No foreign keys")
            
            # Sample data (first 3 records)
            print("\n📄 SAMPLE DATA (First 3 records):")
            try:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 3;")
                sample_data = cursor.fetchall()
                
                # Get column names
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = %s
                    ORDER BY ordinal_position;
                """, [table_name])
                col_names = [row[0] for row in cursor.fetchall()]
                
                if sample_data:
                    for i, row in enumerate(sample_data, 1):
                        print(f"\n  Record {i}:")
                        for col_name, value in zip(col_names, row):
                            # Truncate long values
                            if isinstance(value, str) and len(value) > 100:
                                display_value = value[:100] + "..."
                            elif isinstance(value, list) and len(str(value)) > 100:
                                display_value = "[vector data]"
                            else:
                                display_value = value
                            print(f"    {col_name}: {display_value}")
                else:
                    print("  No data in table")
            except Exception as e:
                print(f"  ⚠ Could not fetch sample data: {e}")
        
        # 3. Check for specific embedding status (if pesti_comp exists)
        if 'pesti_comp' in all_tables:
            print("\n" + "=" * 80)
            print("PESTI_COMP EMBEDDING ANALYSIS")
            print("=" * 80)
            
            cursor.execute("SELECT COUNT(*) FROM pesti_comp WHERE embedding IS NULL;")
            null_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM pesti_comp WHERE embedding IS NOT NULL;")
            filled_count = cursor.fetchone()[0]
            
            total = null_count + filled_count
            percentage = (filled_count / total * 100) if total > 0 else 0
            
            print(f"\n  Total records: {total:,}")
            print(f"  With embeddings: {filled_count:,} ({percentage:.1f}%)")
            print(f"  Without embeddings: {null_count:,} ({100-percentage:.1f}%)")
            
            if null_count > 0:
                print(f"\n  ⚠ {null_count:,} records need embeddings generated")
            else:
                print(f"\n  ✓ All records have embeddings!")
            
            # Get unique crop names
            print("\n  📊 UNIQUE CROPS:")
            cursor.execute("SELECT DISTINCT cropname FROM pesti_comp ORDER BY cropname LIMIT 20;")
            crops = cursor.fetchall()
            print(f"  Found {len(crops)} unique crops (showing first 20):")
            for crop in crops:
                cursor.execute("SELECT COUNT(*) FROM pesti_comp WHERE cropname = %s;", [crop[0]])
                crop_count = cursor.fetchone()[0]
                print(f"    • {crop[0]}: {crop_count:,} records")
        
        # 4. Check for solutions table (old table)
        if 'solutions' in all_tables:
            print("\n" + "=" * 80)
            print("⚠ OLD 'SOLUTIONS' TABLE STILL EXISTS")
            print("=" * 80)
            
            cursor.execute("SELECT COUNT(*) FROM solutions;")
            old_count = cursor.fetchone()[0]
            print(f"  Contains {old_count:,} records")
            
            cursor.execute("SELECT COUNT(*) FROM solutions WHERE embedding IS NOT NULL;")
            old_emb_count = cursor.fetchone()[0]
            print(f"  With embeddings: {old_emb_count:,}")
            
            print("\n  💡 RECOMMENDATION:")
            print("  You may want to drop this old table if pesti_comp has all data:")
            print("  DROP TABLE solutions;")
        
        # 5. Database size summary
        print("\n" + "=" * 80)
        print("DATABASE SIZE SUMMARY")
        print("=" * 80)
        
        cursor.execute("""
            SELECT 
                pg_size_pretty(pg_database_size(current_database())) as db_size;
        """)
        db_size = cursor.fetchone()[0]
        print(f"\n  Total database size: {db_size}")
        
        # 6. Extensions
        print("\n" + "=" * 80)
        print("INSTALLED EXTENSIONS")
        print("=" * 80)
        
        cursor.execute("""
            SELECT extname, extversion 
            FROM pg_extension 
            ORDER BY extname;
        """)
        extensions = cursor.fetchall()
        for ext_name, ext_version in extensions:
            print(f"  • {ext_name} v{ext_version}")
        
        print("\n" + "=" * 80)
        print("✓ ANALYSIS COMPLETE")
        print("=" * 80)

if __name__ == "__main__":
    try:
        analyze_database()
    except Exception as e:
        print(f"\n✗ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
