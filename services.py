from typing import List, Tuple, Optional
from embedding_service import embedding_generator
import logging
import re
import time

logger = logging.getLogger(__name__)


class CropResult:
    """Lightweight result object — mirrors the old SQLAlchemy CropQuestions for compatibility."""
    def __init__(self, id, problem, solution, cropname):
        self.id = id
        self.problem = problem
        self.solution = solution
        self.cropname = cropname
        self.similarity_score = None
        self.search_method = None
        self.detected_crop = None


# ── Crop name mappings ────────────────────────────────────────────────────────
CROP_ALIASES: dict[str, str] = {
    # ── Hindi crop names (from database) ─────────────────────────────────────
    "अंगूर": "अंगूर", "अंगूरों": "अंगूर",
    "अंजीर": "अंजीर",
    "अदरक": "अदरक",
    "अनाज भण्डारण": "अनाज भण्डारण", "अनाज": "अनाज भण्डारण",
    "अनार": "अनार", "अनारों": "अनार",
    "अफीम": "अफीम",
    "अमरख": "अमरख",
    "अमरुद": "अमरुद", "अमरूद": "अमरुद",
    "अरवी": "अरवी",
    "अरहर": "अरहर",
    "अरिस्टोनिया": "अरिस्टोनिया",
    "अरुई": "अरुई",
    "अर्जुन": "अर्जुन",
    "अशोक": "अशोक",
    "आँवला": "आँवला", "आंवला": "आँवला", "आँवले": "आँवला",
    "आड़ू": "आड़ू", "आडू": "आड़ू",
    "आम": "आम", "आमों": "आम",
    "आलू": "आलू", "आलुओं": "आलू",
    "इमली": "इमली",
    "इलाइची": "इलाइची", "इलायची": "इलाइची",
    "उर्द": "उर्द",
    "एन्थूरिया": "एन्थूरिया",
    "एरिका पाम": "एरिका पाम",
    "एरोकेरिया": "एरोकेरिया",
    "ओरत": "ओरत",
    "औषधि": "औषधि",
    "कंटोला": "कंटोला",
    "ककड़ी": "ककड़ी", "ककड़ियाँ": "ककड़ी",
    "कचरिया": "कचरिया",
    "कटहल": "कटहल",
    "कठर": "कठर",
    "कढीपत्ता": "कढीपत्ता", "कड़ीपत्ता": "कढीपत्ता", "करीपत्ता": "कढीपत्ता",
    "कथर": "कथर",
    "कदम": "कदम",
    "कद्दू": "कद्दू",
    "कपास": "कपास",
    "कपूरी": "कपूरी",
    "करेला": "करेला", "करेले": "करेला",
    "करोंदा": "करोंदा",
    "कर्वी": "कर्वी",
    "कल्पित": "कल्पित",
    "कामिनी": "कामिनी",
    "काली फ्लावर": "काली फ्लावर",
    "काली मिर्च": "काली मिर्च",
    "किन्नू": "किन्नू",
    "कीटनाशक": "कीटनाशक",
    "कुंदरु": "कुंदरु",
    "कुट्टी": "कुट्टी",
    "कुर्था": "कुर्था",
    "केला": "केला", "केले": "केला", "केलों": "केला",
    "केवांच": "केवांच",
    "केसर": "केसर",
    "कैथा": "कैथा",
    "कोई भी फसल": "कोई भी फसल",
    "कोदो": "कोदो",
    "कोपी": "कोपी",
    "ख़रबूज़ा": "ख़रबूज़ा", "खरबूजा": "ख़रबूज़ा", "खरबूजे": "ख़रबूज़ा",
    "खीरा": "खीरा", "खीरे": "खीरा", "खीरों": "खीरा",
    "खुत्ती": "खुत्ती",
    "खेत": "खेत",
    "खेत में दीमक": "खेत में दीमक",
    "गंजी": "गंजी",
    "गंधाराब्राज": "गंधाराब्राज",
    "गलगल": "गलगल",
    "गवरजीत": "गवरजीत",
    "गाजर": "गाजर", "गाजरें": "गाजर",
    "गाजर घास": "गाजर घास",
    "गुड़हल": "गुड़हल",
    "गुलदाउदी": "गुलदाउदी",
    "गुलाब": "गुलाब",
    "गूलर": "गूलर",
    "गेंदा": "गेंदा",
    "गेहूँ": "गेहूँ", "गेहूं": "गेहूँ", "गेहु": "गेहूँ",
    "गोभी": "गोभी",
    "गौड़": "गौड़",
    "ग्लेडियोलस": "ग्लेडियोलस",
    "ग्वार": "ग्वार",
    "घास": "घास",
    "घुइयाँ": "घुइयाँ",
    "चकोतरा": "चकोतरा",
    "चकोरी": "चकोरी",
    "चना": "चना", "चने": "चना",
    "चन्दन": "चन्दन",
    "चांदनी": "चांदनी",
    "चारा": "चारा",
    "चावल": "चावल",
    "चिकरी": "चिकरी",
    "चितवन": "चितवन",
    "चित्रा खीरा": "चित्रा खीरा",
    "चिरौंजी": "चिरौंजी",
    "चीकू": "चीकू",
    "चुकंदर": "चुकंदर",
    "चेरी": "चेरी",
    "छुईमुई": "छुईमुई",
    "जई": "जई",
    "जरई": "जरई",
    "जरबेरा": "जरबेरा",
    "जामुन": "जामुन",
    "जायद": "जायद",
    "जिमीकंद": "जिमीकंद",
    "जुनारी": "जुनारी",
    "जुन्डी": "जुन्डी",
    "जैकफ्रूट": "जैकफ्रूट",
    "जैविक फर्टिलाइज़र": "जैविक फर्टिलाइज़र",
    "जैस्मिन": "जैस्मिन",
    "जौ": "जौ",
    "ज्वार": "ज्वार",
    "टमाटर": "टमाटर", "टमाटरों": "टमाटर",
    "टमाटर मिर्च गोभी": "टमाटर मिर्च गोभी",
    "टिंडा": "टिंडा",
    "डच गुलाब": "डच गुलाब",
    "डोडा": "डोडा",
    "ड्रैगन फ्रूट": "ड्रैगन फ्रूट",
    "ढैंचा": "ढैंचा",
    "तरबूज़": "तरबूज़", "तरबूज": "तरबूज़",
    "तरोई": "तरोई",
    "तिल": "तिल",
    "तुलसी": "तुलसी",
    "तेज़पत्ता": "तेज़पत्ता",
    "तेवरा": "तेवरा",
    "तोरिया": "तोरिया",
    "दशहरी": "दशहरी",
    "दूब घास": "दूब घास",
    "धनिया": "धनिया",
    "धान": "धान",
    "धोरी": "धोरी",
    "नारंगी": "नारंगी",
    "नारियल": "नारियल", "नारियलों": "नारियल",
    "नाशपाती": "नाशपाती",
    "निमेटोड": "निमेटोड",
    "निरहुआ": "निरहुआ",
    "निसोडा": "निसोडा",
    "नीबू": "नीबू", "नींबू": "नीबू", "नींबुओं": "नीबू",
    "नीम": "नीम",
    "नेनुआ": "नेनुआ",
    "नेपियर घास": "नेपियर घास",
    "पंडोरा": "पंडोरा",
    "पकरिया": "पकरिया",
    "पछेती": "पछेती",
    "पत्ता": "पत्ता",
    "पत्तागोभी": "पत्तागोभी",
    "पपीता": "पपीता", "पपीते": "पपीता",
    "परवल": "परवल",
    "पानी": "पानी",
    "पापीता": "पपीता",
    "पाम": "पाम",
    "पारिजात": "पारिजात",
    "पालक": "पालक",
    "पावल": "पावल",
    "पिलखन": "पिलखन",
    "पीच": "पीच",
    "पीपल": "पीपल",
    "पेठा": "पेठा",
    "पेठा कददू": "पेठा कददू",
    "पेड़ी": "पेड़ी",
    "पोई": "पोई",
    "प्याज़": "प्याज़", "प्याज": "प्याज़", "प्याजों": "प्याज़",
    "फल": "फल",
    "फसल": "फसल",
    "फालसा": "फालसा",
    "फासबीन": "फासबीन",
    "फूल": "फूल",
    "फूलगोभी": "फूलगोभी",
    "फैकस": "फैकस",
    "फ्रेंचबीन": "फ्रेंचबीन",
    "बंडा": "बंडा",
    "बंदगोभी": "बंदगोभी",
    "बकला": "बकला",
    "बड़ी चमेली": "बड़ी चमेली",
    "बडोन": "बडोन",
    "बथुआ": "बथुआ",
    "बन": "बन",
    "बनकला": "बनकला",
    "बबूल": "बबूल",
    "बाजरा": "बाजरा",
    "बेढन": "बेढन",
    "बेर": "बेर",
    "बैंगन": "बैंगन", "बैंगनों": "बैंगन",
    # ── Additional common variants ────────────────────────────────────────────
    "मक्का": "मक्का", "मक्के": "मक्का",
    "सरसों": "सरसों",
    "मिर्च": "मिर्च", "मिर्चें": "मिर्च", "मिर्चों": "मिर्च",
    "लहसुन": "लहसुन",
    "मूंगफली": "मूंगफली",
    "सोयाबीन": "सोयाबीन",
    "सूरजमुखी": "सूरजमुखी",
    "अरहर": "अरहर",
    "मूंग": "मूंग",
    "मसूर": "मसूर",
    "राजमा": "राजमा",
    "लोबिया": "लोबिया",
    # ── English → Hindi ───────────────────────────────────────────────────────
    "mango": "आम",
    "wheat": "गेहूँ",
    "tomato": "टमाटर", "tomatoes": "टमाटर",
    "brinjal": "बैंगन", "eggplant": "बैंगन",
    "potato": "आलू", "potatoes": "आलू",
    "guava": "अमरुद",
    "pigeon pea": "अरहर", "arhar": "अरहर", "tur": "अरहर",
    "rice": "धान", "paddy": "धान",
    "cucumber": "खीरा",
    "pomegranate": "अनार",
    "pearl millet": "बाजरा", "bajra": "बाजरा",
    "lemon": "नीबू", "lime": "नीबू",
    "bitter gourd": "करेला",
    "cauliflower": "फूलगोभी",
    "cabbage": "पत्तागोभी",
    "papaya": "पपीता",
    "pumpkin": "कद्दू",
    "onion": "प्याज़", "onions": "प्याज़",
    "banana": "केला", "bananas": "केला",
    "chickpea": "चना", "gram": "चना",
    "black gram": "उर्द", "urad": "उर्द",
    "rose": "गुलाब",
    "watermelon": "तरबूज़",
    "jackfruit": "कटहल",
    "sesame": "तिल",
    "coriander": "धनिया",
    "cotton": "कपास",
    "sorghum": "ज्वार",
    "barley": "जौ",
    "grapes": "अंगूर", "grape": "अंगूर",
    "coconut": "नारियल",
    "ginger": "अदरक",
    "maize": "मक्का", "corn": "मक्का",
    "mustard": "सरसों",
    "spinach": "पालक",
    "carrot": "गाजर",
    "chilli": "मिर्च", "chili": "मिर्च", "pepper": "मिर्च",
    "garlic": "लहसुन",
    "groundnut": "मूंगफली", "peanut": "मूंगफली",
    "soybean": "सोयाबीन", "soya": "सोयाबीन",
    "sunflower": "सूरजमुखी",
    "fig": "अंजीर",
    "peach": "आड़ू",
    "pear": "नाशपाती",
    "orange": "नारंगी",
    "cherry": "चेरी",
    "dragon fruit": "ड्रैगन फ्रूट",
    "beetroot": "चुकंदर",
    "tulsi": "तुलसी", "basil": "तुलसी",
    "neem": "नीम",
    "jasmine": "जैस्मिन",
    "marigold": "गेंदा",
    "rose": "गुलाब",
    "gladiolus": "ग्लेडियोलस",
    "saffron": "केसर",
    "cardamom": "इलाइची",
    "black pepper": "काली मिर्च",
    "tamarind": "इमली",
    "lentil": "मसूर",
    "kidney bean": "राजमा",
    "cowpea": "लोबिया",
    "moong": "मूंग", "green gram": "मूंग",
}

