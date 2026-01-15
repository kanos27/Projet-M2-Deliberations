import { useState } from 'react'
import { Header } from './components/Header'
import { LandingPage } from './components/LandingPage'
import { SearchPage } from './components/SearchPage'

type Page = 'accueil' | 'recherche'

function App() {
  const [currentPage, setCurrentPage] = useState<Page>('accueil')

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <a 
        href="#main-content" 
        className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-[100] focus:bg-white focus:px-4 focus:py-2 focus:text-blue-900 focus:rounded focus:shadow-lg"
      >
        Aller au contenu principal
      </a>
      
      <Header 
        currentPage={currentPage} 
        onNavigate={setCurrentPage} 
      />
      
      <main 
        id="main-content"
        role="main"
        className="flex-1 w-full"
      >
        <div className="w-full">
          {currentPage === 'accueil' ? (
            <LandingPage onNavigateToSearch={() => setCurrentPage('recherche')} />
          ) : (
            <SearchPage />
          )}
        </div>
      </main>

      <footer className="bg-gray-900 text-white py-8" role="contentinfo">
        <div className="container mx-auto px-4 text-center">
          <p className="text-sm">
            2026 - 
          </p>
          <p className="text-xs text-gray-400 mt-2">
            Tous les documents sont publics et consultables gratuitement
          </p>
        </div>
      </footer>
    </div>
  )
}

export default App
