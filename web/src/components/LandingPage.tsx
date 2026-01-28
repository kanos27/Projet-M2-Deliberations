import { Search, FileText, Calendar, Users } from 'lucide-react'
import { Button } from './ui/button'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'

interface LandingPageProps {
  onNavigateToSearch: () => void
}

const features = [
  { icon: FileText, title: 'Délibérations complètes', desc: 'Accédez à l\'intégralité des délibérations adoptées.' },
  { icon: Search, title: 'Recherche intelligente', desc: 'Trouvez rapidement par mots-clés, date ou tout autre critère.' },
  { icon: Calendar, title: 'Archives accessibles', desc: 'Consultez l\'historique des décisions prises par le Conseil.' },
]

export function LandingPage({ onNavigateToSearch }: LandingPageProps) {
  return (
    <div className="overflow-x-hidden">
      {/* Hero */}
      <section 
        aria-labelledby="hero-title"
        className="relative min-h-[60vh] flex items-center justify-center bg-gradient-to-br from-blue-900 via-blue-800 to-blue-600"
      >
        <div className="absolute inset-0 opacity-10" aria-hidden="true">
          <div className="absolute top-20 left-10 w-72 h-72 bg-white rounded-full blur-3xl" />
          <div className="absolute bottom-20 right-10 w-96 h-96 bg-white rounded-full blur-3xl" />
        </div>

        <div className="relative z-10 container mx-auto px-4 text-center animate-fade-in">
          <p className="inline-flex items-center gap-2 bg-white/10 backdrop-blur-sm border border-white/20 rounded-full px-4 py-2 mb-8">
            <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse" aria-hidden="true" />
            <span className="text-white text-sm">Accès public aux délibérations</span>
          </p>
          
          <h1 id="hero-title" className="text-4xl md:text-6xl font-bold text-white mb-6">
            Délibérations du Conseil Municipal
          </h1>
          
          <p className="text-xl text-white max-w-2xl mx-auto mb-10">
            Consultez et explorez les délibérations adoptées par le Conseil Municipal de La Rochelle
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button 
              size="lg" 
              onClick={onNavigateToSearch} 
              className="bg-white text-blue-900 px-8"
            >
              <Search className="mr-2 h-5 w-5" aria-hidden="true" />
              Rechercher une délibération
            </Button>
            <Button 
              onClick={() => document.getElementById('about')?.scrollIntoView({ behavior: 'smooth' })} 
              className="border-2 border-white text-white px-8"
              size='lg'
            >
              En savoir plus
            </Button>
          </div>
        </div>
      </section>
      
      {/* Features */}
      <section aria-labelledby="features-title" className="py-16 bg-gray-50">
        <div className="container mx-auto px-4">
          <h2 id="features-title" className="text-2xl font-bold text-gray-900 mb-10">
            Accédez aux décisions de votre ville
          </h2>
          <ul className="grid md:grid-cols-3 gap-8">
            {features.map((f) => (
              <li key={f.title}>
                <Card className="border-0 h-full">
                  <CardHeader>
                    <div className="w-12 h-12 bg-blue-100 rounded-sm flex items-center justify-center mb-3" aria-hidden="true">
                      <f.icon className="h-6 w-6 text-blue-600" />
                    </div>
                    <CardTitle className="text-lg">{f.title}</CardTitle>
                  </CardHeader>
                  <CardContent className="text-gray-600 text-md">{f.desc}</CardContent>
                </Card>
              </li>
            ))}
          </ul>
        </div>
      </section>

      {/* About */}
      <section id="about" aria-labelledby="about-title" className="py-20 bg-white">
        <div className="container mx-auto px-4">
          <div className="flex items-center gap-3 mb-8">
            <div className="w-12 h-12 bg-blue-600 rounded-sm flex items-center justify-center" aria-hidden="true">
              <Users className="h-6 w-6 text-white" />
            </div>
            <h2 id="about-title" className="text-3xl font-bold text-gray-900">À propos</h2>
          </div>
          
          <div className="space-y-5 text-gray-700 text-lg leading-relaxed mb-10">
            {/* Description concernant le a propos */}
          </div>
          
          <div className="border-t border-gray-200 pt-6">
            <address className="not-italic">
              {/* Description concernant le contact */}
            </address>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section aria-labelledby="cta-title" className="py-12 bg-gradient-to-r from-blue-900 to-blue-700 text-center">
        <div className="container mx-auto px-4">
          <h2 id="cta-title" className="text-2xl font-bold text-white mb-6">Trouvez la délibération que vous cherchez</h2>
          <Button 
            size="lg" 
            onClick={onNavigateToSearch} 
            className="bg-white text-blue-900 hover:bg-blue-50 px-8 focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-black"
          >
            <Search className="mr-2 h-5 w-5" aria-hidden="true" />
            Lancer une recherche
          </Button>
        </div>
      </section>
    </div>
  )
}