# ── Agricultural symptom keyword groups ──────────────────────────────────────
# Each category has Hindi + English keywords.
# When a keyword appears in BOTH query and candidate problem → boost score.
SYMPTOM_KEYWORDS: dict[str, list[str]] = {
    "fruit_drop":    ["गिर", "झड़", "टूट", "drop", "fall", "falling"],
    "insect":        ["कीड़", "कीट", "माहू", "सुंडी", "बेधक", "insect", "pest", "bug", "worm"],
    "hole":          ["छेद", "hole", "borer"],
    "crack":         ["फट", "दरार", "crack", "split"],
    "black_spot":    ["काल", "धब्ब", "black", "spot", "dark"],
    "yellow":        ["पील", "yellow", "yellowing"],
    "dry":           ["सूख", "dry", "wilt", "wilting"],
    "rot":           ["सड़", "गल", "rot", "decay"],
    "flower_drop":   ["फूल", "flower", "bloom"],
    "no_fruit":      ["फल नहीं", "फल नही", "no fruit", "not fruiting"],
    "leaf_curl":     ["सिकुड़", "मुड़", "curl", "curling"],
    "white_fly":     ["सफ़ेद", "सफेद", "white", "whitefly"],
    "fungus":        ["फफूंद", "fungus", "fungal", "mold"],
    "termite":       ["दीमक", "termite"],
    "growth":        ["बढ़", "growth", "grow", "नहीं बढ़"],
    "seed":          ["बीज", "seed", "sowing", "बुवाई", "बोन"],
    "irrigation":    ["सिंचाई", "पानी", "irrigation", "water"],
    "fertilizer":    ["खाद", "उर्वरक", "fertilizer", "nutrient"],
    "sour":          ["खट्टा", "खट्टे", "खट्टापन", "sour", "acidic"],
    "sweet":         ["मीठा", "मीठे", "मिठास", "sweet", "sweetness"],
    "taste":         ["स्वाद", "taste", "flavor", "पकने"],
}

