import { useState, useEffect } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import { Search, Menu, X, ChartNoAxesColumnIncreasing, Home } from 'lucide-react'
import logo from '../assets/logo.svg'

export function Navbar() {
  const [isScrolled, setIsScrolled] = useState(false)
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const location = useLocation()

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20)
    }
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  useEffect(() => {
    setIsMobileMenuOpen(false)
  }, [location])

  const isHomePage = location.pathname === '/'

  const navLinkClass = ({ isActive }: { isActive: boolean }) =>
    `px-4 py-2 rounded-full text-sm font-medium transition-all duration-200 ${
      isActive
        ? 'bg-indigo-600 text-white shadow-md'
        : isHomePage && !isScrolled
          ? 'text-white/90 hover:text-white hover:bg-white/10'
          : 'text-gray-700 hover:text-indigo-600 hover:bg-indigo-50'
    }`

  return (
    <>
      <nav
        className={`fixed top-4 left-1/2 -translate-x-1/2 z-50 transition-all duration-300 ${
          isScrolled || !isHomePage
            ? 'bg-white/95 backdrop-blur-md shadow-lg border border-gray-200/50'
            : 'bg-white/10 backdrop-blur-sm border border-white/20'
        } rounded-full px-3 py-2`}
      >
        <div className="flex items-center gap-2">
          <NavLink to="/" className="flex items-center gap-2 px-3 py-1">
            <img src={logo} alt="prism" className="h-8 w-8" />
            <span
              className={`text-xl font-semibold tracking-tight transition-colors ${
                isHomePage && !isScrolled ? 'text-white' : 'text-gray-900'
              }`}
              style={{ letterSpacing: '0.02em' }}
            >
              prism
            </span>
          </NavLink>

          <div className="hidden md:flex items-center gap-1">
            <NavLink to="/" end className={navLinkClass}>
              <span className="flex items-center gap-2">
                <Home className="w-4 h-4" />
                Accueil
              </span> 
            </NavLink>
            <NavLink to="/recherche" className={navLinkClass}>
              <span className="flex items-center gap-2">
                <Search className="w-4 h-4" />
                Explorer
              </span>
            </NavLink>
            <NavLink to="/stats" className={navLinkClass}>
              <span className="flex items-center gap-2">
                <ChartNoAxesColumnIncreasing className="w-4 h-4" />
                Statistiques
              </span>
            </NavLink>
          </div>

          <button
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className={`md:hidden p-2 rounded-full transition-colors ${
              isHomePage && !isScrolled
                ? 'text-white hover:bg-white/10'
                : 'text-gray-700 hover:bg-gray-100'
            }`}
            aria-label="Menu"
          >
            {isMobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </nav>

      {isMobileMenuOpen && (
        <div className="fixed inset-0 z-40 md:hidden">
          <div 
            className="absolute inset-0 bg-black/50 backdrop-blur-sm"
            onClick={() => setIsMobileMenuOpen(false)}
          />
          <div className="absolute top-20 left-4 right-4 bg-white rounded-2xl shadow-2xl p-4 space-y-2">
            <NavLink
              to="/"
              end
              className={({ isActive }) =>
                `block px-4 py-3 rounded-xl text-base font-medium transition-colors ${
                  isActive ? 'bg-indigo-50 text-indigo-700' : 'text-gray-700 hover:bg-gray-50'
                }`
              }
            ><Home className="w-5 h-5" />
              Accueil
            </NavLink>
            <NavLink
              to="/recherche"
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-3 rounded-xl text-base font-medium transition-colors ${
                  isActive ? 'bg-indigo-50 text-indigo-700' : 'text-gray-700 hover:bg-gray-50'
                }`
              }
            >
              <Search className="w-5 h-5" />
              Explorer les données
            </NavLink>
            <NavLink
              to="/stats"
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-3 rounded-xl text-base font-medium transition-colors ${
                  isActive ? 'bg-indigo-50 text-indigo-700' : 'text-gray-700 hover:bg-gray-50'
                }`
              }
            >
              <ChartNoAxesColumnIncreasing className="w-5 h-5" />
              Statistiques
            </NavLink>
          </div>
        </div>
      )}
    </>
  )
}
