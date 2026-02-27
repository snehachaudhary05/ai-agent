import { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import { useTheme } from './useTheme'
import './Onboarding.css'

// ─── Image Utilities ───────────────────────────────────────────────────────────

/**
 * Convert a File/Blob to a compressed base64 JPEG data URL.
 * Resizes to maxW×maxH keeping aspect ratio, then compresses to JPEG.
 * Returns the data URL string (permanent — survives deployment).
 */
function toCompressedBase64(file, maxW = 1200, maxH = 900, quality = 0.78) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onerror = reject
    reader.onload = e => {
      const img = new Image()
      img.onerror = reject
      img.onload = () => {
        let { width: w, height: h } = img
        const ratio = Math.min(maxW / w, maxH / h, 1)   // never upscale
        w = Math.round(w * ratio)
        h = Math.round(h * ratio)
        const canvas = document.createElement('canvas')
        canvas.width  = w
        canvas.height = h
        canvas.getContext('2d').drawImage(img, 0, 0, w, h)
        resolve(canvas.toDataURL('image/jpeg', quality))
      }
      img.src = e.target.result
    }
    reader.readAsDataURL(file)
  })
}

// ─── Constants ────────────────────────────────────────────────────────────────

const BUSINESS_TYPES = [
  { value: 'restaurant', label: 'Restaurant / Café',   emoji: '🍽️', sells: 'services'  },
  { value: 'clothing',   label: 'Clothing Store',      emoji: '👗', sells: 'products'  },
  { value: 'salon',      label: 'Salon / Spa',         emoji: '💅', sells: 'services'  },
  { value: 'gym',        label: 'Gym / Fitness',       emoji: '💪', sells: 'services'  },
  { value: 'real-estate',label: 'Real Estate',         emoji: '🏠', sells: 'services'  },
  { value: 'coaching',   label: 'Coaching / Classes',  emoji: '📚', sells: 'services'  },
  { value: 'online-store',label: 'Online Store',       emoji: '🛒', sells: 'products'  },
  { value: 'other',      label: 'Other Business',      emoji: '💼', sells: 'both'      },
]

const STYLE_OPTIONS = [
  { value: 'modern',   label: 'Modern & Minimal',  desc: 'Clean, spacious, professional',   bg: '#f8fafc', text: '#1e293b' },
  { value: 'bold',     label: 'Bold & Colorful',   desc: 'Vibrant, energetic, eye-catching', bg: '#fbbf24', text: '#1e293b' },
  { value: 'elegant',  label: 'Elegant & Premium', desc: 'Luxury feel, sophisticated',       bg: '#1e293b', text: '#f8fafc' },
  { value: 'simple',   label: 'Simple & Clean',    desc: 'Easy to navigate, friendly',       bg: '#dbeafe', text: '#1e293b' },
  { value: 'dark',     label: 'Dark Theme',        desc: 'Sleek, tech-forward, modern',      bg: '#0f172a', text: '#e2e8f0' },
]

const QUICK_COLORS = ['#6366f1','#0ea5e9','#10b981','#f59e0b','#ef4444','#8b5cf6','#ec4899','#1e293b']

const TOTAL_STEPS = 8
// In production (Railway), frontend is served by the same FastAPI server,
// so relative URLs work. In local dev, VITE_API_URL points to localhost:8000.
const API = import.meta.env.VITE_API_URL || ''

// ─── Shared UI Atoms ──────────────────────────────────────────────────────────

function StepWrapper({ children, title, subtitle, onBack }) {
  return (
    <div className="ob-step">
      {onBack && (
        <button className="ob-back" onClick={onBack} type="button">
          ← Back
        </button>
      )}
      <div className="ob-step-head">
        {title    && <h2 className="ob-title">{title}</h2>}
        {subtitle && <p className="ob-subtitle">{subtitle}</p>}
      </div>
      {children}
    </div>
  )
}

function PrimaryBtn({ onClick, disabled, children }) {
  return (
    <button className="ob-primary-btn" onClick={onClick} disabled={disabled} type="button">
      {children}
    </button>
  )
}

// ─── Step 1 · Business Name ───────────────────────────────────────────────────

function Step1({ data, update, next, back }) {
  const ok = data.businessName.trim().length > 0
  return (
    <StepWrapper
      title="What's your business called? 👋"
      subtitle="Don't worry — you can always change this later."
      onBack={back}
    >
      <input
        className="ob-input ob-input-xl"
        type="text"
        placeholder="e.g.  Raj Bakery"
        value={data.businessName}
        onChange={e => update('businessName', e.target.value)}
        onKeyDown={e => e.key === 'Enter' && ok && next()}
        autoFocus
      />
      <PrimaryBtn onClick={next} disabled={!ok}>Continue →</PrimaryBtn>
    </StepWrapper>
  )
}

// ─── Step 2 · Business Type + selling-type confirmation ──────────────────────