BOOST_PER_MATCH = 0.30   # score added per matching symptom category
MAX_BOOST      = 0.90    # cap total boost

# ── Minimum score to return a result ─────────────────────────────────────────
# Final score (embedding + boost) must meet this to be shown to the user.
# Below this → treated as "no relevant answer found".
MIN_RETURN_SCORE = 0.55

# ── Support contact message (shown when no answer is found) ──────────────────
NO_ANSWER_MESSAGE = (
    "क्षमा करें, इस समस्या का समाधान हमारे डेटाबेस में उपलब्ध नहीं है।\n"
    "अधिक सहायता के लिए कृपया हमारे कृषि विशेषज्ञ से संपर्क करें:\n"
    "📞 किसान हेल्पलाइन: 1800-180-1551 (टोल फ्री)\n"
    "🌐 या नज़दीकी कृषि विभाग कार्यालय से मिलें।"
)

# ── General / how-to query indicators ────────────────────────────────────────
# If query contains these words but NO symptom keyword → it's a general question,
# not a problem query. Return the support message instead of a wrong result.
GENERAL_QUERY_INDICATORS = [
    # Hindi general question words
    "कैसे", "कैसा", "कैसी", "कब", "कहाँ", "कहां", "कितना", "कितनी",
    "कितने", "क्यों", "क्या होता", "बताएं", "बताओ", "जानकारी",
    "उगाये", "उगाएं", "उगाना", "उगाए", "लगाएं", "लगाना", "लगाये",
    "करें", "करना", "करो", "विधि", "तरीका", "तरीके", "प्रक्रिया",
    "फायदे", "नुकसान", "लाभ", "उपयोग", "खेती", "बुवाई कब",
    # English general question words
    "how to", "how do", "when to", "where to", "what is", "tell me",
    "explain", "guide", "tips", "method", "process", "grow", "plant",
    "cultivation", "farming", "harvest", "benefits",
]


