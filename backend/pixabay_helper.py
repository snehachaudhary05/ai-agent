"""
Pixabay Image Search Helper
Fetches relevant images for services dynamically
"""

import os
import requests
from typing import List, Dict

PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY")
PIXABAY_API_URL = "https://pixabay.com/api/"


def search_image(query: str, business_type: str = "") -> str:
    """
    Search for a single image on Pixabay

    Args:
        query: Service name (e.g., "lehenga", "pizza", "espresso")
        business_type: Business category for better context

    Returns:
        Image URL (webformatURL) or fallback Unsplash image
    """
    if not PIXABAY_API_KEY:
        print("[WARNING] Pixabay API key not found, using fallback images")
        return get_fallback_image(business_type)

    try:
        # Combine query with business type for better results
        search_query = f"{query} {business_type}".strip()

        params = {
            "key": PIXABAY_API_KEY,
            "q": search_query,
            "image_type": "photo",
            "per_page": 3,
            "safesearch": "true"
        }

        response = requests.get(PIXABAY_API_URL, params=params, timeout=5)
        response.raise_for_status()

        data = response.json()

        if data.get("hits") and len(data["hits"]) > 0:
            hit = data["hits"][0]

            # Pixabay has multiple URL formats - try them in order of preference
            # Use imageURL (full size, user_id format) or previewURL (stable CDN)
            image_url = None

            # Try to construct a stable Pixabay CDN URL
            image_id = hit.get("id")
            user_id = hit.get("user_id")

            if image_id and user_id:
                # Try the user-based URL format which may be more stable
                # Format: https://cdn.pixabay.com/photo/{upload_date}/{user_id}/{image_id}_640.jpg
                # Since we don't have upload date, try the preview URL which uses CDN
                preview_url = hit.get("previewURL")  # This uses CDN and is stable
                if preview_url and "cdn.pixabay.com" in preview_url:
                    # Modify preview URL to get higher resolution
                    # Preview is 150px, we want 640px
                    image_url = preview_url.replace("_150.", "_640.")
                    print("[SUCCESS] Using modified Pixabay CDN URL")
                else:
                    # Fallback to webformatURL
                    image_url = hit.get("webformatURL")
                    print("[SUCCESS] Using webformatURL")
            else:
                # If ID/user_id not available, use webformatURL
                image_url = hit.get("webformatURL")
                print("[SUCCESS] Using webformatURL")

            return image_url if image_url else get_fallback_image(business_type)
        else:
            print("[WARNING] No Pixabay results, using fallback")
            return get_fallback_image(business_type)

    except Exception as e:
        print("[ERROR] Pixabay API error, using fallback")
        return get_fallback_image(business_type)


def get_service_images(services: List[str], business_type: str = "") -> Dict[str, str]:
    """
    Get images for multiple services

    Args:
        services: List of service names
        business_type: Business category

    Returns:
        Dict mapping service name to image URL
    """
    image_map = {}

    for service in services[:6]:  # Limit to 6 services
        service_name = service.strip()
        if service_name:
            image_url = search_image(service_name, business_type)
            # If fallback was returned, use the service name as unique seed
            # so each service card shows a different image
            if "seed/business" in image_url:
                seed = service_name.lower().replace(' ', '').replace("'", '')
                image_url = f"https://picsum.photos/seed/{seed}/640/400"
            image_map[service_name] = image_url

    return image_map


def get_fallback_image(business_type: str) -> str:
    """
    Get a fallback Unsplash image based on business type
    """
    fallback_images = {
        "boutique": "https://picsum.photos/seed/boutique/640/400",
        "cafe": "https://picsum.photos/seed/cafe/640/400",
        "restaurant": "https://picsum.photos/seed/restaurant/640/400",
        "gym": "https://picsum.photos/seed/gym/640/400",
        "salon": "https://picsum.photos/seed/salon/640/400",
        "hotel": "https://picsum.photos/seed/hotel/640/400",
        "yoga": "https://picsum.photos/seed/yoga/640/400",
        "bakery": "https://picsum.photos/seed/bakery/640/400",
    }

    return fallback_images.get(business_type, "https://picsum.photos/seed/business/640/400")


# Test function
if __name__ == "__main__":
    # Test with different services
    test_services = ["Lehenga", "Saree", "Kurti"]
    print("Testing Pixabay image search...")
    images = get_service_images(test_services, "boutique")

    for service, url in images.items():
        print("Image fetched successfully")
