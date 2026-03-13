"""
React API Routes Extension
Additional API endpoints for React generation and Vercel deployment
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, List
import json
import os
from datetime import datetime

from react_builder import react_builder
from vercel_deployer import vercel_deployer
from supabase_config import supabase_manager
from pixabay_helper import get_service_images
from professional_copywriter import copywriter
from image_proxy import proxy_service_images
import openrouter_helper
import groq_helper

# Create router
router = APIRouter(prefix="/api/react", tags=["React & Deployment"])


# ============================================================
# REQUEST MODELS
# ============================================================

class ReactBuildRequest(BaseModel):
    """Request to build a React website"""
    session_id: str
    business_name: str
    business_type: str
    business_description: str
    services: List[str]
    # Rich service data: [{name, category, subcategory}] — optional, sent from frontend
    service_categories: Optional[List[Dict]] = None
    location: Optional[str] = ""
    style_vibe: Optional[str] = "modern"
    features: Optional[List[str]] = ["contact"]
    deploy: Optional[bool] = False
    # Images pre-fetched from Pexels during onboarding (or base64 data URLs from user uploads)
    hero_image: Optional[str] = None
    about_image: Optional[str] = None
    logo_image: Optional[str] = None   # base64 data URL if user uploaded a logo
    service_images: Optional[List[Optional[str]]] = None
    gallery_images: Optional[List[Optional[str]]] = None
    # Branding & contact
    brand_color: Optional[str] = None
    contact: Optional[Dict] = None
    use_own_photos: Optional[bool] = False


class DeployRequest(BaseModel):
    """Request to deploy an existing React website"""
    session_id: str
    deploy: bool = True


class StaticHtmlDeployRequest(BaseModel):
    """Deploy a raw HTML string as a static Vercel site"""
    project_name: str
    html_content: str


class EditReactRequest(BaseModel):
    """Request to edit a React website"""
    session_id: str
    edit_request: str
    deploy: Optional[bool] = False


# ============================================================
# ENDPOINTS
# ============================================================

@router.post("/build")
async def build_react_website(request: ReactBuildRequest):
    """
    Build a complete React/Vite website with optional Vercel deployment

    Returns:
        - files: Dictionary of all project files
        - components: List of generated components
        - deployment_url: Vercel URL (if deployed)
        - session_id: Website session ID
    """
    try:
        # Prepare business analysis
        from react_builder import ReactWebsiteBuilder
        import google.generativeai as genai

        model = genai.GenerativeModel('gemini-2.5-flash')

        analysis_prompt = f"""You are an expert business analyst for a website builder.

Business type: {request.business_type}
Business name: {request.business_name}
Location: {request.location}
Description: {request.business_description}
Services: {', '.join(request.services)}
Style: {request.style_vibe}