def detect_crop(query: str) -> Optional[str]:
    """Detect crop name from query using exact, prefix, and substring matching."""
    query_stripped = query.strip()
    query_lower    = query_stripped.lower()

    # 1. Full query exact match
    if query_lower in CROP_ALIASES:
        return CROP_ALIASES[query_lower]
    if query_stripped in CROP_ALIASES:
        return CROP_ALIASES[query_stripped]

    tokens = [t for t in re.split(r'[\s,।?!]+', query_stripped) if t]

    # 2. Exact token match
    for token in tokens:
        if token.lower() in CROP_ALIASES:
            logger.info(f"Crop detected (exact): '{token}' → '{CROP_ALIASES[token.lower()]}'")
            return CROP_ALIASES[token.lower()]
        if token in CROP_ALIASES:
            logger.info(f"Crop detected (exact): '{token}' → '{CROP_ALIASES[token]}'")
            return CROP_ALIASES[token]

    # 3. Prefix match (token length >= 3)
    for token in tokens:
        if len(token) < 3:
            continue
        token_lower = token.lower()
        for alias, canonical in CROP_ALIASES.items():
            if alias.startswith(token_lower) or alias.startswith(token):
                logger.info(f"Crop detected (prefix): '{token}' → '{canonical}'")
                return canonical

    # 4. Substring match
    for token in tokens:
        if len(token) < 3:
            continue
        for alias, canonical in CROP_ALIASES.items():
            if len(alias) >= 3 and (alias in token or alias.lower() in token.lower()):
                logger.info(f"Crop detected (substring): '{token}' contains '{alias}' → '{canonical}'")
                return canonical

    logger.info(f"No crop detected in query: '{query}'")
    return None


