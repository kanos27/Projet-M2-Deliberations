import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, FileText, Calendar, Users, MapPin, ArrowRight, Loader2, Database, TrendingUp } from 'lucide-react'
import { searchApi } from '../services/api'

export function HomePage() {
  const navigate = useNavigate()
  const [searchQuery, setSearchQuery] = useState('')
  const [stats, setStats] = useState({
    totalDeliberations: 0,
    loading: true
  })

  useEffect(() => {
    fetchStats()
  }, [])

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

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    navigate(`/recherche?q=${encodeURIComponent(searchQuery)}`)
  }

  const categories = [
    {
      icon: FileText,
      label: 'Toutes les délibérations',
      description: "Parcourir l'ensemble des actes",
      color: 'from-blue-500 to-indigo-600',
      bgColor: 'bg-blue-50',
      iconColor: 'text-blue-600',
      href: '/recherche'
    },
    {
      icon: Calendar,
      label: 'Par date',
      description: 'Filtrer par période',
      color: 'from-emerald-500 to-teal-600',
      bgColor: 'bg-emerald-50',
      iconColor: 'text-emerald-600',
      href: '/recherche'
    },
    {
      icon: Users,
      label: 'Par commission',
      description: 'Rechercher par organe',
      color: 'from-purple-500 to-violet-600',
      bgColor: 'bg-purple-50',
      iconColor: 'text-purple-600',
      href: '/recherche'
    },
    {
      icon: MapPin,
      label: 'Par collectivité',
      description: 'Explorer par territoire',
      color: 'from-orange-500 to-red-600',
      bgColor: 'bg-orange-50',
      iconColor: 'text-orange-600',
      href: '/recherche'
    }
  ]

  return (
    <div className="min-h-screen">
      {/* Hero Section with gradient background */}
      <section className="relative min-h-[70vh] flex items-center justify-center overflow-hidden">
        {/* Background gradient */}
        <div className="absolute inset-0 bg-gradient-to-br from-indigo-900 via-indigo-800 to-purple-900" />
        
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute -top-40 -right-40 w-80 h-80 bg-indigo-500/20 rounded-full blur-3xl animate-pulse" />
          <div className="absolute -bottom-40 -left-40 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl animate-pulse"/>
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-indigo-400/10 rounded-full blur-3xl" />
        </div>

        <div 
          className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='1'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`
          }}
        />

        <div className="relative z-10 max-w-5xl mx-auto px-6 text-center">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-white/10 backdrop-blur-sm rounded-full text-white/80 text-sm mb-8 border border-white/20">
            <Database className="w-4 h-4" />
            <span>Portail Open Data des délibérations</span>
          </div>

          {/* Main title */}
          <h1 className="text-4xl md:text-6xl lg:text-7xl font-bold text-white mb-6 leading-tight">
            <span className="block">Explorez les</span>
            <span className="bg-gradient-to-r from-indigo-200 via-purple-200 to-pink-200 bg-clip-text text-transparent">
              délibérations publiques
            </span>
          </h1>

          <p className="text-lg md:text-xl text-indigo-100/80 mb-10 max-w-2xl mx-auto">
            Accédez librement aux actes et décisions du Conseil régional. 
            Recherchez, filtrez et téléchargez en toute transparence.
          </p>

          {/* Search bar */}
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
                  Explorer
                </button>
              </div>
            </div>
          </form>

          {/* Stats */}
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
            <div className="w-px h-5 bg-white/30" />
            <div className="flex items-center gap-2">
              <TrendingUp className="w-5 h-5" />
              <span>Mise à jour quotidienne</span>
            </div>
          </div>
        </div>

        {/* Bottom wave */}
        <div className="absolute bottom-0 left-0 right-0">
          <svg viewBox="0 0 1440 120" fill="none" xmlns="http://www.w3.org/2000/svg" className="w-full">
            <path 
              d="M0 120L60 110C120 100 240 80 360 70C480 60 600 60 720 65C840 70 960 80 1080 85C1200 90 1320 90 1380 90L1440 90V120H1380C1320 120 1200 120 1080 120C960 120 840 120 720 120C600 120 480 120 360 120C240 120 120 120 60 120H0Z" 
              fill="#f9fafb"
            />
          </svg>
        </div>
      </section>

      {/* Categories Section */}
      <section className="py-20 px-6 bg-gray-50">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">Explorer par catégorie</h2>
            <p className="text-gray-600 max-w-2xl mx-auto">
              Naviguez facilement dans l'ensemble des données ouvertes grâce à nos différents modes d'exploration
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {categories.map((category, index) => (
              <button
                key={index}
                onClick={() => navigate(category.href)}
                className="group relative bg-white rounded-2xl p-6 shadow-sm hover:shadow-xl transition-all duration-300 border border-gray-100 hover:border-indigo-200 text-left overflow-hidden"
              >
                <div className={`absolute inset-0 bg-gradient-to-br ${category.color} opacity-0 group-hover:opacity-5 transition-opacity`} />
                
                <div className={`inline-flex p-3 rounded-xl ${category.bgColor} mb-4 group-hover:scale-110 transition-transform`}>
                  <category.icon className={`w-6 h-6 ${category.iconColor}`} />
                </div>
                
                <h3 className="font-semibold text-gray-900 mb-2 group-hover:text-indigo-600 transition-colors">
                  {category.label}
                </h3>
                <p className="text-sm text-gray-500 mb-4">{category.description}</p>
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 px-6 bg-white">
        <div className="max-w-6xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
            <div>
              <span className="inline-block px-3 py-1 bg-indigo-100 text-indigo-700 text-sm font-medium rounded-full mb-4">
                Transparence
              </span>
              <h2 className="text-3xl font-bold text-gray-900 mb-6">
                Accès libre aux données publiques
              </h2>
              <p className="text-gray-600 mb-8 leading-relaxed">
                Dans le cadre de l'ouverture des données publiques, nous mettons à disposition 
                l'ensemble des délibérations du Conseil régional. Chaque citoyen peut librement 
                consulter, télécharger et réutiliser ces informations.
              </p>
              
              <ul className="space-y-4">
                {[
                  'Recherche en texte intégral',
                  'Filtres avancés (date, commission, vote)',
                  'Téléchargement des documents PDF',
                  'API ouverte pour les développeurs'
                ].map((feature, i) => (
                  <li key={i} className="flex items-center gap-3 text-gray-700">
                    <div className="w-5 h-5 rounded-full bg-green-100 flex items-center justify-center">
                      <svg className="w-3 h-3 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    </div>
                    {feature}
                  </li>
                ))}
              </ul>
            </div>

            <div className="relative">
              <div className="absolute -inset-4 bg-gradient-to-r from-indigo-100 to-purple-100 rounded-3xl blur-2xl opacity-60" />
              <div className="relative bg-white rounded-2xl shadow-xl p-8 border border-gray-100">
                <div className="flex items-center gap-4 mb-6">
                  <div className="w-12 h-12 bg-indigo-100 rounded-xl flex items-center justify-center">
                    <FileText className="w-6 h-6 text-indigo-600" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-gray-900">Exemple de délibération</h4>
                    <p className="text-sm text-gray-500">Document type disponible</p>
                  </div>
                </div>
                
                <div className="space-y-3">
                  <div className="h-3 bg-gray-100 rounded-full w-full" />
                  <div className="h-3 bg-gray-100 rounded-full w-5/6" />
                  <div className="h-3 bg-gray-100 rounded-full w-4/6" />
                  <div className="h-3 bg-gray-100 rounded-full w-full" />
                  <div className="h-3 bg-gray-100 rounded-full w-3/4" />
                </div>

                <div className="mt-6 pt-6 border-t border-gray-100 flex items-center justify-between">
                  <div className="flex items-center gap-2 text-sm text-gray-500">
                    <Calendar className="w-4 h-4" />
                    <span>15 janvier 2026</span>
                  </div>
                  <span className="px-3 py-1 bg-green-100 text-green-700 text-xs font-medium rounded-full">
                    Adopté
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="py-16 px-6 bg-gradient-to-r from-indigo-600 to-purple-600">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-2xl md:text-3xl font-bold text-white mb-4">
            Prêt à explorer les données ?
          </h2>
          <p className="text-indigo-100 mb-8">
            Commencez votre recherche dès maintenant et accédez à l'ensemble des délibérations publiques.
          </p>
          <button
            onClick={() => navigate('/recherche')}
            className="inline-flex items-center gap-2 px-8 py-4 bg-white text-indigo-600 font-semibold rounded-xl hover:bg-indigo-50 transition-colors shadow-lg"
          >
            <Search className="w-5 h-5" />
            Accéder au catalogue
            <ArrowRight className="w-5 h-5" />
          </button>
        </div>
      </section>

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
              <a href="#" className="hover:text-white transition-colors">Mentions légales</a>
              <a href="#" className="hover:text-white transition-colors">Contact</a>
              <a href="#" className="hover:text-white transition-colors">API</a>
            </div>
          </div>
          
          <div className="mt-8 pt-8 border-t border-gray-800 text-center text-sm text-gray-500">
            © 2026 prism - Données ouvertes en accès libre
          </div>
        </div>
      </footer>
    </div>
  )
}
