"""
React/Vite Template Generator
Creates complete React + Vite projects with Tailwind CSS and Supabase integration
"""

import json
from typing import Dict, List, Optional

class ReactTemplateGenerator:
    """Generates React/Vite project files with modern setup"""

    def __init__(self):
        self.supabase_enabled = True
        self.tailwind_enabled = True

    def generate_complete_project(
        self,
        project_name: str,
        description: str,
        components: List[Dict],
        theme: Dict,
        features: List[str],
        supabase_config: Optional[Dict] = None
    ) -> Dict[str, str]:
        """
        Generate all files for a complete React/Vite project

        Args:
            project_name: Name of the project
            description: Project description
            components: List of React components to generate
            theme: Theme configuration (colors, fonts, etc.)
            features: List of features (auth, booking, ecommerce, etc.)
            supabase_config: Supabase configuration if enabled

        Returns:
            Dictionary of {file_path: file_content}
        """
        files = {}

        # Core configuration files
        files["package.json"] = self.generate_package_json(project_name, description, features)
        files["vite.config.js"] = self.generate_vite_config()
        files["index.html"] = self.generate_index_html(project_name)
        files[".gitignore"] = self.generate_gitignore()
        files["README.md"] = self.generate_readme(project_name, description)

        # Tailwind CSS configuration
        if self.tailwind_enabled:
            files["tailwind.config.js"] = self.generate_tailwind_config(theme)
            files["postcss.config.js"] = self.generate_postcss_config()

        # Main application files
        files["src/main.jsx"] = self.generate_main_jsx()
        files["src/App.jsx"] = self.generate_app_jsx(components, features)
        files["src/index.css"] = self.generate_index_css()

        # Supabase integration
        if supabase_config and "database" in features:
            files["src/lib/supabase.js"] = self.generate_supabase_client(supabase_config)

        # Generate component files
        for component in components:
            comp_name = component.get("name")
            comp_code = component.get("code", "")
            files[f"src/components/{comp_name}.jsx"] = comp_code

        # Generate pages
        if "routing" in features:
            files["src/pages/Home.jsx"] = self.generate_home_page(components)
            files["src/pages/About.jsx"] = self.generate_about_page()

        # Add utility files
        files["src/utils/helpers.js"] = self.generate_helpers()

        # Environment template
        files[".env.example"] = self.generate_env_example(features)

        return files

    def generate_package_json(self, project_name: str, description: str, features: List[str]) -> str:
        """Generate package.json with all dependencies"""
        package_data = {
            "name": project_name.lower().replace(" ", "-"),
            "private": True,
            "version": "0.1.0",
            "type": "module",
            "description": description,
            "scripts": {
                "dev": "vite",
                "build": "vite build",
                "preview": "vite preview",
                "lint": "eslint . --ext js,jsx --report-unused-disable-directives --max-warnings 0"
            },
            "dependencies": {
                "react": "^18.3.1",
                "react-dom": "^18.3.1",
                "react-router-dom": "^6.22.0"
            },
            "devDependencies": {
                "@vitejs/plugin-react": "^4.2.1",
                "vite": "^5.1.0",
                "eslint": "^8.56.0",
                "eslint-plugin-react": "^7.33.2",
                "eslint-plugin-react-hooks": "^4.6.0",
                "eslint-plugin-react-refresh": "^0.4.5"
            }
        }

        # Add Tailwind CSS if enabled
        if self.tailwind_enabled:
            package_data["devDependencies"]["tailwindcss"] = "^3.4.1"
            package_data["devDependencies"]["postcss"] = "^8.4.35"
            package_data["devDependencies"]["autoprefixer"] = "^10.4.17"

        # Add feature-specific dependencies
        if "auth" in features or "database" in features or "storage" in features:
            package_data["dependencies"]["@supabase/supabase-js"] = "^2.39.7"

        if "animation" in features:
            package_data["dependencies"]["framer-motion"] = "^11.0.5"

        if "forms" in features:
            package_data["dependencies"]["react-hook-form"] = "^7.50.1"

        if "icons" in features:
            package_data["dependencies"]["lucide-react"] = "^0.336.0"

        if "charts" in features:
            package_data["dependencies"]["recharts"] = "^2.12.0"

        return json.dumps(package_data, indent=2)

    def generate_vite_config(self) -> str:
        """Generate vite.config.js"""
        return """import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    open: true
  },
  build: {
    outDir: 'dist',
    sourcemap: false
  }
})
"""

    def generate_index_html(self, project_name: str) -> str:
        """Generate index.html"""
        return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{project_name}</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
"""

    def generate_gitignore(self) -> str:
        """Generate .gitignore"""
        return """# Logs