def classify_query(query: str) -> str:
    """
    Classify query intent before searching.

    Returns:
        "problem"  — query describes a crop problem (proceed to search)
        "general"  — general how-to / informational question (skip search)

    Logic:
        - If query contains ANY symptom keyword → always treat as "problem"
          (symptom keywords are strong indicators regardless of other words)
        - Else if query contains a general indicator word → "general"
        - Otherwise → "problem" (give benefit of doubt, let threshold filter it)
    """
    query_lower = query.lower()

    # Check for symptom keywords first — these override everything
    for keywords in SYMPTOM_KEYWORDS.values():
        if any(kw in query_lower for kw in keywords):
            logger.info(f"Query classified as 'problem' (symptom keyword match)")
            return "problem"

    # Check for general question indicators
    for indicator in GENERAL_QUERY_INDICATORS:
        if indicator in query_lower:
            logger.info(f"Query classified as 'general' (indicator: '{indicator}')")
            return "general"

    return "problem"


def keyword_boost(query: str, problem: str) -> float:
    """
    Calculate symptom keyword boost score.

    For each symptom category, if ANY keyword from that category appears
    in BOTH the query AND the candidate problem → add BOOST_PER_MATCH.

    Args:
        query:   User search query
        problem: Candidate problem text from DB

    Returns:
        Boost value between 0.0 and MAX_BOOST
    """
    query_lower   = query.lower()
    problem_lower = problem.lower()
    boost         = 0.0
    matched_categories = []

    for category, keywords in SYMPTOM_KEYWORDS.items():
        query_hit   = any(kw in query_lower   for kw in keywords)
        problem_hit = any(kw in problem_lower for kw in keywords)
        if query_hit and problem_hit:
            boost += BOOST_PER_MATCH
            matched_categories.append(category)
            logger.debug(f"Keyword boost +{BOOST_PER_MATCH} for category '{category}'")

    if matched_categories:
        logger.info(f"Keyword matches: {', '.join(matched_categories)} → boost = {boost}")
    
    return min(boost, MAX_BOOST)