Return ONLY valid JSON:
{{
  "business_name": "{request.business_name}",
  "business_type": "{request.business_type}",
  "location": {{"city": "city", "country": "country"}},
  "vibe": "{request.style_vibe}",
  "target_audience": "target audience",
  "services": {json.dumps(request.services[:6])},
  "hero_headline": "powerful headline (max 8 words)",
  "hero_subtext": "supporting text (1-2 sentences)",
  "tagline": "memorable 3-5 word tagline",
  "about_text": "compelling 2-3 sentence story",
  "cta_text": "action button text"
}}"""

        resp = model.generate_content(analysis_prompt)
        text = resp.text.strip()
        json_start = text.find('{')
        json_end = text.rfind('}') + 1
        analysis = json.loads(text[json_start:json_end])

        # Generate professional copy (OpenRouter → Gemini fallback)
        print("[COPYWRITER] Generating professional copy...")
        copy_data = copywriter.generate_website_copy(
            business_name=request.business_name,
            business_type=request.business_type,
            business_description=request.business_description,
            services=request.services,
            location=request.location,
            style_vibe=request.style_vibe,
            service_categories=request.service_categories or [],
        )
        print("[SUCCESS] Professional copy generated!")

        # Generate per-service AI descriptions (OpenRouter → Groq fallback)
        service_descriptions = copy_data.get("service_descriptions", {})
        if not service_descriptions:
            if openrouter_helper.is_available():
                print("[OPENROUTER] Generating per-service descriptions...")
                service_descriptions = openrouter_helper.generate_service_descriptions(
                    services=request.services,
                    business_name=request.business_name,
                    business_type=request.business_type,
                    location=request.location or "",
                    service_categories=request.service_categories or [],
                )
            if not service_descriptions and groq_helper.is_available():
                print("[GROQ] Generating per-service descriptions...")
                service_descriptions = groq_helper.generate_service_descriptions(
                    services=request.services,
                    business_name=request.business_name,
                    business_type=request.business_type,
                    location=request.location or "",
                    service_categories=request.service_categories or [],
                )
            print("[SUCCESS] Service descriptions generated!")

        # Normalize service_descriptions keys to exactly match request.services names
        # (AI may return lowercased or slightly different keys)
        if service_descriptions and request.services:
            normalized = {}
            sd_lower = {k.lower(): v for k, v in service_descriptions.items()}
            for svc in request.services:
                val = service_descriptions.get(svc) or sd_lower.get(svc.lower())
                if val:
                    normalized[svc] = val
            service_descriptions = normalized

        # Use Pexels images from onboarding if provided, otherwise fetch from Pixabay
        pexels_service_urls = [url for url in (request.service_images or []) if url]
        if pexels_service_urls:
            print("[PEXELS] Using pre-fetched Pexels images from onboarding...")
            images = [{"url": url} for url in pexels_service_urls[:6]]
            service_images_cdn = {svc: pexels_service_urls[i] for i, svc in enumerate(request.services[:len(pexels_service_urls)])}
            service_images = service_images_cdn  # already permanent URLs, no proxy needed
        else:
            print("[PIXABAY] Fetching dynamic images from Pixabay...")
            service_images_cdn = get_service_images(request.services, request.business_type)
            print("[SUCCESS] Got service images!")
            print("[PROXY] Converting Pixabay URLs to permanent data URLs...")
            service_images = proxy_service_images(service_images_cdn)
            print("[SUCCESS] Images proxied successfully!")
            images = [
                {"url": service_images_cdn[svc]}
                for svc in request.services[:6]
                if service_images_cdn.get(svc)
            ]
            if not images:
                images = [{"url": "https://picsum.photos/seed/business/1920/1080"}]

        # If a dedicated hero image was fetched, use it as images[0] for the hero section
        hero_image_url = request.hero_image
        if hero_image_url:
            images = [{"url": hero_image_url}] + [img for img in images if img.get("url") != hero_image_url]

        # Append dedicated gallery images (indices 7+) so react_builder can use them in the gallery section
        gallery_image_urls = [url for url in (request.gallery_images or []) if url]
        if gallery_image_urls:
            images = images + [{"url": url} for url in gallery_image_urls]

        # Update analysis with AI-generated copy and service images
        analysis["hero_headline"] = copy_data.get("hero_headline", analysis.get("hero_headline"))
        analysis["hero_subtext"] = copy_data.get("hero_subtext", analysis.get("hero_subtext"))
        analysis["tagline"] = copy_data.get("tagline", analysis.get("tagline"))
        analysis["about_text"] = copy_data.get("about_text", analysis.get("about_text"))
        analysis["cta_text"] = copy_data.get("cta_text", analysis.get("cta_text"))
        analysis["service_images"] = service_images
        analysis["about_image"] = request.about_image  # dedicated about section image (Pexels or base64)
        analysis["logo_image"] = request.logo_image    # user-uploaded logo (base64 data URL or None)
        analysis["service_descriptions"] = service_descriptions  # AI descriptions per service
        analysis["service_categories"] = request.service_categories or []  # category/subcategory/price per service
        # Always use the user's exact service names — Gemini may invent/alter them in its JSON
        analysis["services"] = request.services

        # Color schemes — use user brand color if provided
        vibe = analysis.get("vibe", "modern").lower()
        color_schemes = {
            "luxury": {"primary": "#C9A96E", "secondary": "#1A1A1A", "accent": "#F5F5F5"},
            "modern": {"primary": "#6366F1", "secondary": "#0F172A", "accent": "#F59E0B"},
            "cozy": {"primary": "#D97706", "secondary": "#78350F", "accent": "#FEF3C7"},
            "energetic": {"primary": "#EF4444", "secondary": "#991B1B", "accent": "#FEE2E2"},
        }
        colors = color_schemes.get(vibe, color_schemes["modern"])
        if request.brand_color:
            colors["primary"] = request.brand_color

        # Generate React website
        result = await react_builder.generate_react_website(
            session_id=request.session_id,
            analysis=analysis,
            colors=colors,
            images=images,
            features=request.features,
            business_description=request.business_description,
            deploy_to_vercel=request.deploy
        )

        return {
            "success": True,
            "message": "React website generated successfully!",
            "session_id": result["session_id"],
            "files": result["files"],
            "components": result["components"],
            "framework": result["framework"],
            "deployment_url": result.get("deployment_url"),
            "deployment_id": result.get("deployment_id"),
            "deployed": result.get("deployment_url") is not None,
            # Include AI-generated copy and dynamic images for frontend preview
            "hero_headline": analysis.get("hero_headline"),
            "hero_subtext": analysis.get("hero_subtext"),
            "tagline": analysis.get("tagline"),
            "about_text": analysis.get("about_text"),
            "cta_text": analysis.get("cta_text"),
            "service_images": service_images,
            "service_descriptions": service_descriptions  # AI-generated per-service copy
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/deploy")
async def deploy_existing_website(request: DeployRequest):
    """
    Deploy an existing React website to Vercel

    Reads the website files from session storage and deploys
    """
    try:
        if not vercel_deployer.is_enabled():
            raise HTTPException(status_code=400, detail="Vercel not configured")

        # Load website state
        state_path = f"website_states/{request.session_id}.json"
        if not os.path.exists(state_path):
            raise HTTPException(status_code=404, detail="Website not found")

        with open(state_path, "r") as f:
            state = json.load(f)

        # Get website files (assuming they're stored)
        # This is a simplified version - in production, you'd load from storage
        files = state.get("files", {})

        if not files:
            raise HTTPException(status_code=400, detail="No files to deploy")

        analysis = state.get("analysis", {})
        business_name = analysis.get("business_name", "website")

        # Deploy to Vercel
        deployment = await vercel_deployer.create_deployment(
            project_name=business_name,
            files=files,
            env_vars={
                "VITE_SUPABASE_URL": os.getenv("SUPABASE_URL", ""),
                "VITE_SUPABASE_ANON_KEY": os.getenv("SUPABASE_KEY", "")
            }
        )

        if not deployment:
            raise HTTPException(status_code=500, detail="Deployment failed")

        # Update Supabase
        if supabase_manager.is_enabled():
            await supabase_manager.update_website_metadata(
                request.session_id,
                {
                    "deployment_url": deployment.get("url"),
                    "deployment_id": deployment.get("id"),
                    "status": "deployed",
                    "deployed_at": datetime.now().isoformat()
                }
            )

        return {
            "success": True,
            "message": "Website deployed successfully!",
            "deployment_url": deployment.get("url"),
            "deployment_id": deployment.get("id"),
            "status": deployment.get("status")
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/deployment/{deployment_id}")
async def get_deployment_status(deployment_id: str):
    """Get deployment status and details"""
    try:
        if not vercel_deployer.is_enabled():
            raise HTTPException(status_code=400, detail="Vercel not configured")

        deployment = await vercel_deployer.get_deployment(deployment_id)

        if not deployment:
            raise HTTPException(status_code=404, detail="Deployment not found")

        return {
            "success": True,
            "deployment": {
                "id": deployment.get("id"),
                "url": f"https://{deployment.get('url')}",
                "status": deployment.get("readyState"),
                "created": deployment.get("createdAt"),
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/deployments")
async def list_deployments():
    """List all deployments"""
    try:
        if not vercel_deployer.is_enabled():
            raise HTTPException(status_code=400, detail="Vercel not configured")

        deployments = await vercel_deployer.list_deployments()

        return {
            "success": True,
            "count": len(deployments),
            "deployments": [
                {
                    "id": d.get("uid"),
                    "name": d.get("name"),
                    "url": f"https://{d.get('url')}",
                    "status": d.get("state"),
                    "created": d.get("createdAt")
                }
                for d in deployments
            ]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/deployment/{deployment_id}")
async def delete_deployment(deployment_id: str):
    """Delete a Vercel deployment"""
    try:
        if not vercel_deployer.is_enabled():
            raise HTTPException(status_code=400, detail="Vercel not configured")

        success = await vercel_deployer.delete_deployment(deployment_id)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete deployment")

        return {
            "success": True,
            "message": "Deployment deleted successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/website/{session_id}/data")
async def get_website_data(session_id: str):
    """Get all data for a website (bookings, orders, contacts)"""
    try:
        if not supabase_manager.is_enabled():
            raise HTTPException(status_code=400, detail="Supabase not configured")

        # Get website metadata
        website = await supabase_manager.get_website_metadata(session_id)

        # Get all related data
        bookings = await supabase_manager.get_bookings(session_id)
        orders = await supabase_manager.get_orders(session_id)
        contacts = await supabase_manager.get_contacts(session_id)

        return {
            "success": True,
            "website": website,
            "data": {
                "bookings": bookings,
                "orders": orders,
                "contacts": contacts
            },
            "stats": {
                "total_bookings": len(bookings),
                "total_orders": len(orders),
                "total_contacts": len(contacts)
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/deploy-html")
async def deploy_html_as_static(request: StaticHtmlDeployRequest):
    """
    Deploy a raw HTML string as a static Vercel site.
    The deployed site will look exactly like the in-app preview.
    """
    if not vercel_deployer.is_enabled():
        raise HTTPException(status_code=400, detail="Vercel not configured")

    result = await vercel_deployer.deploy_static_html(
        project_name=request.project_name,
        html_content=request.html_content
    )
    if not result:
        raise HTTPException(status_code=500, detail="Deployment failed")

    return {"success": True, "deployment_url": result["url"]}


@router.get("/status")
async def get_system_status():
    """Get status of all integrated services"""
    return {
        "success": True,
        "services": {
            "vercel": {
                "enabled": vercel_deployer.is_enabled(),
                "status": "ready" if vercel_deployer.is_enabled() else "not configured"
            },
            "supabase": {
                "enabled": supabase_manager.is_enabled(),
                "status": "ready" if supabase_manager.is_enabled() else "not configured"
            },
            "react_builder": {
                "enabled": True,
                "status": "ready"
            }
        }
    }
