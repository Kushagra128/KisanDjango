import logging
import re
import time
import unicodedata
import difflib
from functools import lru_cache
from typing import List, Tuple, Optional

from embedding_service import embedding_generator

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
        self.confidence = None  # "high", "medium", or "low"
        self.solution_count = 1  # How many times this solution appears (for frequency ranking)


# ── Crop name mappings ────────────────────────────────────────────────────────
CROP_ALIASES: dict[str, str] = {
    # -- अंगूर
    "grape": "अंगूर",
    "grapes": "अंगूर",
    "अंगूर": "अंगूर",
    "अंगूरों": "अंगूर",

    # -- अंजीर
    "fig": "अंजीर",
    "अंजीर": "अंजीर",

    # -- अदरक
    "ginger": "अदरक",
    "अदरक": "अदरक",

    # -- अनाज भण्डारण
    "अनाज": "अनाज भण्डारण",
    "अनाज भण्डारण": "अनाज भण्डारण",

    # -- अनार
    "pomegranate": "अनार",
    "अनार": "अनार",
    "अनारों": "अनार",

    # -- अफीम
    "अफीम": "अफीम",

    # -- अमरख
    "अमरख": "अमरख",

    # -- अमरुद
    "guava": "अमरुद",
    "अमरुद": "अमरुद",
    "अमरूद": "अमरुद",

    # -- अरवी
    "अरवी": "अरवी",

    # -- अरहर
    "arhar": "अरहर",
    "pigeon pea": "अरहर",
    "tur": "अरहर",
    "अरहर": "अरहर",

    # -- अरिस्टोनिया
    "अरिस्टोनिया": "अरिस्टोनिया",

    # -- अरुई
    "अरुई": "अरुई",

    # -- अर्जुन
    "अर्जुन": "अर्जुन",

    # -- अशोक
    "अशोक": "अशोक",

    # -- आँवला
    "आँवला": "आँवला",
    "आँवले": "आँवला",
    "आंवला": "आँवला",

    # -- आड़ू
    "peach": "आड़ू",
    "आड़ू": "आड़ू",
    "आडू": "आड़ू",

    # -- आम
    "mango": "आम",
    "आम": "आम",
    "आमों": "आम",

    # -- आलू
    "potato": "आलू",
    "potatoes": "आलू",
    "आलुओं": "आलू",
    "आलू": "आलू",

    # -- इमली
    "tamarind": "इमली",
    "इमली": "इमली",

    # -- इलाइची
    "cardamom": "इलाइची",
    "इलाइची": "इलाइची",
    "इलायची": "इलाइची",

    # -- उर्द
    "black gram": "उर्द",
    "urad": "उर्द",
    "उर्द": "उर्द",

    # -- एन्थूरिया
    "एन्थूरिया": "एन्थूरिया",

    # -- एरिका पाम
    "एरिका पाम": "एरिका पाम",

    # -- एरोकेरिया
    "एरोकेरिया": "एरोकेरिया",

    # -- ओरत
    "ओरत": "ओरत",

    # -- औषधि
    "औषधि": "औषधि",

    # -- कंटोला
    "कंटोला": "कंटोला",

    # -- ककड़ी
    "ककड़ियाँ": "ककड़ी",
    "ककड़ी": "ककड़ी",

    # -- कचरिया
    "कचरिया": "कचरिया",

    # -- कटहल
    "jackfruit": "कटहल",
    "कटहल": "कटहल",

    # -- कठर
    "कठर": "कठर",

    # -- कढीपत्ता
    "कड़ीपत्ता": "कढीपत्ता",
    "कढीपत्ता": "कढीपत्ता",
    "करीपत्ता": "कढीपत्ता",

    # -- कथर
    "कथर": "कथर",

    # -- कदम
    "कदम": "कदम",

    # -- कद्दू
    "pumpkin": "कद्दू",
    "कद्दू": "कद्दू",

    # -- कपास
    "cotton": "कपास",
    "कपास": "कपास",

    # -- कपूरी
    "कपूरी": "कपूरी",

    # -- करेला
    "bitter gourd": "करेला",
    "करेला": "करेला",
    "करेले": "करेला",

    # -- करोंदा
    "करोंदा": "करोंदा",

    # -- कर्वी
    "कर्वी": "कर्वी",

    # -- कल्पित
    "कल्पित": "कल्पित",

    # -- कामिनी
    "कामिनी": "कामिनी",

    # -- काली फ्लावर
    "काली फ्लावर": "काली फ्लावर",

    # -- काली मिर्च
    "black pepper": "काली मिर्च",
    "काली मिर्च": "काली मिर्च",

    # -- किन्नू
    "किन्नू": "किन्नू",

    # -- कीटनाशक
    "कीटनाशक": "कीटनाशक",

    # -- कुंदरु
    "कुंदरु": "कुंदरु",

    # -- कुट्टी
    "कुट्टी": "कुट्टी",

    # -- कुर्था
    "कुर्था": "कुर्था",

    # -- केला
    "banana": "केला",
    "bananas": "केला",
    "केला": "केला",
    "केले": "केला",
    "केलों": "केला",

    # -- केवांच
    "केवांच": "केवांच",

    # -- केसर
    "saffron": "केसर",
    "केसर": "केसर",

    # -- कैथा
    "कैथा": "कैथा",

    # -- कोई भी फसल
    "कोई भी फसल": "कोई भी फसल",

    # -- कोदो
    "कोदो": "कोदो",

    # -- कोपी
    "कोपी": "कोपी",

    # -- ख़रबूज़ा
    "खरबूजा": "ख़रबूज़ा",
    "खरबूजे": "ख़रबूज़ा",
    "ख़रबूज़ा": "ख़रबूज़ा",

    # -- खीरा
    "cucumber": "खीरा",
    "खीरा": "खीरा",
    "खीरे": "खीरा",
    "खीरों": "खीरा",

    # -- खुत्ती
    "खुत्ती": "खुत्ती",

    # -- खेत
    "खेत": "खेत",

    # -- खेत में दीमक
    "खेत में दीमक": "खेत में दीमक",

    # -- गंजी
    "गंजी": "गंजी",

    # -- गंधाराब्राज
    "गंधाराब्राज": "गंधाराब्राज",

    # -- गलगल
    "गलगल": "गलगल",

    # -- गवरजीत
    "गवरजीत": "गवरजीत",

    # -- गाजर
    "carrot": "गाजर",
    "गाजर": "गाजर",
    "गाजरें": "गाजर",

    # -- गाजर घास
    "गाजर घास": "गाजर घास",

    # -- गुड़हल
    "गुड़हल": "गुड़हल",

    # -- गुलदाउदी
    "गुलदाउदी": "गुलदाउदी",

    # -- गुलाब
    "rose": "गुलाब",
    "गुलाब": "गुलाब",

    # -- गूलर
    "गूलर": "गूलर",

    # -- गेंदा
    "marigold": "गेंदा",
    "गेंदा": "गेंदा",

    # -- गेहूँ
    "wheat": "गेहूँ",
    "गेहु": "गेहूँ",
    "गेहूँ": "गेहूँ",
    "गेहूं": "गेहूँ",

    # -- गोभी
    "गोभी": "गोभी",

    # -- गौड़
    "गौड़": "गौड़",

    # -- ग्लेडियोलस
    "gladiolus": "ग्लेडियोलस",
    "ग्लेडियोलस": "ग्लेडियोलस",

    # -- ग्वार
    "ग्वार": "ग्वार",

    # -- घास
    # "घास": "घास",

    # -- घुइयाँ
    "घुइयाँ": "घुइयाँ",

    # -- चकोतरा
    "चकोतरा": "चकोतरा",

    # -- चकोरी
    "चकोरी": "चकोरी",

    # -- चना
    "chickpea": "चना",
    "gram": "चना",
    "चना": "चना",
    "चने": "चना",

    # -- चन्दन
    "चन्दन": "चन्दन",

    # -- चांदनी
    "चांदनी": "चांदनी",

    # -- चारा
    "चारा": "चारा",

    # -- चावल
    "चावल": "चावल",

    # -- चिकरी
    "चिकरी": "चिकरी",

    # -- चितवन
    "चितवन": "चितवन",

    # -- चित्रा खीरा
    "चित्रा खीरा": "चित्रा खीरा",

    # -- चिरौंजी
    "चिरौंजी": "चिरौंजी",

    # -- चीकू
    "चीकू": "चीकू",

    # -- चुकंदर
    "beetroot": "चुकंदर",
    "चुकंदर": "चुकंदर",

    # -- चेरी
    "cherry": "चेरी",
    "चेरी": "चेरी",

    # -- छुईमुई
    "छुईमुई": "छुईमुई",

    # -- जई
    "जई": "जई",

    # -- जरई
    "जरई": "जरई",

    # -- जरबेरा
    "जरबेरा": "जरबेरा",

    # -- जामुन
    "जामुन": "जामुन",

    # -- जायद
    "जायद": "जायद",

    # -- जिमीकंद
    "जिमीकंद": "जिमीकंद",

    # -- जुनारी
    "जुनारी": "जुनारी",

    # -- जुन्डी
    "जुन्डी": "जुन्डी",

    # -- जैकफ्रूट
    "जैकफ्रूट": "जैकफ्रूट",

    # -- जैविक फर्टिलाइज़र
    "जैविक फर्टिलाइज़र": "जैविक फर्टिलाइज़र",

    # -- जैस्मिन
    "jasmine": "जैस्मिन",
    "जैस्मिन": "जैस्मिन",

    # -- जौ
    "barley": "जौ",
    "जौ": "जौ",

    # -- ज्वार
    "sorghum": "ज्वार",
    "ज्वार": "ज्वार",

    # -- टमाटर
    "tomato": "टमाटर",
    "tomatoes": "टमाटर",
    "टमाटर": "टमाटर",
    "टमाटरों": "टमाटर",

    # -- टमाटर मिर्च गोभी
    "टमाटर मिर्च गोभी": "टमाटर मिर्च गोभी",

    # -- टिंडा
    "टिंडा": "टिंडा",

    # -- डच गुलाब
    "डच गुलाब": "डच गुलाब",

    # -- डोडा
    "डोडा": "डोडा",

    # -- ड्रैगन फ्रूट
    "dragon fruit": "ड्रैगन फ्रूट",
    "ड्रैगन फ्रूट": "ड्रैगन फ्रूट",

    # -- ढैंचा
    "ढैंचा": "ढैंचा",

    # -- तरबूज़
    "watermelon": "तरबूज़",
    "तरबूज": "तरबूज़",
    "तरबूज़": "तरबूज़",

    # -- तरोई
    "तरोई": "तरोई",

    # -- तिल
    "sesame": "तिल",
    "तिल": "तिल",

    # -- तुलसी
    "basil": "तुलसी",
    "tulsi": "तुलसी",
    "तुलसी": "तुलसी",

    # -- तेज़पत्ता
    "तेज़पत्ता": "तेज़पत्ता",

    # -- तेवरा
    "तेवरा": "तेवरा",

    # -- तोरिया
    "तोरिया": "तोरिया",

    # -- दशहरी
    "दशहरी": "दशहरी",

    # -- दूब घास
    "दूब घास": "दूब घास",

    # -- धनिया
    "coriander": "धनिया",
    "धनिया": "धनिया",

    # -- धान
    "paddy": "धान",
    "rice": "धान",
    "धान": "धान",
}