def hybrid_score(embedding_score: float, query: str, problem: str) -> float:
    """
    Final hybrid score = embedding + keyword boost (additive).
    
    Keyword matches are heavily weighted to ensure exact symptom matches
    rank higher than pure semantic similarity.

    Args:
        embedding_score: Raw cosine similarity (0–1)
        query:           User query
        problem:         Candidate problem text

    Returns:
        Final score (can exceed 1.0 to prioritize keyword matches)
    """
    boost = keyword_boost(query, problem)
    # Additive combination - keyword matches can significantly boost score
    # Don't cap at 1.0 to allow keyword matches to dominate
    score = embedding_score + boost
    return round(score, 6)


def search_crop_solution_semantic(
    db,
    user_question: str,
    limit: int = 10,
    threshold: float = 0.8,  # Lowered from 0.2 to include more candidates
    crop_filter: Optional[str] = None,
) -> List[Tuple[CropResult, float]]:
    """
    Hybrid retrieval:
      Step 1 — Vector search (top K=30) filtered by crop if detected
      Step 2 — Keyword boost re-ranking
      Step 3 — Return top `limit` by final score

    Args:
        db:           Database session
        user_question: User query
        limit:        Final result count (default 10)
        threshold:    Minimum embedding score to enter candidate pool (default 0.2)
        crop_filter:  Detected crop name (optional)

    Returns:
        List of (CropResult, final_score) sorted by final_score DESC
    """
    try:
        query_embedding = embedding_generator.generate_embedding(user_question)
        if query_embedding is None:
            logger.info("Embeddings disabled or failed, skipping semantic search")
            return []
    except Exception as e:
        logger.warning(f"Embedding generation error: {e}, skipping semantic search")
        return []

    emb_str  = str(query_embedding)
    top_k    = limit * 5   # fetch 5× candidates for re-ranking

    # ── Step 1: Vector search ─────────────────────────────────────────────────
    if crop_filter:
        sql = """
            SELECT id, problem, solution, cropname,
                   (1 - (embedding <=> %s)) AS emb_score
            FROM solutions
            WHERE embedding IS NOT NULL
              AND cropname = %s
              AND (1 - (embedding <=> %s)) >= %s
            ORDER BY emb_score DESC
            LIMIT %s
        """
        params = [emb_str, crop_filter, emb_str, threshold, top_k]
    else:
        sql = """
            SELECT id, problem, solution, cropname,
                   (1 - (embedding <=> %s)) AS emb_score
            FROM solutions
            WHERE embedding IS NOT NULL
              AND (1 - (embedding <=> %s)) >= %s
            ORDER BY emb_score DESC
            LIMIT %s
        """
        params = [emb_str, emb_str, threshold, top_k]

    from django.db import connection as django_conn
    with django_conn.cursor() as cursor:
        cursor.execute(sql, params)
        columns = [col[0] for col in cursor.description]
        rows = [type('Row', (), dict(zip(columns, row)))() for row in cursor.fetchall()]

    if not rows:
        logger.warning(f"No candidates found (crop='{crop_filter}', threshold={threshold})")
        return []

    logger.info(f"Vector search returned {len(rows)} candidates for re-ranking")

    # ── Step 2: Keyword boost re-ranking ──────────────────────────────────────
    scored: List[Tuple[CropResult, float]] = []
    for row in rows:
        crop_obj = CropResult(
            id=row.id,
            problem=row.problem,
            solution=row.solution,
            cropname=row.cropname,
        )
        final = hybrid_score(float(row.emb_score), user_question, row.problem)
        scored.append((crop_obj, final))
        
        # Log top candidates with their scores
        if len(scored) <= 8:
            logger.info(f"  Candidate ID {row.id}: emb={row.emb_score:.4f} → final={final:.4f}")

    # Sort by final score descending
    scored.sort(key=lambda x: x[1], reverse=True)

    # ── Step 3: Return top limit — apply minimum score filter ────────────────
    top = scored[:limit]

    # Filter by minimum return score — discard low-confidence results
    top = [(obj, score) for obj, score in top if score >= MIN_RETURN_SCORE]

    if not top:
        logger.warning(
            f"All candidates below MIN_RETURN_SCORE={MIN_RETURN_SCORE} — returning empty"
        )
        return []

    logger.info(
        f"After re-ranking: top score={top[0][1]:.4f}, "
        f"bottom score={top[-1][1]:.4f}, returned={len(top)}"
    )
    return top


