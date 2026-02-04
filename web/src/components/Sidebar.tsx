import { Home, FileText, Search, Settings } from 'lucide-react'
import { NavLink } from 'react-router-dom'
import logo from '../assets/logo.svg'

export function Sidebar() {
  const linkClass = ({ isActive }: { isActive: boolean }) =>
    `w-full flex items-center gap-4 px-4 py-3 rounded-lg text-base font-medium transition-colors ${
      isActive
        ? 'bg-indigo-50 text-indigo-700'
        : 'text-gray-700 hover:bg-gray-100'
    }`

  return (
    <aside className="fixed left-0 top-0 w-72 h-screen bg-white border-r border-gray-200 flex flex-col z-10">
      <div className="p-8 pb-6 flex items-center gap-3">
        <img src={logo} alt="prism logo" className="h-20" />
        <span className="text-3xl font-medium -tracking-[0.06em]">
          prism
        </span>
      </div>

      <nav className="flex-1 px-4" aria-label="Navigation principale">
        <NavLink to="/" end className={linkClass}>
          <Home className="w-5 h-5" />
          Accueil
        </NavLink>

        <div className="mt-6 mb-6">
          <p className="px-4 text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
            Consulter
          </p>
          <div className="space-y-2">
            <NavLink to="/deliberations" className={linkClass}>
              <FileText className="w-5 h-5" />
              Délibérations
            </NavLink>
            <NavLink to="/recherche" className={linkClass}>
              <Search className="w-5 h-5" />
              Recherche avancée
            </NavLink>
          </div>
        </div>

        <div>
          <p className="px-3 text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
            Statistiques
          </p>
          <div className="space-y-2">
            <NavLink to="/stats" className={linkClass}>
              <Settings className="w-5 h-5" />
              Statistiques
            </NavLink>
          </div>
        </div>
      </nav>
    </aside>
  )
}