# ── Common Hindi words that should NEVER be detected as crops ────────────────
# These are everyday agricultural words (tree, plant, seed, etc.) that
# coincidentally resemble prefixes/substrings of real crop names.
CROP_STOP_WORDS: set[str] = {
    # Plant structure
    "पेड़", "पेड़ों",           # tree(s)
    "पौधा", "पौधे", "पौधों",     # plant(s)
    "बीज", "बीजों",            # seed(s)
    
    # Plant parts (IMPORTANT - these were missing!)
    "पत्ता", "पत्ते", "पत्तियां", "पत्तियों", "पत्ती",  # leaf/leaves
    "पत्तों",                  # leaves
    "तना", "तने",              # stem(s)
    "जड़", "जड़ें", "जड़ों",     # root(s)
    "फूल", "फूलों",            # flower(s) - generic
    "फल", "फलों",              # fruit(s) — generic category
    "शाखा", "शाखाएं",          # branch(es)
    "डाल", "डाली",             # branch(es)
    
    # Symptom words (colors/conditions)
    "पीला", "पीली", "पीले",     # yellow
    "काला", "काली", "काले",     # black
    "सफेद", "सफेदी",           # white
    "भूरा", "भूरी", "भूरे",     # brown
    "लाल", "लाली",             # red
    "सूखा", "सूखी", "सूखे",     # dry
    "पाला", "पाले",            # frost (weather condition, not crop!)
    
    # Generic agricultural terms
    "मिट्टी",                  # soil
    "खाद",                     # fertilizer / manure
    "दवा", "दवाई",             # medicine / pesticide (generic)
    "सब्जी", "सब्जियां",       # vegetable(s) — generic
    "फलदार",                   # fruit-bearing
    "खेत", "खेतों",            # field(s)
    "खेती",                    # farming/cultivation (generic activity)
    "फसल",                     # crop (generic)
    
    # Trees that are NOT crops (ornamental/wild)
    "पीपल",                    # peepal tree (not a crop!)
    "बरगद",                    # banyan tree
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
    "dry":           ["सूख", "मुरझा", "मुरझान", "कुम्हला", "dry", "wilt", "wilting"],
    "rot":           ["सड़", "गल", "rot", "decay"],
    "flower_drop":   ["फूल", "flower", "bloom"],
    "no_fruit":      ["फल नहीं", "फल नही", "no fruit", "not fruiting"],
    "leaf_curl":     ["सिकुड़", "मुड़", "curl", "curling"],
    "white_fly":     ["सफ़ेद", "सफेद", "white", "whitefly"],
    "fungus":        ["फफूंद", "fungus", "fungal", "mold"],
    "termite":       ["दीमक", "termite"],
    "growth":        ["बढ़", "growth", "नहीं बढ़"],
    "seed":          ["बीज", "seed", "sowing", "बुवाई", "बोन"],
    "irrigation":    ["सिंचाई", "पानी", "irrigation", "water"],
    "fertilizer":    ["खाद", "उर्वरक", "fertilizer", "nutrient"],
    "sour":          ["खट्टा", "खट्टे", "खट्टापन", "sour", "acidic"],
    "sweet":         ["मीठा", "मीठे", "मिठास", "sweet", "sweetness"],
    "taste":         ["स्वाद", "taste", "flavor", "पकने"],
}

