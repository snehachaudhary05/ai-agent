"""
Helper to integrate React builder with chat workflow
"""
import asyncio
import json
import hashlib
from typing import Dict
from react_builder import ReactWebsiteBuilder
from vercel_deployer import VercelDeployer
from professional_copywriter import copywriter
import os
import requests
import google.generativeai as genai


# Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# ── Image Cache (in-memory + disk) ───────────────────────────────────────────
_IMAGE_CACHE: dict = {}
_CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "image_cache.json")

def _load_disk_cache():
    global _IMAGE_CACHE
    try:
        with open(_CACHE_FILE, "r") as f:
            _IMAGE_CACHE = json.load(f)
        print(f"[ImageCache] Loaded {len(_IMAGE_CACHE)} cached entries from disk")
    except Exception:
        _IMAGE_CACHE = {}

def _save_disk_cache():
    try:
        with open(_CACHE_FILE, "w") as f:
            json.dump(_IMAGE_CACHE, f, indent=2)
    except Exception as e:
        print(f"[ImageCache] Save failed: {e}")

def _cache_key(query: str, decision: str) -> str:
    """Stable hash key for (query, image_type) pair."""
    normalized = f"{decision}:{query.lower().strip()}"
    return hashlib.md5(normalized.encode()).hexdigest()[:16]

# Load cache at import time
_load_disk_cache()


