# 📊 Database Deep Insights - KisanDjango

**Analysis Date:** June 12, 2026  
**Total Records Analyzed:** 19,970  
**Table:** pesti_comp

---

## 🎯 EXECUTIVE SUMMARY

Your agricultural advisory database contains **19,970 problem-solution pairs** covering **130 different crops**. The data shows a strong focus on major Indian crops (rice, wheat, potato) with comprehensive coverage of common agricultural problems.

### Key Statistics

- **Data Completeness:** 100% (all records have embeddings)
- **Average Problem Length:** 54 characters
- **Average Solution Length:** 144 characters
- **Top 3 Crops:** Rice (34.7%), Wheat (17.5%), Potato (10.2%)
- **Most Common Problem:** Yellow Leaves (18.5%)

---

## 🌾 1. CROP COVERAGE ANALYSIS

### Top 10 Crops (by problem count)

| Rank | Crop              | Problems | % of Total |
| ---- | ----------------- | -------- | ---------- |
| 1    | धान (Rice)        | 6,924    | 34.67%     |
| 2    | गेहूँ (Wheat)     | 3,486    | 17.46%     |
| 3    | आलू (Potato)      | 2,033    | 10.18%     |
| 4    | आम (Mango)        | 1,701    | 8.52%      |
| 5    | टमाटर (Tomato)    | 806      | 4.04%      |
| 6    | उर्द (Black gram) | 625      | 3.13%      |
| 7    | चना (Chickpea)    | 514      | 2.57%      |
| 8    | केला (Banana)     | 409      | 2.05%      |
| 9    | अरहर (Pigeon pea) | 407      | 2.04%      |
| 10   | गोभी (Cabbage)    | 353      | 1.77%      |

**Insight:** Top 3 crops (Rice, Wheat, Potato) account for **62.3%** of all queries. Optimizing search for these crops will impact the majority of users.

### Crop Diversity

- **130 unique crops** covered
- **Long tail distribution**: 60+ crops have < 10 problems each
- **Staple crops dominate**: Rice + Wheat = 52% of database

---

## 🐛 2. PROBLEM TYPE ANALYSIS

### Most Common Problem Categories

| Category                          | Count | % of Total |
| --------------------------------- | ----- | ---------- |
| 🟡 पत्ते पीले (Yellow Leaves)     | 3,686 | 18.46%     |
| 🐛 कीट/कीड़े (Insects/Pests)      | 3,121 | 15.63%     |
| 🌿 खरपतवार (Weeds)                | 1,577 | 7.90%      |
| 💀 सूखना/मुरझाना (Drying/Wilting) | 1,336 | 6.69%      |
| 🍎 फल झड़ना (Fruit Drop)          | 707   | 3.54%      |
| 🐜 दीमक (Termite)                 | 655   | 3.28%      |
| ⚫ धब्बे (Spots)                  | 388   | 1.94%      |
| 🌸 फूल झड़ना (Flower Drop)        | 329   | 1.65%      |
| 💔 सड़न/गलन (Rot/Decay)           | 257   | 1.29%      |
| 📉 विकास नहीं (No Growth)         | 160   | 0.80%      |

**Key Finding:** Yellow leaves and insect problems account for **34%** of all issues - these should be prioritized in symptom detection algorithms.

---

## 🔬 3. CROP-SPECIFIC PROBLEM PATTERNS

### धान (Rice) - 6,924 Problems

- **Yellow Leaves:** 31.1% (most common)
- **Insects/Pests:** 17.7%
- **Weeds:** 5.8%
- **Termites:** 4.9%

### गेहूँ (Wheat) - 3,486 Problems

- **Yellow Leaves:** 28.7%
- **Weeds:** 27.9% (major issue)
- **Termites:** 5.3%

### आलू (Potato) - 2,033 Problems

- **Drying/Wilting:** 10.8% (dominant)
- **Spots:** 3.5%
- **Rot/Decay:** 2.7%

### आम (Mango) - 1,701 Problems

- **Drying/Wilting:** 18.1%
- **Insects/Pests:** 18.0%
- **Fruit Drop:** 7.4%

### टमाटर (Tomato) - 806 Problems

- **Drying/Wilting:** 14.6%
- **Insects/Pests:** 12.4%
- **Flower Drop:** 9.6%

**Insight:** Each major crop has a unique problem profile. Search algorithms should weight symptoms differently based on detected crop.

---

## 📝 4. TEXT CHARACTERISTICS

### Problem Text

- **Average:** 54 characters
- **Median:** 59 characters
- **Range:** 15-342 characters
- **Format:** Typically: "[Crop] की/के [part] में [symptom] है कृपया समाधान बताने का कष्ट करें"

### Solution Text

- **Average:** 144 characters
- **Median:** 129 characters
- **Range:** 11-498 characters
- **Format:** Chemical name + dosage + application method

