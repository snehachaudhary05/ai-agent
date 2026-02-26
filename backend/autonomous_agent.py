
from dotenv import load_dotenv
load_dotenv()
"""
AI WEBSITE BUILDER AGENT - Interactive Chat + Full Websites
Conversational chatbot that guides users to build production-ready websites
with e-commerce, booking, media uploads, and admin panels.
"""

import sys
import os
import json
import uuid
import random
import requests

# Ensure stdout uses UTF-8 on Windows (avoids cp1252 UnicodeEncodeError for arrow chars in print)
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import zipfile
import io
import shutil
import base64
from datetime import datetime
from typing import Dict, Optional, List
import google.generativeai as genai
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse, JSONResponse
from pydantic import BaseModel
from autonomous_agent_react_helper import build_react_website_from_chat
from professional_copywriter import copywriter
from pexels_helper import search_pexels_image, search_pexels_images

# Import React and Vercel modules
try:
    from react_builder import ReactWebsiteBuilder
    from vercel_deployer import VercelDeployer
    REACT_VERCEL_AVAILABLE = True
except ImportError as e:
    print(f"[WARNING] React/Vercel modules not available: {e}")
    REACT_VERCEL_AVAILABLE = False

# Load environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not set")

genai.configure(api_key=GEMINI_API_KEY)

# Initialize FastAPI
app = FastAPI(title="Sitekraft Agent")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create directories
os.makedirs("generated_websites", exist_ok=True)
os.makedirs("website_states", exist_ok=True)
os.makedirs("static/uploads", exist_ok=True)
os.makedirs("site_data", exist_ok=True)

# Mount static files for uploads (used by chat image uploads)
app.mount("/static", StaticFiles(directory="static"), name="static")

# ============================================================
# IN-MEMORY STATE
# ============================================================
CHAT_SESSIONS = {}  # session_id -> conversation state
WEBSITE_STATES = {}  # session_id -> website state


# ============================================================
# REQUEST MODELS
# ============================================================
class ChatMessage(BaseModel):
    session_id: str
    message: str
    uploaded_files: Optional[List[str]] = []

class BuildRequest(BaseModel):
    description: str
    preferences: Optional[Dict] = None

class EditRequest(BaseModel):
    session_id: str
    edit_request: str

class BookingRequest(BaseModel):
    name: str
    email: str
    phone: str
    service: str
    date: str
    time: str
    notes: Optional[str] = ""

class OrderRequest(BaseModel):
    name: str
    email: str
    phone: str
    address: str
    items: List[Dict]
    notes: Optional[str] = ""

class ContactRequest(BaseModel):
    name: str
    email: str
    phone: Optional[str] = ""
    message: str


# ============================================================
# CONVERSATION STATE MACHINE
# ============================================================
CONVERSATION_STAGES = [
    "greeting",           # Ask business type
    "business_details",   # Ask name, location, description
    "services",           # Ask about services/products
    "media",              # Ask for photos/videos
    "features",           # Ask what features they need
    "style",              # Ask about colors/vibe
    "building",           # AI is building the website
    "review",             # Website built, user can edit via chat
]

BUSINESS_TYPE_QUESTIONS = {
    "restaurant": {
        "services": "What type of cuisine do you serve? List your signature dishes or menu categories.",
        "media": "Do you have photos of your restaurant or dishes? Share them and I'll add them to your website! If not, I'll find beautiful stock photos.",
        "features": "Which features do you need?",
        "features_options": ["Online Menu", "Table Booking", "Online Ordering", "Delivery Tracking", "Reviews Section", "Photo Gallery"],
    },
    "salon": {
        "services": "What services do you offer? (e.g., Haircuts, Coloring, Manicure, Facial, etc.)",
        "media": "Do you have photos of your salon or your work? Share them! If not, I'll use professional stock images.",
        "features": "Which features do you need?",
        "features_options": ["Online Booking", "Service Menu with Prices", "Before/After Gallery", "Reviews", "Gift Cards"],
    },
    "gym": {
        "services": "What fitness programs do you offer? (e.g., HIIT, Yoga, CrossFit, Personal Training)",
        "media": "Do you have photos of your gym or training sessions? Share them!",
        "features": "Which features do you need?",
        "features_options": ["Membership Plans", "Class Schedule", "Online Booking", "Trainer Profiles", "Transformation Gallery"],
    },
    "shop": {
        "services": "What products do you sell? List your main categories.",
        "media": "Do you have product photos? Share them and I'll showcase them beautifully!",
        "features": "Which features do you need?",
        "features_options": ["Product Catalog", "Online Ordering", "Shopping Cart", "Reviews", "Size Guide"],
    },
    "clinic": {
        "services": "What medical services do you provide? (e.g., General Practice, Dental, Dermatology)",
        "media": "Do you have photos of your clinic or team? Share them!",
        "features": "Which features do you need?",
        "features_options": ["Appointment Booking", "Doctor Profiles", "Service List", "Patient Reviews", "Insurance Info"],
    },
    "cafe": {
        "services": "What do you serve? (e.g., Specialty Coffee, Pastries, Breakfast, Lunch)",
        "media": "Do you have photos of your cafe or menu items? Share them!",
        "features": "Which features do you need?",
        "features_options": ["Menu Display", "Online Ordering", "Table Reservation", "Photo Gallery", "Loyalty Program"],
    },
    "default": {
        "services": "What are your main services or products?",
        "media": "Do you have any photos or videos of your business? Share them and I'll add them to your website!",
        "features": "Which features do you need?",
        "features_options": ["Contact Form", "Service Catalog", "Online Booking", "Photo Gallery", "Testimonials", "Blog"],
    }
}


def get_business_questions(business_type):
    btype = business_type.lower()
    for key in BUSINESS_TYPE_QUESTIONS:
        if key in btype:
            return BUSINESS_TYPE_QUESTIONS[key]
    return BUSINESS_TYPE_QUESTIONS["default"]


# ============================================================
# IMAGE SEARCH ENDPOINT
# ============================================================

@app.get("/api/image-search")
async def image_search(query: str, orientation: str = ""):
    """Search Pexels and return the direct image URL.
    Direct Pexels URLs work fine in <img> tags and CSS url() on any page (blob, Vercel, etc.).
    Returning the URL directly keeps the HTML tiny, makes deployment reliable, and is ~10x faster.
    """
    pexels_url = search_pexels_image(query, orientation)
    print(f"[image-search] '{query}' -> {(pexels_url or 'none')[:80]}")
    return {"url": pexels_url}


# ============================================================
# CHAT ENDPOINTS
# ============================================================

@app.post("/api/chat/start")
async def start_chat():
    """Start a new chat session"""
    session_id = str(uuid.uuid4())
    CHAT_SESSIONS[session_id] = {
        "stage": "greeting",
        "business_type": None,
        "business_name": None,
        "location": None,
        "description": None,
        "services": [],
        "uploaded_media": [],
        "features": [],
        "style_vibe": None,
        "conversation_history": [],
        "website_session_id": None,
    }

    return {
        "session_id": session_id,
        "message": "Hey there! I'm your AI website builder. I'll help you create a stunning, fully functional website for your business.\n\nWhat kind of business do you have?",
        "quick_replies": ["Restaurant", "Salon / Spa", "Gym / Fitness", "Online Shop", "Clinic / Healthcare", "Cafe / Coffee", "Other"]
    }


@app.post("/api/chat")
async def chat(request: ChatMessage):
    """Process a chat message and return AI response"""
    session_id = request.session_id
    message = request.message.strip()
    uploaded_files = request.uploaded_files or []

    if session_id not in CHAT_SESSIONS:
        # Auto-create session if missing
        CHAT_SESSIONS[session_id] = {
            "stage": "greeting",
            "business_type": None,
            "business_name": None,
            "location": None,
            "description": None,
            "services": [],
            "uploaded_media": [],
            "features": [],
            "style_vibe": None,
            "conversation_history": [],
            "website_session_id": None,
        }

    session = CHAT_SESSIONS[session_id]
    stage = session["stage"]

    # Store uploaded files
    if uploaded_files:
        session["uploaded_media"].extend(uploaded_files)

    # Add to conversation history
    session["conversation_history"].append({"role": "user", "content": message, "files": uploaded_files})

    response_data = {"session_id": session_id, "preview_ready": False, "website_code": "", "quick_replies": []}

    try:
        # ---- GREETING STAGE: Identify business type ----
        if stage == "greeting":
            business_type = identify_business_type(message)
            session["business_type"] = business_type
            session["stage"] = "business_details"

            response_data["message"] = (
                f"Great, a **{business_type}** business! Let me help you build an amazing website.\n\n"
                f"Tell me a bit more:\n"
                f"- What's your business name?\n"
                f"- Where is it located (city)?\n"
                f"- A brief description of what makes it special"
            )

        # ---- BUSINESS DETAILS STAGE ----
        elif stage == "business_details":
            # Use AI to extract business details
            details = extract_business_details(message, session["business_type"])
            session["business_name"] = details.get("name", "My Business")
            session["location"] = details.get("location", "")
            session["description"] = message
            session["stage"] = "services"

            questions = get_business_questions(session["business_type"])
            response_data["message"] = (
                f"**{session['business_name']}** sounds wonderful!\n\n"
                f"{questions['services']}"
            )

        # ---- SERVICES STAGE ----
        elif stage == "services":
            services = extract_services(message, session["business_type"])
            session["services"] = services
            session["stage"] = "media"

            questions = get_business_questions(session["business_type"])
            response_data["message"] = (
                f"Noted! I'll feature these on your website.\n\n"
                f"{questions['media']}\n\n"
                f"You can upload photos using the **+** button, or type **skip** to use stock images."
            )
            response_data["quick_replies"] = ["Skip - use stock photos", "I'll upload some photos"]

        # ---- MEDIA STAGE ----
        elif stage == "media":
            if uploaded_files:
                count = len(session["uploaded_media"])
                response_data["message"] = (
                    f"Got {count} photo(s)! They'll look great on your website.\n\n"
                    f"Want to add more, or shall we move on to features?"
                )
                response_data["quick_replies"] = ["Add more photos", "Move on to features"]
                # Stay in media stage if they want to add more
                if "more" not in message.lower() and "add" not in message.lower():
                    session["stage"] = "features"
                    questions = get_business_questions(session["business_type"])
                    response_data["message"] = (
                        f"Got {count} photo(s)! They'll look great on your website.\n\n"
                        f"{questions['features']}"
                    )
                    response_data["quick_replies"] = questions["features_options"]
                    response_data["multi_select"] = True
            else:
                if "skip" in message.lower() or "stock" in message.lower() or "no" in message.lower() or "don't" in message.lower():
                    session["stage"] = "features"
                    questions = get_business_questions(session["business_type"])
                    response_data["message"] = (
                        f"No worries! I'll find beautiful professional photos for you.\n\n"
                        f"{questions['features']}"
                    )
                    response_data["quick_replies"] = questions["features_options"]
                    response_data["multi_select"] = True
                elif "upload" in message.lower() or "photo" in message.lower() or "i'll" in message.lower():
                    response_data["message"] = "Go ahead! Click the **+** button to upload your photos. You can upload multiple at once."
                else:
                    session["stage"] = "features"
                    questions = get_business_questions(session["business_type"])
                    response_data["message"] = (
                        f"Got it! Moving on.\n\n{questions['features']}"
                    )
                    response_data["quick_replies"] = questions["features_options"]
                    response_data["multi_select"] = True

        # ---- FEATURES STAGE ----
        elif stage == "features":
            features = extract_features(message, session["business_type"])
            session["features"] = features
            session["stage"] = "style"

            response_data["message"] = (
                f"Great choices! Last question - what **style/vibe** do you want for your website?"
            )
            response_data["quick_replies"] = ["Modern & Clean", "Luxury & Elegant", "Warm & Cozy", "Bold & Energetic", "Minimalist", "Let AI decide"]

        # ---- STYLE STAGE ----
        elif stage == "style":
            session["style_vibe"] = message.lower().replace("let ai decide", "modern")
            session["stage"] = "building"

            response_data["message"] = (
                f"Perfect! I have everything I need. Let me build your website now...\n\n"
                f"**Building your {session['business_type']} website for {session['business_name']}**\n\n"
                f"Hold on while I create something amazing..."
            )

            # Actually build the React website
            try:
                import uuid
                session["website_session_id"] = str(uuid.uuid4())[:8]
                build_result = await build_react_website_from_chat(session)
                website_session_id = build_result["session_id"]
                session["website_session_id"] = website_session_id
                session["stage"] = "review"

                response_data["session_id"] = website_session_id
                response_data["preview_ready"] = True
                response_data["website_code"] = build_result["html"]

                # Get Vercel URL from build result
                vercel_url = build_result.get("vercel_url")
                if vercel_url:
                    session["vercel_url"] = vercel_url
                    print(f"[OK] Deployed to Vercel: {vercel_url}")

                message_text = f"\n\n**Your website is ready!** Check the preview on the right.\n\n"
                if vercel_url:
                    message_text += f"**Live Link:** {vercel_url}\n(Your website is live and shareable!)\n\n"
                message_text += "Want to make any changes? Just tell me what you'd like to modify - colors, text, layout, anything!"

                response_data["message"] += message_text
                response_data["vercel_url"] = vercel_url
                response_data["quick_replies"] = ["Change colors", "Edit text", "Add more sections", "Looks perfect!", "Download it"]

            except Exception as e:
                print(f"Build error: {e}")
                session["stage"] = "style"
                response_data["message"] = f"Sorry, I hit an issue building your website. Let me try again. Error: {str(e)[:100]}"

        # ---- REVIEW/EDIT STAGE ----
        elif stage == "review":
            if "download" in message.lower():
                response_data["message"] = "You can download your website using the **Download** button in the preview panel!"
                response_data["quick_replies"] = ["Change colors", "Edit text", "Add more sections", "Start over"]
            elif "perfect" in message.lower() or "great" in message.lower() or "love it" in message.lower() or "looks good" in message.lower():
                response_data["message"] = (
                    "Awesome! Your website is ready to go.\n\n"
                    "You can:\n"
                    "- **Download** it using the button in the preview panel\n"
                    "- **Open in new tab** to see the full version\n"
                    "- Keep chatting with me to make more changes\n\n"
                    "Need anything else?"
                )
                response_data["quick_replies"] = ["Make more changes", "Download", "Start a new website"]
            elif "start over" in message.lower() or "new website" in message.lower():
                # Reset session
                new_session = await start_chat()
                return new_session
            else:
                # Apply edit via AI
                try:
                    edit_result = edit_website_from_chat(session, message)
                    session["website_session_id"] = edit_result["session_id"]

                    response_data["session_id"] = edit_result["session_id"]
                    response_data["preview_ready"] = True
                    response_data["website_code"] = edit_result["html"]
                    response_data["message"] = (
                        f"Done! I've applied your changes. Check the updated preview.\n\n"
                        f"Want to change anything else?"
                    )
                    response_data["quick_replies"] = ["Change colors", "Edit text", "Add sections", "Looks perfect!", "Download"]

                except Exception as e:
                    print(f"Edit error: {e}")
                    response_data["message"] = f"Sorry, I couldn't apply that change. Could you try rephrasing? Error: {str(e)[:100]}"

        # ---- BUILDING STAGE (shouldn't normally reach here) ----
        elif stage == "building":
            response_data["message"] = "I'm still building your website. Please wait a moment..."

    except Exception as e:
        print(f"Chat error: {e}")
        response_data["message"] = "Sorry, something went wrong. Could you try again?"

    # Store AI response in history
    session["conversation_history"].append({"role": "assistant", "content": response_data["message"]})

    return response_data