def get_smart_query_for_service(service, business_type):
    """Get specific image query for a service/product"""
    svc_lower = service.lower()

    # COMPREHENSIVE service-to-query mapping for ALL business types
    service_queries = {
        # E-commerce / Fashion - Western
        "jeans": "women jeans denim fashion stylish",
        "tops": "women tops blouse fashion trendy",
        "top": "women top blouse fashion casual",
        "dresses": "women dress fashion elegant",
        "dress": "women dress fashion elegant",
        "skorts": "women casual fashion shorts summer",
        "skort": "women casual fashion shorts summer",
        "skirts": "women skirt fashion midi maxi",
        "skirt": "women skirt fashion midi maxi",
        "bell bottom": "women bell bottom pants flare jeans retro",
        "bell-bottom": "women bell bottom pants flare jeans retro",
        "palazzo": "women palazzo pants wide leg fashion",
        "trousers": "women trousers formal pants fashion",
        "shorts": "women shorts casual fashion summer",
        "co-ord": "women co-ord set matching outfit",
        "coord": "women co-ord set matching outfit",
        "handbags": "women handbag purse fashion luxury",
        "accessories": "women fashion accessories jewelry",
        "shoes": "women shoes heels fashion footwear",
        "jackets": "women jacket fashion outerwear blazer",
        "jacket": "women jacket fashion outerwear",
        "sweaters": "women sweater knitwear fashion cozy",
        "sweater": "women sweater knitwear fashion",
        "activewear": "women activewear gym fitness sportswear",
        "lingerie": "women lingerie innerwear",
        "swimwear": "women swimwear beach fashion",
        "western wear": "women western fashion clothing",

        # E-commerce / Fashion - Indian Ethnic
        "kurta": "women kurta kurti ethnic indian fashion",
        "kurti": "women kurta kurti ethnic indian fashion",
        "saree": "women saree sari indian ethnic fashion",
        "sarree": "women saree sari indian ethnic fashion",
        "sari": "women saree sari indian ethnic fashion",
        "lehenga": "women lehenga bridal indian wedding fashion",
        "lehnga": "women lehenga bridal indian wedding fashion",
        "suits": "women salwar suit punjabi ethnic indian",
        "suit": "women salwar suit punjabi ethnic indian",
        "salwar": "women salwar kameez suit indian ethnic",
        "anarkali": "women anarkali suit indian ethnic fashion",
        "indo-western": "women indo western fusion indian fashion",
        "indo western": "women indo western fusion indian fashion",
        "dupatta": "women dupatta scarf indian ethnic",
        "churidar": "women churidar pants indian ethnic",
        "palazzo suit": "women palazzo suit indian ethnic fusion",
        "indian wear": "women indian ethnic fashion",

        # Salon / Spa / Beauty
        "facial": "woman facial spa treatment skincare glowing",
        "massage": "spa massage therapy relaxation wellness luxury",
        "body massage": "spa body massage therapy wellness relax",
        "hair styling": "hairstylist salon hair beauty styling",
        "hair cut": "hairdresser salon haircut styling modern",
        "haircut": "hairdresser salon haircut styling",
        "bridal makeup": "bridal makeup wedding beauty bride",
        "makeup": "makeup artist beauty cosmetics professional",
        "manicure": "manicure nails beauty salon polish",
        "pedicure": "pedicure feet spa treatment nails",
        "waxing": "beauty salon spa waxing treatment",
        "hair color": "hair coloring salon hairdresser dye",
        "spa": "luxury spa wellness relaxation massage",
        "beauty": "beauty salon treatment skincare cosmetics",
        "skincare": "skincare facial beauty treatment serum",
        "threading": "eyebrow threading beauty salon",
        "bleach": "facial bleach beauty salon treatment",
        "cleanup": "facial cleanup beauty salon skincare",

        # Fitness / Gym
        "hiit": "HIIT workout fitness gym training intense",
        "yoga": "yoga meditation fitness wellness peaceful",
        "crossfit": "crossfit gym workout training athletes",
        "personal training": "personal trainer gym fitness coaching",
        "gym": "modern fitness gym workout equipment",
        "fitness": "fitness training workout gym active",
        "cardio": "cardio workout fitness gym running",
        "strength": "strength training weights gym muscle",
        "strength training": "strength training weights gym dumbbells",
        "pilates": "pilates workout fitness studio mat",
        "zumba": "zumba dance fitness class energetic",
        "aerobics": "aerobics fitness class workout group",
        "spinning": "spinning bike cycling fitness gym",
        "weight training": "weight training gym dumbbells fitness",
        "bodybuilding": "bodybuilding gym muscles fitness",
        "martial arts": "martial arts karate fitness training",
        "boxing": "boxing gym fitness training punching",
        "dance": "dance fitness class studio energetic",

        # Indian Restaurant / Food
        "paneer tikka": "paneer tikka indian food restaurant plate",
        "paneer": "paneer indian cheese curry food restaurant",
        "chicken tikka": "chicken tikka indian food restaurant plate",
        "chicken 65": "chicken 65 indian food restaurant spicy",
        "butter chicken": "butter chicken curry indian food restaurant",
        "dal makhani": "dal makhani lentil curry indian food restaurant",
        "dal": "dal lentil curry indian food restaurant",
        "biryani": "biryani rice indian food restaurant",
        "pulao": "pulao rice indian food restaurant",
        "naan": "naan bread indian food restaurant",
        "roti": "roti chapati indian bread food",
        "paratha": "paratha indian bread breakfast food",
        "dosa": "dosa south indian food crispy restaurant",
        "idli": "idli south indian food restaurant",
        "samosa": "samosa indian snack food crispy",
        "tikka masala": "tikka masala curry indian food restaurant",
        "palak paneer": "palak paneer spinach curry indian food",
        "chole": "chole chickpea curry indian food restaurant",
        "rajma": "rajma kidney bean curry indian food",
        "gulab jamun": "gulab jamun indian sweet dessert syrup",
        "jalebi": "jalebi indian sweet dessert crispy",
        "rasgulla": "rasgulla indian sweet dessert white",
        "kheer": "kheer rice pudding indian dessert sweet",
        "halwa": "halwa indian sweet dessert",
        "kulfi": "kulfi indian ice cream dessert",
        "mango lassi": "mango lassi yogurt drink indian beverage",
        "lassi": "lassi yogurt drink indian beverage glass",
        "chaas": "chaas buttermilk indian drink",
        "cold coffee": "cold coffee iced latte cafe drink glass",
        "iced coffee": "iced coffee cold brew cafe drink",
        "fresh lime soda": "lime soda fizzy drink refreshing glass",
        "lemonade": "lemonade fresh lemon drink glass refreshing",
        "mocktail": "mocktail drink colorful glass refreshing bar",
        "mocktails": "mocktails drinks colorful glasses refreshing bar",
        "milkshake": "milkshake creamy drink glass cafe",
        "shakes": "milkshake creamy drink glass sweet",

        # Restaurant / Cafe / Food
        "pizza": "pizza italian food restaurant delicious",
        "pasta": "pasta italian cuisine food restaurant",
        "burger": "burger food restaurant gourmet delicious",
        "sushi": "sushi japanese food restaurant fresh",
        "dessert": "dessert pastry cake bakery sweet",
        "coffee": "coffee cafe espresso latte barista",
        "salad": "fresh salad healthy food bowl colorful",
        "steak": "steak meat grill restaurant juicy",
        "seafood": "seafood fish restaurant cuisine fresh",
        "wine": "wine bottle glass restaurant elegant",
        "cocktail": "cocktail drink bar mixology colorful",
        "breakfast": "breakfast food cafe morning pancakes",
        "lunch": "lunch food restaurant meal delicious",
        "dinner": "dinner food restaurant meal elegant",
        "brunch": "brunch food cafe breakfast lunch",
        "appetizers": "appetizers food restaurant starter",
        "sandwiches": "sandwich food cafe fresh deli",
        "wraps": "wraps food healthy lunch fresh",
        "smoothies": "smoothie bowl healthy fruit fresh",
        "juice": "fresh juice fruit healthy colorful",
        "ice cream": "ice cream dessert sweet colorful",
        "donuts": "donuts pastry bakery sweet glazed",
        "cupcakes": "cupcakes bakery sweet frosting colorful",
        "cookies": "cookies bakery sweet homemade",
        "waffles": "waffles breakfast cafe sweet syrup",
        "crepes": "crepes french thin pancake sweet cafe",
        "pancakes": "pancakes breakfast fluffy syrup stack",
        "french fries": "french fries crispy fast food snack",
        "fries": "french fries crispy fast food snack",
        "nachos": "nachos cheese snack mexican food",
        "noodles": "noodles bowl asian food restaurant",
        "fried rice": "fried rice asian food restaurant wok",
        "rice": "rice dish food restaurant bowl",
        "soup": "soup bowl hot food restaurant",
        "chicken": "chicken dish grilled food restaurant",
        "mutton": "mutton curry dish food restaurant",
        "lamb": "lamb chops grilled food restaurant",
        "fish": "fish fillet grilled food restaurant",
        "prawns": "prawns shrimp seafood dish food",
        "tacos": "tacos mexican food restaurant fresh",
        "sandwich": "sandwich food cafe fresh deli",
        "milkshake": "milkshake creamy thick drink sweet",
        "mocktail": "mocktail colorful drink fresh fruit",
        "lassi": "lassi yogurt drink indian refreshing",
        "tea": "tea cup hot drink cafe",
        "chai": "masala chai tea indian hot drink",

        # Indian Food
        "biryani": "biryani rice aromatic indian food",
        "curry": "curry indian food spicy bowl",
        "dal": "dal lentil soup indian food",
        "dal makhani": "dal makhani indian food creamy",
        "naan": "naan bread indian restaurant flatbread",
        "roti": "roti chapati indian bread food",
        "chapati": "chapati roti indian bread food",
        "tandoori": "tandoori chicken indian food grill",
        "tikka": "chicken tikka indian food grill spicy",
        "tikka masala": "chicken tikka masala indian curry food",
        "butter chicken": "butter chicken makhani indian curry",
        "paneer": "paneer tikka indian food restaurant",
        "dosa": "dosa south indian food crispy",
        "idli": "idli sambar south indian food",
        "samosa": "samosa indian snack fried crispy",
        "chaat": "chaat indian street food snack",
        "pav bhaji": "pav bhaji indian street food",
        "chole": "chole bhature indian food chickpea",
        "rajma": "rajma chawal indian food kidney beans",
        "gulab jamun": "gulab jamun indian sweet dessert",
        "rasgulla": "rasgulla indian sweet dessert syrup",
        "kheer": "kheer rice pudding indian dessert",
        "halwa": "halwa indian sweet dessert",
        "kulfi": "kulfi indian ice cream dessert",
        "ladoo": "ladoo indian sweet dessert ball",
        "barfi": "barfi indian sweet dessert milk",
        "jalebi": "jalebi indian sweet dessert crispy",

        # Bakery / Pastry
        "bread": "fresh bread bakery artisan loaves",
        "croissant": "croissant pastry bakery french flaky",
        "croissants": "croissants pastry bakery french",
        "pastries": "pastries bakery sweet danish croissant",
        "pastry": "pastry bakery sweet delicate",
        "cakes": "cakes bakery celebration birthday wedding",
        "cake": "cake bakery celebration frosting layers",
        "cheesecake": "cheesecake dessert creamy slice",
        "cheese cake": "cheesecake dessert creamy slice",
        "brownies": "brownies chocolate bakery fudge",
        "muffins": "muffins bakery breakfast blueberry",
        "tarts": "tarts pastry bakery fruit elegant",
        "pies": "pies bakery fruit dessert homemade",
        "macarons": "macarons pastry bakery french colorful",
        "eclairs": "eclairs pastry bakery french chocolate",
        "baguette": "baguette bread bakery french artisan",
        "custom cakes": "custom cake bakery celebration decorated",
        "wedding cakes": "wedding cake bakery elegant tiered",
        "birthday cakes": "birthday cake bakery celebration colorful",

        # Salon / Spa extras
        "nail extensions": "nail extensions acrylic nails beauty salon",
        "gel nails": "gel nails manicure beauty salon",
        "nail art": "nail art design beauty salon colorful",
        "eyelash extensions": "eyelash extensions beauty salon glam",
        "keratin treatment": "keratin hair treatment salon smooth",
        "hair treatment": "hair treatment salon spa deep conditioning",
        "hair spa": "hair spa treatment salon nourishing",
        "balayage": "balayage hair color salon highlights",
        "highlights": "hair highlights color salon styling",
        "eyebrow shaping": "eyebrow shaping beauty salon grooming",
        "pre-bridal": "pre-bridal package beauty salon bride",
        "bridal package": "bridal makeup package salon bride",
        "detan": "tan removal detan beauty treatment face",

        # Fitness extras
        "swimming": "swimming pool fitness workout laps",
        "kickboxing": "kickboxing martial arts fitness training",
        "meditation": "meditation yoga peaceful mindfulness wellness",
        "stretching": "stretching flexibility yoga fitness",
        "nutrition": "nutrition healthy food diet wellness",
        "nutrition counseling": "nutrition counseling diet healthy food",
        "functional training": "functional training workout fitness gym",
        "group fitness": "group fitness class gym workout energetic",
        "cycling": "cycling bike fitness workout gym",

        # Clinic / Healthcare
        "physiotherapy": "physiotherapy physical therapy rehabilitation exercise",
        "dermatology": "dermatology skin treatment clinic doctor",
        "cardiology": "cardiology heart care clinic doctor",
        "pediatrics": "pediatrics children health clinic doctor",
        "gynecology": "gynecology women health clinic doctor",
        "orthopedics": "orthopedics bone joint clinic doctor",
        "ophthalmology": "ophthalmology eye care clinic doctor",
        "ayurveda": "ayurveda herbal medicine treatment wellness",
        "homeopathy": "homeopathy medicine treatment clinic",
        "dentist": "dentist dental clinic teeth care professional",
        "doctor": "doctor clinic healthcare professional stethoscope",
        "blood test": "blood test laboratory clinic healthcare",
        "x-ray": "x-ray radiology clinic medical imaging",
        "ultrasound": "ultrasound scan clinic medical",

        # Men's Fashion
        "shirts": "men shirts fashion formal casual",
        "shirt": "men shirt fashion formal casual",
        "t-shirts": "men t-shirt casual fashion streetwear",
        "t-shirt": "men t-shirt casual fashion streetwear",
        "men jeans": "men jeans denim fashion casual",
        "men kurta": "men kurta ethnic indian fashion",
        "sherwani": "men sherwani wedding indian ethnic fashion",
        "blazer": "men blazer suit formal fashion",
        "formal wear": "men formal wear suit professional",
        "ethnic wear": "men ethnic wear indian fashion kurta",

        # Jewelry / Accessories
        "necklace": "necklace jewelry fashion gold silver",
        "earrings": "earrings jewelry fashion gold silver",
        "bangles": "bangles jewelry indian fashion gold",
        "rings": "rings jewelry fashion gold diamond",
        "bracelet": "bracelet jewelry fashion wrist",
        "anklet": "anklet jewelry fashion gold",
        "jewelry": "jewelry fashion gold silver elegant",
        "watch": "watch wristwatch fashion luxury timepiece",
        "sunglasses": "sunglasses eyewear fashion trendy",
        "bag": "handbag purse fashion women leather",
        "clutch": "clutch bag fashion women evening",
        "wallet": "wallet leather fashion men women",

        # Footwear
        "heels": "women heels shoes fashion elegant",
        "sandals": "sandals shoes fashion summer casual",
        "boots": "boots shoes fashion leather",
        "sneakers": "sneakers shoes fashion casual sporty",
        "flats": "flat shoes women fashion casual",
        "footwear": "footwear shoes fashion collection",

        # General Services
        "consulting": "business consulting professional meeting office",
        "photography": "photography camera professional portrait studio",
        "videography": "videography video camera production",
        "graphic design": "graphic design creative work computer",
        "web design": "web design website development computer",
        "marketing": "digital marketing strategy business creative",
        "accounting": "accounting finance calculator business",
        "legal": "legal law office lawyer professional",
        "tutoring": "tutoring education student learning books",
        "music lessons": "music lessons guitar piano teaching",
        "art classes": "art class painting creative studio",
        "pet grooming": "pet grooming dog salon care",
        "veterinary": "veterinary clinic pet dog cat care",
        "dental": "dental clinic dentist teeth care",
        "medical": "medical clinic doctor healthcare professional",
        "cleaning": "house cleaning service professional home",
        "plumbing": "plumber plumbing repair tools professional",
        "electrical": "electrician electrical work tools professional",
        "gardening": "gardening landscaping plants flowers garden",
        "catering": "catering food service event professional",
        "event planning": "event planning wedding party decoration",
        "tailoring": "tailoring sewing clothes fashion custom",
        "pharmacy": "pharmacy medicine healthcare professional",
        "optician": "optician eyewear glasses vision care",
        "car rental": "car rental vehicle luxury automobile",
        "car wash": "car wash cleaning service vehicle",
        "repair": "repair service tools professional workshop",
        "printing": "printing service design professional",
        "travel": "travel destination landscape beautiful scenic",
        "hotel": "hotel luxury room interior elegant",
        "architecture": "architecture building design modern exterior",

        # Coaching / Education
        "python": "python programming code laptop developer",
        "java": "java programming software developer laptop",
        "web development": "web development coding laptop developer",
        "data science": "data science analytics laptop charts",
        "machine learning": "machine learning artificial intelligence technology",
        "ielts": "ielts english test preparation study books",
        "spoken english": "english speaking class students learning",
        "public speaking": "public speaking presentation confident stage",
        "personality development": "personality development coaching professional confident",
        "interview preparation": "job interview preparation coaching professional",
        "soft skills": "soft skills training workshop professional team",
        "leadership": "leadership training workshop professional business",
        "career counseling": "career counseling guidance professional mentor",
        "aptitude training": "aptitude test preparation study mathematics",
        "gate coaching": "engineering gate exam preparation study",
        "neet coaching": "medical neet exam preparation study books",
        "jee coaching": "engineering jee exam preparation study",
        "mba coaching": "mba business school preparation study professional",

        # Real Estate
        "apartment": "modern apartment interior living room elegant",
        "villa": "luxury villa exterior architecture swimming pool",
        "flat": "modern flat apartment interior bright",
        "plot": "land plot aerial view residential",
        "commercial space": "commercial office space modern interior",
        "office space": "modern office space interior professional bright",
        "warehouse": "industrial warehouse space interior large",
        "shop space": "retail shop space interior modern",
        "penthouse": "luxury penthouse interior view modern",
        "studio apartment": "studio apartment modern interior compact",
        "bungalow": "bungalow house exterior architecture garden",
        "property management": "property management real estate professional",
        "home loan": "home loan mortgage financial planning professional",
        "interior design": "interior design modern home elegant beautiful",
    }

    # Try exact or partial match
    for key, query in service_queries.items():
        if key in svc_lower:
            return query

    # Business type fallbacks
    if business_type in ["shop", "store", "ecommerce", "boutique", "clothing", "online-store"]:
        return f"{service} fashion clothing wear"
    elif business_type in ["salon", "spa", "beauty"]:
        return f"{service} beauty spa treatment"
    elif business_type in ["gym", "fitness", "studio"]:
        return f"{service} fitness workout gym"
    elif business_type in ["restaurant", "cafe", "food"]:
        return f"{service} food plated dish restaurant"
    elif business_type in ["bakery", "pastry"]:
        return f"{service} bakery pastry fresh"
    elif business_type in ["coaching", "education", "tutoring", "academy"]:
        return f"{service} education learning class professional"
    elif business_type in ["real-estate", "property", "realty"]:
        return f"{service} property real estate home interior"
    elif business_type in ["clinic", "medical", "dental", "health"]:
        return f"{service} medical clinic healthcare professional"
    elif business_type in ["photography", "videography"]:
        return f"{service} photography studio camera professional"
    elif business_type in ["hotel", "resort", "hospitality"]:
        return f"{service} hotel luxury interior elegant"

    return f"{service} professional"