BOOST_PER_MATCH = 0.30   # score added per matching symptom category
MAX_BOOST      = 0.90    # cap total boost

# ── Step 6: Query normalization map ──────────────────────────────────────────
QUERY_NORMALIZATION: dict[str, str] = {
    # Rot/decay symptoms (normalize to root "सड़")  
    "सड़ रहे हैं": "सड़", "सड़ रही है": "सड़", "सड़ रहा है": "सड़",
    "सड़ रहे": "सड़", "सड़ रही": "सड़", "सड़ रहा": "सड़",
    "सड़न हो रही": "सड़", "सड़न हो रहा": "सड़", "सड़न हो रहे": "सड़",
    "सड़न हो": "सड़", "सड़न": "सड़", "गलन": "सड़", "गलना": "सड़",
    "सड़ना": "सड़", "सड़ी": "सड़", "सड़े": "सड़",
    "सड़ गया": "सड़", "सड़ गई": "सड़",
    
    # Color variations
    "पीली": "पीला", "पीले": "पीला", "पीलापन": "पीला",
    "सूखे": "सूखा", "सूखी": "सूखा", "सूखना": "सूखा",
    "काली": "काला", "काले": "काला", "कालापन": "काला",
    "भूरी": "भूरा", "भूरे": "भूरा",
    "सफेदी": "सफेद", "सफ़ेद": "सफेद",
    "लाली": "लाल", "लाले": "लाल",
    
    # Spot/mark variations
    "धब्बे": "धब्बा", "दाग": "धब्बा", "दागों": "धब्बा",
    "धब्बों": "धब्बा", "धब्बो": "धब्बा",
    
    # Falling/dropping
    "गिरना": "गिर", "गिरे": "गिर", "गिरी": "गिर", "गिरा": "गिर",
    "झड़ना": "झड़", "झड़े": "झड़", "झड़ी": "झड़", "झड़ा": "झड़",
    
    # Growth/development
    "बढ़ना": "बढ़", "बढ़े": "बढ़", "बढ़ी": "बढ़", "बढ़ा": "बढ़",
    "विकास": "बढ़", "वृद्धि": "बढ़",
    
    # Action verbs
    "करना": "कर", "करें": "कर", "करूं": "कर", "करो": "कर",
    "लगना": "लग", "लगे": "लग", "लगी": "लग", "लगा": "लग",
    "होना": "हो", "हुआ": "हो", "हुई": "हो", "हुए": "हो",
    "हो रही": "हो", "हो रहा": "हो", "हो रहे": "हो",
    "आना": "आ", "आये": "आ", "आई": "आ", "आए": "आ",
    "जाना": "जा", "जाये": "जा", "जाए": "जा",
    
    # Continuous tense helpers (remove completely)
    "रहे हैं": "", "रहा है": "", "रही है": "", "रहे": "", "रहा": "", "रही": "",
    "हैं": "", "है": "",
    
    # Postpositions (remove)
    "में": "", "पर": "", "से": "", "को": "", "का": "", "की": "", "के": "",
}

# ── Minimum score to return a result ─────────────────────────────────────────
# Final score (embedding + boost) must meet this to be shown to the user.
# Below this → treated as "no relevant answer found".
# Set to 0.35 to allow semantic matches (base embeddings score ~0.39 for exact matches)
MIN_RETURN_SCORE = 0.35

# ── Support contact message (shown when no answer is found) ──────────────────
NO_ANSWER_MESSAGE = (
    "क्षमा करें, इस समस्या का समाधान हमारे डेटाबेस में उपलब्ध नहीं है।\n"
    "अधिक सहायता के लिए कृपया हमारे कृषि विशेषज्ञ से संपर्क करें:\n"
    "📞 किसान हेल्पलाइन: 1800-180-1551 (टोल फ्री)\n"
    "🌐 या नज़दीकी कृषि विभाग कार्यालय से मिलें।"
)

