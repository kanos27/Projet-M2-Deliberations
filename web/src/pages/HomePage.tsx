import { useNavigate } from 'react-router-dom'
import { FileText, Calendar, Users, ArrowRight, TrendingUp, Search } from 'lucide-react'
import { HeroSection, Footer } from '../components/layout'

export function HomePage() {
  const navigate = useNavigate()

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
      icon: TrendingUp,
      label: 'Délibérations adoptées',
      description: 'Voir les actes adoptés',
      color: 'from-emerald-500 to-teal-600',
      bgColor: 'bg-emerald-50',
      iconColor: 'text-emerald-600',
      href: '/recherche?vote_resultat=ADOPTÉE'
    },
    {
      icon: Users,
      label: 'Par commission',
      description: 'Filtrer par organe délibérant',
      color: 'from-purple-500 to-violet-600',
      bgColor: 'bg-purple-50',
      iconColor: 'text-purple-600',
      href: '/recherche'
    },
    {
      icon: Calendar,
      label: 'Recherche avancée',
      description: 'Tous les filtres disponibles',
      color: 'from-orange-500 to-amber-600',
      bgColor: 'bg-orange-50',
      iconColor: 'text-orange-600',
      href: '/recherche'
    }
  ]

  return (
    <div className="min-h-screen">
      <HeroSection />

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
                Dans le cadre de l'ouverture des données publiques, notre outil met à disposition
                l'ensemble des délibérations d'une collectivité sous un format structuré et facilement exploitable.
                Cela permet aux citoyens, chercheurs et développeurs de consulter les décisions publiques
                de manière transparente et efficace.
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
            Explorez les données ouvertes dès aujourd'hui
          </h2>
          <p className="text-indigo-100 mb-8">
            Commencez votre recherche dès maintenant et accédez à l'ensemble des délibérations publiques lié à votre collectivité. 
          </p>
          <button
            onClick={() => navigate('/recherche')}
            className="inline-flex items-center gap-2 px-8 py-4 bg-white text-indigo-600 font-semibold rounded-xl hover:bg-indigo-50 transition-colors shadow-lg"
          >
            <Search className="w-5 h-5" />
            Accéder au données
            <ArrowRight className="w-5 h-5" />
          </button>
        </div>
      </section>

      <Footer />
    </div>
  )
}
