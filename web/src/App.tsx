import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Navbar } from './components/Navbar'
import { RecherchePage } from './pages/RecherchePage'
import { HomePage } from './pages/HomePage'
import { AdminPage } from './pages/AdminPage'

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50">
        <a 
          href="#main-content" 
          className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-[100] focus:bg-white focus:px-4 focus:py-2 focus:text-blue-900 focus:rounded focus:shadow-lg"
        >
          Aller au contenu principal
        </a>
        
        <Navbar />
        
        <main 
          id="main-content"
          role="main"
          className="min-h-screen"
        >
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/recherche" element={<RecherchePage />} />
            <Route path="/admin" element={<AdminPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}

export default App