function Step2({ data, update, next, back, onTypeSelect }) {
  // Sub-state A: no type chosen yet
  if (!data.businessType) {
    return (
      <StepWrapper
        title="What type of business is this?"
        subtitle="Pick the one that fits best — you can fine-tune after."
        onBack={back}
      >
        <div className="ob-type-grid">
          {BUSINESS_TYPES.map(bt => (
            <button
              key={bt.value}
              className="ob-type-card"
              onClick={() => onTypeSelect(bt.value, bt.sells)}
              type="button"
            >
              <span className="ob-type-emoji">{bt.emoji}</span>
              <span className="ob-type-label">{bt.label}</span>
            </button>
          ))}
        </div>
      </StepWrapper>
    )
  }

  // Sub-state B: type chosen, awaiting selling-type confirmation
  const sellingLabels = { products: 'Products', services: 'Services', both: 'Products & Services' }
  return (
    <StepWrapper
      title={`Looks like you sell ${sellingLabels[data.sellingType]} 🎯`}
      subtitle={`Based on your business type, we auto-selected "${sellingLabels[data.sellingType]}". Is this right?`}
      onBack={() => { update('businessType', ''); update('sellingType', '') }}
    >
      <div className="ob-confirm-list">
        <button className="ob-confirm-yes" onClick={() => next()} type="button">
          ✅  Yes, that's right
        </button>
        {[
          { v: 'products', icon: '📦', label: 'I sell Products' },
          { v: 'services', icon: '🛠️', label: 'I sell Services' },
          { v: 'both',     icon: '🔄', label: 'I sell Both' },
        ].filter(o => o.v !== data.sellingType).map(o => (
          <button
            key={o.v}
            className="ob-confirm-alt"
            onClick={() => { update('sellingType', o.v); next() }}
            type="button"
          >
            {o.icon}  {o.label}
          </button>
        ))}
      </div>
    </StepWrapper>
  )
}

// ─── Step 3 · Location ────────────────────────────────────────────────────────

function Step3({ data, update, next, back }) {
  const ok = data.location.trim().length > 0
  return (
    <StepWrapper
      title="Where is your business located? 📍"
      subtitle="Just city and country is enough."
      onBack={back}
    >
      <input
        className="ob-input ob-input-xl"
        type="text"
        placeholder="e.g.  Mumbai, India"
        value={data.location}
        onChange={e => update('location', e.target.value)}
        onKeyDown={e => e.key === 'Enter' && ok && next()}
        autoFocus
      />
      <PrimaryBtn onClick={next} disabled={!ok}>Continue →</PrimaryBtn>
    </StepWrapper>
  )
}

// ─── Step 4 · Style ───────────────────────────────────────────────────────────

function Step4({ data, update, next, back }) {
  return (
    <StepWrapper
      title="What style do you prefer? 🎨"
      subtitle="Sets the look and feel of your entire website."
      onBack={back}
    >
      <div className="ob-style-list">
        {STYLE_OPTIONS.map(opt => (
          <button
            key={opt.value}
            className={`ob-style-card${data.style === opt.value ? ' ob-style-selected' : ''}`}
            onClick={() => { update('style', opt.value); setTimeout(next, 180) }}
            type="button"
          >
            <div className="ob-style-swatch" style={{ background: opt.bg }}>
              <span style={{ color: opt.text, fontWeight: 800, fontSize: 12 }}>Aa</span>
            </div>
            <div className="ob-style-text">
              <span className="ob-style-name">{opt.label}</span>
              <span className="ob-style-desc">{opt.desc}</span>
            </div>
          </button>
        ))}
      </div>
    </StepWrapper>
  )
}

// ─── Step 5 · Brand Color ─────────────────────────────────────────────────────

function Step5({ data, update, next, back }) {
  return (
    <StepWrapper
      title="Choose your main brand color 🖌️"
      subtitle="Used for buttons, highlights, and accents."
      onBack={back}
    >
      <div className="ob-color-wrap">

        {!data.aiColor && (
          <div className="ob-color-picker-row">
            <input
              type="color"
              className="ob-color-input"
              value={data.brandColor}
              onChange={e => update('brandColor', e.target.value)}
            />
            <span className="ob-color-hex">{data.brandColor.toUpperCase()}</span>
          </div>
        )}

        <div className="ob-quick-colors">
          {QUICK_COLORS.map(c => (
            <button
              key={c}
              className={`ob-dot${!data.aiColor && data.brandColor === c ? ' ob-dot-active' : ''}`}
              style={{ background: c }}
              onClick={() => { update('brandColor', c); update('aiColor', false) }}
              type="button"
            />
          ))}
        </div>

        <button
          className={`ob-ai-color-btn${data.aiColor ? ' ob-ai-active' : ''}`}
          onClick={() => update('aiColor', !data.aiColor)}
          type="button"
        >
          ✨  {data.aiColor ? 'AI will pick the perfect color' : 'Let AI decide for me'}
        </button>
      </div>

      <PrimaryBtn onClick={next}>Continue →</PrimaryBtn>
    </StepWrapper>
  )
}

// ─── Step 6 · Products / Services ────────────────────────────────────────────