# ── Image Fetch with Cache ────────────────────────────────────────────────────

def smart_fetch_image(query: str, slot_key: str) -> dict:
    """
    Fetch a single image via Pexels with in-memory + disk caching.
    Returns: {"url": "<image URL>"}
    """
    from pexels_helper import search_pexels_image

    key = _cache_key(query, "realistic")

    if key in _IMAGE_CACHE:
        print(f"[ImageCache] HIT '{query}' → {_IMAGE_CACHE[key][:60]}...")
        return {"url": _IMAGE_CACHE[key]}

    print(f"[Images] Fetching '{query}' via Pexels")
    url = search_pexels_image(query) or f"https://picsum.photos/seed/{slot_key}/1920/1080"

    _IMAGE_CACHE[key] = url
    _save_disk_cache()
    return {"url": url}


async def build_react_website_from_chat(session: Dict) -> Dict:
    """
    Build a React website from chat session data

    Args:
        session: Chat session with business details

    Returns:
        Dict with website files and Vercel URL
    """
    # Prepare analysis data
    business_name = session.get("business_name", "My Business")
    business_type = session.get("business_type", "business")
    description = session.get("description", "")
    location = session.get("location", "")
    services_list = session.get("services", [])

    # Create professional copy based on business type - COMPREHENSIVE FOR ALL BUSINESSES
    hero_headlines = {
        # Fashion/Retail
        "shop": f"Discover Your Perfect Style at {business_name}",
        "store": f"Your Premium Shopping Destination - {business_name}",
        "ecommerce": f"Shop the Latest Trends at {business_name}",
        "boutique": f"Exclusive Fashion Finds at {business_name}",

        # Beauty/Wellness
        "salon": f"Transform Your Look at {business_name}",
        "spa": f"Experience Ultimate Relaxation at {business_name}",
        "beauty": f"Enhance Your Natural Beauty at {business_name}",

        # Fitness/Health
        "gym": f"Transform Your Body at {business_name}",
        "fitness": f"Your Fitness Journey Starts at {business_name}",
        "studio": f"Where Wellness Meets Excellence - {business_name}",
        "clinic": f"Trusted Healthcare at {business_name}",
        "dental": f"Your Smile is Our Priority - {business_name}",
        "medical": f"Comprehensive Care at {business_name}",

        # Food/Beverage
        "restaurant": f"Exquisite Dining Experience at {business_name}",
        "cafe": f"Your Favorite Coffee Destination - {business_name}",
        "bakery": f"Freshly Baked Goodness from {business_name}",
        "food": f"Delicious Cuisine at {business_name}",
        "pastry": f"Sweet Perfection from {business_name}",

        # Professional Services
        "photography": f"Capturing Life's Precious Moments - {business_name}",
        "videography": f"Professional Video Production by {business_name}",
        "consulting": f"Expert Business Solutions from {business_name}",
        "legal": f"Trusted Legal Expertise - {business_name}",
        "accounting": f"Professional Financial Services - {business_name}",

        # Education/Training
        "tutoring": f"Empowering Students to Excel - {business_name}",
        "education": f"Quality Education at {business_name}",
        "music lessons": f"Discover Your Musical Talent at {business_name}",
        "art classes": f"Unleash Your Creativity at {business_name}",

        # Pet Services
        "pet grooming": f"Pamper Your Furry Friends at {business_name}",
        "veterinary": f"Compassionate Pet Care at {business_name}",

        # Home Services
        "cleaning": f"Professional Cleaning Services by {business_name}",
        "plumbing": f"Reliable Plumbing Solutions - {business_name}",
        "electrical": f"Expert Electrical Services - {business_name}",
        "gardening": f"Transform Your Outdoor Space - {business_name}",

        # Events
        "event planning": f"Making Your Events Unforgettable - {business_name}",
        "catering": f"Exceptional Catering Services by {business_name}",
    }

    hero_subtexts = {
        # Fashion/Retail
        "shop": f"Premium fashion and style in {location}. Discover our curated collection of {', '.join(services_list[:3])} and more.",
        "store": f"Located in {location}. Explore our exclusive range of {', '.join(services_list[:3])} crafted for you.",
        "ecommerce": f"Online shopping made easy from {location}. Browse our {', '.join(services_list[:3])} collection.",
        "boutique": f"Luxury fashion boutique in {location}. Featuring {', '.join(services_list[:3])} and exclusive pieces.",

        # Beauty/Wellness
        "salon": f"Professional beauty services in {location}. We offer {', '.join(services_list[:3])} and more.",
        "spa": f"Luxury wellness in {location}. Indulge in our {', '.join(services_list[:3])} treatments.",
        "beauty": f"Expert beauty care in {location}. Specializing in {', '.join(services_list[:3])} services.",

        # Fitness/Health
        "gym": f"Modern fitness facility in {location}. Join us for {', '.join(services_list[:3])} and transform your life.",
        "fitness": f"Expert training in {location}. Specializing in {', '.join(services_list[:3])} programs.",
        "studio": f"Boutique fitness studio in {location}. Offering {', '.join(services_list[:3])} classes.",
        "clinic": f"Professional medical care in {location}. Providing {', '.join(services_list[:3])} services.",
        "dental": f"Advanced dental care in {location}. Expert {', '.join(services_list[:3])} treatments.",
        "medical": f"Comprehensive healthcare in {location}. Trusted for {', '.join(services_list[:3])} care.",

        # Food/Beverage
        "restaurant": f"Fine dining in {location}. Savor our signature {', '.join(services_list[:3])} dishes.",
        "cafe": f"Artisan cafe in {location}. Enjoy our {', '.join(services_list[:3])} and cozy ambiance.",
        "bakery": f"Artisan bakery in {location}. Fresh {', '.join(services_list[:3])} baked daily.",
        "food": f"Delicious cuisine in {location}. Famous for our {', '.join(services_list[:3])}.",
        "pastry": f"Gourmet pastries in {location}. Handcrafted {', '.join(services_list[:3])} daily.",

        # Professional Services
        "photography": f"Professional photography in {location}. Specializing in {', '.join(services_list[:3])} photography.",
        "videography": f"Expert video production in {location}. Creating stunning {', '.join(services_list[:3])} videos.",
        "consulting": f"Business consulting in {location}. Expert guidance in {', '.join(services_list[:3])}.",
        "legal": f"Legal services in {location}. Experienced in {', '.join(services_list[:3])} law.",
        "accounting": f"Professional accounting in {location}. Trusted for {', '.join(services_list[:3])} services.",

        # Education/Training
        "tutoring": f"Quality education in {location}. Expert tutoring in {', '.join(services_list[:3])}.",
        "education": f"Learning center in {location}. Offering {', '.join(services_list[:3])} courses.",
        "music lessons": f"Music instruction in {location}. Teaching {', '.join(services_list[:3])} and more.",
        "art classes": f"Art education in {location}. Classes in {', '.join(services_list[:3])}.",

        # Pet Services
        "pet grooming": f"Pet care in {location}. Expert {', '.join(services_list[:3])} services for your pets.",
        "veterinary": f"Veterinary care in {location}. Providing {', '.join(services_list[:3])} treatment.",

        # Home Services
        "cleaning": f"Cleaning services in {location}. Professional {', '.join(services_list[:3])} solutions.",
        "plumbing": f"Plumbing services in {location}. Expert {', '.join(services_list[:3])} repairs.",
        "electrical": f"Electrical services in {location}. Licensed {', '.join(services_list[:3])} experts.",
        "gardening": f"Landscaping services in {location}. Beautiful {', '.join(services_list[:3])} designs.",

        # Events
        "event planning": f"Event services in {location}. Specializing in {', '.join(services_list[:3])} planning.",
        "catering": f"Catering services in {location}. Delicious {', '.join(services_list[:3])} menus.",
    }

    # Simple color scheme (set before parallel tasks)
    colors = {
        "primary": "#667eea",
        "secondary": "#764ba2",
        "accent": "#f093fb"
    }

    # Build image query list: hero + one per service (all fetched in parallel)
    hero_queries = {
        "shop": "fashion model women clothing store boutique",
        "store": "fashion boutique women clothing interior",
        "ecommerce": "fashion model women online shopping",
        "boutique": "luxury fashion boutique interior clothing",
        "salon": "luxury salon interior beauty spa elegant",
        "spa": "luxury spa wellness relaxation interior",
        "beauty": "beauty salon interior elegant modern",
        "gym": "modern gym fitness equipment interior",
        "fitness": "fitness studio workout space equipment",
        "studio": "fitness yoga studio interior peaceful",
        "clinic": "medical clinic interior professional modern",
        "dental": "dental clinic modern interior professional",
        "restaurant": "elegant restaurant interior dining ambiance",
        "cafe": "modern cafe interior coffee shop cozy",
        "food": "restaurant food interior ambiance",
        "bakery": "bakery interior pastries display artisan",
        "pastry": "pastry shop bakery interior french",
        "photography": "photography studio professional camera equipment",
        "consulting": "modern office meeting professional business",
        "legal": "law office professional interior modern",
        "accounting": "professional office business interior",
        "tutoring": "education classroom tutoring learning",
        "coaching": "modern learning center classroom professional bright",
        "education": "education classroom modern school learning center",
        "real-estate": "luxury modern property architecture interior home",
        "property": "luxury property interior architecture modern",
        "online-store": "ecommerce warehouse modern shopping lifestyle",
        "ecommerce": "ecommerce lifestyle shopping modern bright",
        "clothing": "fashion boutique clothing store elegant interior",
        "boutique": "fashion boutique clothing luxury elegant store",
        "other": "modern professional business office interior bright",
        "veterinary": "veterinary clinic interior modern pet",
        "pet grooming": "pet grooming salon interior professional",
        "cleaning": "professional cleaning service home",
        "event planning": "event planning decoration wedding elegant",
    }
    hero_query = hero_queries.get(business_type, f"{business_type} professional modern interior")

    # All image slots to fetch: (slot_key, query)
    image_slots = [("hero", hero_query)] + [
        (f"service_{svc}", get_smart_query_for_service(svc, business_type))
        for svc in services_list[:8]
    ]

    # Run copywriter + all image fetches in parallel
    from concurrent.futures import ThreadPoolExecutor, as_completed
    images = [None] * len(image_slots)
    print(f"[Build] Fetching {len(image_slots)} images + copy in parallel...")

    with ThreadPoolExecutor(max_workers=min(len(image_slots) + 1, 12)) as executor:
        # Submit copywriter
        copy_future = executor.submit(
            copywriter.generate_website_copy,
            business_name=business_name,
            business_type=business_type,
            business_description=description,
            services=services_list,
            location=location,
            style_vibe="modern",
        )
        # Submit all image fetches
        future_to_idx = {
            executor.submit(smart_fetch_image, query, slot_key): idx
            for idx, (slot_key, query) in enumerate(image_slots)
        }
        # Collect image results
        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            try:
                images[idx] = future.result(timeout=15)
            except Exception as e:
                slot_key = image_slots[idx][0]
                print(f"[Images] Failed for {slot_key}: {e}")
                images[idx] = {"url": f"https://picsum.photos/seed/{slot_key}/1920/1080"}
        # Collect copy result
        copy_data = copy_future.result()

    print(f"[Build] {len(images)} images + copy ready.")

    hero_headline = copy_data.get("hero_headline", hero_headlines.get(business_type, f"Welcome to {business_name}"))
    hero_subtext = copy_data.get("hero_subtext", hero_subtexts.get(business_type, f"Your trusted {business_type} in {location}."))

    analysis = {
        "business_name": business_name,
        "business_type": business_type,
        "tagline": copy_data.get("tagline", hero_subtext),
        "hero_headline": hero_headline,
        "hero_subtext": hero_subtext,
        "about_text": copy_data.get("about_text", f"At {business_name}, we're passionate about delivering exceptional {business_type} services in {location}."),
        "services": services_list,
        "cta_text": copy_data.get("cta_text", "Get Started"),
        "sections": ["hero", "about", "services", "contact"],
        "cta": "Contact Us",
        "service_categories": session.get("service_categories", []),
    }
    
    # Features
    features = session.get("features", ["contact"])
    
    # Business description
    business_description = f"{session['description']}. Located in {session.get('location', 'our city')}. We offer: {', '.join(session.get('services', []))}"
    
    # Build React website
    builder = ReactWebsiteBuilder()
    react_result = await builder.generate_react_website(
        session_id=session.get("website_session_id", ""),
        analysis=analysis,
        colors=colors,
        images=images,
        features=features,
        business_description=business_description,
        deploy_to_vercel=False  # We'll deploy separately
    )
    
    # Deploy to Vercel
    deployer = VercelDeployer()
    deployment = await deployer.create_deployment(
        project_name=f"{session['business_name'].lower().replace(' ', '-')}",
        files=react_result['files']
    )

    vercel_url = None
    if deployment and 'url' in deployment:
        vercel_url = deployment['url']  # Already includes https://
        
    return {
        "session_id": session.get("website_session_id", ""),
        "files": react_result['files'],
        "vercel_url": vercel_url,
        "html": None  # React websites don't have standalone HTML preview
    }

def build_react_sync(session: Dict) -> Dict:
    """Synchronous wrapper"""
    return asyncio.run(build_react_website_from_chat(session))
