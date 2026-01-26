import { Button } from './ui/button'

interface HeaderProps {
  currentPage: 'accueil' | 'recherche'
  onNavigate: (page: 'accueil' | 'recherche') => void
}

export function Header({ currentPage, onNavigate }: HeaderProps) {
  const scrollToAbout = () => {
    const aboutSection = document.getElementById('about')
    if (aboutSection) {
      aboutSection.scrollIntoView({ behavior: 'smooth' })
    }
  }

  return (
    <header 
      className="bg-white shadow-md border-b border-gray-200"
      role="banner"
    >
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <button 
            onClick={() => onNavigate('accueil')}
            aria-label="Délibérations - Ville de La Rochelle - Retour à l'accueil"
            className="flex items-center gap-3 hover:opacity-80 transition-opacity focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-blue-500 rounded-lg"
          >
            <div 
              className="w-10 h-10 rounded-full flex items-center justify-center bg-blue-600"
              aria-hidden="true"
            >
              <span className="text-lg font-bold text-white">LR</span>
            </div>
            <div className="text-left">
              <span className="text-xl font-bold block text-gray-900">
                Délibérations
              </span>
              <span className="text-xs block text-gray-600">
                Ville de La Rochelle
              </span>
            </div>
          </button>
          
          <div className="flex items-center gap-8">
            <nav className="hidden md:flex items-center gap-8" aria-label="Navigation principale">
              <button
                onClick={() => onNavigate('accueil')}
                aria-current={currentPage === 'accueil' ? 'page' : undefined}
                className={`text-sm font-medium transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 rounded px-2 py-1 hover:text-blue-600 ${
                  currentPage === 'accueil' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-700'
                }`}
              >
                Accueil
              </button>
              <button
                onClick={() => onNavigate('recherche')}
                aria-current={currentPage === 'recherche' ? 'page' : undefined}
                className={`text-sm font-medium transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 rounded px-2 py-1 hover:text-blue-600 ${
                  currentPage === 'recherche' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-700'
                }`}
              >
                Recherche
              </button>
              <button
                onClick={scrollToAbout}
                className="text-sm font-medium transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 rounded px-2 py-1 text-gray-700 hover:text-blue-600"
              >
                À propos
              </button>
            </nav>
            
            <Button 
              aria-label="Accès administration"
              className="bg-blue-600 focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-blue-500 px-4"
            >
              Admin
            </Button>
          </div>
        </div>
      </div>
    </header>
  )
}