# ============================================================
# AI HELPER FUNCTIONS
# ============================================================

def identify_business_type(message):
    """Identify business type from user message"""
    msg = message.lower()
    type_map = {
        "restaurant": ["restaurant", "food", "dining", "eatery", "bistro", "diner"],
        "salon": ["salon", "spa", "beauty", "hair", "nail", "barber"],
        "gym": ["gym", "fitness", "workout", "training", "crossfit", "yoga"],
        "shop": ["shop", "store", "ecommerce", "e-commerce", "retail", "boutique", "clothing", "fashion"],
        "clinic": ["clinic", "hospital", "doctor", "medical", "dental", "healthcare", "health"],
        "cafe": ["cafe", "coffee", "bakery", "tea", "pastry"],
    }
    for btype, keywords in type_map.items():
        if any(kw in msg for kw in keywords):
            return btype

    # Use AI for ambiguous cases
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        resp = model.generate_content(
            f'What type of business is this? "{message}". '
            f'Reply with ONLY one word from: restaurant, salon, gym, shop, clinic, cafe, business'
        )
        return resp.text.strip().lower().replace('.', '')
    except:
        return "business"


def extract_business_details(message, business_type):
    """Extract business name and location from message"""
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        resp = model.generate_content(
            f'Extract the business name and city/location from this text: "{message}". '
            f'The business type is: {business_type}. '
            f'Return ONLY valid JSON with no extra text: {{"name": "exact business name from text", "location": "city, country"}}'
        )
        text = resp.text.strip()
        json_start = text.find('{')
        json_end = text.rfind('}') + 1
        if json_start >= 0:
            result = json.loads(text[json_start:json_end])
            print(f"Extracted details: {result}")
            return result
    except Exception as e:
        print(f"Extract details error: {e}")

    # Fallback: try to find name in the message itself
    msg_lower = message.lower()
    name = "My Business"
    # Simple heuristic: look for "name is X" or "called X"
    for pattern in ["name is ", "name's ", "called ", "named "]:
        if pattern in msg_lower:
            idx = msg_lower.index(pattern) + len(pattern)
            rest = message[idx:].strip()
            # Take until next punctuation or common word
            for end_word in [" i ", " we ", " in ", " at ", " located", " based", ",", "."]:
                if end_word in rest.lower():
                    name = rest[:rest.lower().index(end_word)].strip()
                    break
            else:
                name = rest.split()[0] if rest else "My Business"
            break
    return {"name": name, "location": ""}


def extract_services(message, business_type):
    """Extract services/products from message"""
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        resp = model.generate_content(
            f'Extract the specific product categories or services mentioned in this text: "{message}". '
            f'Business type: {business_type}. '
            f'Return ONLY a JSON array of the items mentioned, keep the exact names: ["Item 1", "Item 2", ...]'
        )
        text = resp.text.strip()
        json_start = text.find('[')
        json_end = text.rfind(']') + 1
        if json_start >= 0:
            result = json.loads(text[json_start:json_end])
            if result and len(result) > 0:
                print(f"Extracted services: {result}")
                return result
    except Exception as e:
        print(f"Extract services error: {e}")

    # Fallback: split by commas and common separators
    parts = []
    for sep in [",", " - ", "-", " and ", "\n", "/"]:
        if sep in message:
            parts = [p.strip() for p in message.split(sep) if p.strip() and len(p.strip()) > 1]
            break
    if parts:
        return parts[:8]
    return [message.strip()] if message.strip() else ["Products"]


def extract_features(message, business_type):
    """Extract requested features from message - captures ALL selected features"""
    features = []
    msg = message.lower()

    # Comprehensive feature mapping - maps user selections to internal feature names
    feature_mappings = {
        # Booking related
        "booking": ["booking", "appointment", "schedule", "reserve", "online booking", "table booking"],

        # Ordering/Shopping related
        "ordering": ["order", "cart", "buy", "purchase", "delivery", "online ordering", "shopping cart"],

        # Menu/Catalog related
        "menu": ["menu", "catalog", "product", "items", "service menu", "product catalog", "class schedule"],

        # Gallery related
        "gallery": ["gallery", "photos", "portfolio", "before/after", "photo gallery", "transformation gallery"],

        # Reviews related
        "reviews": ["review", "testimonial", "feedback", "patient reviews"],

        # Contact related
        "contact": ["contact", "form", "inquiry", "enquiry", "contact form"],

        # Blog/Content related
        "blog": ["blog", "news", "articles"],

        # Membership/Plans
        "membership": ["membership", "plans", "pricing", "packages", "membership plans"],

        # Profiles
        "profiles": ["profiles", "team", "trainers", "doctors", "trainer profiles", "doctor profiles"],

        # Tracking
        "tracking": ["tracking", "delivery tracking", "order tracking"],

        # Size guide
        "size_guide": ["size", "sizing", "size guide", "size chart"],

        # Gift cards
        "gift_cards": ["gift", "cards", "gift cards", "vouchers"],

        # Loyalty
        "loyalty": ["loyalty", "rewards", "loyalty program"],

        # Insurance
        "insurance": ["insurance", "insurance info"],
    }

    # Check each feature mapping
    for feature, keywords in feature_mappings.items():
        if any(kw in msg for kw in keywords):
            if feature not in features:  # Avoid duplicates
                features.append(feature)

    # If still no features found, use defaults
    if not features:
        defaults = {
            "restaurant": ["menu", "ordering", "reviews", "gallery", "contact"],
            "salon": ["booking", "gallery", "reviews", "contact"],
            "gym": ["booking", "membership", "gallery", "reviews", "contact"],
            "shop": ["menu", "ordering", "reviews", "gallery", "contact"],
            "store": ["menu", "ordering", "reviews", "gallery", "contact"],
            "ecommerce": ["menu", "ordering", "reviews", "gallery", "contact"],
            "boutique": ["menu", "ordering", "reviews", "gallery", "contact"],
            "clinic": ["booking", "profiles", "reviews", "contact"],
            "cafe": ["menu", "ordering", "gallery", "reviews", "contact"],
        }
        features = defaults.get(business_type, ["contact", "gallery", "reviews"])

    print(f"[Features] Extracted from '{message}': {features}")
    return features


# ============================================================
# PEXELS IMAGE FETCHING
# ============================================================

def fetch_pexels_images(query, count=1):
    """Fetch images from Pexels API"""
    urls = search_pexels_images(query, count=count, orientation="landscape")
    if urls:
        return urls
    # picsum fallback if Pexels fails
    print(f"[Pexels] Using fallback images for '{query}'")
    return [f"https://picsum.photos/seed/{query.replace(' ', '')}/1920/1080" for _ in range(count)]


def get_images_for_website(session):
    """Get images - use uploaded ones first, fill with Pexels (all fetches run in parallel)"""
    from concurrent.futures import ThreadPoolExecutor, as_completed

    uploaded = session.get("uploaded_media", [])
    business_type = session.get("business_type", "business")
    business_name = session.get("business_name", "")
    services = session.get("services", [])

    images = {"hero": "", "about": "", "services": [], "gallery": [], "products": {}}

    # Uploaded images become gallery/service images
    uploaded_urls = [f"{u}" if u.startswith("http") else u for u in uploaded]

    # Specific image queries for better results across different business types
    service_queries = {
        # E-commerce / Fashion - Western
        "jeans": "women jeans denim fashion stylish",
        "tops": "women tops blouse fashion trendy",
        "top": "women top blouse fashion casual",
        "dresses": "women dress fashion elegant",
        "dress": "women dress fashion elegant",
        "skorts": "women skort fashion active trendy",
        "skort": "women skort fashion active trendy",
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
        "micro facial": "facial skincare microdermabrasion beauty spa",
        "threading": "eyebrow threading beauty salon",
        "bleach": "facial bleach beauty salon treatment",
        "cleanup": "facial cleanup beauty salon skincare",
        "tan removal": "tan removal beauty treatment skincare",

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

        # Bakery / Pastry
        "bread": "fresh bread bakery artisan loaves",
        "croissant": "croissant pastry bakery french flaky",
        "croissants": "croissants pastry bakery french",
        "pastries": "pastries bakery sweet danish croissant",
        "pastry": "pastry bakery sweet delicate",
        "cakes": "cakes bakery celebration birthday wedding",
        "cake": "cake bakery celebration frosting layers",
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
    }

    def get_smart_query(service, btype):
        """Get a specific image search query based on service/product category"""
        svc_lower = service.lower()

        # Try to find a specific match first
        for key, query in service_queries.items():
            if key in svc_lower:
                return query

        # Business type specific fallbacks
        if btype in ["shop", "store", "ecommerce", "boutique"]:
            return f"women {service} fashion clothing"
        elif btype in ["salon", "spa", "beauty"]:
            return f"{service} beauty spa treatment"
        elif btype in ["gym", "fitness", "studio"]:
            return f"{service} fitness workout gym"
        elif btype in ["restaurant", "cafe", "food"]:
            return f"{service} food restaurant cuisine"

        # Generic fallback
        return f"{service} professional high quality"

    fallback = "https://picsum.photos/seed/business/1920/1080"

    hero_queries = {
        "shop": "fashion model women clothing store",
        "store": "fashion model women clothing store",
        "ecommerce": "fashion model women clothing store",
        "boutique": "fashion model women clothing store",
        "salon": "luxury salon interior beauty spa",
        "spa": "luxury spa wellness relaxation interior",
        "beauty": "beauty salon interior elegant",
        "gym": "modern gym fitness equipment interior",
        "fitness": "fitness studio workout space",
        "studio": "fitness yoga studio interior",
        "restaurant": "elegant restaurant interior dining",
        "cafe": "modern cafe interior coffee shop",
        "food": "restaurant food interior ambiance",
    }
    about_queries = {
        "shop": "fashion designer workspace boutique",
        "store": "fashion designer workspace boutique",
        "ecommerce": "fashion designer workspace boutique",
        "boutique": "fashion designer workspace boutique",
        "salon": "beauty salon professional team staff",
        "spa": "spa therapist massage wellness professional",
        "beauty": "beauty professional makeup artist",
        "gym": "fitness trainer gym coach professional",
        "fitness": "personal trainer fitness professional",
        "studio": "fitness instructor yoga teacher",
        "restaurant": "chef kitchen restaurant professional",
        "cafe": "barista coffee cafe professional",
        "food": "chef cooking restaurant kitchen",
    }
    gallery_queries = {
        "shop": "fashion lookbook editorial style",
        "store": "fashion lookbook editorial style",
        "ecommerce": "fashion lookbook editorial style",
        "boutique": "fashion lookbook editorial style",
        "salon": "beauty salon hair makeup before after",
        "spa": "spa wellness relaxation massage treatment",
        "beauty": "beauty makeup skincare treatment",
        "gym": "fitness workout gym training results",
        "fitness": "fitness training workout motivation",
        "studio": "fitness yoga studio class workout",
        "restaurant": "restaurant food plating delicious",
        "cafe": "cafe coffee latte food dessert",
        "food": "food plating restaurant delicious meal",
    }

    is_ecommerce = business_type in ["shop", "store", "ecommerce", "boutique"]

    # Build the list of Pexels tasks (only for slots not covered by uploads)
    # Each task: (task_key, query, count)
    tasks = []
    if len(uploaded_urls) < 1:
        tasks.append(("hero", hero_queries.get(business_type.lower(), f"{business_type} interior modern professional"), 1))
    if len(uploaded_urls) < 2:
        tasks.append(("about", about_queries.get(business_type.lower(), f"{business_type} professional team workspace"), 1))

    for i, service in enumerate(services[:8]):
        if i + 2 >= len(uploaded_urls):
            query = get_smart_query(service, business_type)
            # For ecommerce, fetch 5 images per service: [0] for card, [1:5] for product grid
            count = 5 if (is_ecommerce and i < 6) else 1
            tasks.append((f"service_{i}", query, count))

    remaining_uploads = uploaded_urls[2 + len(services):]
    if not remaining_uploads:
        gallery_query = gallery_queries.get(business_type.lower(), f"{business_type} gallery showcase")
        tasks.append(("gallery", gallery_query, 3))

    # Run ALL Pexels fetches in parallel
    results = {}
    if tasks:
        print(f"[Images] Fetching {len(tasks)} image sets in parallel...")
        with ThreadPoolExecutor(max_workers=min(len(tasks), 12)) as executor:
            future_to_key = {
                executor.submit(fetch_pexels_images, query, count): key
                for key, query, count in tasks
            }
            for future in as_completed(future_to_key):
                key = future_to_key[future]
                try:
                    results[key] = future.result(timeout=15)
                except Exception as e:
                    print(f"[Images] Failed for {key}: {e}")
                    results[key] = []
        print(f"[Images] All parallel fetches done.")

    # Assign results
    images["hero"] = uploaded_urls[0] if uploaded_urls else (results.get("hero") or [fallback])[0]
    images["about"] = uploaded_urls[1] if len(uploaded_urls) > 1 else (results.get("about") or [fallback])[0]

    for i, service in enumerate(services[:8]):
        if i + 2 < len(uploaded_urls):
            svc_img = uploaded_urls[i + 2]
            images["services"].append(svc_img)
            if is_ecommerce and i < 6:
                images["products"][service] = [svc_img] * 4
        else:
            imgs = results.get(f"service_{i}") or [fallback]
            images["services"].append(imgs[0])
            if is_ecommerce and i < 6:
                # Reuse extra images fetched in the same call (no extra API call)
                product_imgs = imgs[1:5] if len(imgs) > 1 else [imgs[0]] * 4
                while len(product_imgs) < 4:
                    product_imgs.append(imgs[0])
                images["products"][service] = product_imgs

    if remaining_uploads:
        images["gallery"] = remaining_uploads[:6]
    else:
        images["gallery"] = results.get("gallery") or [fallback] * 3

    return images


# ============================================================
# WEBSITE BUILDING FROM CHAT
# ============================================================

