"""
React Website Builder
Generates complete React/Vite websites from business descriptions
"""

import json
import os
import re
import traceback
from typing import Dict, List, Optional
import google.generativeai as genai
from react_template_generator import react_template
from vercel_deployer import vercel_deployer
from supabase_config import supabase_manager

# Initialize Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


class ReactWebsiteBuilder:
    """Builds complete React websites with AI"""

    def __init__(self):
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    async def generate_react_website(
        self,
        session_id: str,
        analysis: Dict,
        colors: Dict,
        images: List[Dict],
        features: List[str],
        business_description: str,
        deploy_to_vercel: bool = False
    ) -> Dict:
        """
        Generate a complete React/Vite website

        Args:
            session_id: Unique session identifier
            analysis: Business analysis data
            colors: Color scheme
            images: List of images to use
            features: List of features to include
            business_description: Full business description
            deploy_to_vercel: Whether to deploy to Vercel

        Returns:
            Dict with website files and deployment info
        """

        business_name = analysis.get("business_name", "My Business")
        business_type = analysis.get("business_type", "business")

        print(f" Generating React website for: {business_name}")

        # Step 1: Generate React components using AI
        components = await self._generate_components(analysis, colors, features, images)

        # Step 2: Extract Supabase features
        supabase_features = self._extract_supabase_features(features)

        # Step 3: Create theme configuration
        theme = {
            "colors": colors,
            "fonts": {
                "heading": "Poppins",
                "body": "Inter"
            }
        }

        # Step 4: Generate all project files
        project_files = react_template.generate_complete_project(
            project_name=business_name,
            description=business_description,
            components=components,
            theme=theme,
            features=supabase_features + ["routing", "animation", "forms", "icons"],
            supabase_config={
                "url": os.getenv("SUPABASE_URL", ""),
                "key": os.getenv("SUPABASE_KEY", "")
            }
        )

        # Step 5: Save to Supabase
        if supabase_manager.is_enabled():
            await supabase_manager.save_website_metadata({
                "session_id": session_id,
                "title": business_name,
                "description": business_description,
                "framework": "react-vite",
                "features": supabase_features,
                "status": "generated",
                "metadata": {
                    "business_type": business_type,
                    "colors": colors,
                    "component_count": len(components)
                }
            })

        result = {
            "session_id": session_id,
            "files": project_files,
            "components": [c["name"] for c in components],
            "framework": "react-vite",
            "deployment_url": None,
            "deployment_id": None
        }

        # Step 6: Deploy to Vercel if requested
        if deploy_to_vercel and vercel_deployer.is_enabled():
            print(f" Deploying {business_name} to Vercel...")
            deployment = await vercel_deployer.create_deployment(
                project_name=business_name,
                files=project_files,
                env_vars={
                    "VITE_SUPABASE_URL": os.getenv("SUPABASE_URL", ""),
                    "VITE_SUPABASE_ANON_KEY": os.getenv("SUPABASE_KEY", "")
                }
            )

            if deployment:
                result["deployment_url"] = deployment.get("url")
                result["deployment_id"] = deployment.get("id")

                # Update Supabase with deployment URL
                if supabase_manager.is_enabled():
                    await supabase_manager.update_website_metadata(
                        session_id,
                        {
                            "deployment_url": deployment.get("url"),
                            "status": "deployed"
                        }
                    )

                print(f"[OK] Deployed successfully: {deployment.get('url')}")
            else:
                print(f"[ERROR] Deployment failed")

        return result

    async def _generate_components(
        self,
        analysis: Dict,
        colors: Dict,
        features: List[str],
        images: List[Dict]
    ) -> List[Dict]:
        """Generate React components using AI"""

        business_name = analysis.get("business_name", "My Business")
        business_type = analysis.get("business_type", "business")
        services = analysis.get("services", [])
        hero_headline = analysis.get("hero_headline", f"Welcome to {business_name}")
        hero_subtext = analysis.get("hero_subtext", "")
        about_text = analysis.get("about_text", "")
        cta_text = analysis.get("cta_text", "Get Started")

        # Hero image
        hero_image = images[0].get("url") if images else "https://picsum.photos/seed/business/1920/1080"

        prompt = f"""Generate modern React components for a {business_type} website.

Business: {business_name}
Style: Modern, responsive, using Tailwind CSS
Colors: Primary {colors.get('primary')}, Secondary {colors.get('secondary')}

Generate these components:

1. **Navbar** - Fixed navigation with logo, links, mobile menu
2. **Hero** - Eye-catching hero section with headline: "{hero_headline}"
3. **Services** - Grid showcasing these services: {', '.join(services[:6])}
4. **About** - About section with text: "{about_text}"
5. **Contact** - Contact form with Supabase integration

For EACH component, return VALID JSX code using:
- Tailwind CSS classes
- Modern React hooks (useState, useEffect)
- Responsive design (mobile-first)
- Smooth animations
- Clean, production-ready code

Return ONLY this JSON structure:
{{
  "components": [
    {{
      "name": "Navbar",
      "description": "Navigation bar",
      "code": "full JSX component code here"
    }},
    {{
      "name": "Hero",
      "description": "Hero section",
      "code": "full JSX component code here"
    }},
    ...
  ]
}}"""

        # NOTE: Skipping Gemini AI generation due to consistent timeouts
        # Using high-quality fallback components instead (faster & more reliable)
        print(f"[INFO] Generating components using production-ready templates...")
        try:
            return self._generate_fallback_components(analysis, colors, images, features)
        except Exception as e:
            print(f"[ERROR] Component generation failed:")
            print(traceback.format_exc())
            raise

    def _generate_fallback_components(
        self,
        analysis: Dict,
        colors: Dict,
        images: List[Dict],
        features: List[str]
    ) -> List[Dict]:
        """Generate comprehensive components based on selected features"""

        business_name = analysis.get("business_name", "My Business")
        hero_headline = analysis.get("hero_headline", f"Welcome to {business_name}")
        hero_subtext = analysis.get("hero_subtext", "")
        services = analysis.get("services", [])
        service_descriptions = analysis.get("service_descriptions", {})

        # Build category/subcategory/price lookup per service
        service_categories_data = analysis.get("service_categories", [])
        service_meta = {}
        for item in service_categories_data:
            name = item.get("name", "").strip()
            if name:
                service_meta[name] = {
                    "category": item.get("category", "").strip().title(),
                    "subcategory": item.get("subcategory", "").strip().title(),
                    "price": item.get("price", "").strip(),
                }

        hero_image = images[0].get("url") if images else "https://picsum.photos/seed/business/1920/1080"
        # Use dedicated about image if provided, otherwise reuse hero image
        about_image = analysis.get("about_image") or hero_image
        # Service images start from index 1 (index 0 is the hero image slot)
        service_images_list = images[1:] if len(images) > 1 else images

        navbar_code = f"""import React, {{ useState, useEffect }} from 'react'

function Navbar() {{
  const [isOpen, setIsOpen] = useState(false)
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {{
    const handleScroll = () => {{
      setScrolled(window.scrollY > 50)
    }}
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }}, [])

  const scrollToSection = (e, sectionId) => {{
    e.preventDefault()
    const element = document.getElementById(sectionId)
    if (element) {{
      const offsetTop = element.offsetTop - 80
      window.scrollTo({{
        top: offsetTop,
        behavior: 'smooth'
      }})
      setIsOpen(false)
    }}
  }}

  return (
    <nav className={{`fixed w-full z-50 transition-all duration-300 ${{scrolled ? 'bg-white/95 backdrop-blur-lg shadow-lg' : 'bg-white/80 backdrop-blur-sm'}}`}}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-20">
          {{/* Logo */}}
          <div className="flex items-center cursor-pointer" onClick={{(e) => scrollToSection(e, 'hero')}}>
            <div className="w-10 h-10 bg-gradient-to-br from-primary to-secondary rounded-xl mr-3 flex items-center justify-center">
              <span className="text-white font-bold text-xl">{{"{business_name[0]}"}}</span>
            </div>
            <span className="text-2xl font-bold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
              {business_name}
            </span>
          </div>

          {{/* Desktop Menu */}}
          <div className="hidden md:flex items-center space-x-8">
            <a href="#hero" onClick={{(e) => scrollToSection(e, 'hero')}} className="text-gray-700 hover:text-primary font-semibold transition-colors cursor-pointer">Home</a>
            <a href="#about" onClick={{(e) => scrollToSection(e, 'about')}} className="text-gray-700 hover:text-primary font-semibold transition-colors cursor-pointer">About</a>
            <a href="#services" onClick={{(e) => scrollToSection(e, 'services')}} className="text-gray-700 hover:text-primary font-semibold transition-colors cursor-pointer">Services</a>
            <a href="#contact" onClick={{(e) => scrollToSection(e, 'contact')}} className="px-6 py-3 bg-gradient-to-r from-primary to-secondary text-white font-bold rounded-xl hover:shadow-xl hover:scale-105 transition-all duration-300 cursor-pointer">
              Contact Us
            </a>
          </div>

          {{/* Mobile Menu Button */}}
          <button
            className="md:hidden p-2 rounded-lg hover:bg-gray-100 transition-colors"
            onClick={{() => setIsOpen(!isOpen)}}
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              {{isOpen ? (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={{2}} d="M6 18L18 6M6 6l12 12" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={{2}} d="M4 6h16M4 12h16M4 18h16" />
              )}}
            </svg>
          </button>
        </div>

        {{/* Mobile Menu */}}
        {{isOpen && (
          <div className="md:hidden py-4 space-y-3 border-t border-gray-200">
            <a href="#hero" onClick={{(e) => scrollToSection(e, 'hero')}} className="block py-3 px-4 rounded-lg hover:bg-gray-100 font-semibold transition-colors cursor-pointer">Home</a>
            <a href="#about" onClick={{(e) => scrollToSection(e, 'about')}} className="block py-3 px-4 rounded-lg hover:bg-gray-100 font-semibold transition-colors cursor-pointer">About</a>
            <a href="#services" onClick={{(e) => scrollToSection(e, 'services')}} className="block py-3 px-4 rounded-lg hover:bg-gray-100 font-semibold transition-colors cursor-pointer">Services</a>
            <a href="#products" onClick={{(e) => scrollToSection(e, 'products')}} className="block py-3 px-4 rounded-lg hover:bg-gray-100 font-semibold transition-colors cursor-pointer">Products</a>
            <a href="#contact" onClick={{(e) => scrollToSection(e, 'contact')}} className="block py-3 px-4 bg-gradient-to-r from-primary to-secondary text-white font-bold rounded-lg text-center cursor-pointer">Contact Us</a>
          </div>
        )}}
      </div>
    </nav>
  )
}}

export default Navbar
"""

        hero_code = f"""import React from 'react'

function Hero() {{
  return (
    <section id="hero" className="relative min-h-[600px] md:min-h-[720px] flex items-center justify-center text-white overflow-hidden pt-20">
      {{/* Background Image with Overlay */}}
      <div
        className="absolute inset-0 bg-cover bg-center scale-105 animate-slow-zoom"
        style={{{{backgroundImage: 'url({hero_image})'}}}}
      >
        <div className="absolute inset-0 bg-gradient-to-br from-primary/80 via-secondary/70 to-black/60"></div>
      </div>

      {{/* Animated Gradient Orbs */}}
      <div className="absolute top-20 left-10 w-72 h-72 bg-primary/30 rounded-full blur-3xl animate-pulse"></div>
      <div className="absolute bottom-20 right-10 w-96 h-96 bg-secondary/30 rounded-full blur-3xl animate-pulse delay-1000"></div>

      {{/* Content */}}
      <div className="relative z-10 text-center px-4 max-w-5xl mx-auto">
        <div className="mb-4 md:mb-6 inline-block px-4 md:px-6 py-2 md:py-3 bg-white/10 backdrop-blur-md rounded-full border border-white/20">
          <span className="text-xs md:text-sm font-semibold tracking-wide">Welcome to Excellence</span>
        </div>

        <h1 className="text-3xl sm:text-4xl md:text-6xl lg:text-7xl xl:text-8xl font-bold mb-6 md:mb-8 leading-tight animate-fade-in-up">
          {hero_headline}
        </h1>

        <p className="text-base sm:text-lg md:text-xl lg:text-2xl xl:text-3xl mb-8 md:mb-12 opacity-95 max-w-3xl mx-auto leading-relaxed animate-fade-in-up animation-delay-200">
          {hero_subtext}
        </p>

        <div className="flex gap-3 md:gap-6 justify-center flex-wrap animate-fade-in-up animation-delay-400">
          <a
            href="#contact"
            className="px-6 md:px-10 py-3 md:py-5 bg-white text-primary font-bold text-sm md:text-lg rounded-xl md:rounded-2xl hover:shadow-2xl hover:scale-105 transition-all duration-300 transform"
          >
            Get Started Today
          </a>
          <a
            href="#services"
            className="px-6 md:px-10 py-3 md:py-5 bg-white/10 backdrop-blur-md border-2 border-white/30 text-white font-bold text-sm md:text-lg rounded-xl md:rounded-2xl hover:bg-white/20 hover:scale-105 transition-all duration-300 transform"
          >
            Explore Services
          </a>
        </div>

        {{/* Scroll Indicator */}}
        <div className="absolute bottom-10 left-1/2 transform -translate-x-1/2 animate-bounce">
          <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={{2}} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
          </svg>
        </div>
      </div>
    </section>
  )
}}

export default Hero
"""

        # Generate proper image URLs for services using dynamic Pixabay images
        _MARKETING_PREFIX = re.compile(
            r'^(premium|special|classic|deluxe|signature|house|royal|chef\'?s?|fresh|homemade)\s+',
            re.IGNORECASE
        )

        def _clean_name(name: str) -> str:
            """Strip common marketing prefixes from service display names."""
            return _MARKETING_PREFIX.sub('', name).strip()

        services_with_images = []
        for idx, service in enumerate(services[:6]):
            # Use pre-fetched service images (offset by 1 since images[0] is the hero)
            if idx < len(service_images_list) and service_images_list[idx].get("url"):
                img_url = service_images_list[idx].get("url")
            else:
                # Fallback: unique seed per service so cards don't all look the same
                seed = service.lower().replace(' ', '').replace("'", '')
                img_url = f"https://picsum.photos/seed/{seed}/640/400"

            meta = service_meta.get(service, {})
            services_with_images.append({
                "name": _clean_name(service),
                "image": img_url,
                "description": service_descriptions.get(service, f"Elevate your {_clean_name(service).lower()} experience with unmatched quality and precision."),
                "category": meta.get("category", ""),
                "subcategory": meta.get("subcategory", ""),
                "price": meta.get("price", ""),
            })

        services_code = f"""import React, {{ useState }} from 'react'

const services = {json.dumps(services_with_images)}

// Build case-insensitive deduplicated category list, preserving first-seen casing
const _catMap = new Map()
services.filter(s => s.category).forEach(s => {{
  const key = s.category.toLowerCase()
  if (!_catMap.has(key)) _catMap.set(key, s.category)
}})
const allCategories = ['All', ...Array.from(_catMap.values())]
const hasCategories = allCategories.length > 1

function Services() {{
  const [activeCategory, setActiveCategory] = useState('All')
  const [activeSubcategory, setActiveSubcategory] = useState('All')

  const filteredByCategory = activeCategory === 'All'
    ? services
    : services.filter(s => s.category?.toLowerCase() === activeCategory.toLowerCase())

  const _subMap = new Map()
  filteredByCategory.filter(s => s.subcategory).forEach(s => {{
    const key = s.subcategory.toLowerCase()
    if (!_subMap.has(key)) _subMap.set(key, s.subcategory)
  }})
  const subcategories = activeCategory === 'All' ? [] : ['All', ...Array.from(_subMap.values())]
  const hasSubcategories = subcategories.length > 1

  const filtered = (hasSubcategories && activeSubcategory !== 'All')
    ? filteredByCategory.filter(s => s.subcategory?.toLowerCase() === activeSubcategory.toLowerCase())
    : filteredByCategory

  const handleCategoryChange = (cat) => {{
    setActiveCategory(cat)
    setActiveSubcategory('All')
  }}

  return (
    <section id="services" className="py-20 bg-gradient-to-br from-gray-50 to-white">
      <div className="container-custom">
        <div className="text-center mb-10 md:mb-12">
          <h2 className="text-3xl md:text-5xl lg:text-6xl font-bold mb-3 md:mb-4 bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
            Our Services
          </h2>
          <p className="text-base md:text-xl text-gray-600 max-w-2xl mx-auto px-4">
            Discover our premium offerings designed to exceed your expectations
          </p>
        </div>

        {{/* Category filter pills — only shown when categories exist */}}
        {{hasCategories && (
          <div className="flex flex-wrap gap-2 justify-center mb-4">
            {{allCategories.map(cat => (
              <button
                key={{cat}}
                onClick={{() => handleCategoryChange(cat)}}
                className={{`px-5 py-2 rounded-full font-semibold text-sm transition-all duration-300 ${{
                  activeCategory === cat
                    ? 'bg-gradient-to-r from-primary to-secondary text-white shadow-lg scale-105'
                    : 'bg-white text-gray-600 border border-gray-200 hover:border-primary hover:text-primary'
                }}`}}
              >
                {{cat}}
              </button>
            ))}}
          </div>
        )}}

        {{/* Subcategory filter pills — only shown when a category with multiple subcategories is selected */}}
        {{hasSubcategories && (
          <div className="flex flex-wrap gap-2 justify-center mb-8">
            {{subcategories.map(sub => (
              <button
                key={{sub}}
                onClick={{() => setActiveSubcategory(sub)}}
                className={{`px-4 py-1.5 rounded-full text-xs font-medium transition-all duration-300 ${{
                  activeSubcategory === sub
                    ? 'bg-secondary text-white shadow-md'
                    : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
                }}`}}
              >
                {{sub}}
              </button>
            ))}}
          </div>
        )}}

        {{!hasCategories && <div className="mb-8" />}}

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 md:gap-8">
          {{filtered.map((service, index) => (
            <div
              key={{index}}
              className="group bg-white rounded-2xl md:rounded-3xl shadow-xl hover:shadow-2xl transition-all duration-500 hover:-translate-y-2 overflow-hidden border border-gray-100"
            >
              {{/* Service Image */}}
              <div className="relative h-48 md:h-56 overflow-hidden">
                <img
                  src={{service.image}}
                  alt={{service.name}}
                  className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
                  onError={{(e) => {{
                    e.target.src = 'https://picsum.photos/seed/service/640/400'
                  }}}}
                />
                {{service.category && (
                  <span className="absolute top-3 left-3 bg-white/90 backdrop-blur-sm text-primary text-xs font-semibold px-3 py-1 rounded-full shadow-sm">
                    {{service.category}}
                  </span>
                )}}
                <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
              </div>

              {{/* Service Content */}}
              <div className="p-5 md:p-8">
                <h3 className="text-xl md:text-2xl font-bold mb-2 text-gray-900 group-hover:text-primary transition-colors">
                  {{service.name}}
                </h3>
                {{service.price && (
                  <p className="text-primary font-bold text-lg mb-2">{{service.price}}</p>
                )}}
                <p className="text-sm md:text-base text-gray-600 mb-4 md:mb-6 leading-relaxed">
                  {{service.description}}
                </p>
                <button className="px-5 md:px-6 py-2.5 md:py-3 bg-gradient-to-r from-primary to-secondary text-white rounded-lg md:rounded-xl font-semibold hover:shadow-lg transition-all duration-300 transform hover:scale-105 text-sm md:text-base w-full md:w-auto">
                  {{service.price ? 'Order Now' : 'Learn More'}}
                </button>
              </div>
            </div>
          ))}}
        </div>
      </div>
    </section>
  )
}}

export default Services
"""

        contact_code = f"""import React, {{ useState }} from 'react'

function Contact() {{
  const [formData, setFormData] = useState({{
    name: '',
    email: '',
    message: ''
  }})
  const [status, setStatus] = useState('')

  const handleSubmit = async (e) => {{
    e.preventDefault()
    setStatus('sending')

    // TODO: Integrate with Supabase or backend API
    setTimeout(() => {{
      setStatus('success')
      setFormData({{ name: '', email: '', message: '' }})
      setTimeout(() => setStatus(''), 3000)
    }}, 1000)
  }}

  return (
    <section id="contact" className="relative py-24 overflow-hidden">
      {{/* Gradient Background */}}
      <div className="absolute inset-0 bg-gradient-to-br from-primary via-secondary to-purple-900"></div>

      {{/* Animated Background Elements */}}
      <div className="absolute top-0 left-0 w-96 h-96 bg-white/10 rounded-full blur-3xl animate-pulse"></div>
      <div className="absolute bottom-0 right-0 w-96 h-96 bg-white/10 rounded-full blur-3xl animate-pulse delay-1000"></div>

      <div className="container-custom max-w-4xl relative z-10">
        <div className="text-center mb-16">
          <h2 className="text-5xl md:text-6xl font-bold text-white mb-6">
            Let's Start a Conversation
          </h2>
          <p className="text-xl text-white/90 max-w-2xl mx-auto">
            Have a question or ready to get started? We'd love to hear from you.
          </p>
        </div>

        <div className="bg-white/10 backdrop-blur-xl rounded-3xl p-8 md:p-12 border border-white/20 shadow-2xl">
          <form onSubmit={{handleSubmit}} className="space-y-6">
            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <label className="block text-white/90 font-semibold mb-2">Full Name</label>
                <input
                  type="text"
                  placeholder="John Doe"
                  required
                  value={{formData.name}}
                  onChange={{(e) => setFormData({{...formData, name: e.target.value}})}}
                  className="w-full px-6 py-4 rounded-xl bg-white/10 backdrop-blur-sm border border-white/30 text-white placeholder-white/50 focus:outline-none focus:border-white/60 focus:bg-white/15 transition-all"
                />
              </div>
              <div>
                <label className="block text-white/90 font-semibold mb-2">Email Address</label>
                <input
                  type="email"
                  placeholder="john@example.com"
                  required
                  value={{formData.email}}
                  onChange={{(e) => setFormData({{...formData, email: e.target.value}})}}
                  className="w-full px-6 py-4 rounded-xl bg-white/10 backdrop-blur-sm border border-white/30 text-white placeholder-white/50 focus:outline-none focus:border-white/60 focus:bg-white/15 transition-all"
                />
              </div>
            </div>
            <div>
              <label className="block text-white/90 font-semibold mb-2">Your Message</label>
              <textarea
                placeholder="Tell us about your project..."
                required
                rows={{6}}
                value={{formData.message}}
                onChange={{(e) => setFormData({{...formData, message: e.target.value}})}}
                className="w-full px-6 py-4 rounded-xl bg-white/10 backdrop-blur-sm border border-white/30 text-white placeholder-white/50 focus:outline-none focus:border-white/60 focus:bg-white/15 transition-all resize-none"
              ></textarea>
            </div>
            <button
              type="submit"
              disabled={{status === 'sending'}}
              className="w-full bg-white text-primary font-bold py-5 px-8 rounded-xl hover:shadow-2xl hover:scale-105 transition-all duration-300 transform disabled:opacity-70 disabled:cursor-not-allowed text-lg"
            >
              {{status === 'sending' ? 'Sending...' : 'Send Message'}}
            </button>
            {{status === 'success' && (
              <div className="text-center p-4 bg-green-500/20 border border-green-400/30 rounded-xl">
                <p className="text-white font-semibold">Message sent successfully! We'll get back to you soon.</p>
              </div>
            )}}
          </form>
        </div>

        {{/* Contact Info */}}
        <div className="mt-12 grid md:grid-cols-3 gap-6 text-center text-white">
          <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 border border-white/20">
            <div className="text-3xl mb-3">📧</div>
            <h3 className="font-bold mb-2">Email</h3>
            <p className="text-white/80">contact@{business_name.lower().replace(' ', '')}.com</p>
          </div>
          <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 border border-white/20">
            <div className="text-3xl mb-3">📞</div>
            <h3 className="font-bold mb-2">Phone</h3>
            <p className="text-white/80">+1 (555) 123-4567</p>
          </div>
          <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 border border-white/20">
            <div className="text-3xl mb-3">📍</div>
            <h3 className="font-bold mb-2">Location</h3>
            <p className="text-white/80">Your City, State</p>
          </div>
        </div>
      </div>
    </section>
  )
}}

export default Contact
"""

        # About Component - Always include
        about_text = analysis.get("about_text", f"At {business_name}, we're dedicated to excellence")
        about_code = f"""import React from 'react'

function About() {{
  return (
    <section id="about" className="py-24 bg-white">
      <div className="container-custom">
        <div className="grid md:grid-cols-2 gap-8 md:gap-12 items-center">
          {{/* About Image */}}
          <div className="relative order-2 md:order-1">
            <div className="relative rounded-2xl md:rounded-3xl overflow-hidden shadow-2xl">
              <img
                src="{about_image}"
                alt="About {business_name}"
                className="w-full h-[300px] md:h-[500px] object-contain bg-gray-50"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent"></div>
            </div>
            {{/* Decorative element - hidden on mobile */}}
            <div className="hidden md:block absolute -bottom-6 -right-6 w-64 h-64 bg-gradient-to-br from-primary to-secondary rounded-3xl opacity-20 -z-10"></div>
          </div>

          {{/* About Content */}}
          <div className="order-1 md:order-2">
            <div className="inline-block px-4 py-2 bg-primary/10 rounded-full mb-4 md:mb-6">
              <span className="text-primary font-semibold text-sm md:text-base">About Us</span>
            </div>
            <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold mb-4 md:mb-6 text-gray-900">
              Your Trusted Partner for Excellence
            </h2>
            <p className="text-base md:text-lg text-gray-600 mb-4 md:mb-6 leading-relaxed">
              {about_text}
            </p>
            <p className="text-base md:text-lg text-gray-600 mb-6 md:mb-8 leading-relaxed">
              With years of experience and a passion for quality, we bring you the best service possible. Our team is dedicated to exceeding your expectations every single time.
            </p>

            {{/* Stats */}}
            <div className="grid grid-cols-3 gap-3 md:gap-6 mt-6 md:mt-8">
              <div className="text-center p-3 md:p-4 bg-gradient-to-br from-primary/10 to-secondary/10 rounded-xl md:rounded-2xl">
                <div className="text-2xl md:text-3xl font-bold text-primary mb-1">500+</div>
                <div className="text-xs md:text-sm text-gray-600">Happy Clients</div>
              </div>
              <div className="text-center p-3 md:p-4 bg-gradient-to-br from-primary/10 to-secondary/10 rounded-xl md:rounded-2xl">
                <div className="text-2xl md:text-3xl font-bold text-primary mb-1">10+</div>
                <div className="text-xs md:text-sm text-gray-600">Years Experience</div>
              </div>
              <div className="text-center p-3 md:p-4 bg-gradient-to-br from-primary/10 to-secondary/10 rounded-xl md:rounded-2xl">
                <div className="text-2xl md:text-3xl font-bold text-primary mb-1">98%</div>
                <div className="text-xs md:text-sm text-gray-600">Satisfaction</div>
              </div>
            </div>

            <button className="mt-6 md:mt-8 px-6 md:px-8 py-3 md:py-4 bg-gradient-to-r from-primary to-secondary text-white font-bold rounded-xl hover:shadow-2xl hover:scale-105 transition-all duration-300 text-sm md:text-base w-full md:w-auto">
              Learn More About Us
            </button>
          </div>
        </div>
      </div>
    </section>
  )
}}

export default About
"""

        # Gallery Component
        # Use dedicated gallery images (appended at index 7+ by react_api_routes),
        # then fill any remaining slots with hero/service images, then picsum fallback
        dedicated_gallery = [img.get("url") for img in images[7:] if img.get("url")]
        hero_service_pool = [img.get("url") for img in images[:7] if img.get("url")]
        gallery_pool = dedicated_gallery + hero_service_pool
        gallery_images_list = []
        for i in range(6):
            if i < len(gallery_pool):
                gallery_images_list.append(gallery_pool[i])
            else:
                gallery_images_list.append(f"https://picsum.photos/seed/gallery{i}/600/400")

        gallery_images_json = json.dumps(gallery_images_list)

        gallery_code = f"""import React from 'react'

const galleryImages = {gallery_images_json}

function Gallery() {{
  return (
    <section id="gallery" className="py-24 bg-gradient-to-b from-gray-50 to-white">
      <div className="container-custom">
        <div className="text-center mb-12 md:mb-16">
          <h2 className="text-3xl md:text-5xl lg:text-6xl font-bold mb-3 md:mb-4 bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
            Our Gallery
          </h2>
          <p className="text-base md:text-xl text-gray-600 max-w-2xl mx-auto px-4">
            Take a look at our work and see why clients love us
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6">
          {{galleryImages.map((image, index) => (
            <div
              key={{index}}
              className="group relative overflow-hidden rounded-xl md:rounded-2xl shadow-lg hover:shadow-2xl transition-all duration-500 aspect-video"
            >
              <img
                src={{image}}
                alt={{`Gallery ${{index + 1}}`}}
                className="w-full h-full object-cover transform group-hover:scale-110 transition-transform duration-500"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-end p-4 md:p-6">
                <div className="text-white">
                  <h3 className="text-lg md:text-xl font-bold">Image {{index + 1}}</h3>
                  <p className="text-xs md:text-sm opacity-90">Click to view</p>
                </div>
              </div>
            </div>
          ))}}
        </div>
      </div>
    </section>
  )
}}

export default Gallery
"""

        # Testimonials Component
        testimonials_code = f"""import React from 'react'

const testimonials = [
  {{
    name: 'Sarah Johnson',
    role: 'Happy Customer',
    image: 'https://i.pravatar.cc/150?img=5',
    text: 'Amazing service! Highly recommend {business_name} to everyone. The quality and attention to detail are outstanding.',
    rating: 5
  }},
  {{
    name: 'Michael Chen',
    role: 'Business Owner',
    image: 'https://i.pravatar.cc/150?img=7',
    text: 'Professional, reliable, and absolutely fantastic. They exceeded all my expectations and delivered on time.',
    rating: 5
  }},
  {{
    name: 'Emily Davis',
    role: 'Regular Client',
    image: 'https://i.pravatar.cc/150?img=12',
    text: 'Best decision ever! The team is incredible and the results speak for themselves. Five stars!',
    rating: 5
  }},
]

function Testimonials() {{
  return (
    <section id="testimonials" className="py-24 bg-gradient-to-br from-primary/5 to-secondary/5">
      <div className="container-custom">
        <div className="text-center mb-12 md:mb-16">
          <h2 className="text-3xl md:text-5xl lg:text-6xl font-bold mb-3 md:mb-4 bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
            What Our Clients Say
          </h2>
          <p className="text-base md:text-xl text-gray-600 max-w-2xl mx-auto px-4">
            Don't just take our word for it - hear from our satisfied customers
          </p>
        </div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6 md:gap-8">
          {{testimonials.map((testimonial, index) => (
            <div
              key={{index}}
              className="bg-white p-6 md:p-8 rounded-2xl md:rounded-3xl shadow-xl hover:shadow-2xl transition-all duration-300 hover:-translate-y-2"
            >
              {{/* Stars */}}
              <div className="flex gap-1 mb-3 md:mb-4">
                {{[...Array(testimonial.rating)].map((_, i) => (
                  <svg key={{i}} className="w-4 h-4 md:w-5 md:h-5 text-yellow-400 fill-current" viewBox="0 0 20 20">
                    <path d="M10 15l-5.878 3.09 1.123-6.545L.489 6.91l6.572-.955L10 0l2.939 5.955 6.572.955-4.756 4.635 1.123 6.545z" />
                  </svg>
                ))}}
              </div>

              {{/* Quote */}}
              <p className="text-sm md:text-base text-gray-600 mb-4 md:mb-6 leading-relaxed italic">
                "{{testimonial.text}}"
              </p>

              {{/* Author */}}
              <div className="flex items-center gap-3 md:gap-4">
                <img
                  src={{testimonial.image}}
                  alt={{testimonial.name}}
                  className="w-10 h-10 md:w-12 md:h-12 rounded-full object-cover ring-2 ring-primary/20"
                />
                <div>
                  <h4 className="font-bold text-sm md:text-base text-gray-900">{{testimonial.name}}</h4>
                  <p className="text-xs md:text-sm text-gray-500">{{testimonial.role}}</p>
                </div>
              </div>
            </div>
          ))}}
        </div>
      </div>
    </section>
  )
}}

export default Testimonials
"""

        # Features/Benefits Component
        features_benefits_code = f"""import React from 'react'

const features = [
  {{
    icon: '⚡',
    title: 'Fast & Efficient',
    description: 'Quick turnaround time without compromising on quality'
  }},
  {{
    icon: '💎',
    title: 'Premium Quality',
    description: 'Only the best materials and techniques used'
  }},
  {{
    icon: '🎯',
    title: 'Attention to Detail',
    description: 'We pay attention to every little detail'
  }},
  {{
    icon: '🤝',
    title: '24/7 Support',
    description: 'Always here when you need us'
  }},
  {{
    icon: '🏆',
    title: 'Award Winning',
    description: 'Recognized for excellence in our industry'
  }},
  {{
    icon: '💰',
    title: 'Best Value',
    description: 'Competitive pricing with unmatched quality'
  }},
]

function Features() {{
  return (
    <section id="features" className="py-24 bg-white">
      <div className="container-custom">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-6xl font-bold mb-4 bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
            Why Choose Us
          </h2>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Discover what makes us the best choice for your needs
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {{features.map((feature, index) => (
            <div
              key={{index}}
              className="group p-8 bg-gradient-to-br from-gray-50 to-white rounded-3xl border border-gray-100 hover:border-primary/30 hover:shadow-xl transition-all duration-300"
            >
              <div className="text-5xl mb-4 group-hover:scale-110 transition-transform duration-300">
                {{feature.icon}}
              </div>
              <h3 className="text-2xl font-bold mb-3 text-gray-900">
                {{feature.title}}
              </h3>
              <p className="text-gray-600 leading-relaxed">
                {{feature.description}}
              </p>
            </div>
          ))}}
        </div>
      </div>
    </section>
  )
}}

export default Features
"""

        # Build components list dynamically based on features
        components = [
            {"name": "Navbar", "description": "Navigation bar", "code": navbar_code},
            {"name": "Hero", "description": "Hero section", "code": hero_code},
            {"name": "About", "description": "About section", "code": about_code},
            {"name": "Services", "description": "Services grid", "code": services_code},
        ]

        # Add feature-based components
        feature_list_lower = [f.lower() for f in features]
        feature_string = " ".join(feature_list_lower)

        # Gallery detection - includes transformation gallery, photos, etc.
        if any(keyword in feature_string for keyword in ["gallery", "photos", "transformation"]):
            components.append({"name": "Gallery", "description": "Image gallery", "code": gallery_code})

        # Testimonials/Reviews detection
        if any(keyword in feature_string for keyword in ["testimonials", "reviews", "success"]):
            components.append({"name": "Testimonials", "description": "Customer testimonials", "code": testimonials_code})

        # E-COMMERCE FEATURES - Product Catalog, Shopping Cart, Online Ordering
        if any(keyword in feature_string for keyword in ["menu", "catalog", "product", "ordering", "cart", "shop"]):
            # Build products list with proper image mapping
            products_list = []
            for idx, service in enumerate(services[:6]):
                product = {
                    "id": idx + 1,
                    "name": service,
                    "price": (idx + 1) * 25 + 99,
                    "category": service
                }

                # Get image from services_with_images or use fallback
                if idx < len(services_with_images):
                    product["image"] = services_with_images[idx]["image"]
                else:
                    product["image"] = f"https://picsum.photos/seed/{service.replace(' ', '')}/640/400"

                products_list.append(product)

            # Product Catalog Component
            product_catalog_code = f"""import React, {{ useState }} from 'react'

const ProductCatalog = () => {{
  const products = {json.dumps(products_list, indent=2)}

  const [selectedCategory, setSelectedCategory] = useState('All')
  const categories = ['All', ...new Set(products.map(p => p.category))]

  const filteredProducts = selectedCategory === 'All'
    ? products
    : products.filter(p => p.category === selectedCategory)

  return (
    <section id="products" className="py-24 bg-gradient-to-b from-gray-50 to-white">
      <div className="container-custom">
        <h2 className="text-4xl md:text-6xl font-bold text-center mb-4 bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
          Our Products
        </h2>
        <p className="text-xl text-gray-600 text-center mb-12 max-w-2xl mx-auto">
          Explore our curated collection
        </p>

        {{/* Category Filter */}}
        <div className="flex flex-wrap justify-center gap-4 mb-12">
          {{categories.map(category => (
            <button
              key={{category}}
              onClick={{() => setSelectedCategory(category)}}
              className={{`px-6 py-3 rounded-full font-semibold transition-all ${{
                selectedCategory === category
                  ? 'bg-primary text-white shadow-lg'
                  : 'bg-white text-gray-700 hover:bg-gray-100'
              }}`}}
            >
              {{category}}
            </button>
          ))}}
        </div>

        {{/* Products Grid */}}
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-8">
          {{filteredProducts.map((product) => (
            <div key={{product.id}} className="group bg-white rounded-3xl overflow-hidden shadow-lg hover:shadow-2xl transition-all duration-300">
              <div className="relative h-64 overflow-hidden">
                <img
                  src={{product.image}}
                  alt={{product.name}}
                  className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
                />
                <div className="absolute top-4 right-4 bg-white/90 backdrop-blur px-4 py-2 rounded-full font-bold text-primary">
                  ₹{{product.price}}
                </div>
              </div>
              <div className="p-6">
                <h3 className="text-xl font-bold mb-2">{{product.name}}</h3>
                <p className="text-gray-600 mb-4">{{product.category}}</p>
                <button className="w-full bg-gradient-to-r from-primary to-secondary text-white font-semibold py-3 rounded-full hover:shadow-lg transition-all">
                  Add to Cart
                </button>
              </div>
            </div>
          ))}}
        </div>
      </div>
    </section>
  )
}}

export default ProductCatalog
"""
            components.append({"name": "ProductCatalog", "description": "Product catalog with cart", "code": product_catalog_code})

        # Size Guide Component (for fashion/clothing stores)
        if any(keyword in feature_string for keyword in ["size_guide", "size", "sizing"]):
            size_guide_code = f"""import React, {{ useState }} from 'react'

const SizeGuide = () => {{
  const [isOpen, setIsOpen] = useState(false)

  const sizeChart = {{
    'XS': {{ chest: '30-32', waist: '24-26', hips: '34-36' }},
    'S': {{ chest: '32-34', waist: '26-28', hips: '36-38' }},
    'M': {{ chest: '34-36', waist: '28-30', hips: '38-40' }},
    'L': {{ chest: '36-38', waist: '30-32', hips: '40-42' }},
    'XL': {{ chest: '38-40', waist: '32-34', hips: '42-44' }},
  }}

  return (
    <>
      <button
        onClick={{() => setIsOpen(true)}}
        className="fixed bottom-8 right-8 bg-primary text-white p-4 rounded-full shadow-2xl hover:shadow-3xl transition-all z-40"
      >
        📏 Size Guide
      </button>

      {{isOpen && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={{() => setIsOpen(false)}}>
          <div className="bg-white rounded-3xl p-8 max-w-2xl w-full" onClick={{e => e.stopPropagation()}}>
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-3xl font-bold">Size Guide</h3>
              <button onClick={{() => setIsOpen(false)}} className="text-3xl">&times;</button>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="bg-gradient-to-r from-primary to-secondary text-white">
                    <th className="p-4 text-left">Size</th>
                    <th className="p-4 text-left">Chest (in)</th>
                    <th className="p-4 text-left">Waist (in)</th>
                    <th className="p-4 text-left">Hips (in)</th>
                  </tr>
                </thead>
                <tbody>
                  {{Object.entries(sizeChart).map(([size, measurements], idx) => (
                    <tr key={{size}} className={{idx % 2 === 0 ? 'bg-gray-50' : 'bg-white'}}>
                      <td className="p-4 font-bold">{{size}}</td>
                      <td className="p-4">{{measurements.chest}}</td>
                      <td className="p-4">{{measurements.waist}}</td>
                      <td className="p-4">{{measurements.hips}}</td>
                    </tr>
                  ))}}
                </tbody>
              </table>
            </div>

            <p className="mt-6 text-sm text-gray-600">
              * All measurements are in inches. For best fit, please measure yourself and compare with our size chart.
            </p>
          </div>
        </div>
      )}}
    </>
  )
}}

export default SizeGuide
"""
            components.append({"name": "SizeGuide", "description": "Size guide modal", "code": size_guide_code})

        # Always add Features/Benefits
        components.append({"name": "Features", "description": "Features and benefits", "code": features_benefits_code})

        # Contact is always last
        components.append({"name": "Contact", "description": "Contact form", "code": contact_code})

        return components

    def _extract_supabase_features(self, features: List[str]) -> List[str]:
        """Extract which Supabase features to enable"""
        supabase_features = []

        # Check if any feature requires database
        if any(f in ["booking", "order", "contact", "auth", "ecommerce"] for f in [f.lower() for f in features]):
            supabase_features.append("database")

        # Check for specific features
        feature_mapping = {
            "booking": "database",
            "order": "database",
            "ecommerce": "database",
            "auth": "auth",
            "login": "auth",
            "upload": "storage",
            "gallery": "storage",
            "real-time": "realtime",
            "chat": "realtime"
        }

        for feature in features:
            feature_lower = feature.lower()
            if feature_lower in feature_mapping:
                mapped = feature_mapping[feature_lower]
                if mapped not in supabase_features:
                    supabase_features.append(mapped)

        return supabase_features


# Global React builder instance
react_builder = ReactWebsiteBuilder()
