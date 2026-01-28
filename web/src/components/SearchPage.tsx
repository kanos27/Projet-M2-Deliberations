import { useState, useEffect } from 'react'
import { SearchBar } from './SearchBar'
import { Filters } from './Filters'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from './ui/card'
import { FileText, Calendar, MapPin, ExternalLink, Loader2 } from 'lucide-react'
import { Button } from './ui/button'
import { documentsApi, type Document } from '../services/api'

export function SearchPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedTheme, setSelectedTheme] = useState('all')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [documents, setDocuments] = useState<Document[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchDocuments()
  }, [])

  const fetchDocuments = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await documentsApi.getDocuments()
      setDocuments(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Une erreur est survenue')
    } finally {
      setLoading(false)
    }
  }

  const filteredDocuments = documents.filter((doc) => {
    const matchesSearch = searchQuery === '' || 
      doc.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      doc.filename.toLowerCase().includes(searchQuery.toLowerCase()) ||
      doc.source.toLowerCase().includes(searchQuery.toLowerCase())
    
    return matchesSearch
  })

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('fr-FR', {
      day: 'numeric',
      month: 'long',
      year: 'numeric'
    })
  }

  return (
    <div className="py-8 container mx-auto px-4">
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
        <div className="lg:col-span-5">
          <SearchBar
            value={searchQuery}
            onChange={setSearchQuery}
            onSearch={() => {}}
          />
        </div>

        <aside className="lg:col-span-1">
          <div className="sticky top-8">
            <Filters
              selectedTheme={selectedTheme}
              onThemeChange={setSelectedTheme}
              startDate={startDate}
              onStartDateChange={setStartDate}
              endDate={endDate}
              onEndDateChange={setEndDate}
            />
          </div>
        </aside>
        
        <div className="lg:col-span-4">
          {loading ? (
            <div className="flex items-center justify-center py-16">
              <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
              <span className="ml-3 text-gray-600">Chargement des délibérations...</span>
            </div>
          ) : error ? (
            <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
              <p className="text-red-600">{error}</p>
              <Button 
                onClick={fetchDocuments} 
                className="mt-4"
              >
                Réessayer
              </Button>
            </div>
          ) : filteredDocuments.length === 0 ? (
            <div className="bg-white border border-gray-200 rounded-xl p-12 text-center">
              <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500 text-lg">
                {searchQuery ? 'Aucun document trouvé pour cette recherche' : 'Aucun document disponible'}
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              <p className="text-sm text-gray-600 mb-4">
                {filteredDocuments.length} document{filteredDocuments.length > 1 ? 's' : ''} trouvé{filteredDocuments.length > 1 ? 's' : ''}
              </p>
              
              <div className="grid gap-4">
                {filteredDocuments.map((doc) => (
                  <Card key={doc._id} className="hover:shadow-md transition-shadow duration-200 bg-white">
                    <CardHeader>
                      <div className="flex items-start justify-between">
                        <div className="flex items-center gap-3">
                          <div className="p-2 bg-blue-100 rounded-lg">
                            <FileText className="h-5 w-5 text-blue-600" />
                          </div>
                          <div>
                            <CardTitle className="text-lg text-gray-900">
                              {doc.title || doc.filename}
                            </CardTitle>
                            <CardDescription className="mt-1">
                              {doc.filename}
                            </CardDescription>
                          </div>
                        </div>
                      </div>
                    </CardHeader>
                    
                    <CardContent>
                      <div className="flex flex-wrap gap-4 text-sm text-gray-600">
                        <div className="flex items-center gap-1.5">
                          <MapPin className="h-4 w-4 text-gray-400" />
                          <span className="font-medium">{doc.source}</span>
                        </div>
                        <div className="flex items-center gap-1.5">
                          <Calendar className="h-4 w-4 text-gray-400" />
                          <span>{formatDate(doc.created_at)}</span>
                        </div>
                      </div>
                      
                      {doc.metadata && Object.keys(doc.metadata).length > 0 && (
                        <div className="mt-3 flex flex-wrap gap-2">
                          {Object.entries(doc.metadata).slice(0, 3).map(([key, value]) => (
                            <span 
                              key={key}
                              className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-700"
                            >
                              {key}: {String(value)}
                            </span>
                          ))}
                        </div>
                      )}
                    </CardContent>
                    
                    <CardFooter className="pt-0">
                      {doc.url && (
                        <a 
                          href={doc.url} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1.5 text-sm font-medium text-blue-600 hover:text-blue-800 transition-colors"
                        >
                          <ExternalLink className="h-4 w-4" />
                          Voir le document original
                        </a>
                      )}
                    </CardFooter>
                  </Card>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
