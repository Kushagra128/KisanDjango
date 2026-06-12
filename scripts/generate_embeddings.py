"""
Generate embeddings for all records without embeddings
This is equivalent to calling POST /generate-embeddings
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kisan.settings')
django.setup()

from django.db import connection
from embedding_service import get_embedding_generator
import time

def generate_embeddings():
    print("=" * 60)
    print("GENERATING EMBEDDINGS FOR ALL RECORDS")
    print("=" * 60)
    
    # Get the embedding generator
    generator = get_embedding_generator()
    
    with connection.cursor() as cursor:
        # Get all records without embeddings
        cursor.execute("""
            SELECT id, cropname, problem 
            FROM pesti_comp 
            WHERE embedding IS NULL
            ORDER BY id
        """)
        records = cursor.fetchall()
        
        total = len(records)
        print(f"\nFound {total} records without embeddings")
        
        if total == 0:
            print("✓ All records already have embeddings!")
            return
        
        print(f"Estimated time: ~{total * 0.2:.0f} seconds ({total * 0.2 / 60:.1f} minutes)")
        print("\nStarting embedding generation...")
        print("(Press Ctrl+C to stop)\n")
        
        start_time = time.time()
        success_count = 0
        error_count = 0
        
        for i, (record_id, cropname, problem) in enumerate(records, 1):
            try:
                # Generate text to embed (same as API does)
                text_to_embed = f"{cropname} {problem}"
                
                # Generate embedding
                embedding = generator.generate_embedding(text_to_embed)
                
                if embedding is not None:
                    # Convert to list for PostgreSQL
                    embedding_list = embedding.tolist()
                    
                    # Update record
                    cursor.execute(
                        "UPDATE pesti_comp SET embedding = %s WHERE id = %s",
                        [embedding_list, record_id]
                    )
                    success_count += 1
                    
                    # Progress update every 100 records
                    if i % 100 == 0 or i == total:
                        elapsed = time.time() - start_time
                        rate = i / elapsed if elapsed > 0 else 0
                        eta = (total - i) / rate if rate > 0 else 0
                        print(f"Progress: {i}/{total} ({i/total*100:.1f}%) | "
                              f"Speed: {rate:.1f} rec/s | "
                              f"ETA: {eta/60:.1f} min")
                else:
                    error_count += 1
                    print(f"  ✗ Failed to generate embedding for ID {record_id}")
                    
            except KeyboardInterrupt:
                print("\n\n⚠ Interrupted by user")
                break
            except Exception as e:
                error_count += 1
                print(f"  ✗ Error processing ID {record_id}: {e}")
        
        elapsed = time.time() - start_time
        
        print("\n" + "=" * 60)
        print("EMBEDDING GENERATION COMPLETE")
        print("=" * 60)
        print(f"Success: {success_count} records")
        print(f"Errors: {error_count} records")
        print(f"Time taken: {elapsed/60:.1f} minutes ({elapsed:.0f} seconds)")
        print(f"Average speed: {success_count/elapsed:.1f} records/second")
        print("=" * 60)
        
        # Verify
        cursor.execute("SELECT COUNT(*) FROM pesti_comp WHERE embedding IS NOT NULL")
        with_embeddings = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM pesti_comp WHERE embedding IS NULL")
        without_embeddings = cursor.fetchone()[0]
        
        print(f"\nFinal status:")
        print(f"  With embeddings: {with_embeddings}")
        print(f"  Without embeddings: {without_embeddings}")
        
        if without_embeddings == 0:
            print(f"\n✓✓✓ ALL RECORDS NOW HAVE EMBEDDINGS! ✓✓✓")
            print(f"\nYou can now test search with:")
            print(f"  python check_api.py")
        else:
            print(f"\n⚠ {without_embeddings} records still need embeddings")
            print(f"  Run this script again to continue")

if __name__ == "__main__":
    try:
        generate_embeddings()
    except Exception as e:
        print(f"\n✗ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