# ── General / how-to query indicators ────────────────────────────────────────
# These words suggest a general/informational question ONLY when no problem
# context is present. They are checked LAST — problem context always wins.
GENERAL_QUERY_INDICATORS = [
    # Hindi script — clearly general farming / cultivation intent
    # "उगाना" verb family — all common forms
    "उगाये", "उगाएं", "उगाना", "उगाए", "उगाया", "उगाई",
    "उगाया जाता", "उगाई जाती", "उगाये जाते",
    "उगाने का", "उगाने की", "उगाने के",
    # "लगाना" verb family
    "लगाएं", "लगाना", "लगाये", "लगाया जाता", "लगाने का",
    # "करना" general farming phrases
    "विधि", "तरीका", "तरीके", "प्रक्रिया",
    "फायदे", "लाभ", "उपयोग",
    "खेती करें", "खेती करना", "खेती कैसे", "खेती कैसे करें",
    "खेती किस तरह", "खेती का तरीका",
    "बुवाई कैसे", "बुवाई कब",
    "कब बोएं", "कब लगाएं", "कब उगाएं",
    "कैसे करें खेती", "कैसे उगाएं", "कैसे उगायें",
    "कैसे उगाया", "कैसे उगाई", "कैसे लगाएं",
    "जाता है कैसे", "जाती है कैसे",
    "कैसे होती है", "कैसे होता है",
    # Hinglish (transliterated) — common user input style
    "kheti kaise", "kheti karna", "kheti kare",
    "kaise ugaye", "kaise ugayen", "kaise lagaye",
    "kaise ugaya", "kaise ugai", "kab boye",
    "kab lagaye", "kab ugaye",
    "tarika batao", "vidhi batao",
    "ugane ka tarika", "lagane ka tarika",
    "kaise hoti hai", "kaise hota hai",
    "kaise ki jati hai", "kaise kiya jata",
    # English — clearly general
    "how to grow", "how to plant", "how to cultivate",
    "cultivation method", "farming method", "when to sow",
    "when to harvest", "benefits of", "advantages of",
]

