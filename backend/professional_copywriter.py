"""
Professional Copywriter Module
Generates compelling, professional copy for websites.
Uses OpenRouter first (if OPENROUTER_API_KEY is set), falls back to Gemini.
"""

import os
import json
import google.generativeai as genai
import openrouter_helper

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


class ProfessionalCopywriter:
    """Generates professional, engaging copy for websites"""

    def __init__(self):
        self.model = genai.GenerativeModel('gemini-2.0-flash')

    def generate_website_copy(
        self,
        business_name: str,
        business_type: str,
        business_description: str,
        services: list,
        location: str = "",
        style_vibe: str = "modern",
        service_categories: list = None,
    ) -> dict:
        """
        Generate professional copy for all website sections

        Returns:
            dict with hero_headline, hero_subtext, about_text, tagline, service_descriptions, cta_text
        """

        # Build enriched service lines with category/subcategory hints
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
        services_display = ', '.join(service_lines) if service_lines else 'Not specified'

        prompt = f"""You are a world-class copywriter for a top web design agency. Create compelling, professional copy for a website.

BUSINESS DETAILS:
- Name: {business_name}
- Type: {business_type}
- Description: {business_description}
- Services: {services_display}
- Location: {location if location else 'Not specified'}
- Style/Vibe: {style_vibe}

TASK: Generate professional, engaging copy that:
✓ Captures the brand's personality
✓ Speaks directly to the target audience
✓ Is compelling and memorable (NOT generic!)
✓ Uses emotional triggers and benefits
✓ Avoids clichés like "best", "welcome to", "your one-stop"
✓ Matches the {style_vibe} style

COPY TO GENERATE:

1. **Hero Headline** (5-10 words)
   - Should be powerful, memorable, and unique
   - Focus on the transformation/feeling, not just the service
   - Examples:
     * Coffee shop: "Where Every Cup Tells a Story"
     * Gym: "Your Journey to Unstoppable Starts Here"
     * Salon: "Confidence Crafted, Beauty Unveiled"

2. **Hero Subtext** (15-25 words)
   - Expand on the headline with specific details
   - Mention location if provided
   - Create desire and urgency
   - Example: "Artisan coffee and fresh pastries in the heart of Mumbai. Your daily escape awaits."

3. **About Section** (40-60 words)
   - Tell the story behind the business
   - Use "we" or "our" voice (first person)
   - Explain what makes them unique
   - Connect emotionally with the reader
   - Example: "Born from a passion for exceptional coffee, we bring together the finest beans from around the world with a warm, inviting atmosphere that feels like home. Every visit is a chance to pause, connect, and savor the moment."

4. **Tagline** (3-6 words)
   - Brand slogan that's catchy and memorable
   - Example: "Fuel Your Fire" (gym), "Crafted with Care" (cafe)

5. **Call-to-Action** (2-4 words)
   - Action-oriented and specific
   - Examples: "Book Your Spot", "Start Your Journey", "Reserve a Table", "Get Started Today"

6. **Service Descriptions** (for each service, 15-25 words each)
   - Focus on benefits, not features
   - Use sensory language and make it desirable
   - Use the [Category] and [Subcategory] hints to make each description highly specific

Return ONLY valid JSON in this exact format:
{{
  "hero_headline": "string",
  "hero_subtext": "string",
  "about_text": "string",
  "tagline": "string",
  "cta_text": "string",
  "service_descriptions": {{
    "service_name": "compelling description"
  }}
}}

NO explanations, NO markdown, JUST the JSON."""

        # ── Try OpenRouter first (free, saves Gemini quota) ─────────────────────
        if openrouter_helper.is_available():
            print("[COPYWRITER] Using OpenRouter AI...")
            result = openrouter_helper.generate_website_copy(
                business_name=business_name,
                business_type=business_type,
                business_description=business_description,
                services=services,
                location=location,
                style_vibe=style_vibe,
                service_categories=service_categories,
            )
            if result:
                print("[SUCCESS] OpenRouter copy generated!")
                return result
            print("[WARN] OpenRouter failed, falling back to Gemini...")

        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()

            # Extract JSON from response (handle markdown code blocks)
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            copy_data = json.loads(response_text)

            print("[SUCCESS] Generated professional copy")
            return copy_data

        except Exception as e:
            print("[WARNING] AI copywriting failed, using enhanced fallback")
            return self._generate_enhanced_fallback(
                business_name, business_type, business_description, services, location, style_vibe
            )

    def _generate_enhanced_fallback(
        self,
        business_name: str,
        business_type: str,
        business_description: str,
        services: list,
        location: str,
        style_vibe: str
    ) -> dict:
        """Generate enhanced fallback copy with better templates"""

        # Business-type specific templates
        templates = {
            "cafe": {
                "hero_headline": f"Where Coffee Meets Community",
                "hero_subtext": f"Experience artisan coffee and warm hospitality at {business_name}. {f'Proudly serving {location}.' if location else 'Your daily ritual starts here.'}",
                "tagline": "Crafted with Passion",
                "cta_text": "Visit Us Today"
            },
            "restaurant": {
                "hero_headline": f"A Culinary Journey Awaits",
                "hero_subtext": f"Savor exceptional flavors and unforgettable moments at {business_name}. {f'Located in the heart of {location}.' if location else 'Every meal tells a story.'}",
                "tagline": "Taste the Difference",
                "cta_text": "Reserve a Table"
            },
            "gym": {
                "hero_headline": f"Transform Your Body, Elevate Your Life",
                "hero_subtext": f"Join {business_name} and discover what you're truly capable of. {f'Now in {location}.' if location else 'Your fitness journey starts now.'}",
                "tagline": "Stronger Every Day",
                "cta_text": "Start Your Journey"
            },
            "salon": {
                "hero_headline": f"Where Beauty Meets Artistry",
                "hero_subtext": f"Experience transformative beauty services at {business_name}. {f'Serving {location} with excellence.' if location else 'You deserve to shine.'}",
                "tagline": "Unleash Your Glow",
                "cta_text": "Book Your Appointment"
            },
            "yoga": {
                "hero_headline": f"Find Your Balance, Transform Your Life",
                "hero_subtext": f"Discover inner peace and physical strength at {business_name}. {f'Your sanctuary in {location}.' if location else 'Every breath brings you closer.'}",
                "tagline": "Breathe, Flow, Transform",
                "cta_text": "Join a Class"
            },
            "hotel": {
                "hero_headline": f"Your Home Away From Home",
                "hero_subtext": f"Luxury, comfort, and hospitality await at {business_name}. {f'Experience the best of {location}.' if location else 'Where memories are made.'}",
                "tagline": "Stay Extraordinary",
                "cta_text": "Book Your Stay"
            },
            "boutique": {
                "hero_headline": f"Style That Speaks Your Language",
                "hero_subtext": f"Curated collections and timeless pieces at {business_name}. {f'Your destination in {location}.' if location else 'Discover your signature look.'}",
                "tagline": "Wear Your Story",
                "cta_text": "Shop Now"
            },
            "clinic": {
                "hero_headline": f"Your Health, Our Priority",
                "hero_subtext": f"Compassionate care and expert treatment at {business_name}. {f'Serving {location} with dedication.' if location else 'Your wellness journey begins here.'}",
                "tagline": "Caring for You",
                "cta_text": "Book Appointment"
            },
            "real-estate": {
                "hero_headline": f"Find the Home You've Always Dreamed Of",
                "hero_subtext": f"Discover premium properties and expert guidance at {business_name}. {f'Your trusted real estate partner in {location}.' if location else 'Your perfect home is just a step away.'}",
                "tagline": "Keys to Your Future",
                "cta_text": "Explore Properties"
            },
            "coaching": {
                "hero_headline": f"Unlock Your Full Potential",
                "hero_subtext": f"Expert guidance and proven strategies at {business_name}. {f'Empowering learners in {location}.' if location else 'Your transformation starts today.'}",
                "tagline": "Learn. Grow. Succeed.",
                "cta_text": "Join a Class"
            },
            "online-store": {
                "hero_headline": f"Shop Smart, Live Better",
                "hero_subtext": f"Curated collections and seamless shopping at {business_name}. {f'Delivering to {location} and beyond.' if location else 'Quality products delivered to your door.'}",
                "tagline": "Style Meets Convenience",
                "cta_text": "Shop Now"
            },
            "default": {
                "hero_headline": f"Excellence in Every Detail",
                "hero_subtext": f"Experience exceptional service at {business_name}. {f'Proudly serving {location}.' if location else 'Where quality meets passion.'}",
                "tagline": "Beyond Expectations",
                "cta_text": "Get Started"
            }
        }

        template = templates.get(business_type, templates["default"])

        # Generate enhanced about text
        about_templates = {
            "cafe": f"At {business_name}, we believe coffee is more than a drink—it's an experience. Our carefully sourced beans, expert baristas, and warm atmosphere create the perfect space to connect, create, or simply unwind. Every cup is crafted with passion and precision.",
            "restaurant": f"Welcome to {business_name}, where culinary tradition meets modern innovation. Our chefs craft each dish with premium ingredients and time-honored techniques, creating flavors that delight and inspire. Join us for an unforgettable dining experience.",
            "gym": f"{business_name} isn't just a gym—it's a community of driven individuals committed to transformation. With state-of-the-art equipment, expert trainers, and proven programs, we provide everything you need to reach your fitness goals and beyond.",
            "salon": f"At {business_name}, we're passionate about bringing out your natural beauty. Our talented stylists stay ahead of trends while honoring timeless techniques. From cuts to color, we deliver results that make you feel confident and radiant.",
            "real-estate": f"At {business_name}, we turn the dream of owning the perfect property into reality. With deep local expertise, a trusted network of developers, and a client-first approach, we guide you through every step of your property journey—from search to possession. Your ideal home is closer than you think.",
            "coaching": f"At {business_name}, we believe every learner has extraordinary potential waiting to be unlocked. Our experienced mentors combine proven teaching methods with personalized attention to help you achieve breakthroughs—in academics, skills, or life. Your success story starts here.",
            "online-store": f"{business_name} brings you a handpicked selection of quality products designed to elevate your everyday life. From discovery to doorstep, we make shopping effortless, enjoyable, and rewarding. Every order is packed with care and delivered with a promise of satisfaction.",
            "default": f"{business_name} is dedicated to providing exceptional {business_type} services. We combine expertise, quality, and genuine care to ensure every experience exceeds your expectations. Let us show you the difference true dedication makes."
        }

        about_text = about_templates.get(business_type, about_templates["default"])

        # Add business description context if provided
        if business_description and len(business_description) > 20:
            about_text = f"{about_text} {business_description}"

        return {
            "hero_headline": template["hero_headline"],
            "hero_subtext": template["hero_subtext"],
            "about_text": about_text,
            "tagline": template["tagline"],
            "cta_text": template["cta_text"],
            "service_descriptions": {}
        }


# Singleton instance
copywriter = ProfessionalCopywriter()