def build_website_from_chat(session):
    """Build a complete website from chat session data"""
    business_type = session["business_type"]
    business_name = session["business_name"] or "My Business"
    location = session["location"] or ""
    description = session["description"] or ""
    services = session["services"] or ["Service 1", "Service 2", "Service 3"]
    features = session["features"] or ["contact"]
    style_vibe = session.get("style_vibe", "modern")

    # Run image fetching and copywriting IN PARALLEL — they are fully independent
    from concurrent.futures import ThreadPoolExecutor
    print("[BUILD] Fetching images + generating copy in parallel...")
    with ThreadPoolExecutor(max_workers=2) as executor:
        images_future = executor.submit(get_images_for_website, session)
        copy_future = executor.submit(
            copywriter.generate_website_copy,
            business_name=business_name,
            business_type=business_type,
            business_description=description,
            services=services,
            location=location,
            style_vibe=style_vibe,
        )
        images = images_future.result()
        copy_data = copy_future.result()
    print("[BUILD] Images + copy ready.")

    # Build complete analysis with professional copy
    analysis = {
        "business_name": business_name,
        "business_type": business_type,
        "location": {"city": location.split(",")[0] if location else "City", "country": location.split(",")[-1].strip() if "," in location else "Country"},
        "vibe": style_vibe.split()[0].lower() if style_vibe else "modern",
        "target_audience": "everyone",
        "services": services[:6],
        "hero_headline": copy_data.get("hero_headline", f"Welcome to {business_name}"),
        "hero_subtext": copy_data.get("hero_subtext", f"Experience exceptional {business_type} services"),
        "tagline": copy_data.get("tagline", "Excellence in Every Detail"),
        "about_text": copy_data.get("about_text", f"{business_name} provides exceptional {business_type} services."),
        "cta_text": copy_data.get("cta_text", "Get Started")
    }

    print("[SUCCESS] Professional copy generated!")

    # Color scheme
    vibe = analysis.get("vibe", "modern")
    color_schemes = {
        "luxury": {"primary": "#C9A96E", "secondary": "#1A1A1A", "accent": "#F5F5F5", "text": "#1A1A1A"},
        "modern": {"primary": "#6366F1", "secondary": "#0F172A", "accent": "#F59E0B", "text": "#1E293B"},
        "cozy": {"primary": "#D97706", "secondary": "#78350F", "accent": "#FEF3C7", "text": "#451A03"},
        "energetic": {"primary": "#EF4444", "secondary": "#991B1B", "accent": "#FEE2E2", "text": "#7F1D1D"},
        "elegant": {"primary": "#8B5CF6", "secondary": "#4C1D95", "accent": "#F3E8FF", "text": "#581C87"},
        "minimalist": {"primary": "#000000", "secondary": "#374151", "accent": "#F3F4F6", "text": "#111827"},
        "warm": {"primary": "#D97706", "secondary": "#78350F", "accent": "#FEF3C7", "text": "#451A03"},
        "bold": {"primary": "#EF4444", "secondary": "#991B1B", "accent": "#FEE2E2", "text": "#7F1D1D"},
        "clean": {"primary": "#6366F1", "secondary": "#0F172A", "accent": "#F59E0B", "text": "#1E293B"},
    }
    colors = color_schemes.get(vibe, color_schemes["modern"])

    # Generate HTML with functional features
    html = generate_full_website(analysis, colors, images, features, session)

    # Save
    website_session_id = session.get("website_session_id") or str(uuid.uuid4())
    html_path = f"generated_websites/{website_session_id}.html"
    state_path = f"website_states/{website_session_id}.json"

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    state = {
        "version": 1,
        "created_at": datetime.now().isoformat(),
        "business_description": description,
        "analysis": analysis,
        "colors": colors,
        "images": images,
        "features": features,
        "chat_session": session.get("conversation_history", [])[-5:],  # Last 5 messages
    }

    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

    WEBSITE_STATES[website_session_id] = state

    return {"session_id": website_session_id, "html": html, "analysis": analysis}


def edit_website_from_chat(session, edit_request):
    """Edit an existing website from chat"""
    website_session_id = session["website_session_id"]
    if not website_session_id:
        raise Exception("No website to edit")

    state_path = f"website_states/{website_session_id}.json"
    if not os.path.exists(state_path):
        raise Exception("Website state not found")

    with open(state_path, "r", encoding="utf-8") as f:
        state = json.load(f)

    original_desc = state.get("business_description", "")
    analysis = state.get("analysis", {})
    features = state.get("features", session.get("features", ["contact"]))

    # Create modified description
    modified_desc = (
        f"{original_desc} (Business: {analysis.get('business_name', '')}, "
        f"Type: {analysis.get('business_type', '')}). "
        f"Apply these changes: {edit_request}"
    )

    # Rebuild
    session["description"] = modified_desc
    result = build_website_from_chat(session)

    # Update version
    new_version = state.get("version", 1) + 1
    updated_state = WEBSITE_STATES.get(result["session_id"], {})
    updated_state["version"] = new_version
    WEBSITE_STATES[result["session_id"]] = updated_state

    state_path = f"website_states/{result['session_id']}.json"
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(updated_state, f, indent=2)

    return result


# ============================================================
# SPECIALIZED E-COMMERCE WEBSITE GENERATOR
# ============================================================