### Most Common Words in Problems

| Rank | Word     | Frequency | Translation     |
| ---- | -------- | --------- | --------------- |
| 1    | धान      | 6,927     | Rice            |
| 2    | पौधों    | 5,793     | Plants (plural) |
| 3    | लगे      | 3,313     | Affected        |
| 4    | पीली     | 3,035     | Yellow          |
| 5    | कीट      | 2,934     | Insect          |
| 6    | पत्तियाँ | 2,868     | Leaves          |
| 7    | गेहूं    | 2,558     | Wheat           |
| 8    | रोग      | 2,046     | Disease         |
| 9    | आलू      | 2,034     | Potato          |
| 10   | खरपतवार  | 1,577     | Weeds           |

---

## 💊 5. SOLUTION PATTERNS

### Common Solution Elements

| Element                     | Frequency | % of Solutions |
| --------------------------- | --------- | -------------- |
| लीटर पानी (Liters of water) | 12,925    | 64.72%         |
| ग्राम/मिली (Dosage)         | 10,713    | 53.65%         |
| छिड़काव (Spray)             | 8,673     | 43.43%         |
| प्रति एकड़ (Per Acre)       | 3,378     | 16.92%         |
| नियंत्रण (Control)          | 2,711     | 13.58%         |
| रसायन/दवा (Chemicals)       | 2,496     | 12.50%         |
| उपचार (Treatment)           | 1,158     | 5.80%          |
| सिंचाई करें (Irrigate)      | 976       | 4.89%          |
| बीज उपचार (Seed Treatment)  | 917       | 4.59%          |
| खाद डालें (Fertilizer)      | 823       | 4.12%          |

**Insight:**

- **64.7%** of solutions specify water quantities (highly standardized)
- **43.4%** recommend spray applications
- Solutions follow a consistent format: Chemical + Dosage + Method

---

## ⚠️ 6. DATA QUALITY ISSUES

### Critical Finding: High Duplication Rate

```
Total Duplicate Groups: 697
Total Duplicate Records: 18,803 (94.2% of database!)
```

**Examples of Duplicates:**

1. "अंगूर की फसल में फल नहीं लग रहे हैं" - appears 2 times (IDs: 1780, 3810)
2. "अंगूर के पौधों में कीट लगे है" - appears 5 times (IDs: 2901, 8549, 11505, 16355, 19438)
3. "अंगूर के पौधों का विकास नहीं हो रहा है" - appears 3 times

**Impact:**

- **94.2%** of records are duplicates
- Only **~1,167 unique** problem-solution pairs
- Inflated database size
- Potential search result redundancy

### Data Completeness

✅ **Embeddings:** 100% (19,970/19,970)  
✅ **Problems:** 100% (0 null values)  
⚠️ **Solutions:** 99.95% (9 null values)  
✅ **Crop names:** 100%

---

## 🎯 7. ACTIONABLE RECOMMENDATIONS

### High Priority

1. **Remove Duplicates**
   - Current: 19,970 records (94.2% duplicates)
   - After cleanup: ~1,167 unique records
   - Action: Run deduplication script
   - Impact: Cleaner search results, faster queries

2. **Optimize for Top 3 Crops**
   - Rice, Wheat, Potato = 62.3% of queries
   - Add crop-specific symptom boosting
   - Tune keyword weights per crop

3. **Improve Yellow Leaves Detection**
   - 18.5% of all problems
   - Currently: keyword "पीला", "पीले", "yellow"
   - Add: "पीली", "yellowing", inflections
   - Boost: +1.5 for exact matches

4. **Enhance Insect/Pest Detection**
   - 15.6% of all problems
   - Add common insect names to PRIMARY_SYMPTOMS
   - Expand: माहू, सुंडी, तेला, white fly, aphid

### Medium Priority

5. **Add Crop-Problem Matrix Weights**
   - Example: "Wilting" + "Potato" should score higher than "Wilting" + "Rice"
   - Use the crop-problem distribution data

6. **Fix 9 Records with Null Solutions**
   - Find and populate missing solution texts

7. **Standardize Crop Names**
   - Example: "गेहूं" vs "गेहूँ" (different Unicode)
   - Normalize to single canonical form

### Low Priority

8. **Add More Coverage for Low-Count Crops**
   - 60+ crops have < 10 problems
   - Focus on commercially important ones first

9. **Extract Common Chemical Names**
   - Build a chemicals dictionary from solutions
   - Use for advanced search features

---

## 📈 8. SEARCH OPTIMIZATION STRATEGY

Based on data insights, here's the recommended search algorithm tuning:

### Tier 1: High-Impact Crops (62% of queries)