logs
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*
pnpm-debug.log*
lerna-debug.log*

node_modules
dist
dist-ssr
*.local

# Editor directories and files
.vscode/*
!.vscode/extensions.json
.idea
.DS_Store
*.suo
*.ntvs*
*.njsproj
*.sln
*.sw?

# Environment variables
.env
.env.local
.env.*.local
"""

    def generate_readme(self, project_name: str, description: str) -> str:
        """Generate README.md"""
        return f"""# {project_name}

{description}

## 🚀 Getting Started

### Prerequisites
- Node.js 18+
- npm or yarn

### Installation

1. Install dependencies:
```bash
npm install
```

2. Copy environment variables:
```bash
cp .env.example .env
```

3. Add your Supabase credentials to `.env`

4. Start development server:
```bash
npm run dev
```

5. Build for production:
```bash
npm run build
```

## 🛠️ Built With

- **React 18** - UI library
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **Supabase** - Backend & Database
- **React Router** - Navigation

## 📝 License

This project was generated by AI Website Builder.

---

Generated with ❤️ by AI Website Builder
"""

    def generate_tailwind_config(self, theme: Dict) -> str:
        """Generate tailwind.config.js with custom theme"""
        colors = theme.get("colors", {})
        fonts = theme.get("fonts", {})

        return f"""/** @type {{import('tailwindcss').Config}} */
export default {{
  content: [
    "./index.html",
    "./src/**/*.{{js,ts,jsx,tsx}}",
  ],
  theme: {{
    extend: {{
      colors: {{
        primary: '{colors.get("primary", "#667eea")}',
        secondary: '{colors.get("secondary", "#764ba2")}',
        accent: '{colors.get("accent", "#f59e0b")}',
      }},
      fontFamily: {{
        sans: ['{fonts.get("body", "Inter")}', 'system-ui', 'sans-serif'],
        heading: ['{fonts.get("heading", "Poppins")}', 'system-ui', 'sans-serif'],
      }},
      animation: {{
        'fade-in': 'fadeIn 0.8s ease-in-out',
        'fade-in-up': 'fadeInUp 0.8s ease-out',
        'slide-in': 'slideIn 0.6s ease-out',
        'slow-zoom': 'slowZoom 20s ease-in-out infinite',
        'bounce': 'bounce 2s infinite',
      }},
      keyframes: {{
        fadeIn: {{
          '0%': {{ opacity: '0' }},
          '100%': {{ opacity: '1' }},
        }},
        fadeInUp: {{
          '0%': {{ opacity: '0', transform: 'translateY(30px)' }},
          '100%': {{ opacity: '1', transform: 'translateY(0)' }},
        }},
        slideIn: {{
          '0%': {{ transform: 'translateX(-100%)' }},
          '100%': {{ transform: 'translateX(0)' }},
        }},
        slowZoom: {{
          '0%, 100%': {{ transform: 'scale(1)' }},
          '50%': {{ transform: 'scale(1.1)' }},
        }},
      }},
    }},
  }},
  plugins: [],
}}
"""

    def generate_postcss_config(self) -> str:
        """Generate postcss.config.js"""
        return """export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
"""

    def generate_main_jsx(self) -> str:
        """Generate src/main.jsx"""
        return """import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
"""

    def generate_app_jsx(self, components: List[Dict], features: List[str]) -> str:
        """Generate src/App.jsx"""
        has_routing = "routing" in features

        if has_routing:
            return """import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Home from './pages/Home'
import About from './pages/About'
import './index.css'

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/about" element={<About />} />
      </Routes>
    </Router>
  )
}

export default App
"""
        else:
            # Simple single-page app
            comp_imports = "\n".join([f"import {c.get('name')} from './components/{c.get('name')}'" for c in components])
            comp_renders = "\n      ".join([f"<{c.get('name')} />" for c in components])

            return f"""import './index.css'
{comp_imports}

function App() {{
  return (
    <div className="app">
      {comp_renders}
    </div>
  )
}}

export default App
"""

    def generate_index_css(self) -> str:
        """Generate src/index.css with Tailwind imports"""
        return """@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  * {
    @apply box-border;
  }

  body {
    @apply antialiased overflow-x-hidden;
  }

  html {
    scroll-behavior: smooth;
    overflow-x: hidden;
  }

  /* Ensure images are responsive */
  img {
    @apply max-w-full h-auto;
  }
}

@layer components {
  .btn {
    @apply px-4 py-2 sm:px-6 sm:py-3 rounded-lg font-semibold transition-all duration-200;
  }

  .btn-primary {
    @apply bg-primary text-white hover:opacity-90;
  }

  .btn-secondary {
    @apply bg-secondary text-white hover:opacity-90;
  }

  .container-custom {
    @apply max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full;
  }

  /* Mobile-optimized section spacing */
  section {
    @apply overflow-x-hidden;
  }
}