def get_all_crops(db=None):
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, problem, solution, cropname FROM solutions ORDER BY id ASC")
        rows = cursor.fetchall()
    return [
        CropResult(id=r[0], problem=r[1], solution=r[2], cropname=r[3])
        for r in rows
    ]


def search_crop_solution(db, user_question: str) -> List[CropResult]:
    """
    Main search entry point.

    Flow:
      1. Classify query intent (problem vs general question)
      2. Detect crop name
      3. Hybrid retrieval (vector + keyword boost + MIN_RETURN_SCORE filter)
      4. ILIKE fallback if semantic returns nothing
      5. Return empty list if no match → caller shows NO_ANSWER_MESSAGE

    Returns:
        List[CropResult] — empty list means "no answer found"
    """
    start_time = time.time()

    # ── Fix 1: Query intent classification ───────────────────────────────────
    intent = classify_query(user_question)
    if intent == "general":
        logger.info(f"General query detected, skipping search: '{user_question}'")
        return []  # caller will show NO_ANSWER_MESSAGE

    detected_crop = detect_crop(user_question)
    if detected_crop:
        logger.info(f"Detected crop: '{detected_crop}'")

    # ── Semantic + keyword hybrid ─────────────────────────────────────────────
    try:
        results_raw = search_crop_solution_semantic(
            db,
            user_question,
            crop_filter=detected_crop,
            threshold=0.8,
            limit=10,
        )

        if results_raw:
            elapsed_ms = (time.time() - start_time) * 1000
            logger.info(
                f"Hybrid search: {len(results_raw)} results in {elapsed_ms:.2f}ms"
            )
            if elapsed_ms > 500:
                logger.warning(f"Search exceeded 500ms: {elapsed_ms:.2f}ms")

            output = []
            for crop_obj, score in results_raw:
                crop_obj.similarity_score = score
                crop_obj.search_method = (
                    "semantic_crop" if detected_crop and crop_obj.cropname == detected_crop
                    else "semantic"
                )
                output.append(crop_obj)
            return output

        logger.warning("Hybrid search returned no results, falling back to ILIKE")

    except Exception as e:
        logger.warning(f"Hybrid search failed: {e}, falling back to ILIKE")

    # ── ILIKE fallback ────────────────────────────────────────────────────────
    try:
        from django.db import connection as django_conn
        with django_conn.cursor() as cursor:
            if detected_crop:
                cursor.execute(
                    "SELECT id, problem, solution, cropname FROM solutions "                    "WHERE cropname = %s ORDER BY id ASC LIMIT 10",
                    [detected_crop]
                )
                fallback_method = "fallback_crop"
            else:
                cursor.execute(
                    "SELECT id, problem, solution, cropname FROM solutions "                    "WHERE problem ILIKE %s ORDER BY id ASC LIMIT 10",
                    [f"%{user_question}%"]
                )
                fallback_method = "fallback"
            rows = cursor.fetchall()

        result = [CropResult(id=r[0], problem=r[1], solution=r[2], cropname=r[3]) for r in rows]
        for r in result:
            r.similarity_score = None
            r.search_method    = fallback_method

        elapsed_ms = (time.time() - start_time) * 1000
        logger.info(f"Fallback: {len(result)} results in {elapsed_ms:.2f}ms")
        return result
    except Exception as e:
        logger.error(f"Fallback search failed: {e}", exc_info=True)
        return []
