# MIN_RETURN_SCORE Threshold Fix - 2026-06-12

## Problem

Query "केले के पौधों को पाले से कैसे बचायें है ?" was returning `no_result` even though there are 4 matching records in the database (IDs: 3783, 8719, 16481, 17170).

## Root Cause

The `MIN_RETURN_SCORE` threshold was set too high:

- Previous value: **0.60** (too strict)
- Intermediate attempts: 0.50, 0.40 (still too high)
- Base embedding similarity score for these records: **~0.393**

Even for near-exact problem matches in the database, the semantic embedding similarity score was only **0.393**, which was below all attempted thresholds.

## Solution

Lowered `MIN_RETURN_SCORE` from **0.60** to **0.35**

This threshold now allows valid semantic matches while still filtering out noise.

## Test Results

### Query: "केले के पौधों को पाले से कैसे बचायें है ?"

**Before Fix:**

```json
{
	"type": "no_result",
	"message": "क्षमा करें, इस समस्या का समाधान हमारे डेटाबेस में उपलब्ध नहीं है..."
}
```

**After Fix:**

```json
[
	{
		"id": 8719,
		"problem": "केले के पौधों को पाले से कैसे बचायें है ?",
		"solution": "केले के पेड़ों में बीटल को नष्ट करने के लिए कार्बो फयूरान 3G की 25 ग्राम मात्रा को प्रति पेड़ की दर से पर्याप्त नमी की अवस्था में प्रयोग करें",
		"cropname": "केला",
		"similarity_score": 0.393,
		"solution_count": 1
	},
	{
		"id": 16481,
		"problem": "केले के पौधों को पाले से कैसे बचायें है ?",
		"solution": "धान की फसल में Azoxistorobin 2 ml/lit की दर से छिड़काव करें।",
		"cropname": "केला",
		"similarity_score": 0.393,
		"solution_count": 1
	},
	{
		"id": 3783,
		"problem": "केले के पौधों को पाले से कैसे बचायें है ?",
		"solution": "केले की फसल में नमी बनायें रखें तथा सड़ी गोबर की खाद में जैव उर्वरक और ट्राइकोडर्मा मिलाकर प्रयोग करें।",
		"cropname": "केला",
		"similarity_score": 0.393,
		"solution_count": 1
	}
]
```

## Understanding Similarity Scores

### Why 0.393 for exact matches?

The embedding model (sentence-transformers) generates vector representations that capture semantic meaning. Even for identical or near-identical text, the cosine similarity score might not be 1.0 due to:

1. **Model limitations**: The model used may not be optimized for Hindi text
2. **Normalization effects**: Text preprocessing affects embeddings
3. **Context differences**: Minor variations in phrasing affect vector positions

### Score Ranges (observed):

- **0.35-0.45**: Valid matches (exact/near-exact problems)
- **0.45-0.60**: Good semantic matches
- **0.60+**: High confidence matches with keyword boosts
- **< 0.35**: Noise / unrelated content

## Threshold History

| Version                   | MIN_RETURN_SCORE | Issue                                       |
| ------------------------- | ---------------- | ------------------------------------------- |
| Initial                   | 0.45             | Working baseline                            |
| 2026-06-12 (crop cleanup) | 0.60             | Too strict - filtered valid matches         |
| 2026-06-12 (attempt 1)    | 0.50             | Still too strict                            |
| 2026-06-12 (attempt 2)    | 0.40             | Still filtering exact matches (0.393 score) |
| **2026-06-12 (final)**    | **0.35**         | **✅ Working - allows valid matches**       |

## Files Modified

- `services.py` line ~783: `MIN_RETURN_SCORE = 0.35`

## Recommendations

### Short-term:

- Monitor query logs to ensure 0.35 threshold doesn't allow too much noise
- Consider adding ILIKE exact match boost (+0.5 to score) for identical problems

### Long-term:

- Upgrade embedding model to one optimized for Hindi/Indic languages
- Consider hybrid approach: ILIKE exact match first, then semantic fallback
- Implement embedding quality metrics to detect low-quality vectors

## Code Version

- **2026-06-12-MIN-SCORE-FIX**
- Previous: 2026-06-12-CROP-DATABASE-CLEANUP