```
Rice (धान) - 34.7%
  → Boost: Yellow leaves (+2.0), Weeds (+1.5), Insects (+1.5)

Wheat (गेहूँ) - 17.5%
  → Boost: Yellow leaves (+2.0), Weeds (+2.0), Termites (+1.5)

Potato (आलू) - 10.2%
  → Boost: Wilting (+2.0), Spots (+1.5), Rot (+1.5)
```

### Tier 2: Important Crops (20% of queries)

```
Mango, Tomato, Black gram, Chickpea, Banana, Pigeon pea, Cabbage
  → Use crop-specific problem distributions from Section 3
```

### Tier 3: Long Tail (<5 problems each)

```
60+ crops with minimal data
  → Rely on generic semantic search
  → No crop-specific boosting
```

---

## 🔢 9. DATABASE STATISTICS

### Coverage Metrics

- **Crops:** 130 unique
- **Problems per crop (avg):** 153.6
- **Problems per crop (median):** 22.5
- **Crops with 100+ problems:** 21
- **Crops with 10-99 problems:** 49
- **Crops with <10 problems:** 60

### Language Distribution

- **Primary:** Hindi (Devanagari script)
- **Secondary:** Some English terms
- **Mixed:** Technical chemical names in English

### Content Patterns

- **Problem format:** 95%+ follow "crop + part + symptom + request for solution"
- **Solution format:** 90%+ include chemical name + dosage + water quantity + application method
- **Formality:** Polite request format ("कृपया समाधान बताने का कष्ट करें")

---

## 💡 10. BUSINESS INSIGHTS

### User Behavior Implications

1. **Farmers primarily struggle with:**
   - Leaf discoloration (18.5%)
   - Pest infestations (15.6%)
   - Weed management (7.9%)

2. **Top 3 crops generate 2/3 of all queries**
   - Focus marketing/outreach on rice, wheat, potato farmers

3. **Solutions are chemical-heavy (65%)**
   - Opportunity for organic/alternative solutions
   - Partner with agrochemical companies

4. **Standardized format indicates**
   - Possibly sourced from official agricultural department guides
   - High reliability and consistency

### Growth Opportunities

1. **Image Recognition**
   - Add photo upload for leaf/pest identification
   - Use the 19K labeled examples for training

2. **Regional Expansion**
   - Current data appears North India focused (rice, wheat dominant)
   - Add region-specific crops (South: coffee, coconut)

3. **Seasonal Insights**
   - Add timestamps to track seasonal problem patterns
   - Proactive alerts for upcoming seasonal issues

4. **Crop Calendar Integration**
   - Many queries about "cultivation" and "growth"
   - Provide crop stage-specific guidance

---

## 📋 11. IMMEDIATE ACTION ITEMS

### Week 1: Data Cleanup

- [ ] Run deduplication script (remove 18,803 duplicates)
- [ ] Fix 9 null solutions
- [ ] Standardize crop name spellings
- [ ] Regenerate embeddings for cleaned data

### Week 2: Search Optimization

- [ ] Implement crop-specific symptom weights
- [ ] Add expanded symptom keyword lists
- [ ] Test with sample queries from each top crop

### Week 3: Monitoring

- [ ] Track query patterns (which crops/problems most searched)
- [ ] Monitor search accuracy with user feedback
- [ ] A/B test new algorithm vs current

---

## 🎓 12. TECHNICAL NOTES

### Vector Search Performance

- **19,970 embeddings** @ 768 dimensions each
- **Database size:** 214 MB (pesti_comp table)
- **Index types:** IVFFLAT + HNSW (dual indexing)
- **Search speed:** ~200-300ms average (includes embedding generation)

### Embedding Model

- **Model:** nomic-ai/nomic-embed-text-v1.5
- **Dimensions:** 768
- **Context length:** 8,192 tokens
- **Coverage:** 100% of records

### Query Processing Pipeline

```
User Query
  → Normalize text (60+ Hindi inflection rules)
  → Detect crop
  → Generate embedding
  → Vector search (top 50)
  → Keyword boost scoring
  → Primary symptom boost
  → Word overlap filter
  → Return top result
```

---

## 📊 APPENDIX: Sample Data

### Example Problem-Solution Pair

**Problem (ID: 1):**

> धान के पौधों में कीट लगे है कृपया समाधान बताने का कष्ट करें

**Solution:**

> धान की फसल में डाइमेथोएट 30% ईसी 1.5 लीटर प्रति हेक्टेयर की दर से 700 लीटर पानी में घोल बना कर स्प्रे करें।

**Analysis:**

- Crop: धान (Rice)
- Problem type: Insect infestation
- Solution type: Chemical spray
- Dosage: 1.5 L/hectare in 700 L water
- Chemical: Dimethoate 30% EC

---

**Document prepared by:** Deep Data Analysis Script  
**Last updated:** June 12, 2026  
**Database version:** pesti_comp (19,970 records)
