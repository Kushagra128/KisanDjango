"""
Check if API is accessible and data is showing
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def check_api():
    print("=" * 60)
    print("API DATA CHECK")
    print("=" * 60)
    
    # Test 1: Health endpoint
    print("\n1. Checking /health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Server is running")
            print(f"  Status: {data.get('status')}")
            print(f"  Embedding Model: {data.get('embedding_model_loaded')}")
            print(f"  Database: {data.get('database_connected')}")
        else:
            print(f"✗ Health check failed: {response.status_code}")
            return
    except requests.exceptions.ConnectionError:
        print(f"✗ Cannot connect to {BASE_URL}")
        print("  Is Django server running? Start with: python manage.py runserver")
        return
    except Exception as e:
        print(f"✗ Error: {e}")
        return
    
    # Test 2: Get all data (paginated)
    print("\n2. Checking /all endpoint (first page)...")
    try:
        response = requests.get(f"{BASE_URL}/all?page=1&page_size=5", timeout=10)
        if response.status_code == 200:
            data = response.json()
            total = data.get('total', 0)
            results = data.get('results', [])
            print(f"✓ Total records in database: {total}")
            print(f"✓ Showing first {len(results)} records:")
            for i, item in enumerate(results[:3], 1):
                print(f"\n  [{i}] ID: {item.get('id')}")
                print(f"      Crop: {item.get('cropname')}")
                print(f"      Problem: {item.get('problem', '')[:80]}...")
        else:
            print(f"✗ Failed to fetch data: {response.status_code}")
            print(f"  Response: {response.text[:200]}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test 3: Check specific ID 120
    print("\n3. Checking ID 120 (problem case from context)...")
    try:
        response = requests.get(f"{BASE_URL}/all?page=1&page_size=200", timeout=10)
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            
            # Find ID 120
            id_120 = next((r for r in results if r.get('id') == 120), None)
            if id_120:
                print(f"✓ ID 120 found:")
                print(f"  Crop: {id_120.get('cropname')}")
                print(f"  Problem: {id_120.get('problem')}")
                print(f"  Solution: {id_120.get('solution', '')[:100]}...")
                
                # Check for Hindi characters
                problem_text = id_120.get('problem', '')
                if "सड़" in problem_text:
                    print(f"  ✓ Contains 'सड़' character")
                if "सड" in problem_text:
                    print(f"  ✓ Contains 'सड' character")
                if "अरवी" in problem_text:
                    print(f"  ✓ Contains 'अरवी' (taro crop)")
            else:
                print(f"✗ ID 120 not found in first 200 records")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test 4: Test search with the problem query
    print("\n4. Testing search with: 'अरवी के पत्ते में सड़न हो रही है'...")
    try:
        query = "अरवी के पत्ते में सड़न हो रही है"
        response = requests.post(
            f"{BASE_URL}/search",
            json={"q": query},
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Search returned result:")
            print(f"  ID: {result.get('id')}")
            print(f"  Crop: {result.get('cropname')}")
            print(f"  Problem: {result.get('problem', '')[:80]}...")
            print(f"  Score: {result.get('similarity_score')}")
            print(f"  Method: {result.get('search_method')}")
            print(f"  Detected Crop: {result.get('detected_crop')}")
            
            if result.get('id') == 120:
                print(f"\n  ✓✓✓ CORRECT! ID 120 returned as top result")
            else:
                print(f"\n  ⚠ Expected ID 120, got ID {result.get('id')}")
        else:
            print(f"✗ Search failed: {response.status_code}")
            print(f"  Response: {response.text[:300]}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test 5: Test search with GET method (returns top 10)
    print("\n5. Testing GET /search (top 10 results)...")
    try:
        query = "अरवी के पत्ते में सड़न हो रही है"
        response = requests.get(
            f"{BASE_URL}/search",
            params={"q": query},
            timeout=15
        )
        if response.status_code == 200:
            results = response.json()
            print(f"✓ Search returned {len(results)} results:")
            
            id_120_found = False
            for i, result in enumerate(results[:5], 1):
                print(f"\n  [{i}] ID: {result.get('id')} | Score: {result.get('similarity_score')}")
                print(f"      Problem: {result.get('problem', '')[:60]}...")
                if result.get('id') == 120:
                    id_120_found = True
                    print(f"      ^^^ This is ID 120! (Rank: {i})")
            
            if id_120_found:
                print(f"\n  ✓ ID 120 appears in top {len(results)} results")
            else:
                print(f"\n  ⚠ ID 120 NOT in top {len(results)} results")
        else:
            print(f"✗ Search failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    print("\n" + "=" * 60)
    print("API CHECK COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    check_api()