def generate_ecommerce_website(analysis, colors, images, features, session):
    """Generate a premium e-commerce website like Zara/H&M/Forever21"""

    name = analysis.get('business_name', 'My Store')
    services = analysis.get('services', [])  # These are product categories
    hero_headline = analysis.get('hero_headline', f'Welcome to {name}')
    hero_subtext = analysis.get('hero_subtext', 'Discover your style')
    tagline = analysis.get('tagline', 'Style Redefined')
    about_text = analysis.get('about_text', f'{name} brings you the latest fashion.')
    cta_text = analysis.get('cta_text', 'Shop Now')
    location = analysis.get('location', {})
    city = location.get('city', 'City')
    country = location.get('country', 'Country')
    website_session_id = session.get("website_session_id") or "preview"

    # Generate realistic product names using AI
    product_name_map = {}
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        cats_str = ", ".join(services[:6])
        resp = model.generate_content(
            f'Generate 3 trendy product names for each of these fashion categories: {cats_str}. '
            f'The brand is "{name}". Make names catchy and realistic like real fashion brands use. '
            f'Return ONLY valid JSON like: {{"category1": ["Name 1", "Name 2", "Name 3"], "category2": [...]}}'
        )
        text = resp.text.strip()
        if '```' in text:
            text = text.split('```')[1].replace('json', '').strip()
        product_name_map = json.loads(text)
    except Exception as e:
        print(f"Product name generation error: {e}")

    # Build collections grid
    collections_html = ""
    for i, category in enumerate(services[:8]):
        img = images['services'][i] if i < len(images['services']) else images['services'][0] if images['services'] else ""
        delay = i * 80
        size_class = "collection-large" if i < 2 else "collection-small"
        collections_html += f'''
        <div class="collection-card {size_class}" data-aos="fade-up" data-aos-delay="{delay}">
            <img src="{img}" alt="{category}">
            <div class="collection-overlay">
                <h3>{category}</h3>
                <span class="collection-count">{random.randint(12, 80)}+ Products</span>
                <a href="#products" class="shop-collection-btn">Shop Now</a>
            </div>
        </div>'''

    # Build product cards with UNIQUE images per product
    products_html = ""
    product_idx = 0
    for cat_idx, category in enumerate(services[:6]):
        # Get unique images for this category's products
        cat_product_imgs = images.get('products', {}).get(category, [])
        if not cat_product_imgs:
            cat_product_imgs = [images['services'][cat_idx]] if cat_idx < len(images['services']) else []

        # Get realistic names or fallback
        cat_names = product_name_map.get(category, [])
        if not cat_names:
            # Try case-insensitive match
            for k, v in product_name_map.items():
                if k.lower() == category.lower():
                    cat_names = v
                    break
        if not cat_names:
            cat_names = [f"{category} Classic", f"{category} Premium", f"{category} Trendy"]

        for j in range(min(3, len(cat_names))):
            # Use a DIFFERENT image for each product
            img = cat_product_imgs[j % len(cat_product_imgs)] if cat_product_imgs else ""
            pname = cat_names[j] if j < len(cat_names) else f"{category} Style {j+1}"
            price = random.randint(499, 2999)
            old_price = price + random.randint(200, 800)
            discount = int((1 - price/old_price) * 100)
            badge_html = f'<span class="product-badge">-{discount}%</span>' if j % 3 != 2 else '<span class="product-badge" style="background:#22c55e">NEW</span>'
            product_idx += 1
            products_html += f'''
            <div class="product-card" data-category="{category.lower()}" data-aos="fade-up" data-aos-delay="{(product_idx % 4) * 60}">
                <div class="product-image">
                    <img src="{img}" alt="{pname}">
                    {badge_html}
                    <div class="product-actions">
                        <button class="product-action-btn" onclick="addToCart(this)" data-name="{pname}" data-price="{price}">Add to Cart</button>
                        <button class="product-action-btn wishlist-btn">♡</button>
                    </div>
                </div>
                <div class="product-info">
                    <span class="product-category">{category}</span>
                    <h4>{pname}</h4>
                    <div class="product-pricing">
                        <span class="current-price">₹{price}</span>
                        <span class="old-price">₹{old_price}</span>
                    </div>
                    <div class="product-sizes">
                        <span class="size">XS</span><span class="size">S</span><span class="size">M</span><span class="size">L</span><span class="size">XL</span>
                    </div>
                </div>
            </div>'''

    # Category filter buttons
    filter_btns = '<button class="filter-btn active" onclick="filterProducts(\'all\', this)">All</button>'
    for cat in services[:6]:
        filter_btns += f'<button class="filter-btn" onclick="filterProducts(\'{cat.lower()}\', this)">{cat}</button>'

    # Gallery / lookbook - use unique gallery images
    gallery_html = ""
    for i, img in enumerate(images.get('gallery', [])[:4]):
        delay = i * 100
        gallery_html += f'''
        <div class="lookbook-item" data-aos="fade-up" data-aos-delay="{delay}">
            <img src="{img}" alt="Lookbook {i+1}">
            <div class="lookbook-overlay">
                <span>View Look</span>
            </div>
        </div>'''

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{name} | {tagline}</title>
    <meta name="description" content="{about_text[:150]}">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;600;700;800;900&family=Inter:wght@300;400;500;600;700;800&family=DM+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link href="https://unpkg.com/aos@2.3.1/dist/aos.css" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        :root {{
            --primary: {colors['primary']};
            --secondary: {colors['secondary']};
            --accent: {colors['accent']};
            --text: {colors['text']};
            --bg: #FAFAF9;
            --card-bg: #FFFFFF;
            --border: #E8E8E5;
        }}
        html {{ scroll-behavior: smooth; }}
        body {{ font-family: 'DM Sans', 'Inter', sans-serif; color: var(--text); line-height: 1.6; background: var(--bg); }}

        /* === ANNOUNCEMENT BAR === */
        .announcement {{ background: var(--secondary); color: white; text-align: center; padding: 0.6rem 1rem; font-size: 0.82rem; font-weight: 500; letter-spacing: 1px; text-transform: uppercase; }}

        /* === NAVBAR === */
        .navbar {{ position: sticky; top: 0; z-index: 1000; background: white; border-bottom: 1px solid var(--border); }}
        .nav-container {{ max-width: 1400px; margin: 0 auto; padding: 0 2rem; display: flex; justify-content: space-between; align-items: center; height: 70px; }}
        .nav-logo {{ font-family: 'Playfair Display', serif; font-size: 1.8rem; font-weight: 800; color: var(--text); text-decoration: none; letter-spacing: -0.5px; }}
        .nav-links {{ display: flex; gap: 2rem; align-items: center; list-style: none; }}
        .nav-links a {{ text-decoration: none; color: var(--text); font-weight: 500; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 1px; transition: color 0.2s; position: relative; }}
        .nav-links a::after {{ content: ''; position: absolute; bottom: -4px; left: 0; width: 0; height: 1.5px; background: var(--primary); transition: width 0.3s; }}
        .nav-links a:hover::after {{ width: 100%; }}
        .nav-links a:hover {{ color: var(--primary); }}
        .nav-icons {{ display: flex; gap: 1.2rem; align-items: center; }}
        .nav-icon {{ background: none; border: none; font-size: 1.2rem; cursor: pointer; color: var(--text); transition: color 0.2s; position: relative; }}
        .nav-icon:hover {{ color: var(--primary); }}
        .cart-badge {{ position: absolute; top: -6px; right: -8px; background: var(--primary); color: white; font-size: 0.65rem; width: 18px; height: 18px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; }}
        .mobile-toggle {{ display: none; background: none; border: none; font-size: 1.5rem; cursor: pointer; }}

        /* === HERO === */
        .hero {{ position: relative; height: 85vh; min-height: 500px; overflow: hidden; display: flex; align-items: center; }}
        .hero-bg {{ position: absolute; inset: 0; }}
        .hero-bg img {{ width: 100%; height: 100%; object-fit: cover; }}
        .hero-bg::after {{ content: ''; position: absolute; inset: 0; background: linear-gradient(90deg, rgba(0,0,0,0.55) 0%, rgba(0,0,0,0.1) 60%); }}
        .hero-content {{ position: relative; z-index: 2; max-width: 1400px; margin: 0 auto; padding: 0 4rem; width: 100%; }}
        .hero-tag {{ display: inline-block; color: rgba(255,255,255,0.9); font-size: 0.85rem; font-weight: 600; text-transform: uppercase; letter-spacing: 3px; margin-bottom: 1.5rem; border-left: 3px solid var(--primary); padding-left: 1rem; }}
        .hero h1 {{ font-family: 'Playfair Display', serif; font-size: clamp(3rem, 6vw, 5.5rem); font-weight: 800; color: white; line-height: 1.08; margin-bottom: 1.5rem; letter-spacing: -1px; max-width: 650px; }}
        .hero p {{ color: rgba(255,255,255,0.85); font-size: 1.15rem; max-width: 480px; margin-bottom: 2.5rem; line-height: 1.7; }}
        .hero-btns {{ display: flex; gap: 1rem; flex-wrap: wrap; }}
        .btn-shop {{ padding: 1rem 2.5rem; background: white; color: var(--text); border: none; font-weight: 700; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 2px; cursor: pointer; transition: all 0.3s; text-decoration: none; }}
        .btn-shop:hover {{ background: var(--primary); color: white; }}
        .btn-outline {{ padding: 1rem 2.5rem; background: transparent; color: white; border: 2px solid white; font-weight: 700; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 2px; cursor: pointer; transition: all 0.3s; text-decoration: none; }}
        .btn-outline:hover {{ background: white; color: var(--text); }}

        /* === MARQUEE === */
        .marquee {{ background: var(--secondary); color: white; padding: 0.8rem 0; overflow: hidden; white-space: nowrap; }}
        .marquee-track {{ display: inline-block; animation: marquee 20s linear infinite; }}
        .marquee-track span {{ display: inline-block; padding: 0 3rem; font-size: 0.85rem; font-weight: 500; text-transform: uppercase; letter-spacing: 2px; }}
        @keyframes marquee {{ 0% {{ transform: translateX(0); }} 100% {{ transform: translateX(-50%); }} }}

        /* === COLLECTIONS === */
        .collections {{ padding: 5rem 2rem; max-width: 1400px; margin: 0 auto; }}
        .section-header {{ text-align: center; margin-bottom: 3.5rem; }}
        .section-header h2 {{ font-family: 'Playfair Display', serif; font-size: clamp(2rem, 4vw, 3rem); font-weight: 700; margin-bottom: 0.8rem; }}
        .section-header p {{ color: #888; font-size: 1rem; max-width: 500px; margin: 0 auto; }}
        .collections-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.5rem; }}
        .collection-card {{ position: relative; border-radius: 12px; overflow: hidden; cursor: pointer; height: 380px; }}
        .collection-large {{ height: 450px; }}
        .collection-card img {{ width: 100%; height: 100%; object-fit: cover; transition: transform 0.6s ease; }}
        .collection-card:hover img {{ transform: scale(1.08); }}
        .collection-overlay {{ position: absolute; inset: 0; background: linear-gradient(180deg, transparent 30%, rgba(0,0,0,0.7) 100%); display: flex; flex-direction: column; justify-content: flex-end; padding: 2rem; }}
        .collection-overlay h3 {{ color: white; font-family: 'Playfair Display', serif; font-size: 1.6rem; font-weight: 700; margin-bottom: 0.3rem; }}
        .collection-count {{ color: rgba(255,255,255,0.7); font-size: 0.85rem; margin-bottom: 1rem; }}
        .shop-collection-btn {{ display: inline-block; padding: 0.6rem 1.5rem; background: white; color: var(--text); text-decoration: none; font-weight: 600; font-size: 0.82rem; text-transform: uppercase; letter-spacing: 1px; transition: all 0.3s; border: none; cursor: pointer; }}
        .shop-collection-btn:hover {{ background: var(--primary); color: white; }}

        /* === PRODUCTS === */
        .products-section {{ padding: 5rem 2rem; background: white; }}
        .products-container {{ max-width: 1400px; margin: 0 auto; }}
        .filter-bar {{ display: flex; gap: 0.8rem; justify-content: center; flex-wrap: wrap; margin-bottom: 3rem; }}
        .filter-btn {{ padding: 0.6rem 1.5rem; border: 1.5px solid var(--border); background: white; color: var(--text); font-family: inherit; font-size: 0.82rem; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; cursor: pointer; border-radius: 30px; transition: all 0.2s; }}
        .filter-btn.active, .filter-btn:hover {{ background: var(--text); color: white; border-color: var(--text); }}
        .products-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 2rem; }}
        .product-card {{ background: var(--card-bg); border-radius: 12px; overflow: hidden; transition: transform 0.3s, box-shadow 0.3s; }}
        .product-card:hover {{ transform: translateY(-5px); box-shadow: 0 15px 40px rgba(0,0,0,0.1); }}
        .product-image {{ position: relative; height: 340px; overflow: hidden; background: #f5f5f3; }}
        .product-image img {{ width: 100%; height: 100%; object-fit: cover; transition: transform 0.5s; }}
        .product-card:hover .product-image img {{ transform: scale(1.05); }}
        .product-badge {{ position: absolute; top: 12px; left: 12px; background: #E53935; color: white; padding: 0.3rem 0.8rem; border-radius: 4px; font-size: 0.75rem; font-weight: 700; }}
        .product-actions {{ position: absolute; bottom: 0; left: 0; right: 0; padding: 1rem; display: flex; gap: 0.5rem; transform: translateY(100%); transition: transform 0.3s; }}
        .product-card:hover .product-actions {{ transform: translateY(0); }}
        .product-action-btn {{ flex: 1; padding: 0.7rem; background: white; border: none; font-family: inherit; font-weight: 600; font-size: 0.82rem; cursor: pointer; transition: all 0.2s; text-transform: uppercase; letter-spacing: 0.5px; }}
        .product-action-btn:hover {{ background: var(--text); color: white; }}
        .wishlist-btn {{ flex: 0 0 44px; font-size: 1.1rem; }}
        .product-info {{ padding: 1.2rem 1rem; }}
        .product-category {{ font-size: 0.75rem; color: #999; text-transform: uppercase; letter-spacing: 1px; }}
        .product-info h4 {{ font-size: 1rem; font-weight: 600; margin: 0.3rem 0 0.5rem; }}
        .product-pricing {{ display: flex; gap: 0.8rem; align-items: center; }}
        .current-price {{ font-weight: 800; font-size: 1.1rem; color: var(--text); }}
        .old-price {{ font-size: 0.9rem; color: #bbb; text-decoration: line-through; }}
        .product-sizes {{ display: flex; gap: 0.4rem; margin-top: 0.8rem; }}
        .size {{ width: 32px; height: 28px; display: flex; align-items: center; justify-content: center; border: 1px solid var(--border); border-radius: 4px; font-size: 0.7rem; font-weight: 600; color: #666; cursor: pointer; transition: all 0.2s; }}
        .size:hover {{ border-color: var(--text); color: var(--text); }}

        /* === LOOKBOOK === */
        .lookbook {{ padding: 5rem 2rem; max-width: 1400px; margin: 0 auto; }}
        .lookbook-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: 1.5rem; }}
        .lookbook-item {{ position: relative; height: 450px; border-radius: 12px; overflow: hidden; cursor: pointer; }}
        .lookbook-item img {{ width: 100%; height: 100%; object-fit: cover; transition: transform 0.6s; }}
        .lookbook-item:hover img {{ transform: scale(1.06); }}
        .lookbook-overlay {{ position: absolute; inset: 0; background: rgba(0,0,0,0.3); display: flex; align-items: center; justify-content: center; opacity: 0; transition: opacity 0.3s; }}
        .lookbook-item:hover .lookbook-overlay {{ opacity: 1; }}
        .lookbook-overlay span {{ background: white; color: var(--text); padding: 0.8rem 2rem; font-weight: 700; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 2px; }}

        /* === FEATURES STRIP === */
        .features-strip {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 0; border-top: 1px solid var(--border); border-bottom: 1px solid var(--border); }}
        .feature-item {{ text-align: center; padding: 2.5rem 1.5rem; border-right: 1px solid var(--border); }}
        .feature-item:last-child {{ border-right: none; }}
        .feature-icon {{ font-size: 1.8rem; margin-bottom: 0.8rem; }}
        .feature-item h4 {{ font-size: 0.9rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 0.3rem; }}
        .feature-item p {{ font-size: 0.82rem; color: #888; }}

        /* === NEWSLETTER === */
        .newsletter {{ padding: 5rem 2rem; background: var(--secondary); color: white; text-align: center; }}
        .newsletter h2 {{ font-family: 'Playfair Display', serif; font-size: clamp(1.8rem, 3vw, 2.5rem); margin-bottom: 0.8rem; }}
        .newsletter p {{ color: rgba(255,255,255,0.7); margin-bottom: 2rem; max-width: 450px; margin-left: auto; margin-right: auto; }}
        .newsletter-form {{ display: flex; gap: 0; max-width: 500px; margin: 0 auto; }}
        .newsletter-form input {{ flex: 1; padding: 1rem 1.5rem; border: none; font-family: inherit; font-size: 0.95rem; outline: none; }}
        .newsletter-form button {{ padding: 1rem 2rem; background: var(--primary); color: white; border: none; font-family: inherit; font-weight: 700; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px; cursor: pointer; transition: background 0.3s; }}
        .newsletter-form button:hover {{ background: white; color: var(--text); }}

        /* === FOOTER === */
        .footer {{ padding: 4rem 2rem 2rem; background: #0a0a0a; color: white; }}
        .footer-grid {{ max-width: 1400px; margin: 0 auto; display: grid; grid-template-columns: 2fr repeat(3, 1fr); gap: 3rem; margin-bottom: 3rem; }}
        .footer-brand {{ font-family: 'Playfair Display', serif; font-size: 1.6rem; font-weight: 800; margin-bottom: 1rem; }}
        .footer-section h4 {{ font-size: 0.85rem; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 1.2rem; font-weight: 700; }}
        .footer-section p, .footer-section a {{ display: block; color: rgba(255,255,255,0.6); text-decoration: none; margin-bottom: 0.6rem; font-size: 0.9rem; transition: color 0.2s; }}
        .footer-section a:hover {{ color: white; }}
        .footer-bottom {{ max-width: 1400px; margin: 0 auto; padding-top: 2rem; border-top: 1px solid rgba(255,255,255,0.1); display: flex; justify-content: space-between; align-items: center; font-size: 0.82rem; color: rgba(255,255,255,0.4); }}
        .social-links {{ display: flex; gap: 1rem; }}
        .social-links a {{ color: rgba(255,255,255,0.5); text-decoration: none; transition: color 0.2s; }}
        .social-links a:hover {{ color: white; }}

        /* === CART SIDEBAR === */
        .cart-sidebar {{ position: fixed; top: 0; right: -450px; width: 420px; height: 100vh; background: white; box-shadow: -10px 0 50px rgba(0,0,0,0.15); z-index: 10001; transition: right 0.35s ease; display: flex; flex-direction: column; }}
        .cart-sidebar.open {{ right: 0; }}
        .cart-overlay {{ position: fixed; inset: 0; background: rgba(0,0,0,0.4); z-index: 10000; display: none; }}
        .cart-overlay.open {{ display: block; }}
        .cart-header {{ display: flex; justify-content: space-between; align-items: center; padding: 1.8rem 2rem; border-bottom: 1px solid #eee; }}
        .cart-header h3 {{ font-family: 'Playfair Display', serif; font-size: 1.3rem; }}
        .cart-close {{ background: none; border: none; font-size: 1.5rem; cursor: pointer; color: #999; }}
        .cart-items {{ flex: 1; overflow-y: auto; padding: 1.5rem 2rem; }}
        .cart-item {{ display: flex; justify-content: space-between; align-items: center; padding: 1rem 0; border-bottom: 1px solid #f0f0f0; }}
        .cart-item strong {{ font-size: 0.95rem; }}
        .cart-item span {{ font-size: 0.85rem; color: #888; }}
        .cart-item-actions {{ display: flex; align-items: center; gap: 0.5rem; }}
        .cart-item-actions button {{ width: 30px; height: 30px; border: 1px solid #e0e0e0; border-radius: 50%; background: white; cursor: pointer; font-weight: 600; font-size: 0.9rem; transition: all 0.2s; }}
        .cart-item-actions button:hover {{ background: var(--text); color: white; border-color: var(--text); }}
        .cart-footer {{ padding: 1.5rem 2rem; border-top: 1px solid #eee; }}
        .cart-total {{ font-size: 1.2rem; font-weight: 800; margin-bottom: 1rem; display: flex; justify-content: space-between; }}
        .checkout-btn {{ width: 100%; padding: 1rem; background: var(--text); color: white; border: none; font-family: inherit; font-size: 0.9rem; font-weight: 700; text-transform: uppercase; letter-spacing: 2px; cursor: pointer; transition: background 0.3s; }}
        .checkout-btn:hover {{ background: var(--primary); }}
        .cart-empty {{ text-align: center; color: #bbb; padding: 3rem 1rem; font-size: 0.95rem; }}

        /* === CHECKOUT MODAL === */
        .checkout-modal {{ position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 10002; display: none; align-items: center; justify-content: center; }}
        .checkout-modal.open {{ display: flex; }}
        .checkout-content {{ background: white; border-radius: 16px; padding: 2.5rem; width: 90%; max-width: 500px; max-height: 90vh; overflow-y: auto; position: relative; }}
        .checkout-content h3 {{ font-family: 'Playfair Display', serif; font-size: 1.4rem; margin-bottom: 1.5rem; }}
        .modal-close {{ position: absolute; top: 1.2rem; right: 1.5rem; background: none; border: none; font-size: 1.3rem; cursor: pointer; color: #999; }}
        .checkout-content input, .checkout-content textarea {{ width: 100%; padding: 0.9rem 1rem; border: 1.5px solid #e0e0e0; border-radius: 8px; margin-bottom: 0.8rem; font-family: inherit; font-size: 0.9rem; }}
        .checkout-content input:focus, .checkout-content textarea:focus {{ outline: none; border-color: var(--text); }}
        .checkout-content .submit-btn {{ width: 100%; padding: 1rem; background: var(--text); color: white; border: none; font-family: inherit; font-size: 0.9rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; cursor: pointer; border-radius: 8px; margin-top: 0.5rem; }}
        .checkout-content .submit-btn:hover {{ background: var(--primary); }}
        .form-message {{ margin-top: 0.5rem; }}

        /* === CONTACT === */
        .contact-section {{ padding: 5rem 2rem; background: #f8f8f6; }}
        .contact-container {{ max-width: 600px; margin: 0 auto; text-align: center; }}
        .contact-form {{ display: flex; flex-direction: column; gap: 1rem; margin-top: 2rem; }}
        .contact-form input, .contact-form textarea {{ padding: 1rem 1.2rem; border: 1.5px solid var(--border); border-radius: 8px; font-family: inherit; font-size: 0.95rem; background: white; }}
        .contact-form input:focus, .contact-form textarea:focus {{ outline: none; border-color: var(--text); }}
        .contact-form .submit-btn {{ padding: 1rem 3rem; background: var(--text); color: white; border: none; font-family: inherit; font-weight: 700; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 2px; cursor: pointer; border-radius: 8px; transition: background 0.3s; align-self: center; }}
        .contact-form .submit-btn:hover {{ background: var(--primary); }}

        /* === MOBILE NAV === */
        .nav-links.mobile-open {{
            display: flex !important;
            flex-direction: column;
            position: absolute;
            top: 70px;
            left: 0;
            right: 0;
            background: white;
            padding: 1.5rem 2rem;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            gap: 1rem;
            z-index: 999;
        }}

        /* === RESPONSIVE === */
        @media (max-width: 968px) {{
            .nav-links {{ display: none; }}
            .mobile-toggle {{ display: block; }}
            .hero-content {{ padding: 0 2rem; }}
            .footer-grid {{ grid-template-columns: 1fr 1fr; }}
            .lookbook-grid {{ grid-template-columns: 1fr 1fr; }}
            .about-grid {{ grid-template-columns: 1fr !important; }}
            .about-grid > div:first-child img {{ height: 300px !important; }}
        }}
        @media (max-width: 640px) {{
            .hero {{ height: 70vh; }}
            .hero h1 {{ font-size: 2.2rem; }}
            .hero p {{ font-size: 0.95rem; }}
            .products-grid {{ grid-template-columns: repeat(2, 1fr); gap: 0.8rem; }}
            .product-image {{ height: 220px; }}
            .product-info {{ padding: 0.8rem 0.6rem; }}
            .product-info h4 {{ font-size: 0.85rem; }}
            .product-sizes {{ display: none; }}
            .collections-grid {{ grid-template-columns: 1fr 1fr; }}
            .collection-card, .collection-large {{ height: 250px; }}
            .collection-overlay h3 {{ font-size: 1.1rem; }}
            .footer-grid {{ grid-template-columns: 1fr; }}
            .newsletter-form {{ flex-direction: column; }}
            .cart-sidebar {{ width: 100%; }}
            .features-strip {{ grid-template-columns: 1fr 1fr; }}
            .feature-item {{ border-right: none; border-bottom: 1px solid var(--border); }}
            .lookbook-grid {{ grid-template-columns: 1fr; }}
            .lookbook-item {{ height: 300px; }}
            .section-header h2 {{ font-size: 1.8rem; }}
            .filter-bar {{ gap: 0.4rem; }}
            .filter-btn {{ padding: 0.4rem 1rem; font-size: 0.75rem; }}
        }}
    </style>
</head>
<body>
    <!-- ANNOUNCEMENT -->
    <div class="announcement">Free Shipping on Orders Above ₹999 | Use Code FIRST10 for 10% Off</div>

    <!-- NAVBAR -->
    <nav class="navbar">
        <div class="nav-container">
            <button class="mobile-toggle" onclick="document.querySelector('.nav-links').classList.toggle('mobile-open')">☰</button>
            <a href="#" class="nav-logo">{name}</a>
            <ul class="nav-links">
                <li><a href="#collections">Collections</a></li>
                <li><a href="#products">Shop</a></li>
                <li><a href="#lookbook">Lookbook</a></li>
                <li><a href="#about">About</a></li>
                <li><a href="#contact">Contact</a></li>
            </ul>
            <div class="nav-icons">
                <button class="nav-icon" onclick="toggleCart()">🛒 <span class="cart-badge" id="cartBadge" style="display:none">0</span></button>
            </div>
        </div>
    </nav>

    <!-- HERO -->
    <section class="hero">
        <div class="hero-bg">
            <img src="{images['hero']}" alt="{name}">
        </div>
        <div class="hero-content">
            <span class="hero-tag">{tagline}</span>
            <h1>{hero_headline}</h1>
            <p>{hero_subtext}</p>
            <div class="hero-btns">
                <a href="#products" class="btn-shop">{cta_text}</a>
                <a href="#collections" class="btn-outline">View Collections</a>
            </div>
        </div>
    </section>

    <!-- MARQUEE -->
    <div class="marquee">
        <div class="marquee-track">
            <span>New Arrivals</span><span>Trending Now</span><span>Free Returns</span><span>COD Available</span><span>Exclusive Online Deals</span><span>Pan India Shipping</span>
            <span>New Arrivals</span><span>Trending Now</span><span>Free Returns</span><span>COD Available</span><span>Exclusive Online Deals</span><span>Pan India Shipping</span>
        </div>
    </div>

    <!-- COLLECTIONS -->
    <section class="collections" id="collections">
        <div class="section-header" data-aos="fade-up">
            <h2>Shop by Collection</h2>
            <p>Curated categories for every mood and occasion</p>
        </div>
        <div class="collections-grid">{collections_html}</div>
    </section>

    <!-- PRODUCTS -->
    <section class="products-section" id="products">
        <div class="products-container">
            <div class="section-header" data-aos="fade-up">
                <h2>Our Bestsellers</h2>
                <p>The pieces our customers can't stop wearing</p>
            </div>
            <div class="filter-bar" data-aos="fade-up">{filter_btns}</div>
            <div class="products-grid" id="productsGrid">{products_html}</div>
        </div>
    </section>

    <!-- LOOKBOOK -->
    <section class="lookbook" id="lookbook">
        <div class="section-header" data-aos="fade-up">
            <h2>Lookbook</h2>
            <p>Get inspired by our latest styled looks</p>
        </div>
        <div class="lookbook-grid">{gallery_html}</div>
    </section>

    <!-- FEATURES -->
    <div class="features-strip">
        <div class="feature-item" data-aos="fade-up">
            <div class="feature-icon">🚚</div>
            <h4>Free Shipping</h4>
            <p>On orders above ₹999</p>
        </div>
        <div class="feature-item" data-aos="fade-up" data-aos-delay="100">
            <div class="feature-icon">↩️</div>
            <h4>Easy Returns</h4>
            <p>7-day return policy</p>
        </div>
        <div class="feature-item" data-aos="fade-up" data-aos-delay="200">
            <div class="feature-icon">💳</div>
            <h4>Secure Payment</h4>
            <p>100% secure checkout</p>
        </div>
        <div class="feature-item" data-aos="fade-up" data-aos-delay="300">
            <div class="feature-icon">💬</div>
            <h4>24/7 Support</h4>
            <p>Chat or call anytime</p>
        </div>
    </div>

    <!-- ABOUT -->
    <section style="padding:5rem 2rem;max-width:1400px;margin:0 auto" id="about">
        <div class="about-grid" style="display:grid;grid-template-columns:1fr 1fr;gap:4rem;align-items:center">
            <div data-aos="fade-right">
                <img src="{images['about']}" alt="About {name}" style="width:100%;height:450px;object-fit:cover;border-radius:12px;">
            </div>
            <div data-aos="fade-left">
                <h2 style="font-family:'Playfair Display',serif;font-size:2.5rem;margin-bottom:1.5rem">About {name}</h2>
                <p style="color:#666;line-height:1.9;margin-bottom:1rem;font-size:1.05rem">{about_text}</p>
                <p style="color:#666;line-height:1.9;font-size:1.05rem">Based in {city}, {country} — shipping across the country with love and care.</p>
            </div>
        </div>
    </section>

    <!-- CONTACT -->
    <section class="contact-section" id="contact">
        <div class="contact-container">
            <div class="section-header" data-aos="fade-up">
                <h2>Get in Touch</h2>
                <p>We'd love to hear from you</p>
            </div>
            <form class="contact-form" id="contactForm" data-aos="fade-up">
                <input type="text" name="name" placeholder="Your Name" required>
                <input type="email" name="email" placeholder="Email Address" required>
                <input type="tel" name="phone" placeholder="Phone Number">
                <textarea name="message" placeholder="Your message..." required rows="4"></textarea>
                <button type="submit" class="submit-btn">Send Message</button>
                <div class="form-message" id="contactMessage"></div>
            </form>
        </div>
    </section>

    <!-- NEWSLETTER -->
    <section class="newsletter">
        <h2 data-aos="fade-up">Stay in the Loop</h2>
        <p data-aos="fade-up" data-aos-delay="100">Subscribe for exclusive drops, styling tips & 15% off your first order</p>
        <form class="newsletter-form" data-aos="fade-up" data-aos-delay="200" onsubmit="event.preventDefault(); this.innerHTML='<p style=\\'padding:1rem;color:white\\'>✓ You\\'re in! Check your inbox.</p>'">
            <input type="email" placeholder="Enter your email" required>
            <button type="submit">Subscribe</button>
        </form>
    </section>

    <!-- FOOTER -->
    <footer class="footer">
        <div class="footer-grid">
            <div class="footer-section">
                <div class="footer-brand">{name}</div>
                <p>{tagline}</p>
                <p style="margin-top:1rem">{city}, {country}</p>
            </div>
            <div class="footer-section">
                <h4>Shop</h4>
                {''.join(f'<a href="#products">{s}</a>' for s in services[:5])}
            </div>
            <div class="footer-section">
                <h4>Help</h4>
                <a href="#contact">Contact Us</a>
                <a href="#">Shipping & Returns</a>
                <a href="#">Size Guide</a>
                <a href="#">FAQ</a>
            </div>
            <div class="footer-section">
                <h4>Contact</h4>
                <p>info@{name.lower().replace(' ', '')}.com</p>
                <p>+91 98765 43210</p>
            </div>
        </div>
        <div class="footer-bottom">
            <p>© 2025 {name}. All rights reserved.</p>
            <div class="social-links">
                <a href="#">Instagram</a>
                <a href="#">Facebook</a>
                <a href="#">Pinterest</a>
            </div>
        </div>
    </footer>

    <!-- CART SIDEBAR -->
    <div class="cart-overlay" id="cartOverlay" onclick="toggleCart()"></div>
    <div class="cart-sidebar" id="cartSidebar">
        <div class="cart-header">
            <h3>Shopping Bag</h3>
            <button class="cart-close" onclick="toggleCart()">✕</button>
        </div>
        <div class="cart-items" id="cartItems">
            <p class="cart-empty">Your bag is empty</p>
        </div>
        <div class="cart-footer">
            <div class="cart-total"><span>Total</span> <span>₹<span id="cartTotal">0</span></span></div>
            <button class="checkout-btn" onclick="showCheckout()">Checkout</button>
        </div>
    </div>

    <!-- CHECKOUT MODAL -->
    <div class="checkout-modal" id="checkoutModal">
        <div class="checkout-content">
            <h3>Checkout</h3>
            <button class="modal-close" onclick="closeCheckout()">✕</button>
            <form id="orderForm" onsubmit="submitOrder(event)">
                <input type="text" name="name" placeholder="Full Name" required>
                <input type="email" name="email" placeholder="Email" required>
                <input type="tel" name="phone" placeholder="Phone" required>
                <textarea name="address" placeholder="Delivery Address" required rows="3"></textarea>
                <textarea name="notes" placeholder="Order notes (optional)" rows="2"></textarea>
                <div id="orderSummary" style="padding:1rem;background:#f8f8f6;border-radius:8px;margin:0.5rem 0;font-size:0.9rem"></div>
                <button type="submit" class="submit-btn">Place Order</button>
                <div class="form-message" id="orderMessage"></div>
            </form>
        </div>
    </div>

    <script src="https://unpkg.com/aos@2.3.1/dist/aos.js"></script>
    <script>
        AOS.init({{ duration: 700, easing: 'ease-out', once: true, offset: 80 }});

        const API = window.location.origin || 'http://localhost:8000';
        const SESSION = '{website_session_id}';

        // Filter products
        function filterProducts(category, btn) {{
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            document.querySelectorAll('.product-card').forEach(card => {{
                if (category === 'all' || card.dataset.category === category) {{
                    card.style.display = '';
                }} else {{
                    card.style.display = 'none';
                }}
            }});
        }}

        // Cart
        let cart = [];
        function addToCart(btn) {{
            const name = btn.dataset.name;
            const price = parseFloat(btn.dataset.price);
            const existing = cart.find(i => i.name === name);
            if (existing) {{ existing.qty++; }}
            else {{ cart.push({{ name, price, qty: 1 }}); }}
            updateCart();
            btn.textContent = '✓ Added';
            setTimeout(() => {{ btn.textContent = 'Add to Cart'; }}, 1200);
        }}

        function updateCart() {{
            const itemsEl = document.getElementById('cartItems');
            const totalEl = document.getElementById('cartTotal');
            const badge = document.getElementById('cartBadge');
            const count = cart.reduce((s, i) => s + i.qty, 0);
            badge.style.display = count > 0 ? 'flex' : 'none';
            badge.textContent = count;

            if (cart.length === 0) {{
                itemsEl.innerHTML = '<p class="cart-empty">Your bag is empty</p>';
                totalEl.textContent = '0';
            }} else {{
                let total = 0;
                itemsEl.innerHTML = cart.map((item, idx) => {{
                    total += item.price * item.qty;
                    return `<div class="cart-item"><div><strong>${{item.name}}</strong><br><span>₹${{item.price}} × ${{item.qty}}</span></div><div class="cart-item-actions"><button onclick="changeQty(${{idx}},-1)">−</button><span>${{item.qty}}</span><button onclick="changeQty(${{idx}},1)">+</button><button onclick="removeItem(${{idx}})" style="color:#e53935;border-color:#e53935">✕</button></div></div>`;
                }}).join('');
                totalEl.textContent = total.toLocaleString();
            }}
        }}

        function changeQty(idx, d) {{ cart[idx].qty += d; if (cart[idx].qty <= 0) cart.splice(idx, 1); updateCart(); }}
        function removeItem(idx) {{ cart.splice(idx, 1); updateCart(); }}

        function toggleCart() {{
            document.getElementById('cartSidebar').classList.toggle('open');
            document.getElementById('cartOverlay').classList.toggle('open');
        }}

        function showCheckout() {{
            if (!cart.length) return;
            const summary = cart.map(i => `${{i.name}} ×${{i.qty}} = ₹${{(i.price*i.qty).toLocaleString()}}`).join('<br>');
            const total = cart.reduce((s, i) => s + i.price * i.qty, 0);
            document.getElementById('orderSummary').innerHTML = `${{summary}}<br><strong style="margin-top:0.5rem;display:block">Total: ₹${{total.toLocaleString()}}</strong>`;
            document.getElementById('checkoutModal').classList.add('open');
            toggleCart();
        }}

        function closeCheckout() {{ document.getElementById('checkoutModal').classList.remove('open'); }}

        async function submitOrder(e) {{
            e.preventDefault();
            const form = e.target;
            const fd = Object.fromEntries(new FormData(form));
            fd.items = cart.map(i => ({{name: i.name, price: i.price, qty: i.qty}}));
            const msg = document.getElementById('orderMessage');
            try {{
                const res = await fetch(`${{API}}/api/site/${{SESSION}}/order`, {{
                    method: 'POST', headers: {{'Content-Type': 'application/json'}}, body: JSON.stringify(fd)
                }});
                if (res.ok) {{
                    msg.innerHTML = '<div style="color:#22c55e;padding:1rem;text-align:center">✅ Order placed! We will contact you shortly.</div>';
                    cart = []; updateCart(); form.reset();
                    setTimeout(closeCheckout, 3000);
                }} else throw new Error();
            }} catch {{ msg.innerHTML = '<div style="color:#e53935;padding:1rem;text-align:center">Could not place order. Try again.</div>'; }}
        }}

        // Contact form
        document.getElementById('contactForm')?.addEventListener('submit', async (e) => {{
            e.preventDefault();
            const form = e.target;
            const data = Object.fromEntries(new FormData(form));
            const msg = document.getElementById('contactMessage');
            try {{
                const res = await fetch(`${{API}}/api/site/${{SESSION}}/contact`, {{
                    method: 'POST', headers: {{'Content-Type': 'application/json'}}, body: JSON.stringify(data)
                }});
                if (res.ok) {{
                    msg.innerHTML = '<div style="color:#22c55e;padding:1rem;background:#f0fdf4;border-radius:8px;margin-top:1rem;text-align:center">✅ Message sent! We\\'ll get back to you soon.</div>';
                    form.reset();
                }} else throw new Error();
            }} catch {{ msg.innerHTML = '<div style="color:#e53935;padding:1rem">Could not send message.</div>'; }}
        }});
    </script>
</body>
</html>'''

    return html


def generate_restaurant_website(analysis, colors, images, features, session):
    """Placeholder - falls back to generic template for now"""
    # Will be specialized later, use generic for now
    return None


# ============================================================
# FULL WEBSITE GENERATOR (with functional features)
# ============================================================

def generate_full_website(analysis, colors, images, features, session):
    """Generate a complete, functional website with booking/ordering/contact"""

    name = analysis.get('business_name', 'My Business')
    business_type = analysis.get('business_type', 'business')
    services = analysis.get('services', [])
    hero_headline = analysis.get('hero_headline', f'Welcome to {name}')
    hero_subtext = analysis.get('hero_subtext', 'Quality service you can trust')
    tagline = analysis.get('tagline', 'Excellence in Every Detail')
    about_text = analysis.get('about_text', f'{name} provides exceptional services.')
    cta_text = analysis.get('cta_text', 'Get Started')
    location = analysis.get('location', {})
    city = location.get('city', 'City')
    country = location.get('country', 'Country')

    website_session_id = session.get("website_session_id") or "preview"

    # Use specialized template for shop/e-commerce
    if business_type in ["shop", "store", "ecommerce", "boutique"]:
        return generate_ecommerce_website(analysis, colors, images, features, session)

    # Build service cards HTML
    service_cards = ""
    for i, service in enumerate(services[:6]):
        img = images['services'][i] if i < len(images['services']) else images['services'][0] if images['services'] else ""
        delay = i * 100
        service_cards += f'''
        <div class="service-card" data-aos="fade-up" data-aos-delay="{delay}">
            <div class="service-image-wrapper">
                <img src="{img}" alt="{service}" class="service-image">
                <div class="service-overlay"></div>
            </div>
            <div class="service-content">
                <h3>{service}</h3>
                <p>Professional {service.lower()} delivered with excellence and care</p>
                <a href="#contact" class="service-link">Learn More →</a>
            </div>
        </div>'''

    # Build gallery HTML
    gallery_items = ""
    for i, img in enumerate(images.get('gallery', [])):
        delay = i * 150
        gallery_items += f'''
        <div class="gallery-item" data-aos="zoom-in" data-aos-delay="{delay}">
            <img src="{img}" alt="Gallery {i+1}">
            <div class="gallery-overlay"><span>🔍</span></div>
        </div>'''

    # Build booking section if needed
    booking_section = ""
    if "booking" in features:
        booking_section = f'''
    <section class="booking-section" id="booking">
        <div class="section-container">
            <h2 class="section-title" data-aos="fade-up">Book an Appointment</h2>
            <p class="section-subtitle" data-aos="fade-up" data-aos-delay="100">Choose your service and preferred time</p>
            <form class="booking-form" id="bookingForm" data-aos="fade-up" data-aos-delay="200">
                <div class="form-grid">
                    <input type="text" name="name" placeholder="Your Name" required>
                    <input type="email" name="email" placeholder="Email Address" required>
                    <input type="tel" name="phone" placeholder="Phone Number" required>
                    <select name="service" required>
                        <option value="">Select Service</option>
                        {''.join(f'<option value="{s}">{s}</option>' for s in services)}
                    </select>
                    <input type="date" name="date" required>
                    <select name="time" required>
                        <option value="">Select Time</option>
                        <option value="09:00">9:00 AM</option>
                        <option value="10:00">10:00 AM</option>
                        <option value="11:00">11:00 AM</option>
                        <option value="12:00">12:00 PM</option>
                        <option value="13:00">1:00 PM</option>
                        <option value="14:00">2:00 PM</option>
                        <option value="15:00">3:00 PM</option>
                        <option value="16:00">4:00 PM</option>
                        <option value="17:00">5:00 PM</option>
                    </select>
                </div>
                <textarea name="notes" placeholder="Any special requests?" rows="3"></textarea>
                <button type="submit" class="submit-btn">Book Now</button>
                <div class="form-message" id="bookingMessage"></div>
            </form>
        </div>
    </section>'''

    # Build ordering/menu section if needed
    menu_section = ""
    if "menu" in features or "ordering" in features:
        menu_items_html = ""
        for i, service in enumerate(services[:8]):
            price = random.randint(5, 50) if business_type in ["restaurant", "cafe"] else random.randint(20, 200)
            menu_items_html += f'''
            <div class="menu-item" data-aos="fade-up" data-aos-delay="{i*80}">
                <img src="{images['services'][i] if i < len(images['services']) else images['services'][0] if images['services'] else ''}" alt="{service}">
                <div class="menu-item-content">
                    <h4>{service}</h4>
                    <p>Premium quality {service.lower()}</p>
                    <div class="menu-item-footer">
                        <span class="price">${price}</span>
                        {"<button class='add-to-cart-btn' onclick='addToCart(this)' data-name='" + service + "' data-price='" + str(price) + "'>Add to Cart</button>" if "ordering" in features else ""}
                    </div>
                </div>
            </div>'''

        menu_section = f'''
    <section class="menu-section" id="menu">
        <div class="section-container">
            <h2 class="section-title" data-aos="fade-up">{"Our Menu" if business_type in ["restaurant", "cafe"] else "Our Products"}</h2>
            <p class="section-subtitle" data-aos="fade-up" data-aos-delay="100">{tagline}</p>
            <div class="menu-grid">{menu_items_html}</div>
        </div>
    </section>'''

    # Cart section for ordering
    cart_section = ""
    if "ordering" in features:
        cart_section = f'''
    <div class="cart-sidebar" id="cartSidebar">
        <div class="cart-header">
            <h3>Your Cart</h3>
            <button class="cart-close" onclick="toggleCart()">✕</button>
        </div>
        <div class="cart-items" id="cartItems">
            <p class="cart-empty">Your cart is empty</p>
        </div>
        <div class="cart-footer">
            <div class="cart-total">Total: $<span id="cartTotal">0</span></div>
            <button class="checkout-btn" onclick="showCheckout()">Proceed to Checkout</button>
        </div>
    </div>
    <button class="cart-fab" id="cartFab" onclick="toggleCart()" style="display:none">
        🛒 <span id="cartCount">0</span>
    </button>

    <div class="checkout-modal" id="checkoutModal">
        <div class="checkout-content">
            <h3>Checkout</h3>
            <button class="modal-close" onclick="closeCheckout()">✕</button>
            <form id="orderForm" onsubmit="submitOrder(event)">
                <input type="text" name="name" placeholder="Your Name" required>
                <input type="email" name="email" placeholder="Email" required>
                <input type="tel" name="phone" placeholder="Phone" required>
                <textarea name="address" placeholder="Delivery Address" required></textarea>
                <textarea name="notes" placeholder="Special instructions (optional)"></textarea>
                <div class="order-summary" id="orderSummary"></div>
                <button type="submit" class="submit-btn">Place Order</button>
                <div class="form-message" id="orderMessage"></div>
            </form>
        </div>
    </div>'''

    # Contact section
    contact_section = f'''
    <section class="contact" id="contact">
        <div class="section-container">
            <h2 data-aos="fade-up">Get In Touch</h2>
            <p data-aos="fade-up" data-aos-delay="100">We'd love to hear from you!</p>
            <form class="contact-form" id="contactForm" data-aos="fade-up" data-aos-delay="200">
                <input type="text" name="name" placeholder="Your Name" required>
                <input type="email" name="email" placeholder="Email Address" required>
                <input type="tel" name="phone" placeholder="Phone Number">
                <textarea name="message" placeholder="Your message..." required rows="4"></textarea>
                <button type="submit" class="submit-btn">{cta_text}</button>
                <div class="form-message" id="contactMessage"></div>
            </form>
        </div>
    </section>'''

    # Navigation links
    nav_links = '<a href="#home">Home</a>'
    nav_links += '<a href="#services">Services</a>'
    if menu_section:
        nav_links += '<a href="#menu">Menu</a>'
    if booking_section:
        nav_links += '<a href="#booking">Book Now</a>'
    nav_links += '<a href="#about">About</a>'
    nav_links += '<a href="#gallery">Gallery</a>'
    nav_links += f'<a href="#contact" class="cta-btn">{cta_text}</a>'

    # JavaScript for functional features
    js_code = f'''
    <script>
        // AOS Init
        AOS.init({{ duration: 800, easing: 'ease-out-cubic', once: true, offset: 100 }});

        // Navbar scroll
        window.addEventListener('scroll', () => {{
            const nav = document.getElementById('navbar');
            if (window.scrollY > 50) nav?.classList.add('scrolled');
            else nav?.classList.remove('scrolled');
        }});

        // Mobile menu
        function toggleMenu() {{
            document.querySelector('.hamburger').classList.toggle('active');
            document.getElementById('navLinks').classList.toggle('active');
        }}
        document.querySelectorAll('.nav-links a').forEach(link => {{
            link.addEventListener('click', () => {{
                document.getElementById('navLinks').classList.remove('active');
                document.querySelector('.hamburger')?.classList.remove('active');
            }});
        }});

        const API = window.location.origin || 'http://localhost:8000';
        const SESSION = '{website_session_id}';
    '''

    # Booking JS
    if "booking" in features:
        js_code += '''
        // Booking
        document.getElementById('bookingForm')?.addEventListener('submit', async (e) => {
            e.preventDefault();
            const form = e.target;
            const data = Object.fromEntries(new FormData(form));
            const msgEl = document.getElementById('bookingMessage');
            try {
                const res = await fetch(`${API}/api/site/${SESSION}/booking`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                if (res.ok) {
                    msgEl.innerHTML = '<div style="color:#22c55e;padding:1rem;background:rgba(34,197,94,0.1);border-radius:10px;margin-top:1rem;">✅ Booking confirmed! We\\'ll contact you shortly.</div>';
                    form.reset();
                } else {
                    throw new Error('Failed');
                }
            } catch (err) {
                msgEl.innerHTML = '<div style="color:#ef4444;padding:1rem;background:rgba(239,68,68,0.1);border-radius:10px;margin-top:1rem;">❌ Could not submit booking. Please try again.</div>';
            }
        });
        '''

    # Ordering/Cart JS
    if "ordering" in features:
        js_code += '''
        // Cart
        let cart = [];

        function addToCart(btn) {
            const name = btn.dataset.name;
            const price = parseFloat(btn.dataset.price);
            const existing = cart.find(i => i.name === name);
            if (existing) { existing.qty++; }
            else { cart.push({ name, price, qty: 1 }); }
            updateCart();
            btn.textContent = '✓ Added';
            setTimeout(() => { btn.textContent = 'Add to Cart'; }, 1000);
        }

        function updateCart() {
            const itemsEl = document.getElementById('cartItems');
            const totalEl = document.getElementById('cartTotal');
            const countEl = document.getElementById('cartCount');
            const fab = document.getElementById('cartFab');

            if (cart.length === 0) {
                itemsEl.innerHTML = '<p class="cart-empty">Your cart is empty</p>';
                fab.style.display = 'none';
            } else {
                fab.style.display = 'flex';
                countEl.textContent = cart.reduce((sum, i) => sum + i.qty, 0);
                let total = 0;
                itemsEl.innerHTML = cart.map((item, idx) => {
                    total += item.price * item.qty;
                    return `<div class="cart-item">
                        <div>
                            <strong>${item.name}</strong>
                            <span>$${item.price} x ${item.qty}</span>
                        </div>
                        <div class="cart-item-actions">
                            <button onclick="changeQty(${idx}, -1)">-</button>
                            <span>${item.qty}</span>
                            <button onclick="changeQty(${idx}, 1)">+</button>
                            <button onclick="removeFromCart(${idx})" style="color:#ef4444">✕</button>
                        </div>
                    </div>`;
                }).join('');
                totalEl.textContent = total.toFixed(2);
            }
        }

        function changeQty(idx, delta) {
            cart[idx].qty += delta;
            if (cart[idx].qty <= 0) cart.splice(idx, 1);
            updateCart();
        }

        function removeFromCart(idx) {
            cart.splice(idx, 1);
            updateCart();
        }

        function toggleCart() {
            document.getElementById('cartSidebar').classList.toggle('open');
        }

        function showCheckout() {
            if (cart.length === 0) return alert('Cart is empty!');
            const summary = cart.map(i => `${i.name} x${i.qty} = $${(i.price*i.qty).toFixed(2)}`).join('<br>');
            const total = cart.reduce((sum, i) => sum + i.price * i.qty, 0);
            document.getElementById('orderSummary').innerHTML = `<div style="padding:1rem;background:rgba(255,255,255,0.05);border-radius:10px;margin:1rem 0;">${summary}<br><strong>Total: $${total.toFixed(2)}</strong></div>`;
            document.getElementById('checkoutModal').classList.add('open');
            document.getElementById('cartSidebar').classList.remove('open');
        }

        function closeCheckout() {
            document.getElementById('checkoutModal').classList.remove('open');
        }

        async function submitOrder(e) {
            e.preventDefault();
            const form = e.target;
            const formData = Object.fromEntries(new FormData(form));
            formData.items = cart.map(i => ({name: i.name, price: i.price, qty: i.qty}));
            const msgEl = document.getElementById('orderMessage');
            try {
                const res = await fetch(`${API}/api/site/${SESSION}/order`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(formData)
                });
                if (res.ok) {
                    msgEl.innerHTML = '<div style="color:#22c55e;padding:1rem;">✅ Order placed successfully! We\\'ll contact you with details.</div>';
                    cart = [];
                    updateCart();
                    form.reset();
                    setTimeout(closeCheckout, 3000);
                } else { throw new Error('Failed'); }
            } catch (err) {
                msgEl.innerHTML = '<div style="color:#ef4444;padding:1rem;">❌ Could not place order. Please try again.</div>';
            }
        }
        '''

    # Contact JS
    js_code += '''
        // Contact
        document.getElementById('contactForm')?.addEventListener('submit', async (e) => {
            e.preventDefault();
            const form = e.target;
            const data = Object.fromEntries(new FormData(form));
            const msgEl = document.getElementById('contactMessage');
            try {
                const res = await fetch(`${API}/api/site/${SESSION}/contact`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                if (res.ok) {
                    msgEl.innerHTML = '<div style="color:#22c55e;padding:1rem;background:rgba(34,197,94,0.1);border-radius:10px;margin-top:1rem;">✅ Message sent! We\\'ll get back to you soon.</div>';
                    form.reset();
                } else { throw new Error('Failed'); }
            } catch (err) {
                msgEl.innerHTML = '<div style="color:#ef4444;padding:1rem;background:rgba(239,68,68,0.1);border-radius:10px;margin-top:1rem;">❌ Could not send message. Please try again.</div>';
            }
        });
    </script>'''

    # ============ FULL HTML ============
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{name} | {tagline}</title>
    <meta name="description" content="{about_text[:150]}">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Playfair+Display:wght@700;800;900&display=swap" rel="stylesheet">
    <link href="https://unpkg.com/aos@2.3.1/dist/aos.css" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        :root {{
            --primary: {colors['primary']};
            --secondary: {colors['secondary']};
            --accent: {colors['accent']};
            --text: {colors['text']};
            --gradient-1: linear-gradient(135deg, {colors['primary']} 0%, {colors['secondary']} 100%);
            --shadow-sm: 0 2px 10px rgba(0,0,0,0.05);
            --shadow-md: 0 8px 30px rgba(0,0,0,0.12);
            --shadow-lg: 0 20px 60px rgba(0,0,0,0.15);
            --shadow-xl: 0 30px 90px rgba(0,0,0,0.2);
        }}
        html {{ scroll-behavior: smooth; scroll-padding-top: 100px; }}
        body {{ font-family: 'Inter', -apple-system, sans-serif; color: var(--text); line-height: 1.7; overflow-x: hidden; background: #fff; }}

        /* NAV */
        .nav {{ position: fixed; top: 0; width: 100%; background: rgba(255,255,255,0.95); backdrop-filter: blur(20px); padding: 1.2rem 5%; display: flex; justify-content: space-between; align-items: center; z-index: 10000; box-shadow: 0 4px 30px rgba(0,0,0,0.08); transition: all 0.3s; }}
        .nav.scrolled {{ padding: 0.8rem 5%; }}
        .logo {{ font-size: 1.6rem; font-weight: 900; background: var(--gradient-1); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }}
        .nav-links {{ display: flex; gap: 2.5rem; align-items: center; }}
        .nav-links a {{ text-decoration: none; color: var(--text); font-weight: 600; font-size: 0.95rem; transition: color 0.3s; }}
        .nav-links a:hover {{ color: var(--primary); }}
        .cta-btn {{ background: var(--primary); color: white !important; padding: 0.75rem 2rem; border-radius: 50px; font-weight: 700; transition: all 0.3s; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }}
        .cta-btn:hover {{ transform: translateY(-2px); box-shadow: 0 8px 25px rgba(0,0,0,0.2); }}
        .hamburger {{ display: none; flex-direction: column; gap: 5px; cursor: pointer; z-index: 1001; }}
        .hamburger span {{ width: 25px; height: 3px; background: var(--text); border-radius: 3px; transition: all 0.3s; }}
        .hamburger.active span:nth-child(1) {{ transform: rotate(45deg) translate(8px, 8px); }}
        .hamburger.active span:nth-child(2) {{ opacity: 0; }}
        .hamburger.active span:nth-child(3) {{ transform: rotate(-45deg) translate(7px, -7px); }}

        /* HERO */
        .hero {{ position: relative; min-height: 100vh; display: flex; align-items: center; justify-content: center; text-align: center; color: white; padding: 120px 5% 2rem; overflow: hidden; }}
        .hero::before {{ content: ''; position: absolute; inset: 0; background: linear-gradient(135deg, rgba(0,0,0,0.5), rgba(0,0,0,0.3)); z-index: 1; }}
        .hero-bg {{ position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; z-index: 0; }}
        .hero-content {{ position: relative; z-index: 2; max-width: 1000px; }}
        .hero h1 {{ font-family: 'Playfair Display', serif; font-size: clamp(2.5rem, 8vw, 5.5rem); font-weight: 900; margin-bottom: 1.5rem; line-height: 1.1; letter-spacing: -2px; animation: fadeInUp 0.8s ease-out; }}
        .hero p {{ font-size: clamp(1.1rem, 2.5vw, 1.6rem); margin-bottom: 3rem; opacity: 0.95; max-width: 700px; margin-left: auto; margin-right: auto; animation: fadeInUp 0.8s ease-out 0.2s both; }}
        .hero-cta {{ display: flex; gap: 1.5rem; justify-content: center; flex-wrap: wrap; animation: fadeInUp 0.8s ease-out 0.4s both; }}
        @keyframes fadeInUp {{ from {{ opacity: 0; transform: translateY(30px); }} to {{ opacity: 1; transform: translateY(0); }} }}
        .btn {{ padding: 1.2rem 3rem; border-radius: 50px; font-weight: 700; font-size: 1.05rem; text-decoration: none; transition: all 0.3s; cursor: pointer; border: none; display: inline-block; }}
        .btn-primary {{ background: white; color: var(--primary); box-shadow: 0 8px 30px rgba(255,255,255,0.3); }}
        .btn-primary:hover {{ transform: translateY(-3px); box-shadow: 0 15px 50px rgba(255,255,255,0.4); }}
        .btn-secondary {{ background: rgba(255,255,255,0.1); color: white; border: 2px solid rgba(255,255,255,0.8); backdrop-filter: blur(10px); }}
        .btn-secondary:hover {{ background: white; color: var(--primary); }}

        /* SECTIONS */
        .section-container {{ max-width: 1400px; margin: 0 auto; }}
        .section-title {{ text-align: center; font-size: clamp(2.5rem, 6vw, 4rem); font-weight: 900; margin-bottom: 1rem; letter-spacing: -1px; background: var(--gradient-1); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }}
        .section-subtitle {{ text-align: center; font-size: clamp(1.1rem, 2vw, 1.4rem); color: #64748b; margin-bottom: 4rem; font-weight: 500; }}

        /* SERVICES */
        .services {{ padding: 100px 5%; background: linear-gradient(180deg, #fff, #f8f9fb, #fff); }}
        .services-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 2.5rem; max-width: 1400px; margin: 0 auto; }}
        .service-card {{ background: white; border-radius: 24px; overflow: hidden; box-shadow: var(--shadow-md); transition: all 0.4s; border: 1px solid rgba(0,0,0,0.05); }}
        .service-card:hover {{ transform: translateY(-12px); box-shadow: var(--shadow-xl); }}
        .service-image-wrapper {{ position: relative; height: 240px; overflow: hidden; }}
        .service-image {{ width: 100%; height: 100%; object-fit: cover; transition: transform 0.5s; }}
        .service-card:hover .service-image {{ transform: scale(1.1); }}
        .service-overlay {{ position: absolute; inset: 0; background: linear-gradient(180deg, transparent, rgba(0,0,0,0.3)); }}
        .service-content {{ padding: 2rem; }}
        .service-content h3 {{ font-size: 1.4rem; margin-bottom: 0.8rem; font-weight: 800; }}
        .service-content p {{ color: #64748b; font-size: 1rem; line-height: 1.7; margin-bottom: 1.2rem; }}
        .service-link {{ color: var(--primary); text-decoration: none; font-weight: 700; transition: all 0.3s; }}

        /* MENU */
        .menu-section {{ padding: 100px 5%; background: #f8f9fb; }}
        .menu-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 2rem; max-width: 1400px; margin: 0 auto; }}
        .menu-item {{ background: white; border-radius: 20px; overflow: hidden; box-shadow: var(--shadow-sm); transition: all 0.3s; }}
        .menu-item:hover {{ transform: translateY(-5px); box-shadow: var(--shadow-md); }}
        .menu-item img {{ width: 100%; height: 200px; object-fit: cover; }}
        .menu-item-content {{ padding: 1.5rem; }}
        .menu-item-content h4 {{ font-size: 1.2rem; margin-bottom: 0.5rem; }}
        .menu-item-content p {{ color: #64748b; font-size: 0.9rem; margin-bottom: 1rem; }}
        .menu-item-footer {{ display: flex; justify-content: space-between; align-items: center; }}
        .price {{ font-size: 1.4rem; font-weight: 800; color: var(--primary); }}
        .add-to-cart-btn {{ padding: 0.5rem 1.2rem; background: var(--primary); color: white; border: none; border-radius: 25px; font-weight: 600; cursor: pointer; transition: all 0.2s; font-size: 0.85rem; }}
        .add-to-cart-btn:hover {{ transform: scale(1.05); }}

        /* BOOKING */
        .booking-section {{ padding: 100px 5%; background: white; }}
        .booking-form {{ max-width: 700px; margin: 0 auto; }}
        .form-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1rem; }}
        .booking-form input, .booking-form select, .booking-form textarea {{ padding: 1rem 1.5rem; border: 2px solid #e0e0e0; border-radius: 12px; font-size: 1rem; font-family: inherit; transition: border-color 0.3s; width: 100%; }}
        .booking-form input:focus, .booking-form select:focus, .booking-form textarea:focus {{ outline: none; border-color: var(--primary); }}

        /* ABOUT */
        .about {{ padding: 100px 5%; background: var(--gradient-1); color: white; position: relative; overflow: hidden; }}
        .about::before {{ content: ''; position: absolute; width: 500px; height: 500px; background: rgba(255,255,255,0.05); border-radius: 50%; top: -250px; right: -250px; }}
        .about-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 5rem; max-width: 1400px; margin: 0 auto; align-items: center; position: relative; z-index: 1; }}
        .about-content h2 {{ font-family: 'Playfair Display', serif; font-size: clamp(2.5rem, 5vw, 4rem); margin-bottom: 2rem; font-weight: 900; line-height: 1.2; }}
        .about-content p {{ font-size: 1.15rem; line-height: 1.9; opacity: 0.95; margin-bottom: 1.5rem; }}
        .about-image {{ height: 500px; border-radius: 30px; overflow: hidden; box-shadow: 0 30px 90px rgba(0,0,0,0.3); }}
        .about-image img {{ width: 100%; height: 100%; object-fit: cover; }}

        /* GALLERY */
        .gallery {{ padding: 100px 5%; background: #fff; }}
        .gallery-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 2rem; max-width: 1400px; margin: 3rem auto 0; }}
        .gallery-item {{ position: relative; height: 350px; border-radius: 24px; overflow: hidden; cursor: pointer; box-shadow: var(--shadow-md); transition: all 0.4s; }}
        .gallery-item img {{ width: 100%; height: 100%; object-fit: cover; transition: transform 0.5s; }}
        .gallery-item:hover img {{ transform: scale(1.1); }}
        .gallery-overlay {{ position: absolute; inset: 0; background: rgba(0,0,0,0.6); display: flex; align-items: center; justify-content: center; opacity: 0; transition: opacity 0.3s; font-size: 3rem; }}
        .gallery-item:hover .gallery-overlay {{ opacity: 1; }}

        /* CONTACT */
        .contact {{ padding: 100px 5%; background: linear-gradient(135deg, #1e293b, #0f172a); color: white; text-align: center; }}
        .contact h2 {{ font-size: clamp(2.5rem, 5vw, 4rem); margin-bottom: 1.5rem; font-weight: 900; }}
        .contact > .section-container > p {{ font-size: 1.3rem; margin-bottom: 3rem; opacity: 0.9; }}
        .contact-form {{ max-width: 600px; margin: 0 auto; display: flex; flex-direction: column; gap: 1.2rem; }}
        .contact-form input, .contact-form textarea {{ padding: 1.2rem 1.5rem; border: 2px solid rgba(255,255,255,0.1); border-radius: 14px; font-size: 1rem; font-family: inherit; background: rgba(255,255,255,0.05); color: white; transition: all 0.3s; }}
        .contact-form input:focus, .contact-form textarea:focus {{ outline: none; border-color: var(--primary); background: rgba(255,255,255,0.1); }}
        .contact-form input::placeholder, .contact-form textarea::placeholder {{ color: rgba(255,255,255,0.4); }}
        .submit-btn {{ background: white; color: var(--primary); padding: 1.2rem 3rem; border: none; border-radius: 50px; font-size: 1.1rem; font-weight: 800; cursor: pointer; transition: all 0.3s; box-shadow: 0 10px 40px rgba(255,255,255,0.2); }}
        .submit-btn:hover {{ transform: translateY(-3px); box-shadow: 0 15px 50px rgba(255,255,255,0.3); }}

        /* FOOTER */
        .footer {{ background: #0a0a0a; color: white; padding: 4rem 5% 2rem; }}
        .footer-content {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 3rem; max-width: 1400px; margin: 0 auto 2rem; }}
        .footer-section h4 {{ font-size: 1.3rem; margin-bottom: 1rem; font-weight: 800; }}
        .footer-section p {{ opacity: 0.7; margin: 0.5rem 0; line-height: 1.8; }}
        .footer-section a {{ color: inherit; text-decoration: none; }}
        .footer-bottom {{ text-align: center; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 2rem; opacity: 0.5; }}

        /* CART */
        .cart-sidebar {{ position: fixed; top: 0; right: -400px; width: 380px; height: 100vh; background: white; box-shadow: -10px 0 40px rgba(0,0,0,0.15); z-index: 10001; transition: right 0.3s; display: flex; flex-direction: column; color: #333; }}
        .cart-sidebar.open {{ right: 0; }}
        .cart-header {{ display: flex; justify-content: space-between; align-items: center; padding: 1.5rem; border-bottom: 1px solid #eee; }}
        .cart-header h3 {{ font-size: 1.3rem; }}
        .cart-close {{ background: none; border: none; font-size: 1.5rem; cursor: pointer; }}
        .cart-items {{ flex: 1; overflow-y: auto; padding: 1rem; }}
        .cart-item {{ display: flex; justify-content: space-between; align-items: center; padding: 1rem 0; border-bottom: 1px solid #f0f0f0; }}
        .cart-item-actions {{ display: flex; align-items: center; gap: 0.5rem; }}
        .cart-item-actions button {{ width: 28px; height: 28px; border: 1px solid #ddd; border-radius: 50%; background: white; cursor: pointer; font-weight: bold; }}
        .cart-footer {{ padding: 1.5rem; border-top: 1px solid #eee; }}
        .cart-total {{ font-size: 1.3rem; font-weight: 800; margin-bottom: 1rem; }}
        .checkout-btn {{ width: 100%; padding: 1rem; background: var(--primary); color: white; border: none; border-radius: 50px; font-size: 1rem; font-weight: 700; cursor: pointer; }}
        .cart-fab {{ position: fixed; bottom: 2rem; right: 2rem; background: var(--primary); color: white; border: none; border-radius: 50px; padding: 1rem 1.5rem; font-size: 1rem; cursor: pointer; box-shadow: var(--shadow-lg); z-index: 10000; display: flex; align-items: center; gap: 0.5rem; font-weight: 700; }}
        .cart-empty {{ text-align: center; color: #999; padding: 2rem; }}

        /* CHECKOUT MODAL */
        .checkout-modal {{ position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 10002; display: none; align-items: center; justify-content: center; }}
        .checkout-modal.open {{ display: flex; }}
        .checkout-content {{ background: white; border-radius: 24px; padding: 2rem; width: 90%; max-width: 500px; max-height: 90vh; overflow-y: auto; color: #333; position: relative; }}
        .checkout-content h3 {{ margin-bottom: 1.5rem; font-size: 1.4rem; }}
        .modal-close {{ position: absolute; top: 1rem; right: 1rem; background: none; border: none; font-size: 1.3rem; cursor: pointer; }}
        .checkout-content input, .checkout-content textarea {{ width: 100%; padding: 0.8rem 1rem; border: 2px solid #e0e0e0; border-radius: 10px; margin-bottom: 0.8rem; font-family: inherit; font-size: 0.95rem; }}
        .checkout-content input:focus, .checkout-content textarea:focus {{ outline: none; border-color: var(--primary); }}
        .checkout-content .submit-btn {{ width: 100%; margin-top: 0.5rem; color: white; background: var(--primary); }}

        /* RESPONSIVE */
        @media (max-width: 968px) {{
            .about-grid {{ grid-template-columns: 1fr; gap: 3rem; }}
            .form-grid {{ grid-template-columns: 1fr; }}
        }}
        @media (max-width: 768px) {{
            .nav-links {{ position: fixed; top: 0; right: -100%; height: 100vh; width: 70%; max-width: 400px; background: rgba(255,255,255,0.98); backdrop-filter: blur(20px); flex-direction: column; padding: 6rem 2rem 2rem; box-shadow: -5px 0 30px rgba(0,0,0,0.1); transition: right 0.4s; justify-content: flex-start; gap: 2rem; }}
            .nav-links.active {{ right: 0; }}
            .nav-links a {{ font-size: 1.2rem; }}
            .hamburger {{ display: flex; }}
            .cart-sidebar {{ width: 100%; }}
        }}
    </style>
</head>
<body>
    <!-- NAV -->
    <nav class="nav" id="navbar">
        <div class="logo">{name}</div>
        <div class="hamburger" onclick="toggleMenu()"><span></span><span></span><span></span></div>
        <div class="nav-links" id="navLinks">{nav_links}</div>
    </nav>

    <!-- HERO -->
    <section class="hero" id="home">
        <img src="{images['hero']}" alt="{name}" class="hero-bg">
        <div class="hero-content">
            <h1>{hero_headline}</h1>
            <p>{hero_subtext}</p>
            <div class="hero-cta">
                <a href="#{'booking' if 'booking' in features else 'contact'}" class="btn btn-primary">{cta_text}</a>
                <a href="#services" class="btn btn-secondary">Explore Services</a>
            </div>
        </div>
    </section>

    <!-- SERVICES -->
    <section class="services" id="services">
        <div class="section-container">
            <h2 class="section-title" data-aos="fade-up">Our Services</h2>
            <p class="section-subtitle" data-aos="fade-up" data-aos-delay="100">{tagline}</p>
            <div class="services-grid">{service_cards}</div>
        </div>
    </section>

    {menu_section}

    {booking_section}

    <!-- ABOUT -->
    <section class="about" id="about">
        <div class="about-grid">
            <div class="about-content" data-aos="fade-right">
                <h2>About {name}</h2>
                <p>{about_text}</p>
                <p>Located in {city}, {country}, we bring excellence to everything we do.</p>
            </div>
            <div class="about-image" data-aos="fade-left">
                <img src="{images['about']}" alt="About {name}">
            </div>
        </div>
    </section>

    <!-- GALLERY -->
    <section class="gallery" id="gallery">
        <div class="section-container">
            <h2 class="section-title" data-aos="fade-up">Gallery</h2>
            <p class="section-subtitle" data-aos="fade-up" data-aos-delay="100">See what we've accomplished</p>
            <div class="gallery-grid">{gallery_items}</div>
        </div>
    </section>

    {contact_section}

    <!-- FOOTER -->
    <footer class="footer">
        <div class="footer-content">
            <div class="footer-section">
                <h4>{name}</h4>
                <p>{tagline}</p>
                <p>{city}, {country}</p>
            </div>
            <div class="footer-section">
                <h4>Quick Links</h4>
                <p><a href="#home">Home</a></p>
                <p><a href="#services">Services</a></p>
                <p><a href="#about">About</a></p>
                <p><a href="#contact">Contact</a></p>
            </div>
            <div class="footer-section">
                <h4>Contact</h4>
                <p>Email: info@{name.lower().replace(' ', '')}.com</p>
                <p>Phone: +1 (555) 123-4567</p>
            </div>
        </div>
        <div class="footer-bottom">
            <p>&copy; 2025 {name}. All rights reserved.</p>
        </div>
    </footer>

    {cart_section}

    <script src="https://unpkg.com/aos@2.3.1/dist/aos.js"></script>
    {js_code}
</body>
</html>'''

    return html


# ============================================================
# FILE UPLOAD ENDPOINT
# ============================================================

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...), session_id: str = Form(...)):
    """Upload a photo or video"""
    # Validate file type
    allowed = ["image/jpeg", "image/png", "image/webp", "image/gif", "video/mp4", "video/webm"]
    if file.content_type not in allowed:
        raise HTTPException(status_code=400, detail=f"File type {file.content_type} not allowed")

    # Create session upload directory
    upload_dir = f"static/uploads/{session_id}"
    os.makedirs(upload_dir, exist_ok=True)

    # Save file
    filename = f"{uuid.uuid4().hex[:8]}_{file.filename}"
    filepath = os.path.join(upload_dir, filename)

    with open(filepath, "wb") as f:
        content = await file.read()
        if len(content) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(status_code=400, detail="File too large (max 10MB)")
        f.write(content)

    url = f"/static/uploads/{session_id}/{filename}"
    return {"url": url, "filename": filename}


# ============================================================
# SITE-SPECIFIC API ENDPOINTS (for generated websites)
# ============================================================

@app.post("/api/site/{session_id}/booking")
async def handle_booking(session_id: str, request: BookingRequest):
    """Handle booking submission from generated website"""
    data_dir = f"site_data/{session_id}"
    os.makedirs(data_dir, exist_ok=True)

    bookings_file = os.path.join(data_dir, "bookings.json")
    bookings = []
    if os.path.exists(bookings_file):
        with open(bookings_file, "r") as f:
            bookings = json.load(f)

    booking = {
        "id": str(uuid.uuid4())[:8],
        "timestamp": datetime.now().isoformat(),
        **request.dict()
    }
    bookings.append(booking)

    with open(bookings_file, "w") as f:
        json.dump(bookings, f, indent=2)

    return {"status": "success", "booking_id": booking["id"]}


@app.post("/api/site/{session_id}/order")
async def handle_order(session_id: str, request: OrderRequest):
    """Handle order submission from generated website"""
    data_dir = f"site_data/{session_id}"
    os.makedirs(data_dir, exist_ok=True)

    orders_file = os.path.join(data_dir, "orders.json")
    orders = []
    if os.path.exists(orders_file):
        with open(orders_file, "r") as f:
            orders = json.load(f)

    order = {
        "id": str(uuid.uuid4())[:8],
        "timestamp": datetime.now().isoformat(),
        **request.dict()
    }
    orders.append(order)

    with open(orders_file, "w") as f:
        json.dump(orders, f, indent=2)

    return {"status": "success", "order_id": order["id"]}


@app.post("/api/site/{session_id}/contact")
async def handle_contact(session_id: str, request: ContactRequest):
    """Handle contact form submission from generated website"""
    data_dir = f"site_data/{session_id}"
    os.makedirs(data_dir, exist_ok=True)

    contacts_file = os.path.join(data_dir, "contacts.json")
    contacts = []
    if os.path.exists(contacts_file):
        with open(contacts_file, "r") as f:
            contacts = json.load(f)

    contact = {
        "id": str(uuid.uuid4())[:8],
        "timestamp": datetime.now().isoformat(),
        **request.dict()
    }
    contacts.append(contact)

    with open(contacts_file, "w") as f:
        json.dump(contacts, f, indent=2)

    return {"status": "success", "message_id": contact["id"]}


@app.get("/api/site/{session_id}/admin")
async def admin_panel(session_id: str):
    """Simple admin panel to view bookings/orders/contacts"""
    data_dir = f"site_data/{session_id}"

    bookings = []
    orders = []
    contacts = []

    if os.path.exists(f"{data_dir}/bookings.json"):
        with open(f"{data_dir}/bookings.json") as f:
            bookings = json.load(f)
    if os.path.exists(f"{data_dir}/orders.json"):
        with open(f"{data_dir}/orders.json") as f:
            orders = json.load(f)
    if os.path.exists(f"{data_dir}/contacts.json"):
        with open(f"{data_dir}/contacts.json") as f:
            contacts = json.load(f)

    html = f'''<!DOCTYPE html>
<html><head><title>Admin Panel</title>
<style>
    body {{ font-family: 'Inter', sans-serif; padding: 2rem; background: #f5f5f5; }}
    h1 {{ color: #6366F1; margin-bottom: 2rem; }}
    h2 {{ color: #333; margin: 2rem 0 1rem; padding-bottom: 0.5rem; border-bottom: 2px solid #6366F1; }}
    table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 2rem; }}
    th {{ background: #6366F1; color: white; padding: 1rem; text-align: left; }}
    td {{ padding: 0.8rem 1rem; border-bottom: 1px solid #eee; }}
    tr:hover td {{ background: #f8f9ff; }}
    .badge {{ padding: 0.3rem 0.8rem; border-radius: 20px; font-size: 0.8rem; font-weight: 600; }}
    .count {{ background: #6366F1; color: white; padding: 0.2rem 0.6rem; border-radius: 10px; font-size: 0.85rem; }}
    .empty {{ text-align: center; color: #999; padding: 2rem; }}
</style></head>
<body>
    <h1>Admin Panel</h1>

    <h2>Bookings <span class="count">{len(bookings)}</span></h2>
    {'<table><tr><th>Date</th><th>Name</th><th>Email</th><th>Phone</th><th>Service</th><th>Appt Date</th><th>Time</th></tr>' + ''.join(f'<tr><td>{b.get("timestamp","")[:10]}</td><td>{b.get("name","")}</td><td>{b.get("email","")}</td><td>{b.get("phone","")}</td><td>{b.get("service","")}</td><td>{b.get("date","")}</td><td>{b.get("time","")}</td></tr>' for b in bookings) + '</table>' if bookings else '<p class="empty">No bookings yet</p>'}

    <h2>Orders <span class="count">{len(orders)}</span></h2>
    {'<table><tr><th>Date</th><th>Name</th><th>Email</th><th>Phone</th><th>Items</th><th>Address</th></tr>' + ''.join(f'<tr><td>{o.get("timestamp","")[:10]}</td><td>{o.get("name","")}</td><td>{o.get("email","")}</td><td>{o.get("phone","")}</td><td>{", ".join(i.get("name","") for i in o.get("items",[]))}</td><td>{o.get("address","")}</td></tr>' for o in orders) + '</table>' if orders else '<p class="empty">No orders yet</p>'}

    <h2>Contact Messages <span class="count">{len(contacts)}</span></h2>
    {'<table><tr><th>Date</th><th>Name</th><th>Email</th><th>Phone</th><th>Message</th></tr>' + ''.join(f'<tr><td>{c.get("timestamp","")[:10]}</td><td>{c.get("name","")}</td><td>{c.get("email","")}</td><td>{c.get("phone","")}</td><td>{c.get("message","")[:100]}</td></tr>' for c in contacts) + '</table>' if contacts else '<p class="empty">No messages yet</p>'}
</body></html>'''

    return HTMLResponse(content=html)


# ============================================================
# LEGACY API ENDPOINTS (keep for backwards compatibility)
# ============================================================

@app.post("/api/build")
async def build_website(request: BuildRequest):
    """Legacy BUILD MODE"""
    try:
        session_id = str(uuid.uuid4())
        session = {
            "stage": "building",
            "business_type": "business",
            "business_name": None,
            "location": None,
            "description": request.description,
            "services": [],
            "uploaded_media": [],
            "features": ["contact", "gallery"],
            "style_vibe": "modern",
            "conversation_history": [],
            "website_session_id": session_id,
        }
        CHAT_SESSIONS[session_id] = session

        result = build_website_from_chat(session)

        return {
            "session_id": result["session_id"],
            "status": "success",
            "mode": "BUILD",
            "website_code": result["html"],
            "website_state": WEBSITE_STATES.get(result["session_id"], {}),
            "business_name": result["analysis"]["business_name"],
            "explanation": f"Generated website for {result['analysis']['business_name']}",
            "ai_model": "gemini-2.5-flash",
            "model_reasoning": "Fast and efficient for website generation"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/edit")
async def edit_website(request: EditRequest):
    """Legacy EDIT MODE"""
    try:
        if request.session_id not in CHAT_SESSIONS:
            # Load from state
            state_path = f"website_states/{request.session_id}.json"
            if not os.path.exists(state_path):
                raise HTTPException(status_code=404, detail="Website not found")
            with open(state_path) as f:
                state = json.load(f)
            CHAT_SESSIONS[request.session_id] = {
                "stage": "review",
                "business_type": state.get("analysis", {}).get("business_type", "business"),
                "business_name": state.get("analysis", {}).get("business_name"),
                "location": None,
                "description": state.get("business_description", ""),
                "services": state.get("analysis", {}).get("services", []),
                "uploaded_media": [],
                "features": state.get("features", ["contact"]),
                "style_vibe": state.get("analysis", {}).get("vibe", "modern"),
                "conversation_history": [],
                "website_session_id": request.session_id,
            }

        session = CHAT_SESSIONS[request.session_id]
        result = edit_website_from_chat(session, request.edit_request)

        return {
            "session_id": result["session_id"],
            "status": "success",
            "mode": "EDIT",
            "website_code": result["html"],
            "website_state": WEBSITE_STATES.get(result["session_id"], {}),
            "business_name": result["analysis"]["business_name"],
            "explanation": f"Updated website: {request.edit_request}",
            "ai_model": "gemini-2.5-flash",
            "model_reasoning": "Fast editing"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/preview/{session_id}")
async def preview_website(session_id: str):
    """Preview the generated website"""
    html_path = f"generated_websites/{session_id}.html"
    if not os.path.exists(html_path):
        raise HTTPException(status_code=404, detail="Website not found")
    with open(html_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.get("/api/website/{session_id}/html")
async def get_website_html(session_id: str):
    """Get HTML preview for website (supports both legacy HTML and React)"""
    # First check if it's a React website in CHAT_SESSIONS
    for chat_id, chat_session in CHAT_SESSIONS.items():
        if chat_session.get("website_session_id") == session_id:
            # This is a React website from chat flow
            vercel_url = chat_session.get("vercel_url")
            html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Your React Website is Ready!</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
        }}
        .container {{
            background: white;
            border-radius: 12px;
            padding: 40px;
            max-width: 600px;
            text-align: center;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }}
        h1 {{
            color: #333;
            margin: 0 0 10px 0;
            font-size: 32px;
        }}
        .checkmark {{
            font-size: 64px;
            color: #4CAF50;
            margin: 20px 0;
        }}
        p {{
            color: #666;
            line-height: 1.6;
            margin: 15px 0;
        }}
        .btn {{
            display: inline-block;
            padding: 12px 30px;
            margin: 10px 5px;
            background: #667eea;
            color: white;
            text-decoration: none;
            border-radius: 6px;
            font-weight: 600;
            transition: transform 0.2s;
        }}
        .btn:hover {{
            transform: translateY(-2px);
            background: #5568d3;
        }}
        .info {{
            background: #f5f5f5;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        .vercel-link {{
            color: #667eea;
            word-break: break-all;
            font-weight: 600;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="checkmark">✓</div>
        <h1>Your React Website is Ready!</h1>
        <p>Your professional React website has been generated successfully.</p>

        {f'<div class="info"><p>🚀 <strong>Live Website:</strong><br><a href="{vercel_url}" target="_blank" class="vercel-link">{vercel_url}</a></p></div>' if vercel_url else '<div class="info"><p>⚠️ Deployment is in progress. Your website will be available shortly.</p></div>'}

        <p><strong>What's Next?</strong></p>
        <p>Go back to the chat to:</p>
        <ul style="text-align: left; display: inline-block;">
            <li>Download the React source code</li>
            <li>Make changes to colors, text, or layout</li>
            <li>Add more sections and features</li>
        </ul>

        {f'<a href="{vercel_url}" target="_blank" class="btn">Visit Live Website →</a>' if vercel_url else ''}
    </div>
</body>
</html>
"""
            return HTMLResponse(content=html_content)

    # Otherwise check for legacy HTML file
    html_path = f"generated_websites/{session_id}.html"
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())

    # Not found
    raise HTTPException(status_code=404, detail="Website not found. Please build a website first.")


@app.get("/api/download/{session_id}")
async def download_website(session_id: str, format: str = "html"):
    """Download website"""
    html_path = f"generated_websites/{session_id}.html"
    if not os.path.exists(html_path):
        raise HTTPException(status_code=404, detail="Website not found")

    if format.lower() == "html":
        return FileResponse(html_path, media_type="text/html", filename=f"website-{session_id}.html")
    elif format.lower() == "zip":
        # Create zip with separate HTML, CSS, JS files
        import re

        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        # Extract CSS from <style> tags
        css_match = re.search(r'<style>(.*?)</style>', html_content, re.DOTALL)
        css_content = css_match.group(1).strip() if css_match else ""

        # Extract JS from <script> tags (exclude external scripts)
        js_matches = re.findall(r'<script>(.*?)</script>', html_content, re.DOTALL)
        js_content = "\n\n".join(match.strip() for match in js_matches if match.strip())

        # Replace style and script tags with links to external files
        html_clean = html_content
        if css_match:
            html_clean = html_clean.replace(css_match.group(0), '<link rel="stylesheet" href="styles.css">')

        # Remove all inline scripts and add external script tag before </body>
        html_clean = re.sub(r'<script>.*?</script>', '', html_clean, flags=re.DOTALL)
        html_clean = html_clean.replace('</body>', '<script src="script.js"></script>\n</body>')

        # Create zip file in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add index.html
            zip_file.writestr('index.html', html_clean)
            # Add styles.css
            if css_content:
                zip_file.writestr('styles.css', css_content)
            # Add script.js
            if js_content:
                zip_file.writestr('script.js', js_content)
            # Add README
            readme = f"""Website Package
================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Files included:
- index.html - Main HTML file
- styles.css - Stylesheet
- script.js - JavaScript functionality

To use:
1. Extract this zip file
2. Open index.html in your web browser

Note: This is a standalone website. All functionality is self-contained.
"""
            zip_file.writestr('README.txt', readme)

        zip_buffer.seek(0)
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename=website-{session_id}.zip"}
        )
    else:
        raise HTTPException(status_code=400, detail="Use 'html' or 'zip' format")


@app.get("/")
async def health_check():
    """Backend health check"""
    return {"status": "ok", "service": "Sitekraft API"}



# ============================================================
# REACT & DEPLOYMENT ROUTES (Auto-integrated)
# ============================================================
from react_api_routes import router as react_router
app.include_router(react_router)


# ============================================================
# STATIC HTML DEPLOYMENT (inline fallback for hot-reload)
# ============================================================
class _StaticHtmlDeployRequest(BaseModel):
    project_name: str
    html_content: str

@app.post("/api/react/deploy-html")
async def _deploy_html_inline(request: _StaticHtmlDeployRequest):
    """Deploy raw HTML string as a static Vercel site (identical to preview)."""
    from vercel_deployer import vercel_deployer as _vd
    if not _vd.is_enabled():
        raise HTTPException(status_code=400, detail="Vercel not configured")
    result = await _vd.deploy_static_html(
        project_name=request.project_name,
        html_content=request.html_content
    )
    if not result:
        raise HTTPException(status_code=500, detail="Deployment failed")
    return {"success": True, "deployment_url": result["url"]}


if __name__ == "__main__":
    import uvicorn
    import sys

    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    print("\n" + "="*60)
    print("AI WEBSITE BUILDER AGENT")
    print("="*60)
    print("\nServer: http://localhost:8000")
    print("API Docs: http://localhost:8000/docs")
    print("="*60 + "\n")

    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