# ── Problem context words ─────────────────────────────────────────────────────
# If ANY of these appear in the query, it is a PROBLEM query regardless of
# any general indicator words also present.
PROBLEM_CONTEXT_WORDS = [
    # Protection / treatment intent (these appear in how-to problem queries)
    "बचायें", "बचाएं", "बचाव", "बचाना", "उपाय", "समाधान", "इलाज",
    "रोकें", "रोकना", "दवाई", "दवा", "छिड़काव", "उपचार",
    # Damage / disease words not in SYMPTOM_KEYWORDS
    "रोग", "बीमारी", "नुकसान", "खराब", "मर", "नष्ट",
    "काला", "भूरा", "लाल धब्बे", "धब्बे", "धब्बा",
    "फट", "टूट", "गिर", "झड़", "सड़", "गल",
    "पीला", "पीले", "सूख", "मुरझा",
    "कमज़ोर", "कमजोर", "कम", "छोटे", "पतले",
    "खरपतवार", "दीमक", "कीड़", "कीट",
    "पाला", "पाले", "ठंड", "लू", "तेज़ धूप",
    # Hinglish problem context
    "bachao", "bachaye", "bachana", "upay", "upchar", "ilaj",
    "rog", "bimari", "nuksan", "kharab", "mar raha", "sukh raha",
    "peela", "peele", "kala", "dhabba", "dhabba", "kide", "kida",
    "sad raha", "gal raha", "jhad raha", "gir raha",
    "dawai", "dawa", "spray kare", "chidkav",
    # English problem context
    "protect", "protection", "prevent", "treatment", "cure",
    "disease", "damage", "pest", "attack", "control",
    "black", "yellow", "rot", "wilt", "blight", "fungus",
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

    # Split into tokens, filtering out common Hindi stop-words
    tokens = [t for t in re.split(r'[\s,।?!]+', query_stripped) if t
              and t.lower() not in CROP_STOP_WORDS
              and t not in CROP_STOP_WORDS]

    # 2. Exact token match
    for token in tokens:
        if token.lower() in CROP_ALIASES:
            logger.info(f"Crop detected (exact): '{token}' → '{CROP_ALIASES[token.lower()]}'")
            return CROP_ALIASES[token.lower()]
        if token in CROP_ALIASES:
            logger.info(f"Crop detected (exact): '{token}' → '{CROP_ALIASES[token]}'")
            return CROP_ALIASES[token]

    # 3. Prefix match (token length >= 3; alias must be ≥ token + 2 chars
    #    to avoid matching short common words like "पेड़" against "पेड़ी")
    for token in tokens:
        if len(token) < 3:
            continue
        token_lower = token.lower()
        for alias, canonical in CROP_ALIASES.items():
            if len(alias) < len(token) + 2:
                continue  # skip if alias is too close in length (false positive risk)
            if alias.startswith(token_lower) or alias.startswith(token):
                logger.info(f"Crop detected (prefix): '{token}' → '{canonical}'")
                return canonical

    # 4. Substring match (alias must be ≥ 65% of token length to avoid
    #    matching short crop names embedded in longer unrelated words,
    #    e.g. "धान" inside "समाधान" which means "solution", not paddy)
    for token in tokens:
        if len(token) < 3:
            continue
        for alias, canonical in CROP_ALIASES.items():
            if len(alias) >= 3 and len(token) > 0 and (len(alias) / len(token)) >= 0.65 and (alias in token or alias.lower() in token.lower()):
                logger.info(f"Crop detected (substring): '{token}' contains '{alias}' → '{canonical}'")
                return canonical

    # 5. Fuzzy / spell correction match (for misspelled or transliterated crops)
    # Only attempt when we have a substantial token (>= 4 chars)
    # Increased cutoff from 0.72 to 0.85 for stricter matching
    all_aliases = list(CROP_ALIASES.keys())
    for token in tokens:
        if len(token) < 4:
            continue
        close_matches = difflib.get_close_matches(token, all_aliases, n=1, cutoff=0.85)
        if close_matches:
            matched = close_matches[0]
            canonical = CROP_ALIASES[matched]
            logger.info(f"Crop detected (fuzzy): '{token}' ≈ '{matched}' → '{canonical}'")
            return canonical

    logger.info(f"No crop detected in query: '{query}'")
    return None


def detect_all_crops(query: str) -> List[str]:
    """
    Detect ALL crop names from query — used to detect multi-crop queries.

    Unlike detect_crop (which returns the first match), this collects every
    distinct canonical crop name found across all tokens.
    """
    query_stripped = query.strip()
    query_lower = query_stripped.lower()
    detected: List[str] = []
    seen: set = set()

    def _add(canonical: str):
        if canonical not in seen:
            seen.add(canonical)
            detected.append(canonical)

    # 1. Full query exact match
    if query_lower in CROP_ALIASES:
        _add(CROP_ALIASES[query_lower])
        return detected
    if query_stripped in CROP_ALIASES:
        _add(CROP_ALIASES[query_stripped])
        return detected

    tokens = [t for t in re.split(r'[\s,।?!]+', query_stripped) if t
              and t.lower() not in CROP_STOP_WORDS
              and t not in CROP_STOP_WORDS]

    # 2. Exact token match
    for token in tokens:
        if token.lower() in CROP_ALIASES:
            _add(CROP_ALIASES[token.lower()])
        elif token in CROP_ALIASES:
            _add(CROP_ALIASES[token])

    # 3. Prefix match (only for tokens not yet matched;
    #    alias must be ≥ token + 2 chars to avoid false positives)
    for token in tokens:
        if len(token) < 3:
            continue
        token_lower = token.lower()
        for alias, canonical in CROP_ALIASES.items():
            if len(alias) < len(token) + 2:
                continue  # skip if alias is too close in length (false positive risk)
            if alias.startswith(token_lower) or alias.startswith(token):
                _add(canonical)

    # 4. Substring match (same ratio guard as detect_crop)
    for token in tokens:
        if len(token) < 3:
            continue
        for alias, canonical in CROP_ALIASES.items():
            if len(alias) >= 3 and len(token) > 0 and (len(alias) / len(token)) >= 0.65 and (alias in token or alias.lower() in token.lower()):
                _add(canonical)

    # 5. Fuzzy match (stricter cutoff to prevent false matches)
    all_aliases = list(CROP_ALIASES.keys())
    for token in tokens:
        if len(token) < 4:
            continue
        close_matches = difflib.get_close_matches(token, all_aliases, n=1, cutoff=0.85)
        if close_matches:
            _add(CROP_ALIASES[close_matches[0]])

    if detected:
        logger.info(f"Crops detected: {detected}")
    else:
        logger.info(f"No crop detected in query: '{query}'")
    return detected


def classify_query(query: str) -> str:
    """
    Classify query intent before searching.

    Returns:
        "problem"  — proceed to search
        "general"  — skip search, return support message

    Logic:
      Layer 1 — SYMPTOM keywords → always "problem"
      Layer 2 — PROBLEM_CONTEXT words → always "problem"
      Layer 3 — GENERAL indicators WITH no crop detected → "general"
                If a crop IS detected, always search — the DB may have
                a record for that exact question (e.g. "केले की खेती कैसे करें?")
      Default  → "problem"
    """
    query_lower = query.lower()
    # Normalize chandrabindu → anusvara so उगाएँ matches उगाएं
    query_lower = query_lower.replace('\u0901', '\u0902')

    # Layer 1: symptom keywords — strongest signal
    for keywords in SYMPTOM_KEYWORDS.values():
        if any(kw in query_lower for kw in keywords):
            logger.info("Query classified as 'problem' (symptom keyword)")
            return "problem"

    # Layer 2: problem context words — overrides general indicators
    for word in PROBLEM_CONTEXT_WORDS:
        if word in query_lower:
            logger.info(f"Query classified as 'problem' (problem context: '{word}')")
            return "problem"

    # Layer 3: general indicator — only block if NO crop is detected.
    # If a crop IS present, the DB may have cultivation records (e.g.
    # "केले की खेती कैसे करें?"). Scoring will handle re-ranking so
    # cultivation results beat disease results via symptom penalty.
    for indicator in GENERAL_QUERY_INDICATORS:
        if indicator in query_lower:
            detected = detect_crop(query)
            if not detected:
                logger.info(f"Query classified as 'general' (indicator: '{indicator}', no crop)")
                return "general"
            else:
                logger.info(
                    f"General indicator '{indicator}' found, crop '{detected}' detected "
                    f"— searching DB (re-ranking will prioritize cultivation over disease)"
                )
                return "problem"

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
    # NFC-normalize to handle Devanagari encoding variations
    query_lower   = unicodedata.normalize('NFC', query.lower())
    problem_lower = unicodedata.normalize('NFC', problem.lower())
    # Also normalize chandrabindu → anusvara (उगाएँ → उगाएं)
    query_lower   = query_lower.replace('\u0901', '\u0902')
    problem_lower = problem_lower.replace('\u0901', '\u0902')
    boost         = 0.0
    matched_categories = []

    for category, keywords in SYMPTOM_KEYWORDS.items():
        query_hit   = any(unicodedata.normalize('NFC', kw) in query_lower   for kw in keywords)
        problem_hit = any(unicodedata.normalize('NFC', kw) in problem_lower for kw in keywords)
        if query_hit and problem_hit:
            boost += BOOST_PER_MATCH
            matched_categories.append(category)
            logger.debug(f"Keyword boost +{BOOST_PER_MATCH} for category '{category}'")

    if matched_categories:
        logger.info(f"Keyword matches: {', '.join(matched_categories)} → boost = {boost}")
    
    return min(boost, MAX_BOOST)


# ── Step 6: Text normalization ────────────────────────────────────────────────

def normalize_text(text: str) -> str:
    """
    Normalize Hindi text by replacing inflected/variant forms with
    canonical forms for better matching in keyword_boost and overlap filter.

    Process longer phrases first to avoid partial replacements breaking them.

    Applies Unicode NFC normalization first to handle Devanagari characters
    that have multiple byte representations (e.g. "सड़" as U+095C vs U+0921+U+093C).
    """
    # Force NFC normalization so characters like "सड़" (Devanagari RRA)
    # have a consistent byte representation regardless of input source
    text = unicodedata.normalize('NFC', text.lower())

    # Normalize chandrabindu (ँ, U+0901) to anusvara (ं, U+0902).
    # These are semantically interchangeable in modern Hindi typing and
    # failing to unify them breaks keyword matching (उगाएँ vs उगाएं).
    text = text.replace('\u0901', '\u0902')

    # Sort by length (longest first) to handle multi-word phrases correctly
    sorted_normalizations = sorted(QUERY_NORMALIZATION.items(), key=lambda x: len(x[0]), reverse=True)

    for old, new in sorted_normalizations:
        text = text.replace(old, new)
    return text


def hybrid_score(embedding_score: float, query: str, problem: str) -> float:
    """
    Final score = embedding + keyword boost + primary symptom boost.
    
    Primary symptom boost (+1.50) fires when query and problem share 
    the exact same symptom (rot, yellow, dry, etc.) after normalization.
    This ensures exact symptom matches rank highest.

    Args:
        embedding_score: Raw cosine similarity (0–1)
        query:           User query
        problem:         Candidate problem text

    Returns:
        Final score (can exceed 1.0 to prioritize exact matches)
    """
    boost = keyword_boost(query, problem)
    
    # Step 3.5: Primary symptom boost (differentiate rot vs yellow vs dry etc)
    # Check ALL symptoms and apply the strongest boost/penalty
    # Keywords should match NORMALIZED forms (after QUERY_NORMALIZATION is applied)
    PRIMARY_SYMPTOMS = {
        "rot": ["सड़", "सड", "गल", "rot", "decay"],
        "yellow": ["पील", "पीला", "yellow", "yellowing"],
        "dry": ["सूख", "सूखा", "मुरझा", "मुरझान", "कुम्हला", "dry", "wilt", "wilting"],
        "black_spot": ["काला", "धब्ब", "black", "spot"],
        "insect": ["कीट", "insect", "pest", "bug", "worm", "माहू", "सुंडी"],
        # Expanded categories — aligned with SYMPTOM_KEYWORDS
        "fruit_drop": ["गिर", "झड़", "टूट", "drop", "fall", "falling"],
        "flower_drop": ["फूल", "flower", "bloom"],
        "no_fruit": ["फल नहीं", "फल नही", "no fruit", "not fruiting"],
        "leaf_curl": ["सिकुड़", "मुड़", "curl", "curling"],
        "white_fly": ["सफ़ेद", "सफेद", "white", "whitefly"],
        "fungus": ["फफूंद", "fungus", "fungal", "mold"],
        "termite": ["दीमक", "termite"],
        "growth": ["बढ़", "growth", "नहीं बढ़"],
        "seed": ["बीज", "seed", "sowing", "बुवाई", "बोन"],
        "irrigation": ["सिंचाई", "पानी", "irrigation", "water"],
        "fertilizer": ["खाद", "उर्वरक", "fertilizer", "nutrient"],
        "sour": ["खट्टा", "खट्टे", "खट्टापन", "sour", "acidic"],
        "sweet": ["मीठा", "मीठे", "मिठास", "sweet", "sweetness"],
        "taste": ["स्वाद", "taste", "flavor", "पकने"],
        "hole": ["छेद", "hole", "borer"],
        "crack": ["फट", "दरार", "crack", "split"],
    }
    
    # Apply normalization to both query and problem BEFORE symptom detection
    query_normalized = normalize_text(query.lower())
    problem_normalized = normalize_text(problem.lower())
    logger.info(f"Q_norm: '{query_normalized[:50]}' | P_norm: '{problem_normalized[:50]}'")
    logger.info(f"Q_norm repr: {repr(query_normalized[:30])} | P_norm repr: {repr(problem_normalized[:30])}")
    
    # Find which symptoms are present in query and problem
    query_symptoms = []
    problem_symptoms = []
    
    for symptom_type, keywords in PRIMARY_SYMPTOMS.items():
        if any(unicodedata.normalize('NFC', kw) in query_normalized for kw in keywords):
            query_symptoms.append(symptom_type)
        for kw in keywords:
            if unicodedata.normalize('NFC', kw) in problem_normalized:
                problem_symptoms.append(symptom_type)
                logger.info(f"Detected '{symptom_type}' in problem (keyword: '{kw}')")
                break
    
    logger.info(f"Q_symptoms: {query_symptoms} | P_symptoms: {problem_symptoms}")
    
    primary_symptom_boost = 0.0
    
    if query_symptoms and problem_symptoms:
        # Check for matches
        matches = set(query_symptoms) & set(problem_symptoms)
        if matches:
            # At least one symptom matches - give VERY strong boost to override keyword boosts
            primary_symptom_boost = 1.50
            logger.info(f"Primary symptom boost +{primary_symptom_boost} (matched: {matches})")
        else:
            # Query has symptoms but they don't match problem's symptoms - strong penalty
            primary_symptom_boost = -1.50
            logger.info(f"Primary symptom mismatch penalty {primary_symptom_boost} (query: {query_symptoms}, problem: {problem_symptoms})")
    elif query_symptoms and not problem_symptoms:
        # Query has specific symptom but problem has none - penalty
        primary_symptom_boost = -0.80
        logger.info(f"Primary symptom penalty {primary_symptom_boost} (query has {query_symptoms}, problem has none)")
    elif not query_symptoms and problem_symptoms:
        # Query is cultivation/general but result is about disease/problem — penalty
        primary_symptom_boost = -0.80
        logger.info(f"Primary symptom penalty {primary_symptom_boost} (disease result for cultivation query: {problem_symptoms})")

    # Extra check: even if no PRIMARY_SYMPTOM matched, penalize results that
    # contain problem-context words (बचायें, रोग, कीड़े, etc.) when the query
    # is a general/cultivation query (no symptoms of its own).
    if primary_symptom_boost == 0.0 and not query_symptoms:
        result_has_problem_context = any(
            word in problem_normalized for word in PROBLEM_CONTEXT_WORDS
        )
        if result_has_problem_context:
            primary_symptom_boost = -0.60
            logger.info(f"Problem-context penalty {primary_symptom_boost} (cultivation query vs problem result)")

    score = embedding_score + boost + primary_symptom_boost
    return round(score, 6)


def _filter_by_word_overlap(
    query: str,
    scored: List[Tuple[CropResult, float]],
    min_overlap: int = 1,
    detected_crop: Optional[str] = None,
) -> List[Tuple[CropResult, float]]:
    """
    Remove results whose problem text shares no meaningful TOPIC words
    with the query — after excluding crop name and stopwords.

    The crop name is always shared (we searched by crop filter), so it
    contributes no topical signal and must be excluded from the overlap check.

    Example:
      query  = "केले के पौधे को कैसे उगाये"
      tokens after removing केला + stopwords = {"पौधे", "उगाये"}
      result = "केले के पौधों को पाले से कैसे बचायें है ?"
      overlap = 0 ("पौधे" is NOT in result, "उगाये" is NOT in result)
      → dropped ✅
    """
    STOPWORDS = {
        "के", "की", "का", "में", "से", "को", "पर", "है", "हैं", "हो",
        "रहे", "रहा", "रही", "गए", "गया", "गई", "लग", "हुए", "हुआ",
        "कैसे", "कैसा", "क्यों", "कब", "कहाँ", "कितना", "और", "या",
        "यह", "वह", "इस", "उस", "जो", "तो", "भी", "ही", "एक", "सभी",
        "कृपया", "बताने", "बताएं", "बताओ", "करें", "करना", "करो",
        "the", "is", "are", "in", "of", "to", "a", "an", "and", "or",
        "for", "on", "at", "by", "how", "why", "when", "what", "where",
    }
    HIGH_CONFIDENCE = 1.0

    query_lower = query.lower()
    # Normalize chandrabindu → anusvara for consistent matching
    query_lower = query_lower.replace('\u0901', '\u0902')

    # General/cultivation queries ("how to grow", "कैसे उगाए") use different
    # vocabulary than disease queries. The word overlap filter can't match
    # "उगाए" to "खेती" — rely on embedding similarity + symptom penalty instead.
    if any(indicator in query_lower for indicator in GENERAL_QUERY_INDICATORS):
        logger.info("General query — skipping word-overlap filter")
        return scored

    # Collect crop name tokens to exclude from overlap (they're always shared)
    crop_tokens: set = set()
    if detected_crop:
        # Add canonical crop name tokens
        crop_tokens.update(
            t for t in re.split(r'[\s,।?!\-]+', detected_crop.lower()) if t
        )
        # Add ALL alias keys that map to this crop (e.g. "केला" -> "केले", "केलों", "banana")
        for alias, canonical in CROP_ALIASES.items():
            if canonical == detected_crop:
                crop_tokens.update(
                    t for t in re.split(r'[\s,।?!\-]+', alias.lower()) if t
                )

    query_tokens = {
        t for t in re.split(r'[\s,।?!\-]+', query_lower)
        if len(t) >= 3 and t not in STOPWORDS and t not in crop_tokens
    }

    if not query_tokens:
        # After removing crop name + stopwords, nothing left to check
        # Cannot determine topic → skip filter, return all
        logger.info("No content tokens after removing crop/stopwords — skipping overlap filter")
        return scored

    logger.info(f"Overlap filter content tokens: {query_tokens}")

    filtered = []
    for crop_obj, score in scored:
        problem_lower = crop_obj.problem.lower()

        # Always keep high-confidence results (keyword boost > 1.0)
        if score >= HIGH_CONFIDENCE:
            filtered.append((crop_obj, score))
            continue

        overlap = sum(1 for token in query_tokens if token in problem_lower)

        if overlap >= min_overlap:
            filtered.append((crop_obj, score))
        else:
            logger.info(
                f"  Dropped id={crop_obj.id} "
                f"(overlap={overlap}/{len(query_tokens)}): "
                f"'{crop_obj.problem[:60]}'"
            )

    return filtered


# ── In-memory embedding cache ─────────────────────────────────────────────────
# Cache frequently-asked queries to avoid recomputing embeddings (100-200ms each).
# Uses an LRU cache bounded at 256 entries — about ~200KB of memory.

@lru_cache(maxsize=256)
def _cached_embed(query: str) -> Optional[Tuple[float, ...]]:
    """Cached wrapper around embedding_generator.generate_embedding."""
    emb = embedding_generator.generate_embedding(query)
    return tuple(emb) if emb else None


def _get_query_embedding(query: str) -> Optional[List[float]]:
    """Get embedding with cache. Returns list for pgvector compatibility."""
    cached = _cached_embed(query)
    return list(cached) if cached else None


# ── Confidence scoring ─────────────────────────────────────────────────────────

def _compute_confidence(score: float) -> str:
    """Map final_score to a human-readable confidence level."""
    if score >= 2.0:
        return "high"
    elif score >= 1.0:
        return "medium"
    return "low"


# ── Query suggestions for no-result cases ─────────────────────────────────────

def get_crop_suggestions(query: str, max_suggestions: int = 4) -> List[str]:
    """
    When no crop is detected, search without crop filter and return
    the top matching crop names as suggestions to help the user rephrase.
    """
    from django.db import connection as django_conn

    try:
        query_embedding = _get_query_embedding(query)
        if query_embedding is None:
            return []

        emb_str = str(query_embedding)
        with django_conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT DISTINCT cropname,
                       (1 - (embedding <=> %s)) AS emb_score
                FROM pesti_comp
                WHERE embedding IS NOT NULL
                ORDER BY emb_score DESC
                LIMIT %s
                """,
                [emb_str, max_suggestions * 2],
            )
            rows = cursor.fetchall()

        seen = set()
        suggestions = []
        for cropname, _score in rows:
            if cropname not in seen:
                seen.add(cropname)
                suggestions.append(cropname)
            if len(suggestions) >= max_suggestions:
                break

        logger.info(f"Crop suggestions for '{query[:40]}': {suggestions}")
        return suggestions

    except Exception as exc:
        logger.warning(f"Failed to generate crop suggestions: {exc}")
        return []


def search_crop_solution_semantic(
    db,
    user_question: str,
    limit: int = 10,
    threshold: float = 0.15,  # pgvector candidate pool — cast wide net
    crop_filter: Optional[str] = None,
) -> List[Tuple[CropResult, float]]:
    """
    Hybrid retrieval:
      Step 1 — Vector search (top K=30) filtered by crop if detected
      Step 2 — Keyword boost re-ranking
      Step 3 — Group by solution and count occurrences
      Step 4 — Return top `limit` by frequency (most repeated solutions first)

    Args:
        db:           Database session
        user_question: User query
        limit:        Final result count (default 10)
        threshold:    Minimum embedding score to enter candidate pool (default 0.2)
        crop_filter:  Detected crop name (optional)

    Returns:
        List of (CropResult, final_score) sorted by frequency DESC
    """
    try:
        query_embedding = _get_query_embedding(user_question)
        if query_embedding is None:
            logger.info("Embeddings disabled or failed, skipping semantic search")
            return []
    except Exception as e:
        logger.warning(f"Embedding generation error: {e}, skipping semantic search")
        return []

    emb_str  = str(query_embedding)
    # CHANGED: Remove limit - fetch ALL matching records above threshold

    # ── Step 1: Vector search (ALL matching records) ──────────────────────────
    if crop_filter:
        sql = """
            SELECT id, problem, solution, cropname,
                   (1 - (embedding <=> %s)) AS emb_score
            FROM pesti_comp
            WHERE embedding IS NOT NULL
              AND cropname = %s
              AND (1 - (embedding <=> %s)) >= %s
            ORDER BY emb_score DESC
        """
        params = [emb_str, crop_filter, emb_str, threshold]
    else:
        sql = """
            SELECT id, problem, solution, cropname,
                   (1 - (embedding <=> %s)) AS emb_score
            FROM pesti_comp
            WHERE embedding IS NOT NULL
              AND (1 - (embedding <=> %s)) >= %s
            ORDER BY emb_score DESC
        """
        params = [emb_str, emb_str, threshold]

    from django.db import connection as django_conn
    with django_conn.cursor() as cursor:
        cursor.execute(sql, params)
        columns = [col[0] for col in cursor.description]
        rows = [type('Row', (), dict(zip(columns, row)))() for row in cursor.fetchall()]

    if not rows:
        logger.warning(f"No candidates found (crop='{crop_filter}', threshold={threshold})")
        return []

    logger.info(f"Vector search returned {len(rows)} candidates (ALL records above threshold)")
    logger.info("!!! CODE VERSION: 2026-06-12-ALL-RECORDS-FREQUENCY-COUNT !!!")

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
        crop_obj.confidence = _compute_confidence(final)
        scored.append((crop_obj, final))
        
        # Log top candidates with their scores
        if len(scored) <= 8:
            logger.info(f"  Candidate ID {row.id}: emb={row.emb_score:.4f} → final={final:.4f}")

    # Sort by final score descending
    scored.sort(key=lambda x: x[1], reverse=True)

    # ── Step 3: Apply minimum score filter ────────────────────────────────────
    # Filter by minimum return score — discard low-confidence results
    scored = [(obj, score) for obj, score in scored if score >= MIN_RETURN_SCORE]

    if not scored:
        logger.warning(
            f"All candidates below MIN_RETURN_SCORE={MIN_RETURN_SCORE} — returning empty"
        )
        return []

    # ── Step 4: Word-overlap relevance check ──────────────────────────────────
    scored = _filter_by_word_overlap(user_question, scored, detected_crop=crop_filter)

    if not scored:
        return []

    # ── Step 5: Group by solution and count frequency ─────────────────────────
    from collections import defaultdict
    
    solution_groups = defaultdict(list)  # solution_text -> [(CropResult, score), ...]
    
    for crop_obj, score in scored:
        # Normalize solution text for grouping (strip whitespace, lowercase)
        solution_key = crop_obj.solution.strip().lower()
        solution_groups[solution_key].append((crop_obj, score))
    
    # Create ranked list: (best_crop_obj, best_score, count)
    ranked_solutions = []
    for solution_text, instances in solution_groups.items():
        # Sort instances by score descending
        instances.sort(key=lambda x: x[1], reverse=True)
        
        # Take the best instance (highest score) as representative
        best_crop_obj, best_score = instances[0]
        count = len(instances)
        
        # Store count in the CropResult object for reference
        best_crop_obj.solution_count = count
        
        ranked_solutions.append((best_crop_obj, best_score, count))
        
        logger.info(
            f"Solution group: '{solution_text[:50]}...' appears {count} times "
            f"(out of {len(scored)} total filtered results), best_score={best_score:.4f}"
        )
    
    # Sort by score (descending) FIRST, then by count (descending) as tiebreaker
    # This prioritizes similarity score over frequency
    ranked_solutions.sort(key=lambda x: (x[1], x[2]), reverse=True)
    
    # Return top `limit` unique solutions
    top_unique = [(obj, score) for obj, score, count in ranked_solutions[:limit]]
    
    if top_unique:
        logger.info(
            f"After score-priority ranking: top score={top_unique[0][1]:.4f}, "
            f"top count={ranked_solutions[0][2]}, returned={len(top_unique)} unique solutions"
        )
    
    return top_unique


def get_all_crops(db=None):
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, problem, solution, cropname FROM pesti_comp ORDER BY id ASC")
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
            threshold=0.15,
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

        # Semantic search ran but found nothing above threshold / overlap filter.
        # Do NOT fall back to ILIKE here — that would return random crop records
        # with no relevance. Return empty so caller shows the support message.
        logger.warning("Hybrid search returned no results — returning empty (no ILIKE fallback)")
        return []

    except Exception as e:
        logger.warning(f"Hybrid search failed: {e}, falling back to ILIKE")

    # ── ILIKE fallback — only reached on exception, not empty results ─────────
    try:
        from django.db import connection as django_conn
        with django_conn.cursor() as cursor:
            cursor.execute(
                "SELECT id, problem, solution, cropname FROM pesti_comp "
                "WHERE problem ILIKE %s ORDER BY id ASC LIMIT 5",
                [f"%{user_question}%"]
            )
            rows = cursor.fetchall()

        result = [CropResult(id=r[0], problem=r[1], solution=r[2], cropname=r[3]) for r in rows]
        for r in result:
            r.similarity_score = None
            r.search_method    = "fallback"

        elapsed_ms = (time.time() - start_time) * 1000
        logger.info(f"Fallback: {len(result)} results in {elapsed_ms:.2f}ms")
        return result
    except Exception as e:
        logger.error(f"Fallback search failed: {e}", exc_info=True)
        return []