@layer utilities {
  /* Animation Delays */
  .animation-delay-200 {
    animation-delay: 200ms;
  }

  .animation-delay-400 {
    animation-delay: 400ms;
  }

  .animation-delay-600 {
    animation-delay: 600ms;
  }

  .delay-1000 {
    animation-delay: 1000ms;
  }

  /* Fade in animations */
  @keyframes fade-in-up {
    from {
      opacity: 0;
      transform: translateY(20px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  .animate-fade-in-up {
    animation: fade-in-up 0.6s ease-out forwards;
  }

  @keyframes slow-zoom {
    0%, 100% {
      transform: scale(1);
    }
    50% {
      transform: scale(1.05);
    }
  }

  .animate-slow-zoom {
    animation: slow-zoom 20s ease-in-out infinite;
  }
}

/* Mobile-specific optimizations */
@media (max-width: 640px) {
  h1 {
    @apply text-3xl;
  }

  h2 {
    @apply text-2xl;
  }

  h3 {
    @apply text-xl;
  }

  /* Reduce padding on mobile */
  .py-24 {
    @apply py-12;
  }

  .py-20 {
    @apply py-10;
  }

  /* Ensure content doesn't hide under fixed navbar */
  body {
    padding-top: 0;
  }
}
"""

    def generate_supabase_client(self, config: Dict) -> str:
        """Generate Supabase client configuration"""
        return f"""import {{ createClient }} from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

// Helper functions
export const supabaseAuth = {{
  signUp: async (email, password) => {{
    return await supabase.auth.signUp({{ email, password }})
  }},

  signIn: async (email, password) => {{
    return await supabase.auth.signInWithPassword({{ email, password }})
  }},

  signOut: async () => {{
    return await supabase.auth.signOut()
  }},

  getUser: async () => {{
    return await supabase.auth.getUser()
  }}
}}

export const supabaseDB = {{
  // Generic query helper
  from: (table) => supabase.from(table),

  // Insert data
  insert: async (table, data) => {{
    return await supabase.from(table).insert(data)
  }},

  // Update data
  update: async (table, id, data) => {{
    return await supabase.from(table).update(data).eq('id', id)
  }},

  // Delete data
  delete: async (table, id) => {{
    return await supabase.from(table).delete().eq('id', id)
  }},

  // Select all
  selectAll: async (table) => {{
    return await supabase.from(table).select('*')
  }}
}}

export default supabase
"""

    def generate_helpers(self) -> str:
        """Generate utility helpers"""
        return """/**
 * Utility helper functions
 */

// Format date
export const formatDate = (date) => {
  return new Date(date).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

// Format currency
export const formatCurrency = (amount, currency = 'USD') => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency
  }).format(amount)
}

// Truncate text
export const truncate = (text, length = 100) => {
  if (text.length <= length) return text
  return text.substring(0, length) + '...'
}

// Debounce function
export const debounce = (func, wait) => {
  let timeout
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout)
      func(...args)
    }
    clearTimeout(timeout)
    timeout = setTimeout(later, wait)
  }
}

// Generate random ID
export const generateId = () => {
  return Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15)
}
"""

    def generate_env_example(self, features: List[str]) -> str:
        """Generate .env.example"""
        env_lines = ["# Environment Variables"]

        if any(f in features for f in ["auth", "database", "storage"]):
            env_lines.extend([
                "",
                "# Supabase Configuration",
                "VITE_SUPABASE_URL=your_supabase_project_url",
                "VITE_SUPABASE_ANON_KEY=your_supabase_anon_key"
            ])

        return "\n".join(env_lines)

    def generate_home_page(self, components: List[Dict]) -> str:
        """Generate Home page component using generated components"""
        # Import all available components
        imports = []
        component_renders = []

        for comp in components:
            comp_name = comp.get("name", "")
            if comp_name:
                imports.append(f"import {comp_name} from '../components/{comp_name}'")
                component_renders.append(f"      <{comp_name} />")

        imports_str = "\n".join(imports)
        renders_str = "\n".join(component_renders)

        return f"""import React from 'react'
{imports_str}

function Home() {{
  return (
    <div className="min-h-screen">
{renders_str}
    </div>
  )
}}

export default Home
"""

    def generate_about_page(self) -> str:
        """Generate beautiful About page component"""
        return """import React from 'react'
import Navbar from '../components/Navbar'

