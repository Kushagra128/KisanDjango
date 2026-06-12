"""
Deep analysis of all 19,970 entries in pesti_comp table
Extract patterns, insights, and data characteristics
"""
import os
import django
import re
from collections import Counter, defaultdict

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kisan.settings')
django.setup()

from django.db import connection
from api.models import Solution

def analyze_all_data():
    print("=" * 100)
    print("DEEP DATA ANALYSIS - All 19,970 Entries")
    print("=" * 100)
    
    print("\n⏳ Loading all records from database...")
    all_records = list(Solution.objects.all())
    total_records = len(all_records)
    print(f"✓ Loaded {total_records:,} records\n")
    
    # ==================== CROP ANALYSIS ====================
    print("=" * 100)
    print("1️⃣  CROP ANALYSIS")
    print("=" * 100)
    
    crop_counter = Counter(record.cropname for record in all_records)
    unique_crops = len(crop_counter)
    
    print(f"\n📊 Total unique crops: {unique_crops}")
    print(f"\n🔝 Top 30 crops by problem count:")
    print("-" * 100)
    
    for i, (crop, count) in enumerate(crop_counter.most_common(30), 1):
        percentage = (count / total_records) * 100
        bar = "█" * int(percentage * 2)
        print(f"  {i:2}. {crop:20} {count:5,} records ({percentage:5.2f}%) {bar}")
    
    # Bottom crops
    print(f"\n🔻 Bottom 10 crops (least problems):")
    for crop, count in crop_counter.most_common()[-10:]:
        print(f"  • {crop:20} {count} record(s)")
    
    # ==================== PROBLEM TYPE ANALYSIS ====================
    print("\n" + "=" * 100)
    print("2️⃣  PROBLEM TYPE ANALYSIS")
    print("=" * 100)
    
    # Define problem categories with keywords
    problem_categories = {
        "कीट/कीड़े (Insects/Pests)": ["कीट", "कीड़", "सुंडी", "माहू", "insect", "pest", "bug", "worm"],
        "पत्ते पीले (Yellow Leaves)": ["पीला", "पील", "पीले", "yellow"],
        "सड़न/गलन (Rot/Decay)": ["सड़", "गल", "rot", "decay"],
        "सूखना/मुरझाना (Drying/Wilting)": ["सूख", "मुरझा", "कुम्हला", "dry", "wilt"],
        "फल झड़ना (Fruit Drop)": ["फल", "झड़", "गिर", "टूट", "fruit", "drop", "fall"],
        "फूल झड़ना (Flower Drop)": ["फूल", "flower", "bloom"],
        "धब्बे (Spots)": ["धब्ब", "spot", "काला"],
        "खरपतवार (Weeds)": ["खरपतवार", "weed"],
        "सफेद मक्खी (White Fly)": ["सफेद", "सफ़ेद", "white", "whitefly"],
        "फफूंद (Fungus)": ["फफूंद", "fungus", "fungal", "mold"],
        "विकास नहीं (No Growth)": ["विकास नहीं", "बढ़ नहीं", "growth", "नहीं बढ़"],
        "खेती/उगाना (Cultivation)": ["कैसे उगा", "खेती", "बुवाई", "cultivation", "grow"],
        "खाद (Fertilizer)": ["खाद", "उर्वरक", "fertilizer"],
        "सिंचाई (Irrigation)": ["सिंचाई", "पानी", "irrigation", "water"],
        "दीमक (Termite)": ["दीमक", "termite"],
    }
    
    category_counts = defaultdict(int)
    
    print("\n🔍 Analyzing problem patterns...")
    for record in all_records:
        problem_text = record.problem.lower()
        for category, keywords in problem_categories.items():
            if any(keyword in problem_text for keyword in keywords):
                category_counts[category] += 1
    
    print("\n📊 Problem distribution by category:")
    print("-" * 100)
    sorted_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
    
    for category, count in sorted_categories:
        percentage = (count / total_records) * 100
        bar = "█" * int(percentage * 2)
        print(f"  {category:30} {count:5,} ({percentage:5.2f}%) {bar}")
    
    # ==================== TEXT LENGTH ANALYSIS ====================
    print("\n" + "=" * 100)
    print("3️⃣  TEXT LENGTH ANALYSIS")
    print("=" * 100)
    
    problem_lengths = [len(r.problem) for r in all_records if r.problem]
    solution_lengths = [len(r.solution) for r in all_records if r.solution]
    
    print("\n📏 Problem text statistics:")
    print(f"  Average length: {sum(problem_lengths) / len(problem_lengths):.1f} characters")
    print(f"  Shortest: {min(problem_lengths)} characters")
    print(f"  Longest: {max(problem_lengths)} characters")
    print(f"  Median: {sorted(problem_lengths)[len(problem_lengths)//2]} characters")
    
    print("\n📏 Solution text statistics:")
    print(f"  Average length: {sum(solution_lengths) / len(solution_lengths):.1f} characters")
    print(f"  Shortest: {min(solution_lengths)} characters")
    print(f"  Longest: {max(solution_lengths)} characters")
    print(f"  Median: {sorted(solution_lengths)[len(solution_lengths)//2]} characters")
    
    # ==================== COMMON WORDS ANALYSIS ====================
    print("\n" + "=" * 100)
    print("4️⃣  COMMON WORDS IN PROBLEMS")
    print("=" * 100)
    
    # Stop words to ignore
    stop_words = {
        "के", "की", "का", "में", "से", "को", "पर", "है", "हैं", "हो", "रहे", "रहा", "रही",
        "कृपया", "समाधान", "बताने", "कष्ट", "करें", "कर", "गए", "गया", "गई", "ने", "और",
        "?", "।", "!", "भाई", "किसान", "प्रिय"
    }
    
    all_problem_words = []
    for record in all_records:
        if record.problem:
            words = re.findall(r'[\u0900-\u097F]+|[a-zA-Z]+', record.problem.lower())
            all_problem_words.extend([w for w in words if len(w) > 2 and w not in stop_words])
    
    word_counter = Counter(all_problem_words)
    
    print("\n🔤 Top 30 most common words in problems:")
    print("-" * 100)
    for i, (word, count) in enumerate(word_counter.most_common(30), 1):
        print(f"  {i:2}. {word:20} appears {count:5,} times")
    
    # ==================== SOLUTION PATTERNS ====================
    print("\n" + "=" * 100)
    print("5️⃣  SOLUTION PATTERNS")
    print("=" * 100)
    
    solution_keywords = {
        "रसायन/दवा (Chemicals)": ["रसायन", "दवा", "chemical", "pesticide"],
        "छिड़काव (Spray)": ["छिड़काव", "spray", "स्प्रे"],
        "नियंत्रण (Control)": ["नियंत्रण", "control"],
        "उपचार (Treatment)": ["उपचार", "treatment"],
        "खाद डालें (Apply Fertilizer)": ["खाद", "उर्वरक", "fertilizer"],
        "सिंचाई करें (Irrigate)": ["सिंचाई", "irrigation", "पानी दें"],
        "बीज उपचार (Seed Treatment)": ["बीज", "seed"],
        "ग्राम/मिली (Dosage)": ["ग्राम", "मिली", "gram", "ml"],
        "लीटर पानी (Liters of water)": ["लीटर", "लिटर", "liter"],
        "प्रति एकड़ (Per Acre)": ["एकड़", "acre"],
    }
    
    solution_pattern_counts = defaultdict(int)
    
    for record in all_records:
        if record.solution:
            solution_text = record.solution.lower()
            for pattern, keywords in solution_keywords.items():
                if any(keyword in solution_text for keyword in keywords):
                    solution_pattern_counts[pattern] += 1
    
    print("\n📋 Common solution elements:")
    print("-" * 100)
    sorted_solutions = sorted(solution_pattern_counts.items(), key=lambda x: x[1], reverse=True)
    
    for pattern, count in sorted_solutions:
        percentage = (count / total_records) * 100
        print(f"  {pattern:30} {count:5,} solutions ({percentage:5.2f}%)")
    
    # ==================== CROP-PROBLEM MATRIX ====================
    print("\n" + "=" * 100)
    print("6️⃣  CROP-PROBLEM MATRIX (Top 10 Crops)")
    print("=" * 100)
    
    top_crops = [crop for crop, _ in crop_counter.most_common(10)]
    
    print("\n📊 Most common problems per crop:")
    print("-" * 100)
    
    for crop in top_crops:
        crop_records = [r for r in all_records if r.cropname == crop]
        
        # Categorize problems for this crop
        crop_problem_counts = defaultdict(int)
        for record in crop_records:
            problem_text = record.problem.lower()
            for category, keywords in problem_categories.items():
                if any(keyword in problem_text for keyword in keywords):
                    crop_problem_counts[category] += 1
        
        print(f"\n  🌱 {crop} ({len(crop_records)} total problems):")
        top_problems = sorted(crop_problem_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        for prob_type, count in top_problems:
            percentage = (count / len(crop_records)) * 100
            print(f"     • {prob_type:30} {count:3} ({percentage:5.1f}%)")
    
    # ==================== DATA QUALITY ANALYSIS ====================
    print("\n" + "=" * 100)
    print("7️⃣  DATA QUALITY ANALYSIS")
    print("=" * 100)
    
    # Check for duplicates
    problem_hash = {}
    duplicate_groups = defaultdict(list)
    
    for record in all_records:
        # Simple duplicate check based on normalized problem text
        normalized = record.problem.lower().strip()
        key = (record.cropname, normalized)
        if key in problem_hash:
            duplicate_groups[key].append(record.id)
            if problem_hash[key] not in duplicate_groups[key]:
                duplicate_groups[key].insert(0, problem_hash[key])
        else:
            problem_hash[key] = record.id
    
    print(f"\n🔍 Duplicate analysis:")
    print(f"  Total duplicate groups: {len(duplicate_groups)}")
    print(f"  Total duplicate records: {sum(len(ids)-1 for ids in duplicate_groups.values())}")
    
    if duplicate_groups:
        print(f"\n  Sample duplicate groups (showing first 5):")
        for i, ((crop, prob), ids) in enumerate(list(duplicate_groups.items())[:5], 1):
            print(f"    {i}. {crop} - {prob[:50]}...")
            print(f"       IDs: {ids}")
    
    # Check embeddings
    with_embeddings = sum(1 for r in all_records if r.embedding is not None)
    print(f"\n📊 Embedding coverage:")
    print(f"  Records with embeddings: {with_embeddings:,} ({with_embeddings/total_records*100:.1f}%)")
    print(f"  Records without embeddings: {total_records - with_embeddings:,}")
    
    # Check for empty/short content
    short_problems = sum(1 for r in all_records if r.problem and len(r.problem) < 10)
    short_solutions = sum(1 for r in all_records if r.solution and len(r.solution) < 10)
    null_problems = sum(1 for r in all_records if not r.problem)
    null_solutions = sum(1 for r in all_records if not r.solution)
    
    print(f"\n⚠️  Short/null content:")
    print(f"  Problems < 10 chars: {short_problems}")
    print(f"  Solutions < 10 chars: {short_solutions}")
    print(f"  Null problems: {null_problems}")
    print(f"  Null solutions: {null_solutions}")
    
    # ==================== SAMPLE RECORDS ====================
    print("\n" + "=" * 100)
    print("8️⃣  SAMPLE RECORDS FROM DIFFERENT CROPS")
    print("=" * 100)
    
    sample_crops = ['आम', 'आलू', 'टमाटर', 'धान', 'गेहूं']
    
    for crop in sample_crops:
        crop_record = next((r for r in all_records if r.cropname == crop), None)
        if crop_record:
            print(f"\n🌾 {crop} (ID: {crop_record.id}):")
            print(f"  Problem:  {crop_record.problem[:100]}...")
            print(f"  Solution: {crop_record.solution[:100]}...")
    
    # ==================== FINAL SUMMARY ====================
    print("\n" + "=" * 100)
    print("🎯 KEY INSIGHTS SUMMARY")
    print("=" * 100)
    
    top_3_crops = crop_counter.most_common(3)
    top_3_problems = sorted_categories[:3]
    
    print(f"""
📊 DATABASE OVERVIEW:
  • Total records: {total_records:,}
  • Unique crops: {unique_crops}
  • Data completeness: {with_embeddings/total_records*100:.1f}% with embeddings
  
🌱 TOP CROPS:
  1. {top_3_crops[0][0]} - {top_3_crops[0][1]:,} problems
  2. {top_3_crops[1][0]} - {top_3_crops[1][1]:,} problems
  3. {top_3_crops[2][0]} - {top_3_crops[2][1]:,} problems
  
🐛 TOP PROBLEM TYPES:
  1. {top_3_problems[0][0]} - {top_3_problems[0][1]:,} cases
  2. {top_3_problems[1][0]} - {top_3_problems[1][1]:,} cases
  3. {top_3_problems[2][0]} - {top_3_problems[2][1]:,} cases

💡 RECOMMENDATIONS:
  • Focus search optimization on top 3 crops (cover {sum(c for _, c in top_3_crops)/total_records*100:.1f}% of all queries)
  • Improve symptom detection for top problem types
  • {f"Remove {sum(len(ids)-1 for ids in duplicate_groups.values())} duplicate records" if duplicate_groups else "Data is clean (no duplicates)"}
  • Consider adding more coverage for crops with < 5 problems
    """)
    
    print("=" * 100)
    print("✓ ANALYSIS COMPLETE - Generated comprehensive insights from all 19,970 records")
    print("=" * 100)

if __name__ == "__main__":
    try:
        analyze_all_data()
    except Exception as e:
        print(f"\n✗ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
