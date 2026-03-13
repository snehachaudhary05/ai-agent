import { useState, useEffect } from 'react'
import axios from 'axios'
import JSZip from 'jszip'
import Onboarding from './Onboarding'
import { useTheme } from './useTheme'
import './App.css'

const API = import.meta.env.VITE_API_URL || ''

// ─── Result View (shown after website is built) ───────────────────────────────

function ResultView({ result, userData, onStartOver }) {
  const [theme, toggleTheme]            = useTheme()
  const [deployedUrl, setDeployedUrl]   = useState(result.deployment_url || null)
  const [deploying, setDeploying]       = useState(false)
  const [downloading, setDownloading]   = useState(false)
  const [previewOpen, setPreviewOpen]   = useState(false)

  const generatePreviewHTML = () => {
    const btype     = userData?.businessType || 'business'
    const bname     = userData?.businessName || 'Your Business'
    const blocation = userData?.location || 'your city'
    const items     = userData?.items || []
    // Default brand colors chosen to feel natural for each business type
    const typeDefaultColors = {
      salon:         '#b5838d', // dusty rose — feminine, luxurious
      gym:           '#f97316', // vivid orange — energetic, powerful
      restaurant:    '#c2622d', // warm terracotta — cozy, appetizing
      clothing:      '#6b21a8', // deep purple — fashion-forward
      'real-estate': '#1d4ed8', // strong blue — trustworthy, professional
      coaching:      '#0d9488', // teal — progressive, educational
      'online-store':'#059669', // emerald — fresh, modern ecommerce
      other:         '#6366f1', // indigo default
    }
    const color = userData?.aiColor
      ? (typeDefaultColors[btype] || '#6366f1')
      : (userData?.brandColor || typeDefaultColors[btype] || '#6366f1')
    const isProduct = userData?.sellingType === 'products'
    const phone     = userData?.phone || ''
    const email     = userData?.email || ''
    const instagram = userData?.instagram || ''

    // Derive a light tint from the brand color for backgrounds
    const colorLight = color + '18'

    // ── Per-business-type design themes ──────────────────────────────────────
    const typeThemes = {
      salon: {
        fonts: 'Playfair+Display:ital,wght@0,700;1,400;1,700&family=Lato:wght@300;400;700',
        sectionLabel: 'Treatments',
        css: `body{font-family:'Lato',sans-serif;background:#fffbf9}.logo,.section-title{font-family:'Playfair Display',serif;font-style:italic}.hero h1{font-style:italic;letter-spacing:1px}.nav-links a{letter-spacing:2px;text-transform:uppercase;font-size:11px}.item-card{border:1px solid #f5e6e8;border-radius:28px}.btn{border-radius:50px}.section{background:#fffbf9}.about-bg{background:#fdf3f0!important}.stats-bar{background:#fff6f3}`,
      },
      gym: {
        fonts: 'Oswald:wght@500;600;700&family=Roboto:wght@300;400;700',
        sectionLabel: 'Programs',
        css: `body{background:#080808;color:#e0e0e0;font-family:'Roboto',sans-serif}nav{background:rgba(8,8,8,0.98)!important;border-bottom:1px solid #1a1a1a}.logo{font-family:'Oswald',sans-serif;text-transform:uppercase;letter-spacing:3px;color:${color}!important}.nav-links a{color:#888!important;text-transform:uppercase;letter-spacing:2px;font-size:11px}.nav-links a:hover{color:${color}!important}h2.section-title{font-family:'Oswald',sans-serif;text-transform:uppercase;letter-spacing:3px;color:#fff}.section-sub{color:#888}.section{background:#0d0d0d}.about-bg{background:#080808!important}.stats-bar{background:#050505;border-top:3px solid ${color}}.stat-num{color:${color};font-size:40px}.stat-label{color:#666}.item-card{background:#141414;border:1px solid #252525;border-radius:6px}.item-card-body h3{color:#fff;font-family:'Oswald',sans-serif;text-transform:uppercase;letter-spacing:1px;font-size:15px}.item-card-body p{color:#888}.section-tag{background:${color}20;color:${color}}.btn{border-radius:4px;text-transform:uppercase;letter-spacing:2px;font-size:12px;font-family:'Oswald',sans-serif}footer{background:#030303}.footer-copy,.footer-built{color:#444!important}.footer-desc{color:#444!important}.footer-links ul li a{color:#666}.footer-logo{color:${color}}.why-item{color:#aaa}.contact-info-text strong{color:#fff}.contact-info-text span{color:#888}.testi-card{background:rgba(255,255,255,0.04);border-color:#222}.hero-badge{background:rgba(255,255,255,0.08);border-color:rgba(255,255,255,0.15)}`,
      },
      restaurant: {
        fonts: 'Playfair+Display:ital,wght@0,700;1,400;1,700&family=Lato:wght@300;400;700',
        sectionLabel: 'Menu',
        css: `body{background:#fffdf5;font-family:'Lato',sans-serif}.logo,.section-title{font-family:'Playfair Display',serif;font-style:italic}.hero h1{font-style:italic}.section{background:#fffdf5}.about-bg{background:#fff8e8!important}.item-card{border:1px solid #f5e8d0;background:#fffef9;border-radius:18px}.item-card-body h3{font-family:'Playfair Display',serif}.hero-badge{background:rgba(245,180,50,0.2);border-color:rgba(245,180,50,0.5)}.stats-bar{background:#fff9ef}footer{background:#1a0a00}`,
      },
      clothing: {
        fonts: 'Cormorant+Garamond:ital,wght@0,400;0,600;1,400&family=Inter:wght@300;400;500',
        sectionLabel: 'Collection',
        css: `body{background:#fafafa;font-family:'Inter',sans-serif}.logo{font-family:'Cormorant Garamond',serif;font-size:26px;letter-spacing:6px;text-transform:uppercase;font-weight:400}.nav-links a{letter-spacing:3px;text-transform:uppercase;font-size:10px;font-weight:400}h2.section-title{font-family:'Cormorant Garamond',serif;font-size:2.6rem!important;font-weight:400;letter-spacing:2px;font-style:italic}.section-tag{letter-spacing:4px;font-size:10px;text-transform:uppercase}.item-card,.btn,.item-btn{border-radius:0}.item-card img{height:280px}.item-btn{letter-spacing:2px;text-transform:uppercase;font-size:11px}.btn{letter-spacing:2px;text-transform:uppercase;font-size:12px}footer{background:#0a0a0a}`,
      },
      'online-store': {
        fonts: 'Nunito:wght@400;600;700;800;900',
        sectionLabel: 'Products',
        css: `body{font-family:'Nunito',sans-serif}.logo{font-weight:900;font-size:24px}.item-card{border-radius:20px}.item-price{font-size:20px;font-weight:900}.item-btn{border-radius:10px;font-weight:700}.section-title{font-weight:900}`,
      },
      'real-estate': {
        fonts: 'Raleway:wght@400;600;700;800&family=Open+Sans:wght@300;400;600',
        sectionLabel: 'Properties',
        css: `body{font-family:'Open Sans',sans-serif}.logo{font-family:'Raleway',sans-serif;font-weight:800;letter-spacing:1px}h2.section-title{font-family:'Raleway',sans-serif;font-weight:800}.hero-badge{letter-spacing:2px;text-transform:uppercase;font-size:10px}.item-card img{height:240px}.section-tag{letter-spacing:2px;text-transform:uppercase}`,
      },
      coaching: {
        fonts: 'Poppins:wght@300;400;500;600;700;800',
        sectionLabel: 'Courses',
        css: `body{font-family:'Poppins',sans-serif}.logo,.section-title,.hero h1{font-weight:800}.item-card{border-radius:20px}`,
      },
    }
    const bTheme        = typeThemes[btype] || typeThemes.coaching
    const bFonts        = bTheme.fonts || 'Inter:wght@400;500;600;700;800'
    const bThemeCSS     = bTheme.css   || ''
    const bSectionLabel = isProduct ? 'Products' : (bTheme.sectionLabel || 'Services')

    // Category filtering: detect if any items have categories set
    const hasCategories = items.some(i => i.category && i.category.trim())
    const uniqueCategories = hasCategories
      ? [...new Set(items.filter(i => i.category && i.category.trim()).map(i => i.category.trim()))]
      : []

    // All images come from Pexels via the backend API — no Unsplash fallbacks
    const heroImg  = userData?.heroImage  || null
    const aboutImg = userData?.aboutImage || null

    // Hero background — gradient only if no Pexels image
    const heroBg = heroImg
      ? `linear-gradient(135deg,rgba(0,0,0,0.6) 0%,rgba(0,0,0,0.35) 100%),url('${heroImg}') center/cover no-repeat`
      : `linear-gradient(135deg,#1e293b 0%,#334155 50%,${color} 100%)`

    // About image HTML — gradient placeholder if no Pexels image
    const aboutImgHtml = aboutImg
      ? `<img src="${aboutImg}" alt="About ${bname}" loading="lazy">`
      : `<div style="width:100%;height:460px;background:linear-gradient(135deg,${colorLight} 0%,${color}44 100%);display:flex;align-items:center;justify-content:center;font-size:64px;border-radius:0;">🏪</div>`

    const whyPoints = {
      restaurant:    ['Fresh ingredients daily','Authentic recipes','Warm ambience','Expert chefs'],
      clothing:      ['Premium fabrics','Latest trends','Perfect fit guarantee','Wide collection'],
      salon:         ['Certified professionals','Premium products','Relaxing experience','Latest techniques'],
      gym:           ['Expert trainers','Modern equipment','Personalised plans','Supportive community'],
      coaching:      ['Experienced mentors','Proven curriculum','Small batch sessions','Career support'],
      'real-estate': ['Verified properties','Expert guidance','Best deals','Trusted network'],
      'online-store':['Fast delivery','Secure payments','Easy returns','Wide selection'],
      other:         ['Professional team','Quality service','Customer first','Best results'],
      default:       ['Professional team','Quality service','Customer first','Best results'],
    }
    const whys = whyPoints[btype] || whyPoints.default

    const testimonials = [
      { name: 'Priya S.', text: `${bname} completely exceeded my expectations. Highly recommend!`, stars: 5 },
      { name: 'Rahul M.', text: `Best ${btype} in ${blocation}. The quality is unmatched.`, stars: 5 },
      { name: 'Anjali K.', text: `I've been a loyal customer for years. Always a wonderful experience.`, stars: 5 },
    ]

    return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${bname}</title>
  <link rel="icon" href="data:,">
  <link href="https://fonts.googleapis.com/css2?family=${bFonts}&display=swap" rel="stylesheet">
  <style>
    *{margin:0;padding:0;box-sizing:border-box}
    html{scroll-behavior:smooth}
    body{font-family:'Inter',sans-serif;color:#0f172a;background:#fff}

    /* NAV */
    nav{background:rgba(255,255,255,0.95);backdrop-filter:blur(10px);padding:0 5%;height:68px;display:flex;justify-content:space-between;align-items:center;position:sticky;top:0;z-index:100;border-bottom:1px solid #f1f5f9;box-shadow:0 1px 20px rgba(0,0,0,0.06)}
    .logo{font-size:22px;font-weight:800;color:${color};letter-spacing:-0.5px}
    .nav-links{display:flex;gap:32px;align-items:center}
    .nav-links a{text-decoration:none;color:#475569;font-weight:500;font-size:14px;transition:color .2s}
    .nav-links a:hover{color:${color}}
    .nav-cta{background:${color};color:#fff !important;padding:10px 22px;border-radius:8px;font-weight:600 !important;font-size:13px !important}
    .hamburger{display:none;flex-direction:column;gap:5px;cursor:pointer;background:none;border:none;padding:4px;z-index:101}
    .hamburger span{display:block;width:24px;height:2px;background:#475569;border-radius:2px;transition:all .3s}

    /* HERO */
    .hero{min-height:520px;display:flex;align-items:center;justify-content:center;text-align:center;background:${heroBg};position:relative}
    .hero-badge{display:inline-block;background:rgba(255,255,255,0.15);border:1px solid rgba(255,255,255,0.3);color:#fff;padding:6px 18px;border-radius:50px;font-size:13px;font-weight:600;margin-bottom:20px;backdrop-filter:blur(4px)}
    .hero-inner{max-width:760px;padding:0 24px;color:#fff}
    .hero h1{font-size:clamp(2.2rem,5.5vw,4rem);font-weight:800;line-height:1.1;margin-bottom:20px;letter-spacing:-1px}
    .hero h1 span{color:${color}}
    .hero p{font-size:18px;opacity:.88;margin-bottom:36px;line-height:1.7;max-width:560px;margin-left:auto;margin-right:auto}
    .hero-btns{display:flex;gap:14px;justify-content:center;flex-wrap:wrap}
    .btn{display:inline-flex;align-items:center;gap:8px;padding:14px 32px;border-radius:10px;font-weight:700;font-size:15px;text-decoration:none;cursor:pointer;border:none;transition:all .2s;font-family:inherit}
    .btn-primary{background:${color};color:#fff;box-shadow:0 4px 20px ${color}55}
    .btn-primary:hover{transform:translateY(-2px);box-shadow:0 8px 28px ${color}77}
    .btn-outline{background:transparent;color:#fff;border:2px solid rgba(255,255,255,0.7)}
    .btn-outline:hover{background:rgba(255,255,255,0.1)}

    /* STATS BAR */
    .stats-bar{background:#fff;padding:28px 5%;display:flex;justify-content:center;gap:60px;box-shadow:0 4px 24px rgba(0,0,0,0.08);flex-wrap:wrap}
    .stat{text-align:center}
    .stat-num{font-size:28px;font-weight:800;color:${color}}
    .stat-label{font-size:13px;color:#64748b;font-weight:500;margin-top:2px}

    /* SECTIONS */
    .section{padding:88px 5%}
    .section-inner{max-width:1200px;margin:0 auto}
    .section-tag{display:inline-block;background:${colorLight};color:${color};font-size:12px;font-weight:700;padding:5px 14px;border-radius:50px;text-transform:uppercase;letter-spacing:1px;margin-bottom:14px}
    .section-title{font-size:clamp(1.8rem,3.5vw,2.6rem);font-weight:800;line-height:1.15;margin-bottom:16px;letter-spacing:-0.5px}
    .section-sub{font-size:16px;color:#64748b;line-height:1.7;max-width:580px}
    .section-head{margin-bottom:56px}
    .section-head.center{text-align:center}
    .section-head.center .section-sub{margin:0 auto}

    /* ITEMS GRID */
    .items-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:28px}
    .item-card{border-radius:20px;overflow:hidden;box-shadow:0 2px 20px rgba(0,0,0,0.07);background:#fff;transition:transform .25s,box-shadow .25s;border:1px solid #f1f5f9}
    .item-card:hover{transform:translateY(-6px);box-shadow:0 12px 40px rgba(0,0,0,0.12)}
    .item-card img{width:100%;height:210px;object-fit:cover}
    .item-card-body{padding:22px}
    .item-card-body h3{font-size:17px;font-weight:700;margin-bottom:8px}
    .item-card-body p{font-size:14px;color:#64748b;line-height:1.6}
    .item-card-footer{display:flex;justify-content:space-between;align-items:center;margin-top:16px;padding-top:16px;border-top:1px solid #f1f5f9}
    .item-price{font-weight:800;font-size:18px;color:${color}}
    .item-btn{background:${colorLight};color:${color};border:none;padding:8px 18px;border-radius:8px;font-size:13px;font-weight:600;cursor:pointer;font-family:inherit;transition:background .2s}
    .item-btn:hover{background:${color};color:#fff}

    /* ABOUT */
    .about-bg{background:#f8fafc}
    .about-grid{display:grid;grid-template-columns:1fr 1fr;gap:64px;align-items:center}
    .about-img{border-radius:24px;overflow:hidden;position:relative}
    .about-img img{width:100%;height:460px;object-fit:contain;display:block;background:#f8f9fa}
    .about-img-badge{position:absolute;bottom:24px;left:24px;background:#fff;border-radius:14px;padding:16px 20px;box-shadow:0 8px 32px rgba(0,0,0,0.15)}
    .about-img-badge strong{display:block;font-size:26px;font-weight:800;color:${color}}
    .about-img-badge span{font-size:12px;color:#64748b;font-weight:500}
    .why-list{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:32px}
    .why-item{display:flex;align-items:center;gap:10px;font-size:14px;font-weight:500;color:#374151}
    .why-check{width:22px;height:22px;border-radius:6px;background:${colorLight};display:flex;align-items:center;justify-content:center;flex-shrink:0;color:${color};font-size:13px;font-weight:700}

    /* TESTIMONIALS */
    .testimonials-bg{background:linear-gradient(135deg,#0f172a 0%,#1e293b 100%) !important}
    .testi-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:24px}
    .testi-card{background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.1);border-radius:20px;padding:28px;color:#fff}
    .testi-stars{color:#f59e0b;font-size:16px;margin-bottom:14px}
    .testi-text{font-size:15px;line-height:1.7;opacity:.85;margin-bottom:20px}
    .testi-author{display:flex;align-items:center;gap:12px}
    .testi-avatar{width:42px;height:42px;border-radius:50%;background:${color};display:flex;align-items:center;justify-content:center;font-weight:700;font-size:16px;color:#fff;flex-shrink:0}
    .testi-name{font-weight:600;font-size:14px}
    .testi-role{font-size:12px;opacity:.6;margin-top:2px}

    /* CONTACT */
    .contact-grid{display:grid;grid-template-columns:1fr 1fr;gap:64px;align-items:start}
    .contact-info-list{display:flex;flex-direction:column;gap:20px;margin-top:32px}
    .contact-info-item{display:flex;align-items:center;gap:14px}
    .contact-icon{width:44px;height:44px;border-radius:12px;background:${colorLight};display:flex;align-items:center;justify-content:center;font-size:20px;flex-shrink:0}
    .contact-info-text strong{display:block;font-size:14px;font-weight:700;margin-bottom:2px}
    .contact-info-text span{font-size:13px;color:#64748b}
    .contact-form{background:#f8fafc;border-radius:20px;padding:36px}
    .form-group{margin-bottom:18px}
    .form-group label{display:block;font-size:13px;font-weight:600;color:#374151;margin-bottom:7px}
    .form-group input,.form-group textarea{width:100%;padding:12px 16px;border:1.5px solid #e2e8f0;border-radius:10px;font-size:14px;font-family:inherit;color:#0f172a;outline:none;transition:border-color .2s;background:#fff}
    .form-group input:focus,.form-group textarea:focus{border-color:${color}}
    .form-group textarea{height:110px;resize:none}
    .form-submit{width:100%;padding:14px;background:${color};color:#fff;border:none;border-radius:10px;font-size:15px;font-weight:700;cursor:pointer;font-family:inherit;transition:opacity .2s}
    .form-submit:hover{opacity:.9}

    /* FOOTER */
    footer{background:#0f172a;color:#fff;padding:48px 5% 28px}
    .footer-inner{max-width:1200px;margin:0 auto}
    .footer-top{display:flex;justify-content:space-between;align-items:flex-start;gap:40px;flex-wrap:wrap;padding-bottom:40px;border-bottom:1px solid rgba(255,255,255,0.1)}
    .footer-brand{max-width:300px}
    .footer-logo{font-size:22px;font-weight:800;color:${color};margin-bottom:12px}
    .footer-desc{font-size:14px;opacity:.6;line-height:1.7}
    .footer-links h4{font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:.8px;opacity:.5;margin-bottom:16px}
    .footer-links ul{list-style:none;display:flex;flex-direction:column;gap:10px}
    .footer-links ul li a{text-decoration:none;color:#fff;opacity:.7;font-size:14px;transition:opacity .2s}
    .footer-links ul li a:hover{opacity:1}
    .footer-bottom{padding-top:24px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px}
    .footer-copy{font-size:13px;opacity:.5}
    .footer-built{font-size:12px;opacity:.4}

    /* PREVIEW BANNER */
    .preview-banner{background:#fef3c7;border-bottom:3px solid #f59e0b;padding:10px 20px;text-align:center;font-size:13px;font-weight:600;color:#92400e;display:flex;align-items:center;justify-content:center;gap:8px}

    /* RESPONSIVE */
    @media(max-width:900px){
      .about-grid,.contact-grid{grid-template-columns:1fr}
      .testi-grid{grid-template-columns:1fr}
      .stats-bar{gap:32px}
      .why-list{grid-template-columns:1fr}
      .hamburger{display:flex}
      .nav-links{display:none;position:absolute;top:68px;left:0;right:0;background:rgba(255,255,255,0.98);flex-direction:column;padding:16px 5%;gap:0;box-shadow:0 8px 24px rgba(0,0,0,0.1);border-top:1px solid #f1f5f9;z-index:99}
      .nav-links.open{display:flex}
      .nav-links a{padding:14px 0;border-bottom:1px solid #f1f5f9;font-size:15px}
      .nav-links a:last-child{border-bottom:none}
      .nav-cta{margin-top:8px;text-align:center;border-radius:8px;padding:12px !important}
    }
    @media(max-width:600px){
      .hero h1{font-size:2rem}
      .section{padding:56px 5%}
      .items-grid{grid-template-columns:1fr}
    }

    /* FILTER TABS */
    .filter-tabs-wrap{margin-bottom:36px;text-align:center}
    .filter-tabs{display:flex;flex-wrap:wrap;gap:10px;justify-content:center;margin-bottom:14px}
    .filter-tab{padding:9px 22px;border-radius:50px;border:1.5px solid #e2e8f0;background:#fff;color:#64748b;font-size:13px;font-weight:600;cursor:pointer;transition:all .2s;font-family:inherit}
    .filter-tab.active{background:${color};color:#fff;border-color:${color};box-shadow:0 4px 14px ${color}44}
    .filter-tab:hover:not(.active){border-color:${color};color:${color}}
    .sub-tabs{display:flex;flex-wrap:wrap;gap:8px;justify-content:center}
    .sub-tab{padding:6px 16px;border-radius:50px;border:1.5px solid #e2e8f0;background:transparent;color:#64748b;font-size:12px;font-weight:600;cursor:pointer;transition:all .2s;font-family:inherit}
    .sub-tab.active{background:${color}22;color:${color};border-color:${color}88}
    .sub-tab:hover:not(.active){border-color:${color}66;color:${color}}
    .item-card.hidden{display:none !important}

    /* ── ANIMATIONS ──────────────────────────────────────────── */
    @keyframes ob-fadeUp {from{opacity:0;transform:translateY(48px)}to{opacity:1;transform:translateY(0)}}
    @keyframes ob-fadeIn {from{opacity:0}to{opacity:1}}
    @keyframes ob-slideL {from{opacity:0;transform:translateX(-64px)}to{opacity:1;transform:translateX(0)}}
    @keyframes ob-slideR {from{opacity:0;transform:translateX(64px)}to{opacity:1;transform:translateX(0)}}
    @keyframes ob-scaleUp{from{opacity:0;transform:scale(0.82) translateY(24px)}to{opacity:1;transform:scale(1) translateY(0)}}
    @keyframes ob-float  {0%,100%{transform:translateY(0)}50%{transform:translateY(-10px)}}
    @keyframes ob-pulse  {0%,100%{box-shadow:0 4px 20px ${color}55}50%{box-shadow:0 8px 40px ${color}99}}
    @keyframes hero-rise    {from{opacity:0;transform:translateY(36px)}  to{opacity:1;transform:translateY(0)}}
    @keyframes hero-scaleUp {from{opacity:0;transform:scale(.88) translateY(20px)} to{opacity:1;transform:scale(1) translateY(0)}}
    /* Hero — per-business-type entrance */
    ${{
      salon:         `.hero-badge{animation:hero-rise .9s cubic-bezier(.25,.46,.45,.94) .05s both}.hero h1{animation:hero-rise 1.1s cubic-bezier(.25,.46,.45,.94) .22s both}.hero p{animation:hero-rise 1.1s cubic-bezier(.25,.46,.45,.94) .42s both}.hero-btns{animation:hero-rise 1.1s cubic-bezier(.25,.46,.45,.94) .6s both}`,
      gym:           `.hero-badge{animation:hero-scaleUp .45s cubic-bezier(.22,1,.36,1) .0s both}.hero h1{animation:hero-scaleUp .5s cubic-bezier(.22,1,.36,1) .12s both}.hero p{animation:hero-rise .5s ease .28s both}.hero-btns{animation:hero-scaleUp .5s cubic-bezier(.34,1.56,.64,1) .4s both}`,
      restaurant:    `.hero-badge{animation:hero-rise .8s cubic-bezier(.25,.46,.45,.94) .1s both}.hero h1{animation:hero-rise .95s cubic-bezier(.25,.46,.45,.94) .25s both}.hero p{animation:hero-rise .95s cubic-bezier(.25,.46,.45,.94) .44s both}.hero-btns{animation:hero-rise .95s cubic-bezier(.25,.46,.45,.94) .62s both}`,
      clothing:      `.hero-badge{animation:hero-rise .7s cubic-bezier(.16,1,.3,1) .0s both}.hero h1{animation:hero-rise .8s cubic-bezier(.16,1,.3,1) .18s both}.hero p{animation:hero-rise .8s cubic-bezier(.16,1,.3,1) .36s both}.hero-btns{animation:hero-rise .8s cubic-bezier(.16,1,.3,1) .52s both}`,
      'real-estate': `.hero-badge{animation:hero-rise 1s cubic-bezier(.25,.46,.45,.94) .05s both}.hero h1{animation:hero-rise 1.1s cubic-bezier(.25,.46,.45,.94) .2s both}.hero p{animation:hero-rise 1.1s cubic-bezier(.25,.46,.45,.94) .4s both}.hero-btns{animation:hero-rise 1.1s cubic-bezier(.25,.46,.45,.94) .58s both}`,
      'online-store':`  .hero-badge{animation:hero-scaleUp .5s cubic-bezier(.34,1.56,.64,1) .0s both}.hero h1{animation:hero-scaleUp .55s cubic-bezier(.34,1.56,.64,1) .15s both}.hero p{animation:hero-rise .6s ease .32s both}.hero-btns{animation:hero-scaleUp .55s cubic-bezier(.34,1.56,.64,1) .46s both}`,
    }[btype] || `.hero-badge{animation:hero-rise .8s cubic-bezier(.25,.46,.45,.94) .05s both}.hero h1{animation:hero-rise .9s cubic-bezier(.25,.46,.45,.94) .2s both}.hero p{animation:hero-rise .9s cubic-bezier(.25,.46,.45,.94) .38s both}.hero-btns{animation:hero-rise .9s cubic-bezier(.25,.46,.45,.94) .55s both}`}
    /* Scroll-triggered elements — JS hides them before observing */
    [data-anim].ob-done{opacity:1}
    /* Always-on ambient */
    .about-img-badge{animation:ob-float 3.8s ease-in-out infinite !important}
    .btn-primary{animation:ob-pulse 2.8s ease-in-out infinite}
    /* ── Business-type overrides ── */
    ${bThemeCSS}
  </style>
</head>
<body>

<!-- NAV -->
<nav>
  ${userData?.logoImage
    ? `<img src="${userData.logoImage}" alt="${bname}" class="logo-img" style="height:44px;width:auto;max-width:180px;object-fit:contain;">`
    : `<div class="logo">${bname}</div>`}
  <div class="nav-links" id="nav-menu">
    <a href="#" onclick="event.preventDefault();closeMenu();document.getElementById('home').scrollIntoView({behavior:'smooth'})">Home</a>
    <a href="#" onclick="event.preventDefault();closeMenu();document.getElementById('services').scrollIntoView({behavior:'smooth'})">${bSectionLabel}</a>
    <a href="#" onclick="event.preventDefault();closeMenu();document.getElementById('about').scrollIntoView({behavior:'smooth'})">About</a>
    <a href="#" onclick="event.preventDefault();closeMenu();document.getElementById('contact').scrollIntoView({behavior:'smooth'})">Contact</a>
    <a href="#" class="nav-cta" onclick="event.preventDefault();closeMenu();document.getElementById('contact').scrollIntoView({behavior:'smooth'})">Get Started</a>
  </div>
  <button class="hamburger" id="hamburger-btn" onclick="toggleMenu()" aria-label="Toggle navigation">
    <span></span><span></span><span></span>
  </button>
</nav>
<script>
  function toggleMenu(){
    var menu=document.getElementById('nav-menu');
    var btn=document.getElementById('hamburger-btn');
    menu.classList.toggle('open');
    btn.classList.toggle('active');
  }
  function closeMenu(){
    document.getElementById('nav-menu').classList.remove('open');
    document.getElementById('hamburger-btn').classList.remove('active');
  }
</script>
<script>
(function(){
  /*
   * Per-business-type animation personality:
   * salon       → slow, silky fade-up (luxury spa feel)
   * gym         → fast, punchy scale-up (high energy)
   * restaurant  → warm gentle fade-up (cozy, inviting)
   * clothing    → crisp slide-up with overshoot (editorial fashion)
   * real-estate → steady slow fade-up (trustworthy, premium)
   * coaching    → clean fade-up (clear, professional)
   * online-store→ quick scale-pop (product excitement)
   * other       → smooth fade-up
   */
  var cfg = {
    restaurant:    {anim:'ob-fadeUp',  card:'ob-fadeUp',  dur:'0.8s',  ease:'cubic-bezier(.25,.46,.45,.94)'},
    clothing:      {anim:'ob-fadeUp',  card:'ob-scaleUp', dur:'0.65s', ease:'cubic-bezier(.16,1,.3,1)'},
    salon:         {anim:'ob-fadeUp',  card:'ob-fadeUp',  dur:'1.0s',  ease:'cubic-bezier(.25,.46,.45,.94)'},
    gym:           {anim:'ob-scaleUp', card:'ob-scaleUp', dur:'0.48s', ease:'cubic-bezier(.22,1,.36,1)'},
    coaching:      {anim:'ob-fadeUp',  card:'ob-fadeUp',  dur:'0.72s', ease:'cubic-bezier(.25,.46,.45,.94)'},
    'real-estate': {anim:'ob-fadeUp',  card:'ob-fadeUp',  dur:'0.9s',  ease:'cubic-bezier(.25,.46,.45,.94)'},
    'online-store':{anim:'ob-scaleUp', card:'ob-scaleUp', dur:'0.55s', ease:'cubic-bezier(.34,1.56,.64,1)'},
    other:         {anim:'ob-fadeUp',  card:'ob-fadeUp',  dur:'0.7s',  ease:'cubic-bezier(.25,.46,.45,.94)'},
  }['${btype}'] || {anim:'ob-fadeUp', card:'ob-fadeUp', dur:'0.7s', ease:'cubic-bezier(.25,.46,.45,.94)'};

  /* Named overrides */
  var named = {slideL:'ob-slideL', slideR:'ob-slideR', fadeUp:'ob-fadeUp', fadeIn:'ob-fadeIn', card: cfg.card};

  var io = new IntersectionObserver(function(entries){
    entries.forEach(function(e){
      if(!e.isIntersecting) return;
      var el   = e.target;
      var anim = named[el.dataset.anim] || cfg.anim;
      var delay= el.dataset.delay || '0s';
      el.style.animation = anim+' '+cfg.dur+' '+cfg.ease+' '+delay+' both';
      el.classList.add('ob-done');
      io.unobserve(el);
    });
  },{threshold:0.08, rootMargin:'0px 0px -30px 0px'});

  /* Hide via JS — so elements are visible if JS/observer fails */
  var observed = [];
  document.querySelectorAll('[data-anim]').forEach(function(el){
    el.style.opacity = '0';
    observed.push(el);
    io.observe(el);
  });

  /* Stagger card children automatically if parent has data-stagger */
  document.querySelectorAll('[data-stagger]').forEach(function(parent){
    var step = parseFloat(parent.dataset.stagger) || 0.1;
    Array.from(parent.children).forEach(function(child, i){
      child.dataset.anim  = child.dataset.anim || 'card';
      child.dataset.delay = (i * step).toFixed(2) + 's';
      child.style.opacity = '0';
      observed.push(child);
      io.observe(child);
    });
  });

  /* Safety fallback: after 1.8s show anything the observer missed */
  setTimeout(function(){
    observed.forEach(function(el){
      if(!el.classList.contains('ob-done')){
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        el.style.opacity    = '1';
        el.style.transform  = 'none';
      }
    });
  }, 1800);
})();
</script>

<!-- HERO -->
<section class="hero" id="home">
  <div class="hero-inner">
    <div class="hero-badge">✦ ${blocation}</div>
    <h1>${result.hero_headline || `Welcome to <span>${bname}</span>`}</h1>
    <p>${result.hero_subtext || `Your trusted ${btype} in ${blocation}. Quality, passion, and excellence in every detail.`}</p>
    <div class="hero-btns">
      <button class="btn btn-primary">Get Started →</button>
      <button class="btn btn-outline">Learn More</button>
    </div>
  </div>
</section>

<!-- STATS BAR -->
<div class="stats-bar">
  <div class="stat" data-anim="fadeUp" data-delay="0s"><div class="stat-num">500+</div><div class="stat-label">Happy Customers</div></div>
  <div class="stat" data-anim="fadeUp" data-delay="0.12s"><div class="stat-num">${items.length || 6}+</div><div class="stat-label">${bSectionLabel}</div></div>
  <div class="stat" data-anim="fadeUp" data-delay="0.24s"><div class="stat-num">4.9★</div><div class="stat-label">Average Rating</div></div>
  <div class="stat" data-anim="fadeUp" data-delay="0.36s"><div class="stat-num">5+</div><div class="stat-label">Years Experience</div></div>
</div>

<!-- PRODUCTS / SERVICES -->
<section class="section" id="services">
  <div class="section-inner">
    <div class="section-head center" data-anim="fadeUp">
      <span class="section-tag">Our ${bSectionLabel}</span>
      <h2 class="section-title">What We ${isProduct ? 'Offer' : 'Provide'}</h2>
      <p class="section-sub">Handpicked ${bSectionLabel.toLowerCase()} crafted with care and expertise for the best experience.</p>
    </div>
    ${hasCategories ? `
    <div class="filter-tabs-wrap" data-anim="fadeUp" data-delay="0.1s">
      <div class="filter-tabs" id="cat-tabs">
        <button class="filter-tab active" onclick="setCatTab(this,'all')">All</button>
        ${uniqueCategories.map(cat => `<button class="filter-tab" onclick="setCatTab(this,'${cat.replace(/'/g, "\\'")}')">${cat}</button>`).join('')}
      </div>
      <div class="sub-tabs" id="sub-tabs-wrap" style="display:none"></div>
    </div>
    ` : ''}
    <div class="items-grid" ${!hasCategories ? 'data-stagger="0.1"' : ''}>
      ${items.slice(0, hasCategories ? 30 : 6).map((item, idx) => `
        <div class="item-card" data-anim="card" data-delay="${hasCategories ? '0s' : (idx * 0.1) + 's'}"${item.category && item.category.trim() ? ` data-cat="${item.category.trim().replace(/"/g,'&quot;')}"` : ''}${item.subcategory && item.subcategory.trim() ? ` data-sub="${item.subcategory.trim().replace(/"/g,'&quot;')}"` : ''}>
          ${(() => {
            const imgSrc = item.fetchedImage
              || (result.service_images && result.service_images[item.name])
              || item.imagePreview
              || null
            return imgSrc
              ? `<img src="${imgSrc}" alt="${item.name}" loading="lazy" onerror="this.style.display='none'">`
              : `<div style="width:100%;height:210px;background:linear-gradient(135deg,${colorLight} 0%,${color}44 100%);display:flex;align-items:center;justify-content:center;font-size:40px;">🖼️</div>`
          })()}
          <div class="item-card-body">
            <h3>${item.name}</h3>
            <p>${item.description || (result.service_descriptions && (result.service_descriptions[item.name] || result.service_descriptions[item.name.toLowerCase()] || Object.entries(result.service_descriptions).find(([k]) => k.toLowerCase() === item.name.toLowerCase())?.[1])) || ''}</p>
            <div class="item-card-footer">
              ${item.price ? `<span class="item-price">${item.price}</span>` : `<span class="item-price" style="color:#94a3b8;font-size:14px">Contact for price</span>`}
              <button class="item-btn">${isProduct ? 'Order Now' : 'Book Now'}</button>
            </div>
          </div>
        </div>
      `).join('')}
    </div>
    ${hasCategories ? `
    <script>
    (function(){
      var allCards = document.querySelectorAll('#services .item-card');
      var subWrap  = document.getElementById('sub-tabs-wrap');
      var subMap   = {};
      allCards.forEach(function(el){
        var cat = el.dataset.cat;
        var sub = el.dataset.sub;
        if (!cat) return;
        if (!subMap[cat]) subMap[cat] = [];
        if (sub && subMap[cat].indexOf(sub) === -1) subMap[cat].push(sub);
      });
      var activeCat = 'all', activeSub = 'all';
      function filterItems(){
        allCards.forEach(function(el){
          var cat = el.dataset.cat || '';
          var sub = el.dataset.sub || '';
          var okCat = activeCat === 'all' || cat === activeCat;
          var okSub = activeSub === 'all' || sub === activeSub;
          el.classList.toggle('hidden', !(okCat && okSub));
        });
      }
      function renderSubTabs(cat){
        if (!subWrap) return;
        var subs = (cat !== 'all' && subMap[cat]) ? subMap[cat] : [];
        if (subs.length === 0){ subWrap.style.display = 'none'; return; }
        var h = '<button class="sub-tab active" onclick="setSubTab(this,\\'all\\')">All</button>';
        subs.forEach(function(s){
          h += '<button class="sub-tab" onclick="setSubTab(this,\\'' + s.replace(/'/g,"\\\\'") + '\\')">' + s + '</button>';
        });
        subWrap.innerHTML = h;
        subWrap.style.display = 'flex';
        activeSub = 'all';
      }
      window.setCatTab = function(btn, cat){
        document.querySelectorAll('#cat-tabs .filter-tab').forEach(function(t){ t.classList.remove('active'); });
        btn.classList.add('active');
        activeCat = cat; activeSub = 'all';
        renderSubTabs(cat); filterItems();
      };
      window.setSubTab = function(btn, sub){
        document.querySelectorAll('#sub-tabs-wrap .sub-tab').forEach(function(t){ t.classList.remove('active'); });
        btn.classList.add('active');
        activeSub = sub; filterItems();
      };
      renderSubTabs('all'); filterItems();
    })();
    </script>
    ` : ''}
  </div>
</section>

<!-- ABOUT -->
<section class="section about-bg" id="about">
  <div class="section-inner">
    <div class="about-grid">
      <div class="about-img" data-anim="fadeUp">
        ${aboutImgHtml}
        <div class="about-img-badge">
          <strong>5+</strong>
          <span>Years of Excellence</span>
        </div>
      </div>
      <div data-anim="fadeUp" data-delay="0.18s">
        <span class="section-tag">Our Story</span>
        <h2 class="section-title">Why Choose ${bname}?</h2>
        <p class="section-sub">We are passionate about delivering the best ${btype} experience in ${blocation}. Every detail matters to us — from quality to customer satisfaction.</p>
        <div class="why-list">
          ${whys.map(w => `
            <div class="why-item">
              <div class="why-check">✓</div>
              <span>${w}</span>
            </div>
          `).join('')}
        </div>
        <div style="margin-top:32px">
          <button class="btn btn-primary" style="font-size:14px">Learn More About Us</button>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- TESTIMONIALS -->
<section class="section testimonials-bg">
  <div class="section-inner">
    <div class="section-head center" data-anim="fadeUp" style="color:#fff">
      <span class="section-tag" style="background:rgba(255,255,255,0.1);color:#fff">Reviews</span>
      <h2 class="section-title" style="color:#fff">What Our Customers Say</h2>
      <p class="section-sub" style="color:rgba(255,255,255,0.6)">Real experiences from our happy customers.</p>
    </div>
    <div class="testi-grid">
      ${testimonials.map((t, i) => `
        <div class="testi-card" data-anim="card" data-delay="${i * 0.15}s">
          <div class="testi-stars">${'★'.repeat(t.stars)}</div>
          <p class="testi-text">"${t.text}"</p>
          <div class="testi-author">
            <div class="testi-avatar">${t.name.charAt(0)}</div>
            <div>
              <div class="testi-name">${t.name}</div>
              <div class="testi-role">Verified Customer</div>
            </div>
          </div>
        </div>
      `).join('')}
    </div>
  </div>
</section>

<!-- CONTACT -->
<section class="section" id="contact">
  <div class="section-inner">
    <div class="contact-grid">
      <div data-anim="fadeUp">
        <span class="section-tag">Contact Us</span>
        <h2 class="section-title">Get In Touch</h2>
        <p class="section-sub">We'd love to hear from you. Reach out and we'll respond as soon as possible.</p>
        <div class="contact-info-list">
          ${phone    ? `<div class="contact-info-item"><div class="contact-icon">📞</div><div class="contact-info-text"><strong>Phone</strong><span>${phone}</span></div></div>` : ''}
          ${email    ? `<div class="contact-info-item"><div class="contact-icon">✉️</div><div class="contact-info-text"><strong>Email</strong><span>${email}</span></div></div>` : ''}
          ${instagram? `<div class="contact-info-item"><div class="contact-icon">📸</div><div class="contact-info-text"><strong>Instagram</strong><span>${instagram}</span></div></div>` : ''}
          <div class="contact-info-item"><div class="contact-icon">📍</div><div class="contact-info-text"><strong>Location</strong><span>${blocation}</span></div></div>
        </div>
      </div>
      <div class="contact-form" data-anim="fadeUp" data-delay="0.18s">
        <h3 style="font-size:18px;font-weight:700;margin-bottom:24px">Send a Message</h3>
        <div class="form-group"><label>Your Name</label><input type="text" placeholder="Enter your name"></div>
        <div class="form-group"><label>Email Address</label><input type="email" placeholder="Enter your email"></div>
        <div class="form-group"><label>Message</label><textarea placeholder="How can we help you?"></textarea></div>
        <button class="form-submit">Send Message →</button>
      </div>
    </div>
  </div>
</section>

<!-- FOOTER -->
<footer>
  <div class="footer-inner">
    <div class="footer-top">
      <div class="footer-brand" data-anim="fadeUp">
        ${userData?.logoImage
          ? `<img src="${userData.logoImage}" alt="${bname}" style="height:40px;width:auto;max-width:160px;object-fit:contain;margin-bottom:12px;">`
          : `<div class="footer-logo">${bname}</div>`}
        <p class="footer-desc">Your trusted ${btype} in ${blocation}. Quality and excellence in everything we do.</p>
      </div>
      <div class="footer-links" data-anim="fadeUp" data-delay="0.15s">
        <h4>Quick Links</h4>
        <ul>
          <li><a href="#home">Home</a></li>
          <li><a href="#services">${bSectionLabel}</a></li>
          <li><a href="#about">About Us</a></li>
          <li><a href="#contact">Contact</a></li>
        </ul>
      </div>
      <div class="footer-links" data-anim="fadeUp" data-delay="0.3s">
        <h4>Contact</h4>
        <ul>
          ${phone ? `<li><a href="#">${phone}</a></li>` : ''}
          ${email ? `<li><a href="#">${email}</a></li>` : ''}
          <li><a href="#">${blocation}</a></li>
        </ul>
      </div>
    </div>
    <div class="footer-bottom" data-anim="fadeUp" data-delay="0.1s">
      <span class="footer-copy">© 2025 ${bname}. All rights reserved.</span>
      <span class="footer-built">Built with Sitekraft</span>
    </div>
  </div>
</footer>

</body>
</html>`
  }

  // Deploy the preview HTML to Vercel as a static site on mount
  useEffect(() => {
    if (deployedUrl) return   // already deployed (from backend)
    const projectName = userData?.businessName || 'my-website'
    setDeploying(true)
    const html = generatePreviewHTML()
    axios.post(`${API}/api/react/deploy-html`, {
      project_name: projectName,
      html_content: html
    })
      .then(res => {
        if (res.data?.deployment_url) setDeployedUrl(res.data.deployment_url)
      })
      .catch(err => console.error('[deploy-html]', err))
      .finally(() => setDeploying(false))
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const openPreview = () => {
    if (window.innerWidth <= 768) {
      setPreviewOpen(true)
    } else {
      const html = generatePreviewHTML()
      const blob = new Blob([html], { type: 'text/html' })
      window.open(URL.createObjectURL(blob), '_blank')
    }
  }

  const downloadFiles = async () => {
    if (!result.files || downloading) return
    setDownloading(true)
    try {
      const zip = new JSZip()
      const projectName = userData?.businessName
        ? userData.businessName.toLowerCase().replace(/\s+/g, '-')
        : 'sitekraft-website'

      // ── Step 1: collect all external image URLs from generated files ────────
      const isImageUrl = (url) => {
        if (!url || !url.startsWith('http')) return false
        return (
          /images\.pexels\.com/.test(url) ||
          /cdn\.pixabay\.com/.test(url) ||
          /pixabay\.com\/get/.test(url) ||
          /picsum\.photos/.test(url) ||
          /\.(?:jpg|jpeg|png|webp|gif|svg)(\?|$)/i.test(url)
        )
      }
      const urlRegex = /https?:\/\/[^\s"'`\\,\)\]]+/g
      const urlToLocal = new Map()   // externalURL → "public/images/image-N.ext"
      let imgIdx = 0

      Object.values(result.files).forEach(content => {
        const matches = content.match(urlRegex) || []
        matches.forEach(raw => {
          const url = raw.replace(/[",`']+$/, '')   // strip trailing quotes/commas
          if (isImageUrl(url) && !urlToLocal.has(url)) {
            const extMatch = url.match(/\.(jpg|jpeg|png|webp|gif|svg)/i)
            const ext = extMatch ? extMatch[1].toLowerCase() : 'jpg'
            urlToLocal.set(url, `public/images/image-${imgIdx++}.${ext}`)
          }
        })
      })

      // ── Step 2: fetch images in parallel, add to ZIP ─────────────────────────
      await Promise.allSettled(
        Array.from(urlToLocal.entries()).map(async ([url, localPath]) => {
          try {
            const res = await fetch(url)
            if (!res.ok) { urlToLocal.delete(url); return }
            const blob = await res.blob()
            zip.file(localPath, blob)
          } catch {
            urlToLocal.delete(url)   // keep original URL in code if fetch fails
          }
        })
      )

      // ── Step 3: add code files, rewriting fetched image URLs to local paths ──
      Object.entries(result.files).forEach(([name, content]) => {
        let modified = content
        urlToLocal.forEach((localPath, url) => {
          // Replace external URL with Vite public-asset path
          modified = modified.split(url).join(`/${localPath.replace('public/', '')}`)
        })
        zip.file(name, modified)
      })

      // ── Step 4: generate ZIP and trigger download ─────────────────────────────
      const blob = await zip.generateAsync({ type: 'blob' })
      const a = document.createElement('a')
      a.href = URL.createObjectURL(blob)
      a.download = `${projectName}.zip`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(a.href)
    } finally {
      setDownloading(false)
    }
  }

  return (
    <div className="result-root">
      <header className="result-header">
        <div className="result-brand">✦ Sitekraft</div>
        <div className="result-header-right">
          <button
            className="result-theme-btn"
            onClick={toggleTheme}
            title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
          >
            {theme === 'dark' ? '☀️' : '🌙'}
          </button>
          <button className="result-new-btn" onClick={onStartOver}>+ New Website</button>
        </div>
      </header>

      <div className="result-body">
        {/* Left panel */}
        <div className="result-left">
          <div className="result-success-card">
            <div className="result-tick">✓</div>
            <h2>Your website is ready!</h2>
            <p>{userData?.businessName} · {userData?.businessType}</p>
          </div>


          {deploying && (
            <div style={{background:'#eff6ff',border:'1px solid #bfdbfe',borderRadius:'10px',padding:'12px 16px',fontSize:'13px',color:'#1d4ed8',display:'flex',alignItems:'center',gap:'8px'}}>
              <span style={{display:'inline-block',width:'14px',height:'14px',border:'2px solid #3b82f6',borderTopColor:'transparent',borderRadius:'50%',animation:'spin 0.8s linear infinite'}} />
              Deploying your website to Vercel…
            </div>
          )}

          {deployedUrl && !deploying && (
            <div style={{display:'flex',flexDirection:'column',gap:'8px'}}>
              <button
                className="result-live-link"
                style={{cursor:'pointer',border:'none',textAlign:'center'}}
                onClick={() => window.open(deployedUrl, '_blank')}
              >
                🌐 Open Live Website →
              </button>
              <div style={{background:'#f1f5f9',borderRadius:'8px',padding:'10px 14px',fontSize:'12px',wordBreak:'break-all',color:'#475569'}}>
                <span style={{fontWeight:600,display:'block',marginBottom:'4px'}}>Your shareable link:</span>
                <span style={{userSelect:'all',cursor:'text'}}>{deployedUrl}</span>
              </div>
            </div>
          )}

          <div className="result-actions">
            <button className="result-btn result-btn-primary" onClick={openPreview}>
              👁 Open Preview
            </button>
            {result.files && (
              <button
                className="result-btn result-btn-secondary"
                onClick={downloadFiles}
                disabled={downloading}
                style={downloading ? { opacity: 0.7, cursor: 'wait' } : {}}
              >
                {downloading ? '⏳ Preparing ZIP...' : '💾 Download ZIP'}
              </button>
            )}
          </div>
        </div>

        {/* Right panel — inline preview (desktop only) */}
        <div className="result-right">
          <div className="result-preview-bar">
            <span className="result-preview-dot red" />
            <span className="result-preview-dot yellow" />
            <span className="result-preview-dot green" />
            <span className="result-preview-url">{userData?.businessName?.toLowerCase().replace(/\s+/g,'-')}.vercel.app</span>
          </div>
          <iframe
            className="result-iframe"
            srcDoc={generatePreviewHTML()}
            title="Website Preview"
            sandbox="allow-scripts allow-same-origin"
          />
        </div>
      </div>

      {/* Fullscreen preview modal — mobile only */}
      {previewOpen && (
        <div className="result-preview-modal">
          <div className="result-preview-modal-bar">
            <div style={{display:'flex',alignItems:'center',gap:'6px',flex:1,minWidth:0}}>
              <span className="result-preview-dot red" />
              <span className="result-preview-dot yellow" />
              <span className="result-preview-dot green" />
              <span className="result-preview-url" style={{marginLeft:'8px'}}>
                {userData?.businessName?.toLowerCase().replace(/\s+/g,'-')}.vercel.app
              </span>
            </div>
            <button className="result-preview-modal-close" onClick={() => setPreviewOpen(false)}>✕</button>
          </div>
          <iframe
            className="result-iframe"
            srcDoc={generatePreviewHTML()}
            title="Website Preview"
            sandbox="allow-scripts allow-same-origin"
          />
        </div>
      )}
    </div>
  )
}

// ─── App Root ─────────────────────────────────────────────────────────────────

export default function App() {
  const [result, setResult]           = useState(null)
  const [onboardingData, setOnboardingData] = useState(null)

  const handleComplete = (apiResult, userData) => {
    setResult(apiResult)
    setOnboardingData(userData)
  }

  if (!result) {
    return <Onboarding onComplete={handleComplete} />
  }

  return (
    <ResultView
      result={result}
      userData={onboardingData}
      onStartOver={() => { setResult(null); setOnboardingData(null) }}
    />
  )
}
