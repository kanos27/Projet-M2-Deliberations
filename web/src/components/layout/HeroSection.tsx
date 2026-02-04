import { useState, useEffect, type ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, Loader2, Database, FileText } from 'lucide-react'
import { searchApi } from '../../services/api'

interface HeroSectionProps {
  children?: ReactNode
}

export function HeroSection({ children }: HeroSectionProps) {
  const navigate = useNavigate()
  const [searchQuery, setSearchQuery] = useState('')
  const [stats, setStats] = useState({
    totalDeliberations: 0,
    loading: true
  })

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await searchApi.search({ limit: 1 })
        setStats({
          totalDeliberations: response.total,
          loading: false
        })
      } catch (err) {
        console.error('Erreur lors du chargement des statistiques:', err)
        setStats({ totalDeliberations: 0, loading: false })
      }
    }
    fetchStats()
  }, [])

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    navigate('/recherche', { state: { query: searchQuery.trim() } })
  }

  return (
    <section className="relative min-h-[70vh] flex items-center justify-center overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-br from-indigo-900 via-indigo-800 to-purple-900" />
      
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-indigo-500/20 rounded-full blur-3xl animate-pulse" />
        <div className="absolute -bottom-40 -left-40 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl animate-pulse" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-indigo-400/10 rounded-full blur-3xl" />
      </div>

      <div 
        className="absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='1'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`
        }}
      />

      <div className="relative z-10 max-w-5xl mx-auto px-6 text-center">
        <div className="inline-flex items-center gap-2 px-4 py-2 bg-white/10 backdrop-blur-sm rounded-full text-white/80 text-sm mb-8 border border-white/20">
          <Database className="w-4 h-4" />
          <span>Portail Open Data des délibérations publiques</span>
        </div>

        <h1 className="text-3xl md:text-4xl lg:text-5xl font-bold text-white mb-6 leading-tight">
          <span className="block">Valorisez les données </span>
          <span className="bg-gradient-to-r from-indigo-200 via-purple-200 to-pink-200 bg-clip-text text-transparent">
            de vos délibérations publiques
          </span>
        </h1>

        <p className="text-lg md:text-xl text-indigo-100/80 mb-10 max-w-2xl mx-auto">
          De l'archive PDF à la donnée structurée. Profitez d'une recherche plein texte,
          d'une analyse détaillée des décisions publiques, et d'outils avancés pour explorer les actes
          pris par vos instances délibérantes.
        </p>

        <form onSubmit={handleSearch} className="max-w-2xl mx-auto mb-8">
          <div className="relative group">
            <div className="absolute -inset-1 bg-gradient-to-r from-indigo-400 to-purple-400 rounded-2xl blur-lg opacity-40 group-hover:opacity-60 transition-opacity" />
            <div className="relative flex items-center bg-white rounded-xl shadow-2xl overflow-hidden">
              <Search className="w-6 h-6 text-gray-400 ml-5" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Rechercher une délibération..."
                className="flex-1 px-4 py-5 text-lg text-gray-800 placeholder-gray-400 focus:outline-none"
              />
              <button
                type="submit"
                className="m-2 px-8 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-medium rounded-lg hover:from-indigo-700 hover:to-purple-700 transition-all shadow-lg hover:shadow-xl"
              >
                Rechercher
              </button>
            </div>
          </div>
        </form>

        <div className="flex items-center justify-center gap-8 text-white/70">
          <div className="flex items-center gap-2">
            <FileText className="w-5 h-5" />
            {stats.loading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <span className="font-semibold text-white">{stats.totalDeliberations.toLocaleString('fr-FR')}</span>
            )}
            <span>délibérations</span>
          </div>
        </div>

        {children}
      </div>

      <div className="absolute bottom-[-2px] left-0 right-0">
        <svg viewBox="0 0 1440 120" fill="none" xmlns="http://www.w3.org/2000/svg" className="w-full" preserveAspectRatio="none">
          <path 
            d="M0 120L60 110C120 100 240 80 360 70C480 60 600 60 720 65C840 70 960 80 1080 85C1200 90 1320 90 1380 90L1440 90V120H1380C1320 120 1200 120 1080 120C960 120 840 120 720 120C600 120 480 120 360 120C240 120 120 120 60 120H0Z" 
            fill="#f9fafb"
          />
        </svg>
      </div>
    </section>
  )
}
