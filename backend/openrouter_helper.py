"""
OpenRouter AI Helper
Provides AI text generation via OpenRouter API as an alternative to Gemini.
Set OPENROUTER_API_KEY in your .env file to enable.

Recommended free models (set OPENROUTER_MODEL to one of these):
  meta-llama/llama-3.3-70b-instruct:free  ← best quality (default, 70B, 128K ctx)
  google/gemma-3-27b-it:free              ← great quality, 27B, 131K ctx
  mistralai/mistral-small-3.1-24b-instruct:free  ← fast & precise, 24B, 128K ctx
  deepseek/deepseek-r1-0528:free          ← reasoning model, 163K ctx
  openrouter/free                         ← auto-picks any available free model
"""

import os
import json
import requests

OPENROUTER_API_KEY  = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL    = os.getenv("OPENROUTER_MODEL", "openrouter/free")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"


def is_available() -> bool:
    return bool(OPENROUTER_API_KEY)


def generate_text(prompt: str, max_tokens: int = 1200, system: str = "") -> str:
    """Call OpenRouter and return the raw assistant response text."""
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY is not set")

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    response = requests.post(
        OPENROUTER_BASE_URL,
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://webbuilder-ai.app",
            "X-Title": "WebBuilder AI",
        },
        json={
            "model": OPENROUTER_MODEL,
            "messages": messages,
            "max_tokens": max_tokens,
        },
        timeout=30,
    )
    response.raise_for_status()
    msg = response.json()["choices"][0]["message"]
    # Some reasoning models put output in 'reasoning' when content is empty
    content = msg.get("content") or msg.get("reasoning") or ""
    return content.strip()


def _parse_json(text: str) -> dict:
    """Extract and parse the first JSON object found in text."""
    # Strip markdown fences if present
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    j_start = text.find("{")
    j_end   = text.rfind("}") + 1
    if j_start >= 0 and j_end > j_start:
        return json.loads(text[j_start:j_end])
    raise ValueError("No JSON object found in response")


def generate_service_descriptions(
    services: list,
    business_name: str,
    business_type: str,
    location: str = "",
    service_categories: list = None,
) -> dict:
    """
    Generate a short AI description for each service/product.
    service_categories: list of {name, category, subcategory} dicts (optional).
    Returns: {service_name: "one-sentence description"}
    Falls back to template strings if API call fails.
    """
    if not services:
        return {}

    # Build a lookup for category/subcategory context per item
    cat_map = {}
    for entry in (service_categories or []):
        name = entry.get("name", "").strip()
        if name:
            cat_map[name] = entry

    # Format each item with its category context for the prompt
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
        f"You are a premium copywriter for {business_name}, "
        f"a {business_type} business{location_part}.\n\n"
        "Write one short, compelling sentence (max 18 words) for each item below.\n"
        "Use the category and subcategory hints to make each description highly specific.\n"
        "Make each description feel premium and desirable — focus on the outcome or feeling.\n"
        "Do NOT use generic phrases like 'experience our' or 'crafted with care'.\n\n"
        "Items:\n" + "\n".join(item_lines) + "\n\n"
        "Return ONLY valid JSON — no markdown, no explanation:\n"
        '{"item_name": "short premium description", ...}'
    )

    try:
        text = generate_text(prompt, max_tokens=500)
        return _parse_json(text)
    except Exception as e:
        print(f"[OPENROUTER] generate_service_descriptions failed: {e}")

    # Fallback descriptions
    return {
        svc: f"Elevate your {svc.lower()} experience with unmatched quality and precision."
        for svc in services
    }


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
    Generate complete website copy — same return shape as ProfessionalCopywriter.
    service_categories: list of {name, category, subcategory} dicts (optional).
    Returns {} on failure so the caller can fall back to Gemini.
    """
    # Build enriched service lines with category/subcategory context
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
        f"Services/Products: {services_str}\n\n"
        "Rules:\n"
        "- Hero headline: 5-10 words, powerful and unique\n"
        "- Avoid clichés: 'best', 'welcome to', 'your one-stop'\n"
        "- Match the style vibe\n"
        "- service_descriptions: one specific sentence per service (15-20 words); "
        "use the category/subcategory hints to make each description highly relevant\n\n"
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
        print(f"[OPENROUTER] generate_website_copy failed: {e}")
        return {}