function About() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-white to-gray-50">
      <Navbar />
      {/* Hero Section */}
      <div className="relative h-[400px] bg-gradient-to-br from-primary to-secondary flex items-center justify-center overflow-hidden">
        <div className="absolute inset-0 bg-black/20"></div>
        <div className="relative z-10 text-center text-white px-4">
          <h1 className="text-5xl md:text-7xl font-bold mb-4 animate-fade-in-up">
            About Us
          </h1>
          <p className="text-xl md:text-2xl opacity-90 max-w-2xl mx-auto">
            Discover our story, our mission, and what drives us every day
          </p>
        </div>
        {/* Animated gradient orbs */}
        <div className="absolute top-10 left-10 w-64 h-64 bg-white/10 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-10 right-10 w-96 h-96 bg-white/10 rounded-full blur-3xl animate-pulse delay-1000"></div>
      </div>

      <div className="container-custom py-20">
        {/* Our Story Section */}
        <div className="grid md:grid-cols-2 gap-12 items-center mb-20">
          <div>
            <div className="inline-block px-4 py-2 bg-primary/10 rounded-full mb-6">
              <span className="text-primary font-semibold">Our Story</span>
            </div>
            <h2 className="text-4xl font-bold mb-6 text-gray-900">
              Building Excellence Since Day One
            </h2>
            <p className="text-lg text-gray-600 mb-4 leading-relaxed">
              We started with a simple mission: to deliver exceptional service that exceeds expectations. Over the years, we've grown into a trusted name in our industry, serving hundreds of satisfied customers.
            </p>
            <p className="text-lg text-gray-600 leading-relaxed">
              Our commitment to quality, innovation, and customer satisfaction drives everything we do. We're not just a business - we're your partners in success.
            </p>
          </div>
          <div className="relative">
            <img
              src="https://picsum.photos/seed/aboutus/800/600"
              alt="Our Story"
              className="rounded-3xl shadow-2xl"
            />
            <div className="absolute -bottom-6 -right-6 w-64 h-64 bg-gradient-to-br from-primary to-secondary rounded-3xl opacity-20 -z-10"></div>
          </div>
        </div>

        {/* Our Values */}
        <div className="mb-20">
          <div className="text-center mb-12">
            <h2 className="text-4xl md:text-5xl font-bold mb-4 bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
              Our Values
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              The principles that guide everything we do
            </p>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="bg-white p-8 rounded-3xl shadow-lg hover:shadow-xl transition-all duration-300 border border-gray-100">
              <div className="text-5xl mb-4">🎯</div>
              <h3 className="text-2xl font-bold mb-3">Excellence</h3>
              <p className="text-gray-600">We strive for excellence in everything we do, never settling for anything less than the best.</p>
            </div>
            <div className="bg-white p-8 rounded-3xl shadow-lg hover:shadow-xl transition-all duration-300 border border-gray-100">
              <div className="text-5xl mb-4">💡</div>
              <h3 className="text-2xl font-bold mb-3">Innovation</h3>
              <p className="text-gray-600">We embrace innovation and continuously improve our services to serve you better.</p>
            </div>
            <div className="bg-white p-8 rounded-3xl shadow-lg hover:shadow-xl transition-all duration-300 border border-gray-100">
              <div className="text-5xl mb-4">❤️</div>
              <h3 className="text-2xl font-bold mb-3">Integrity</h3>
              <p className="text-gray-600">We operate with honesty, transparency, and respect in all our relationships.</p>
            </div>
          </div>
        </div>

        {/* Team Section */}
        <div className="text-center">
          <h2 className="text-4xl md:text-5xl font-bold mb-4 bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
            Meet Our Team
          </h2>
          <p className="text-xl text-gray-600 mb-12 max-w-2xl mx-auto">
            Talented professionals dedicated to your success
          </p>
          <div className="grid md:grid-cols-4 gap-8">
            {[
              { name: 'John Smith', role: 'Founder & CEO', image: 'https://i.pravatar.cc/150?img=3' },
              { name: 'Sarah Johnson', role: 'Head of Operations', image: 'https://i.pravatar.cc/150?img=5' },
              { name: 'Michael Chen', role: 'Lead Designer', image: 'https://i.pravatar.cc/150?img=7' },
              { name: 'Emily Davis', role: 'Customer Success', image: 'https://i.pravatar.cc/150?img=12' }
            ].map((member, index) => (
              <div key={index} className="group">
                <div className="relative mb-4 overflow-hidden rounded-2xl">
                  <img
                    src={member.image}
                    alt={member.name}
                    className="w-full aspect-square object-cover transform group-hover:scale-110 transition-transform duration-500"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                </div>
                <h3 className="text-xl font-bold text-gray-900">{member.name}</h3>
                <p className="text-gray-600">{member.role}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

export default About
"""


# Global template generator instance
react_template = ReactTemplateGenerator()
