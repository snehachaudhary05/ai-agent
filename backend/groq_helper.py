"""
Groq AI Helper
Fast AI text generation via Groq's LPU-powered API (OpenAI-compatible).
Set GROQ_API_KEY in your .env file to enable.

Recommended free models:
  llama-3.3-70b-versatile   ← best quality, 70B, 128K ctx (default)
  llama-3.1-8b-instant      ← fastest, lightweight tasks
  gemma2-9b-it              ← Google Gemma, fast & accurate
"""

import os
import json
import requests

GROQ_API_KEY  = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL    = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_BASE_URL = "https://api.groq.com/openai/v1/chat/completions"


def is_available() -> bool:
    return bool(GROQ_API_KEY)


def generate_text(prompt: str, max_tokens: int = 1200, system: str = "") -> str:
    """Call Groq and return the assistant response text."""
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is not set")

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    response = requests.post(
        GROQ_BASE_URL,
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": GROQ_MODEL,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.7,
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()


def _parse_json(text: str) -> dict:
    """Extract and parse the first JSON object found in text."""
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    j_start = text.find("{")
    j_end   = text.rfind("}") + 1
    if j_start >= 0 and j_end > j_start:
        return json.loads(text[j_start:j_end])
    raise ValueError("No JSON object found in response")


def generate_website_copy(
    business_name: str,
    business_type: str,
    business_description: str,
    services: list,
    location: str = "",
    style_vibe: str = "modern",
    service_categories: list = None,
) -> dict:
    """
    Generate complete website copy using Groq.
    Returns {} on failure so the caller can fall back to Gemini.
    """
    cat_map = {}
    for entry in (service_categories or []):
        name = entry.get("name", "").strip()
        if name:
            cat_map[name] = entry

    service_lines = []
    for svc in (services or []):
        entry = cat_map.get(svc, {})
        cat = entry.get("category", "").strip()
        sub = entry.get("subcategory", "").strip()
        if sub:
            service_lines.append(f"{svc} [Category: {cat} | Subcategory: {sub}]")
        elif cat:
            service_lines.append(f"{svc} [Category: {cat}]")
        else:
            service_lines.append(svc)

    services_str = ", ".join(service_lines) if service_lines else "Not specified"

    prompt = (
        "You are a world-class copywriter. Generate compelling website copy.\n\n"
        f"Business: {business_name}\n"
        f"Type: {business_type}\n"
        f"Location: {location or 'Not specified'}\n"
        f"Style: {style_vibe}\n"
        f"Description: {business_description or 'Not specified'}\n"
        f"Services/Products: {services_str}\n\n"
        "Rules:\n"
        "- Hero headline: 5-10 words, powerful and unique\n"
        "- Avoid clichés: 'best', 'welcome to', 'your one-stop'\n"
        "- Match the style vibe\n"
        "- service_descriptions: one specific sentence per service (15-20 words)\n\n"
        "Return ONLY valid JSON:\n"
        "{\n"
        '  "hero_headline": "powerful 5-10 word headline",\n'
        '  "hero_subtext": "1-2 compelling sentences",\n'
        '  "tagline": "3-5 word tagline",\n'
        '  "about_text": "2-3 sentence brand story",\n'
        '  "cta_text": "action button text (2-4 words)",\n'
        '  "service_descriptions": {"service_name": "description"}\n'
        "}"
    )

    try:
        text = generate_text(prompt, max_tokens=600)
        return _parse_json(text)
    except Exception as e:
        print(f"[GROQ] generate_website_copy failed: {e}")
        return {}


def generate_service_descriptions(
    services: list,
    business_name: str,
    business_type: str,
    location: str = "",
    service_categories: list = None,
) -> dict:
    """
    Generate a short AI description for each service/product using Groq.
    Returns fallback strings on failure.
    """
    if not services:
        return {}

    cat_map = {}
    for entry in (service_categories or []):
        name = entry.get("name", "").strip()
        if name:
            cat_map[name] = entry

    item_lines = []
    for svc in services:
        entry = cat_map.get(svc, {})
        cat = entry.get("category", "").strip()
        sub = entry.get("subcategory", "").strip()
        if sub:
            item_lines.append(f"- {svc} [Category: {cat} | Subcategory: {sub}]")
        elif cat:
            item_lines.append(f"- {svc} [Category: {cat}]")
        else:
            item_lines.append(f"- {svc}")

    location_part = f" in {location}" if location else ""
    prompt = (
        f"You are an expert copywriter for {business_name}, "
        f"a {business_type} business{location_part}.\n\n"
        "Write one short, compelling sentence (max 18 words) for each item below.\n"
        "Focus on the outcome, feeling, or specific benefit — make it vivid and specific.\n"
        "Do NOT use overused words like 'premium', 'experience our', 'crafted with care', or 'elevate'.\n\n"
        "Items:\n" + "\n".join(item_lines) + "\n\n"
        "Return ONLY valid JSON — no markdown, no explanation:\n"
        '{"item_name": "short specific description", ...}'
    )

    try:
        text = generate_text(prompt, max_tokens=500)
        return _parse_json(text)
    except Exception as e:
        print(f"[GROQ] generate_service_descriptions failed: {e}")

    # Fallback descriptions — business-type-aware, varied by item hash
    def _fallback_desc(svc: str, btype: str) -> str:
        s = svc.strip()
        sl = s.lower()
        bt = (btype or "").lower()
        if any(t in bt for t in ["restaurant", "cafe", "food", "dhaba", "kitchen", "bistro"]):
            templates = [
                f"A rich and flavorful {sl}, crafted with fresh ingredients and authentic spices.",
                f"Savor the irresistible taste of our {sl}, made fresh to order every time.",
                f"A classic {sl} bursting with bold flavors and time-honored recipes.",
                f"Indulge in our signature {sl}, prepared with the finest seasonal ingredients.",
                f"A beloved {sl} that warms the soul — perfectly spiced and beautifully presented.",
            ]
        elif any(t in bt for t in ["salon", "spa", "beauty", "parlour", "parlor"]):
            templates = [
                f"Rejuvenate with our expert {sl} treatment, tailored to bring out your natural radiance.",
                f"Our professional {sl} service leaves you feeling refreshed, confident, and glowing.",
                f"Our expert {sl} treatment uses top-quality products and skilled hands for real results.",
            ]
        elif any(t in bt for t in ["gym", "fitness", "yoga", "studio", "crossfit"]):
            templates = [
                f"Push your limits with {sl} — expert-led, results-driven, and built for all fitness levels.",
                f"Transform your body with our {sl} program — structured, motivated, and highly effective.",
                f"Our {sl} sessions are designed to maximize results while keeping every workout engaging.",
            ]
        elif any(t in bt for t in ["coaching", "tuition", "classes", "academy", "institute", "tutor"]):
            templates = [
                f"Master {sl} with expert guidance, structured lessons, and proven results.",
                f"Our {sl} program is designed to build deep understanding and exam-ready confidence.",
                f"Excel in {sl} with personalized mentoring and a focused, results-driven curriculum.",
                f"From basics to advanced — our {sl} course prepares you for success at every level.",
            ]
        elif bt == "online-store" or any(t in bt for t in ["clothing", "boutique", "fashion"]):
            templates = [
                f"A stunning {sl} with rich fabric, sharp cuts, and a finish that turns heads.",
                f"A stunning {sl} that blends tradition with modern style — designed to make you stand out.",
                f"Our {sl} collection redefines elegance with superior craftsmanship and rich detailing.",
            ]
        elif any(t in bt for t in ["shop", "store"]):
            templates = [
                f"Discover our {sl} — thoughtfully selected for quality, value, and everyday satisfaction.",
                f"Our {sl} brings you the best in its category — reliable, affordable, and built to impress.",
                f"Experience the difference with our {sl} — a customer favorite for good reason.",
            ]
        elif any(t in bt for t in ["clinic", "hospital", "medical", "dental", "health"]):
            templates = [
                f"Expert {sl} care delivered with compassion, precision, and your wellbeing in mind.",
                f"Our {sl} service combines advanced techniques with personalized, patient-first care.",
            ]
        elif any(t in bt for t in ["real-estate", "property", "realty", "real estate"]):
            templates = [
                f"Discover our {sl} — thoughtfully designed for modern living and lasting value.",
                f"A well-designed {sl} offering the perfect blend of comfort, space, and smart investment.",
            ]
        else:
            templates = [
                f"Our {sl} is delivered with genuine expertise and attention to every detail.",
                f"Our {sl} service is crafted to exceed your expectations every single time.",
                f"Quality you can count on — our {sl} is built around your needs and satisfaction.",
            ]
        return templates[hash(sl) % len(templates)]

    return {svc: _fallback_desc(svc, business_type) for svc in services}