// Business-type-specific placeholder hints shown inside the input fields
const BUSINESS_HINTS = {
  restaurant: {
    name:        'e.g. Dal Makhni',
    price:       'e.g. ₹240',
    description: 'e.g. Slow-cooked black lentils in rich buttery tomato gravy',
    category:    'e.g. Main Course / Starters',
    subcategory: 'e.g. North Indian / South Indian',
  },
  clothing: {
    name:        'e.g. Floral Kurti',
    price:       'e.g. ₹1,299',
    description: 'e.g. Lightweight cotton kurti with floral embroidery',
    category:    'e.g. Kurtis / Lehengas',
    subcategory: 'e.g. Casual Wear / Party Wear',
  },
  salon: {
    name:        'e.g. Hair Cut & Styling',
    price:       'e.g. ₹500 onwards',
    description: 'e.g. Professional cut and blow-dry for all hair types',
    category:    'e.g. Hair Services / Skin Care',
    subcategory: 'e.g. Women\'s Cut / Men\'s Cut',
  },
  gym: {
    name:        'e.g. Personal Training',
    price:       'e.g. ₹2,000/month',
    description: 'e.g. One-on-one sessions with a certified fitness coach',
    category:    'e.g. Fitness / Yoga',
    subcategory: 'e.g. Weight Loss / Muscle Gain',
  },
  'real-estate': {
    name:        'e.g. 2BHK Apartment',
    price:       'e.g. ₹45 Lakh',
    description: 'e.g. Spacious 2BHK with modern amenities in prime location',
    category:    'e.g. Residential / Commercial',
    subcategory: 'e.g. Apartment / Villa',
  },
  coaching: {
    name:        'e.g. Math Coaching',
    price:       'e.g. ₹1,500/month',
    description: 'e.g. Comprehensive coaching for board exams with weekly tests',
    category:    'e.g. Academics / Competitive Exams',
    subcategory: 'e.g. Class 10 / Class 12',
  },
  'online-store': {
    name:        'e.g. Wireless Earbuds',
    price:       'e.g. ₹1,999',
    description: 'e.g. True wireless earbuds with 24-hour battery life',
    category:    'e.g. Electronics / Accessories',
    subcategory: 'e.g. Audio / Wearables',
  },
  other: {
    name:        'e.g. Consultation',
    price:       'e.g. ₹500',
    description: 'e.g. Brief description of what this service includes',
    category:    'e.g. Services / Packages',
    subcategory: 'e.g. Basic / Premium',
  },
}

