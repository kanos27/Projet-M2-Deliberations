import { Link } from 'react-router-dom'

export function Footer() {
  return (
    <footer className="py-12 px-6 bg-gray-900">
      <div className="max-w-6xl mx-auto">
        <div className="flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-3">
            <span className="text-xl font-semibold text-white" style={{ letterSpacing: '0.02em' }}>
              prism
            </span>
            <span className="text-gray-500">|</span>
            <span className="text-gray-400 text-sm">Outil dédié aux données ouvertes des délibérations publiques</span>
          </div>
          
          <div className="flex items-center gap-6 text-sm text-gray-400">
            <Link to="/mentions-legales" className="hover:text-white transition-colors">Mentions légales</Link>
            <Link to="/contact" className="hover:text-white transition-colors">Contact</Link>
            <a href="http://localhost:8000/docs" target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors">API</a>
          </div>
        </div>
        
        <div className="mt-8 pt-8 border-t border-gray-800 text-center text-sm text-gray-500">
          © {new Date().getFullYear()} prism - Données ouvertes en accès libre
        </div>
      </div>
    </footer>
  )
}
