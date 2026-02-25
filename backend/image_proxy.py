"""
Image Proxy - Download and cache images from Pixabay
Converts expiring Pixabay URLs to permanent base64 data URLs
"""

import requests
import base64
from typing import Dict, List

def download_and_encode_image(image_url: str) -> str:
    """
    Download image from URL and convert to base64 data URL

    Args:
        image_url: Original image URL (e.g., Pixabay URL)

    Returns:
        Base64 data URL (permanent, doesn't expire)
    """
    try:
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()

        # Get content type
        content_type = response.headers.get('Content-Type', 'image/jpeg')

        # Convert to base64
        image_data = base64.b64encode(response.content).decode('utf-8')

        # Return as data URL
        data_url = f"data:{content_type};base64,{image_data}"

        print("[SUCCESS] Downloaded and encoded image")
        return data_url

    except Exception as e:
        print("[ERROR] Failed to download image")
        return None


def proxy_service_images(service_images: Dict[str, str]) -> Dict[str, str]:
    """
    Download all service images and convert to base64 data URLs

    Args:
        service_images: Dict mapping service name to Pixabay URL

    Returns:
        Dict mapping service name to base64 data URL
    """
    proxied_images = {}

    for service_name, image_url in service_images.items():
        # Download and encode the image
        data_url = download_and_encode_image(image_url)

        if data_url:
            proxied_images[service_name] = data_url
        else:
            # If download fails, keep original URL (will fallback on frontend)
            proxied_images[service_name] = image_url

    return proxied_images