function Step6({ data, update, next, back }) {
  const isProduct = data.sellingType === 'products'
  const label     = isProduct ? 'Product' : 'Service'
  const hints     = BUSINESS_HINTS[data.businessType] || BUSINESS_HINTS.other

  const lastCardRef  = useRef(null)
  const prevLengthRef = useRef(data.items.length)

  const addItem = () =>
    update('items', [...data.items, { name: '', price: '', description: '', image: null, imagePreview: null, category: '', subcategory: '' }])

  const updateItem = (idx, field, val) =>
    update('items', prevItems => prevItems.map((it, i) => i === idx ? { ...it, [field]: val } : it))

  const removeItem = idx =>
    update('items', data.items.filter((_, i) => i !== idx))

  // Auto-add first row on mount
  useEffect(() => {
    if (data.items.length === 0) {
      update('items', [{ name: '', price: '', description: '', image: null, imagePreview: null, category: '', subcategory: '' }])
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // Auto-scroll + focus when a new item is added
  useEffect(() => {
    if (data.items.length > prevLengthRef.current) {
      lastCardRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
      lastCardRef.current?.querySelector('input')?.focus()
    }
    prevLengthRef.current = data.items.length
  }, [data.items.length])

  const canNext = data.items.length > 0 && data.items.every(i => i.name.trim())

  return (
    <StepWrapper
      title={`Tell us about your ${label.toLowerCase()}s 📋`}
      subtitle={isProduct
        ? 'Add the products you want to showcase on your site.'
        : 'What services do you offer? Add them below.'}
      onBack={back}
    >
      <div className="ob-items-scroll">
        {data.items.map((item, idx) => (
          <div key={idx} className="ob-item-card" ref={idx === data.items.length - 1 ? lastCardRef : null}>
            <div className="ob-item-row-head">
              <span className="ob-item-badge">{label} {idx + 1}</span>
              {data.items.length > 1 && (
                <button className="ob-remove" onClick={() => removeItem(idx)} type="button">✕</button>
              )}
            </div>
            <input
              className="ob-input"
              placeholder={`${label} name * — ${hints.name}`}
              value={item.name}
              onChange={e => updateItem(idx, 'name', e.target.value)}
            />
            <input
              className="ob-input"
              placeholder={`Price — optional  ${hints.price}`}
              value={item.price}
              onChange={e => updateItem(idx, 'price', e.target.value)}
            />
            <textarea
              className="ob-textarea"
              placeholder={`Short description — optional  ${hints.description}`}
              rows={2}
              value={item.description}
              onChange={e => updateItem(idx, 'description', e.target.value)}
            />
            <input
              className="ob-input"
              placeholder={`Category — optional  ${hints.category}`}
              value={item.category}
              onChange={e => updateItem(idx, 'category', e.target.value)}
            />
            <input
              className="ob-input"
              placeholder={`Subcategory — optional  ${hints.subcategory}`}
              value={item.subcategory}
              onChange={e => updateItem(idx, 'subcategory', e.target.value)}
            />

            {/* Per-item photo — uploaded right next to the correct item */}
            <div className="ob-item-img-row">
              {item.imagePreview ? (
                <div className="ob-item-thumb-wrap">
                  <img className="ob-item-thumb" src={item.imagePreview} alt="preview" />
                  <button
                    className="ob-item-thumb-remove"
                    type="button"
                    onClick={() => { updateItem(idx, 'image', null); updateItem(idx, 'imagePreview', null); updateItem(idx, 'uploadedDataUrl', null) }}
                  >✕</button>
                  <span className="ob-item-uploaded-badge">✓ Uploaded</span>
                </div>
              ) : (
                <label className="ob-item-upload-btn">
                  📷 Add photo — optional
                  <input
                    type="file"
                    accept="image/*"
                    style={{ display: 'none' }}
                    onChange={async e => {
                      const file = e.target.files[0]
                      if (!file) return
                      updateItem(idx, 'image', file)
                      updateItem(idx, 'imagePreview', URL.createObjectURL(file))
                      // Also convert to permanent base64 for backend/deployment
                      try {
                        const b64 = await toCompressedBase64(file)
                        updateItem(idx, 'uploadedDataUrl', b64)
                      } catch { /* non-fatal — preview still works */ }
                    }}
                  />
                </label>
              )}
            </div>
          </div>
        ))}
      </div>

      <button className="ob-add-btn" onClick={addItem} type="button">
        + Add Another {label}
      </button>

      <PrimaryBtn onClick={next} disabled={!canNext}>Continue →</PrimaryBtn>
    </StepWrapper>
  )
}

// ─── Step 7 · Photos ──────────────────────────────────────────────────────────

function Step7({ data, update, next, back }) {

  if (data.useOwnPhotos === null) {
    return (
      <StepWrapper
        title="Do you have business photos to upload? 📸"
        subtitle="Great photos make websites shine — but we can also find them for you."
        onBack={back}
      >
        <div className="ob-choice-list">
          <button
            className="ob-choice-card"
            onClick={() => update('useOwnPhotos', true)}
            type="button"
          >
            <span className="ob-choice-icon">📤</span>
            <div className="ob-choice-text">
              <span className="ob-choice-title">Yes, I'll upload my own photos</span>
              <span className="ob-choice-sub">Logo, storefront, team</span>
            </div>
          </button>
          <button
            className="ob-choice-card"
            onClick={() => { update('useOwnPhotos', false); next() }}
            type="button"
          >
            <span className="ob-choice-icon">🤖</span>
            <div className="ob-choice-text">
              <span className="ob-choice-title">Use AI-generated + stock images</span>
              <span className="ob-choice-sub">We'll find the best visuals automatically</span>
            </div>
          </button>
        </div>
      </StepWrapper>
    )
  }

  const UPLOAD_FIELDS = [
    { key: 'logo',       label: 'Logo',               hint: 'PNG or SVG preferred', multiple: false },
    { key: 'storefront', label: 'Store / Office Photo',hint: 'Your physical space',  multiple: false },
    { key: 'team',       label: 'Team Photo',          hint: 'Optional',             multiple: false },
  ]

  return (
    <StepWrapper
      title="Upload your photos 📸"
      subtitle="All uploads are optional — skip any you don't have."
      onBack={() => update('useOwnPhotos', null)}
    >
      <div className="ob-upload-list">
        {UPLOAD_FIELDS.map(({ key, label, hint, multiple }) => {
          const hasFile = data.uploadedPhotos[key] &&
            (Array.isArray(data.uploadedPhotos[key])
              ? data.uploadedPhotos[key].length > 0
              : true)
          return (
            <div key={key} className="ob-upload-row">
              <div className="ob-upload-info">
                <span className="ob-upload-label">{label}</span>
                <span className="ob-upload-hint">{hint}</span>
              </div>
              <label className={`ob-upload-btn${hasFile ? ' ob-uploaded' : ''}`}>
                {hasFile ? '✓ Uploaded' : 'Choose file'}
                <input
                  type="file"
                  accept="image/*"
                  multiple={multiple}
                  style={{ display: 'none' }}
                  onChange={e => {
                    const val = multiple ? Array.from(e.target.files) : e.target.files[0]
                    update('uploadedPhotos', { ...data.uploadedPhotos, [key]: val })
                  }}
                />
              </label>
            </div>
          )
        })}
      </div>
      <PrimaryBtn onClick={next}>Continue →</PrimaryBtn>
    </StepWrapper>
  )
}

// ─── Step 8 · Contact Info ────────────────────────────────────────────────────

function Step8({ data, update, back, onSubmit, loading }) {
  const canSubmit = data.phone.trim() && data.email.trim()

  return (
    <StepWrapper
      title="Almost done! How can customers reach you? 📞"
      subtitle="Phone and email are required. Everything else is optional."
      onBack={back}
    >
      <div className="ob-contact-grid">
        {[
          { key: 'phone',     label: 'Phone number *',          type: 'tel',    ph: '+91 98765 43210'           },
          { key: 'email',     label: 'Email address *',          type: 'email',  ph: 'hello@yourbusiness.com'    },
          { key: 'whatsapp',  label: 'WhatsApp',                 type: 'tel',    ph: '+91 98765 43210'           },
          { key: 'instagram', label: 'Instagram',                type: 'text',   ph: '@yourbusiness'             },
          { key: 'facebook',  label: 'Facebook',                 type: 'text',   ph: 'facebook.com/yourbusiness' },
        ].map(({ key, label, type, ph }) => (
          <div key={key} className="ob-contact-field">
            <label className="ob-field-label">
              {label.replace(' *', '')}
              {label.includes('*')
                ? <span className="ob-required"> *</span>
                : <span className="ob-opt"> (optional)</span>}
            </label>
            <input
              className="ob-input"
              type={type}
              placeholder={ph}
              value={data[key]}
              onChange={e => update(key, e.target.value)}
            />
          </div>
        ))}
      </div>

      <button
        className={`ob-submit-btn${loading ? ' ob-submitting' : ''}`}
        onClick={onSubmit}
        disabled={!canSubmit || loading}
        type="button"
      >
        {loading
          ? <><span className="ob-spinner" /> Building your website…</>
          : '🚀  Build My Website'}
      </button>
    </StepWrapper>
  )
}

// ─── Root Component ───────────────────────────────────────────────────────────

export default function Onboarding({ onComplete }) {
  const [theme, toggleTheme] = useTheme()
  const [step, setStep]     = useState(1)
  const [loading, setLoading] = useState(false)
  const [data, setData]     = useState({
    businessName:   '',
    businessType:   '',
    sellingType:    '',
    location:       '',
    style:          '',
    brandColor:     '#6366f1',
    aiColor:        false,
    items:          [],
    useOwnPhotos:   null,
    uploadedPhotos: { logo: null, storefront: null, products: [], team: null },
    phone:          '',
    whatsapp:       '',
    email:          '',
    instagram:      '',
    facebook:       '',
  })

  const update = (key, val) => setData(prev => ({ ...prev, [key]: typeof val === 'function' ? val(prev[key]) : val }))
  const next   = ()         => setStep(s => Math.min(s + 1, TOTAL_STEPS))
  const back   = ()         => setStep(s => Math.max(s - 1, 1))

  const onTypeSelect = (type, sells) => {
    update('businessType', type)
    update('sellingType', sells)
  }

  const handleSubmit = async () => {
    setLoading(true)
    try {
      // Hero queries: striking full-width background — show the business at its best
      const heroSearchContext = {
        clothing:      'indian ethnic fashion model traditional outfit editorial photoshoot',
        restaurant:    'restaurant dining table food evening ambiance warm candlelight',
        salon:         'luxury beauty salon elegant interior professional hair styling',
        gym:           'modern gym fitness interior athlete workout equipment',
        coaching:      'bright classroom students learning education professional',
        'real-estate': 'luxury house exterior architecture modern property driveway',
        'online-store':'fashion clothing products lifestyle stylish flat lay editorial',
        other:         'modern professional business office interior clean',
      }
      // About queries: warm, human, behind-the-scenes — team or owner feel
      const aboutSearchContext = {
        clothing:      'fashion boutique owner woman ethnic clothing stylish smiling warm',
        restaurant:    'chef kitchen cooking team culinary professional smiling',
        salon:         'hairstylist salon professional woman smiling beauty treatment',
        gym:           'fitness trainer coach gym motivation smiling team',
        coaching:      'teacher mentor student whiteboard classroom smiling',
        'real-estate': 'real estate agent handshake keys house property professional smiling',
        'online-store':'entrepreneur woman business fashion packaging professional smiling',
        other:         'professional business team office smiling warm friendly',
      }
      // Gallery queries: 4 varied visuals per business type for the gallery section
      const gallerySearchContext = {
        restaurant:    ['indian food dish plated presentation', 'restaurant interior ambiance dining', 'dessert sweet food presentation', 'restaurant kitchen cooking chef'],
        clothing:      ['indian ethnic saree woman fashion', 'kurti ethnic clothing woman', 'lehenga traditional indian dress', 'fashion clothing boutique display'],
        salon:         ['hair styling salon professional', 'facial skin care beauty spa', 'nail art manicure beauty', 'makeup beauty professional woman'],
        gym:           ['gym workout weights exercise', 'cardio running fitness treadmill', 'yoga stretch fitness', 'muscle training gym athlete'],
        coaching:      ['students studying classroom education', 'online learning laptop course', 'whiteboard teaching professional', 'graduation certificate achievement'],
        'real-estate': ['luxury living room interior modern', 'bedroom interior elegant design', 'modern kitchen interior house', 'house exterior garden pool'],
        'online-store':['clothing fashion product display', 'online shopping packaging delivery', 'fashion accessories stylish', 'ecommerce product flat lay'],
        other:         ['business office interior professional', 'team meeting professional', 'customer service professional', 'product service quality'],
      }
      const heroQuery  = heroSearchContext[data.businessType]  || 'modern professional business interior'
      const aboutQuery = aboutSearchContext[data.businessType] || 'professional business team smiling'
      const galleryQueries = gallerySearchContext[data.businessType] || gallerySearchContext.other
      const [heroRes, aboutRes, itemsWithImages, galleryResults] = await Promise.all([
        axios.get(`${API}/api/image-search`, { params: { query: heroQuery, orientation: 'landscape' } }).catch(() => ({ data: { url: null } })),
        axios.get(`${API}/api/image-search`, { params: { query: aboutQuery } }).catch(() => ({ data: { url: null } })),
        Promise.all(
          data.items.map(async item => {
            // User uploaded a photo — use their base64 data URL directly (works in deployed site too)
            if (item.uploadedDataUrl) return { ...item, fetchedImage: item.uploadedDataUrl }
            if (item.imagePreview && !item.uploadedDataUrl) return item  // base64 still converting, preview only
            try {
              // Add business-type context so Pexels returns the served product, not the raw ingredient
              const itemContextSuffix = {
                restaurant:    'plated dish',
                clothing:      'fashion clothing wear outfit',
                salon:         'beauty salon spa professional',
                gym:           'fitness workout exercise',
                coaching:      'education learning class study',
                'real-estate': 'property interior home',
                'online-store':'',   // rely on item name + category; generic suffix caused wrong images
                other:         '',
              }
              // Per-service overrides for ambiguous salon terms that return wrong images
              const salonQueryOverrides = {
                'waxing':         'body waxing beauty salon treatment woman',
                'wax':            'body waxing beauty salon treatment woman',
                'manicure':       'nail manicure beauty salon nails',
                'pedicure':       'nail pedicure foot spa treatment',
                'facial':         'facial skin care beauty spa treatment',
                'face treatment': 'facial skin care beauty spa treatment',
                'bleaching':      'hair bleach salon professional treatment',
                'hair color':     'hair coloring salon professional',
                'hair colour':    'hair coloring salon professional',
                'threading':      'eyebrow threading beauty salon',
              }
              // Clothing overrides: correct spelling + visual context for Indian traditional wear
              const clothingQueryOverrides = {
                'lehnga':        'lehenga indian bridal traditional dress woman',
                'lehenga':       'lehenga indian bridal traditional dress woman',
                'bridal lehnga': 'bridal lehenga indian wedding dress woman',
                'kurti':         'kurti indian ethnic kurta woman fashion',
                'kurtis':        'kurti indian ethnic kurta woman fashion',
                'saree':         'saree indian traditional sari woman elegant',
                'sari':          'saree indian traditional sari woman elegant',
                'salwar':        'salwar kameez indian ethnic suit woman',
                'salwar kameez': 'salwar kameez indian ethnic suit woman',
                'churidar':      'churidar indian ethnic wear woman fashion',
                'dupatta':       'dupatta indian ethnic scarf woman fashion',
                'anarkali':      'anarkali suit indian ethnic dress woman',
                'sharara':       'sharara indian ethnic wear woman fashion',
                'palazzo':       'palazzo pants indian ethnic fashion woman',
                'kurta':         'kurta indian ethnic wear man fashion',
              }
              // Gym overrides: specific fitness class/activity visuals
              const gymQueryOverrides = {
                'zumba':          'zumba dance fitness class women energetic colourful',
                'yoga':           'yoga class studio women meditation calm',
                'boxing':         'boxing training gym punching bag gloves athlete',
                'kickboxing':     'kickboxing martial arts training gym athlete',
                'crossfit':       'crossfit gym workout athlete functional fitness',
                'hiit':           'hiit high intensity interval training workout gym',
                'pilates':        'pilates class studio reformer woman fitness',
                'cardio':         'cardio running treadmill gym fitness athlete',
                'swimming':       'swimming pool lane athlete training water',
                'cycling':        'indoor cycling spin class gym fitness',
                'spin':           'spin class indoor cycling bike gym',
                'aerobics':       'aerobics fitness class women gym energetic',
                'strength':       'strength training weight lifting gym dumbbell',
                'weight training':'weight training gym dumbbell barbell athlete',
                'personal training':'personal trainer client gym coaching fitness',
                'martial arts':   'martial arts karate training dojo athlete',
                'dance':          'dance fitness class studio women energetic',
                'functional':     'functional fitness training gym athlete',
                'muscle':         'muscle building gym bodybuilder dumbbell training',
              }
              // Coaching overrides: subject/exam specific study visuals
              const coachingQueryOverrides = {
                'neet':          'medical entrance exam preparation students studying books',
                'jee':           'engineering entrance exam preparation students studying',
                'iit':           'iit jee engineering exam preparation students notes',
                'upsc':          'upsc civil services exam preparation student books',
                'ias':           'upsc ias exam preparation notes student studying',
                'cat':           'mba cat exam preparation students studying notes',
                'gmat':          'gmat mba exam preparation student studying notes',
                'ielts':         'ielts english language test preparation student',
                'toefl':         'toefl english language test preparation student',
                'spoken english':'english speaking class conversation students confident',
                'english speaking':'english speaking class conversation students confident',
                'english':       'english language learning class students whiteboard',
                'mathematics':   'mathematics tutor student whiteboard equations classroom',
                'maths':         'mathematics tutor student whiteboard equations classroom',
                'physics':       'physics experiment lab students science classroom',
                'chemistry':     'chemistry lab experiment students science',
                'biology':       'biology students microscope lab science classroom',
                'science':       'science students lab experiment classroom learning',
                'computer':      'computer programming coding class students laptop',
                'coding':        'coding programming class students laptop technology',
                'python':        'python programming coding class students laptop',
                'accounts':      'accounting finance class students professional study',
                'commerce':      'commerce students classroom education books notes',
                'drawing':       'art drawing class students creative sketch',
                'music':         'music class guitar piano students learning',
                'dance':         'dance class studio students learning performance',
                'abacus':        'abacus mental math kids classroom learning',
              }
              // Restaurant overrides: match specific Indian/popular dishes to vivid food photography
              const restaurantQueryOverrides = {
                'biryani':        'biryani rice indian food plated restaurant',
                'chicken biryani':'chicken biryani rice indian food plated',
                'mutton biryani': 'mutton biryani rice indian food plated',
                'dal makhani':    'dal makhani indian food lentil curry plated',
                'butter chicken': 'butter chicken curry indian food plated restaurant',
                'paneer':         'paneer indian food curry plated restaurant',
                'naan':           'naan bread indian food restaurant baked',
                'roti':           'roti chapati indian bread food restaurant',
                'paratha':        'paratha indian flatbread food plated restaurant',
                'dosa':           'dosa south indian food crepe plated restaurant',
                'idli':           'idli sambar south indian food plated breakfast',
                'thali':          'indian thali platter assorted food restaurant',
                'pizza':          'pizza italian food plated restaurant cheesy',
                'pasta':          'pasta italian food plated restaurant creamy',
                'burger':         'burger sandwich food plated restaurant bun',
                'sandwich':       'sandwich food plated restaurant fresh',
                'momos':          'momos dumplings food steamed plated street food',
                'sushi':          'sushi japanese food plated restaurant fresh',
                'steak':          'steak grilled meat food plated restaurant',
                'soup':           'soup bowl food plated restaurant warm',
                'salad':          'salad fresh bowl food plated restaurant healthy',
                'dessert':        'dessert sweet food plated restaurant elegant',
                'cake':           'cake slice dessert food plated bakery',
                'ice cream':      'ice cream scoop dessert food sweet colorful',
                'coffee':         'coffee cup latte art cafe professional',
                'smoothie':       'smoothie fruit drink colorful glass fresh',
                'juice':          'fresh juice glass fruit colorful healthy',
                'rolls':          'rolls wrap food plated street food fresh',
                'kebab':          'kebab grilled meat skewer food plated restaurant',
                'tandoori':       'tandoori grilled chicken food plated restaurant',
                'curry':          'curry indian food bowl plated restaurant spicy',
                'fried rice':     'fried rice chinese food plated restaurant wok',
                'noodles':        'noodles chinese food plated restaurant wok',
                'chowmein':       'chowmein chinese noodles food plated restaurant',
                'manchurian':     'manchurian chinese food plated restaurant sauce',
                'pav bhaji':      'pav bhaji indian street food plated restaurant',
                'chole':          'chole bhature indian food plated restaurant',
                'samosa':         'samosa indian snack food fried crispy plated',
                'gulab jamun':    'gulab jamun indian sweet dessert plated restaurant',
                'rasgulla':       'rasgulla indian sweet dessert plated restaurant',
                'halwa':          'halwa indian sweet dessert plated restaurant',
                'lassi':          'lassi indian yogurt drink glass restaurant',
                'chai':           'masala chai tea cup indian drink restaurant',
                'tea':            'tea cup hot drink saucer professional',
              }
              // Real-estate overrides: map property types to vivid interior/exterior Pexels queries
              const realEstateQueryOverrides = {
                'studio apartment':  'studio apartment interior modern minimal cozy',
                'studio':            'studio apartment interior modern compact',
                '1bhk':              '1bhk apartment interior living room modern',
                '1 bhk':             '1bhk apartment interior living room modern',
                '1bhk apartment':    '1bhk apartment interior living room modern',
                '2bhk':              '2bhk apartment interior spacious living room',
                '2 bhk':             '2bhk apartment interior spacious living room',
                '2bhk apartment':    '2bhk apartment interior spacious living room',
                '3bhk':              '3bhk apartment interior luxury living room',
                '3 bhk':             '3bhk apartment interior luxury living room',
                '3bhk apartment':    '3bhk apartment interior luxury living room',
                '4bhk':              '4bhk apartment interior premium spacious',
                '4 bhk':             '4bhk apartment interior premium spacious',
                'villa':             'luxury villa exterior pool garden modern',
                'bungalow':          'bungalow house exterior modern architecture',
                'penthouse':         'penthouse apartment interior luxury city view',
                'duplex':            'duplex house interior elegant modern staircase',
                'rowhouse':          'row house exterior modern residential',
                'row house':         'row house exterior modern residential',
                'plot':              'residential plot land green neighbourhood',
                'commercial':        'commercial office space interior modern professional',
                'shop':              'retail shop commercial space interior modern',
                'office space':      'modern office interior professional workspace',
                'warehouse':         'industrial warehouse interior storage large',
              }
              const nameLower = item.name.trim().toLowerCase()
              // Strip marketing prefixes (Premium, Special, etc.) so Pexels finds the actual food/item
              const cleanName = item.name.trim().replace(/^(premium|special|classic|deluxe|signature|house|royal|chef'?s?|fresh|homemade)\s+/i, '')
              // Find best override: check if item name CONTAINS any key (longest key first for specificity)
              const findOverride = (overrides, name) => {
                const key = Object.keys(overrides).sort((a, b) => b.length - a.length).find(k => name.includes(k))
                return key ? overrides[key] : null
              }
              const salonOverride      = data.businessType === 'salon'                                              ? findOverride(salonQueryOverrides, nameLower)      : null
              const clothingOverride   = (data.businessType === 'clothing' || data.businessType === 'online-store') ? findOverride(clothingQueryOverrides, nameLower)    : null
              const gymOverride        = data.businessType === 'gym'                                                ? findOverride(gymQueryOverrides, nameLower)         : null
              const coachingOverride   = data.businessType === 'coaching'                                           ? findOverride(coachingQueryOverrides, nameLower)    : null
              const restaurantOverride = data.businessType === 'restaurant'                                         ? findOverride(restaurantQueryOverrides, nameLower)  : null
              const realEstateOverride = data.businessType === 'real-estate'                                        ? findOverride(realEstateQueryOverrides, nameLower)  : null
              const suffix = itemContextSuffix[data.businessType] || ''
              const subcatCtx = item.subcategory && item.subcategory.trim()
              const catCtx    = item.category    && item.category.trim()
              // Organisational/dietary labels that add noise to image search — skip them
              const NON_VISUAL = new Set(['veg', 'non-veg', 'vegetarian', 'non-vegetarian', 'jain',
                'main course', 'starter', 'starters', 'side', 'sides', 'add-on',
                'ready to move', 'under construction', 'resale', 'new launch', 'pre-launch',
                'affordable', 'luxury', 'budget', 'premium', 'semi-furnished', 'furnished', 'unfurnished'])
              const subcatVisual = subcatCtx && !NON_VISUAL.has(subcatCtx.toLowerCase())
              const catVisual    = catCtx    && !NON_VISUAL.has(catCtx.toLowerCase())
              // Query strategy:
              //   1. Specific override (salon/clothing/gym/coaching/restaurant/real-estate)
              //   2. cleanName + visual subcategory + suffix  (most context)
              //   3. cleanName + suffix  (when subcategory is non-visual or absent)
              //   4. cleanName alone  (no suffix defined for this business type)
              const specificOverride = salonOverride || clothingOverride || gymOverride || coachingOverride || restaurantOverride || realEstateOverride
              const q = specificOverride
                ? specificOverride
                : suffix
                  ? (subcatVisual
                      ? `${cleanName} ${subcatCtx} ${suffix}`
                      : catVisual
                        ? `${cleanName} ${catCtx} ${suffix}`
                        : `${cleanName} ${suffix}`)
                  : subcatVisual
                    ? `${cleanName} ${subcatCtx}`
                    : catVisual
                      ? `${cleanName} ${catCtx}`
                      : cleanName
              const imgRes = await axios.get(`${API}/api/image-search`, { params: { query: q } })
              return { ...item, fetchedImage: imgRes.data.url || null }
            } catch {
              return item
            }
          })
        ),
        // Fetch 4 dedicated gallery images in parallel
        Promise.all(
          galleryQueries.map(q =>
            axios.get(`${API}/api/image-search`, { params: { query: q } }).catch(() => ({ data: { url: null } }))
          )
        ),
      ])

      // Convert uploaded storefront/logo/team photos to base64 (permanent, works in deployed site)
      const storefrontFile = data.uploadedPhotos?.storefront
      const logoFile       = data.uploadedPhotos?.logo
      const teamFile       = data.uploadedPhotos?.team

      const [storefrontB64, logoB64] = await Promise.all([
        storefrontFile ? toCompressedBase64(storefrontFile) : Promise.resolve(null),
        logoFile       ? toCompressedBase64(logoFile, 400, 400, 0.9) : Promise.resolve(null),
      ])

      // About image: prefer user's storefront upload (base64), fall back to Pexels
      const aboutImage = storefrontB64 || aboutRes.data.url || null

      const enrichedData = { ...data, items: itemsWithImages, heroImage: heroRes.data.url || null, aboutImage, logoImage: logoB64 || null }

      // Collect permanent image URLs for each service (base64 if user uploaded, else Pexels URL)
      const serviceImageUrls = itemsWithImages.map(it => it.fetchedImage || null)
      // About image URL — base64 if user uploaded storefront, else Pexels
      const aboutImageUrl = storefrontB64 || aboutRes.data.url || null
      // Gallery images (4 dedicated Pexels shots for the gallery section)
      const galleryImageUrls = galleryResults.map(r => r.data?.url || null).filter(Boolean)

      const res = await axios.post(`${API}/api/react/build`, {
        session_id:           `session-${Date.now()}`,
        business_name:        data.businessName,
        business_type:        data.businessType,
        business_description: `${data.businessName} — a ${data.businessType} business in ${data.location}.`,
        services:             data.items.map(i => i.name).filter(Boolean),
        service_categories:   data.items
          .filter(i => i.name.trim())
          .map(i => ({ name: i.name.trim(), category: i.category || '', subcategory: i.subcategory || '', price: i.price || '' })),
        location:             data.location,
        style_vibe:           data.style || 'modern',
        features:             ['contact', 'gallery', data.sellingType === 'products' ? 'ordering' : 'booking'],
        deploy:               false,  // HTML deployed from frontend via /api/react/deploy-html
        brand_color:          data.aiColor ? null : data.brandColor,
        use_own_photos:       data.useOwnPhotos,
        // Images: Pexels URLs or base64 data URLs (user uploads)
        hero_image:           heroRes.data.url || null,
        about_image:          aboutImageUrl,
        logo_image:           logoB64 || null,
        service_images:       serviceImageUrls,
        gallery_images:       galleryImageUrls,
        contact: {
          phone: data.phone, whatsapp: data.whatsapp,
          email: data.email, instagram: data.instagram, facebook: data.facebook,
        },
      })
      onComplete(res.data, enrichedData)
    } catch (err) {
      alert(err.response?.data?.detail || 'Something went wrong. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const progress = ((step - 1) / (TOTAL_STEPS - 1)) * 100
  const props    = { data, update, next, back }

  return (
    <div className="ob-root">

      {/* ── Header ── */}
      <header className="ob-header">
        <div className="ob-brand">✦ Sitekraft</div>
        <div className="ob-header-right">
          <span className="ob-step-counter">Step {step} of {TOTAL_STEPS}</span>
          <button
            className="ob-theme-btn"
            onClick={toggleTheme}
            title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
          >
            {theme === 'dark' ? '☀️' : '🌙'}
          </button>
        </div>
      </header>

      {/* ── Progress bar ── */}
      <div className="ob-progress-track">
        <div className="ob-progress-fill" style={{ width: `${progress}%` }} />
      </div>

      {/* ── Step card ── */}
      <main className="ob-main">
        <div className="ob-card" key={step}>
          {step === 1 && <Step2 {...props} back={undefined} onTypeSelect={onTypeSelect} />}
          {step === 2 && <Step1 {...props} />}
          {step === 3 && <Step3 {...props} />}
          {step === 4 && <Step4 {...props} />}
          {step === 5 && <Step5 {...props} />}
          {step === 6 && <Step6 {...props} />}
          {step === 7 && <Step7 {...props} />}
          {step === 8 && <Step8 {...props} onSubmit={handleSubmit} loading={loading} />}
        </div>
      </main>

    </div>
  )
}
