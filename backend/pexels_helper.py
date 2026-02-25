"""
Pexels Image Search Helper
Fetches high-quality realistic stock photos via Pexels API.
"""

import os
import random
import requests
from typing import Optional

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
PEXELS_SEARCH_URL = "https://api.pexels.com/v1/search"


def search_pexels_image(query: str, orientation: str = "landscape") -> Optional[str]:
    """
    Search for a single photo on Pexels.

    Args:
        query: Search terms (e.g., "yoga fitness studio")
        orientation: "landscape", "portrait", or "square"

    Returns:
        Direct image URL (large2x quality) or None on failure.
    """
    results = search_pexels_images(query, count=1, orientation=orientation)
    return results[0] if results else None


def search_pexels_images(query: str, count: int = 1, orientation: str = "landscape") -> list:
    """
    Search for multiple unique photos on Pexels.

    Args:
        query: Search terms (e.g., "yoga fitness studio")
        count: Number of unique image URLs to return
        orientation: "landscape", "portrait", or "square"

    Returns:
        List of image URLs (large2x quality). Empty list on failure.
    """
    if not PEXELS_API_KEY:
        print("[Pexels] WARNING: PEXELS_API_KEY not set")
        return []

    try:
        headers = {"Authorization": PEXELS_API_KEY}
        per_page = min(max(count * 3, 15), 80)  # fetch extras for variety
        params = {"query": query, "per_page": per_page}
        if orientation:
            params["orientation"] = orientation
        response = requests.get(PEXELS_SEARCH_URL, headers=headers, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        photos = data.get("photos", [])

        if not photos:
            print(f"[Pexels] No results for '{query}'")
            return []

        # Shuffle and pick `count` unique images
        pool = photos[:min(len(photos), per_page)]
        random.shuffle(pool)
        urls = []
        for photo in pool:
            src = photo["src"]
            url = src.get("large2x") or src.get("large") or src.get("original")
            if url:
                urls.append(url)
                print(f"[Pexels] Found image for '{query}' (photo id: {photo['id']})")
            if len(urls) >= count:
                break

        return urls

    except Exception as e:
        print(f"[Pexels] Error: {e}")
        return []
