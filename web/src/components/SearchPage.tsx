import { useState, useEffect } from 'react'
import { SearchBar } from './SearchBar'
import { Filters } from './Filters'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from './ui/card'
import { FileText, Calendar, MapPin, ExternalLink, Loader2, Users, Vote, Users2, Gavel } from 'lucide-react'
import { Button } from './ui/button'
import { searchApi, type SearchResult } from '../services/api'

export function SearchPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [voteResultat, setVoteResultat] = useState('all')
  const [commission, setCommission] = useState('all')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [person, setPerson] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [totalResults, setTotalResults] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    performSearch()
  }, [voteResultat, commission, startDate, endDate, person])

  const performSearch = async () => {
    setLoading(true)
    setError(null)
    
    try {
      const params = {
        q: searchQuery || undefined,
        vote_resultat: voteResultat !== 'all' ? voteResultat : undefined,
        commission: commission !== 'all' ? commission : undefined,
        date_from: startDate || undefined,
        date_to: endDate || undefined,
        person: person || undefined,
        limit: 50
      }
      
      const response = await searchApi.search(params)
      setResults(response.results)
      setTotalResults(response.total)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Une erreur est survenue')
      setResults([])
      setTotalResults(0)
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = () => {
    performSearch()
  }

  const handleReset = () => {
    setVoteResultat('all')
    setCommission('all')
    setStartDate('')
    setEndDate('')
    setPerson('')
    setSearchQuery('')
  }

  const formatDate = (dateString: string | undefined) => {
    if (!dateString) return 'Date non disponible'
    try {
      return new Date(dateString).toLocaleDateString('fr-FR', {
        day: 'numeric',
        month: 'long',
        year: 'numeric'
      })
    } catch {
      return dateString
    }
  }

  const getVoteResultColor = (voteResult: string | undefined) => {
    if (!voteResult) return 'bg-gray-100 text-gray-700'
    
    const normalized = voteResult.toLowerCase()
    if (normalized.includes('adopt')) return 'bg-green-100 text-green-700'
    if (normalized.includes('rejet')) return 'bg-red-100 text-red-700'
    if (normalized.includes('ajourn')) return 'bg-yellow-100 text-yellow-700'
    if (normalized.includes('retir')) return 'bg-orange-100 text-orange-700'
    return 'bg-gray-100 text-gray-700'
  }

  return (
    <div className="py-8 container mx-auto px-4">
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
        <div className="lg:col-span-5">
          <SearchBar
            value={searchQuery}
            onChange={setSearchQuery}
            onSearch={handleSearch}
          />
        </div>

        <aside className="lg:col-span-1">
          <div className="sticky top-8">
            <Filters
              voteResultat={voteResultat}
              onVoteResultatChange={setVoteResultat}
              commission={commission}
              onCommissionChange={setCommission}
              startDate={startDate}
              onStartDateChange={setStartDate}
              endDate={endDate}
              onEndDateChange={setEndDate}
              person={person}
              onPersonChange={setPerson}
              onReset={handleReset}
            />
          </div>
        </aside>
        
        <div className="lg:col-span-4">
          {loading ? (
            <div className="flex items-center justify-center py-16">
              <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
              <span className="ml-3 text-gray-600">Recherche en cours...</span>
            </div>
          ) : error ? (
            <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
              <p className="text-red-600">{error}</p>
              <Button 
                onClick={performSearch} 
                className="mt-4"
              >
                Réessayer
              </Button>
            </div>
          ) : results.length === 0 ? (
            <div className="bg-white border border-gray-200 rounded-xl p-12 text-center">
              <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500 text-lg">
                Aucune délibération trouvée
              </p>
              <p className="text-gray-400 text-sm mt-2">
                Essayez de modifier vos critères de recherche
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <p className="text-sm text-gray-600">
                  <span className="font-semibold">{totalResults}</span> délibération{totalResults > 1 ? 's' : ''} trouvée{totalResults > 1 ? 's' : ''}
                </p>
              </div>
              
              <div className="grid gap-4">
                {results.map((result) => (
                  <Card key={result._id} className="hover:shadow-lg transition-all duration-200 bg-white border-l-4 border-l-blue-500">
                    <CardHeader className="pb-3">
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-3 mb-2">
                            <div className="p-2 bg-blue-100 rounded-lg flex-shrink-0">
                              <FileText className="h-5 w-5 text-blue-600" />
                            </div>
                            <div className="flex-1 min-w-0">
                              <CardTitle className="text-lg text-gray-900 leading-tight line-clamp-2">
                                {result.delib_objet || result.filename}
                              </CardTitle>
                              <CardDescription className="mt-1 text-xs flex items-center gap-2 flex-wrap">
                                {result.delib_id && <span>ID: {result.delib_id}</span>}
                                {result.delib_numero && <span>• N°{result.delib_numero}</span>}
                              </CardDescription>
                            </div>
                          </div>
                        </div>
                        {result.vote_resultat && (
                          <span className={`px-3 py-1.5 rounded-full text-xs font-semibold flex items-center gap-1.5 flex-shrink-0 ${getVoteResultColor(result.vote_resultat)}`}>
                            <Vote className="h-3 w-3" />
                            {result.vote_resultat}
                          </span>
                        )}
                      </div>
                    </CardHeader>
                    
                    <CardContent className="pt-0">
                      {/* Métadonnées principales */}
                      <div className="flex flex-wrap gap-x-4 gap-y-2 text-sm text-gray-600 mb-4">
                        {result.collectivite && (
                          <div className="flex items-center gap-1.5">
                            <MapPin className="h-4 w-4 text-blue-500" />
                            <span className="font-medium">{result.collectivite}</span>
                          </div>
                        )}
                        <div className="flex items-center gap-1.5">
                          <Calendar className="h-4 w-4 text-red-500" />
                          <span>{formatDate(result.date)}</span>
                        </div>
                        {(result.membres_presents_count !== undefined) && (
                          <div className="flex items-center gap-1.5">
                            <Users className="h-4 w-4 text-cyan-500" />
                            <span>
                              {result.membres_presents_count} présent{(result.membres_presents_count || 0) > 1 ? 's' : ''}
                              {result.membres_absents_count ? `, ${result.membres_absents_count} absent${(result.membres_absents_count || 0) > 1 ? 's' : ''}` : ''}
                            </span>
                          </div>
                        )}
                      </div>
                      
                      {/* Commission et Rapporteur */}
                      {(result.commission || result.rapporteur) && (
                        <div className="flex flex-wrap gap-x-4 gap-y-2 text-sm text-gray-600 mb-4 pb-4 border-b border-gray-100">
                          {result.commission && (
                            <div className="flex items-center gap-1.5">
                              <Users2 className="h-4 w-4 text-purple-500" />
                              <span>{result.commission}</span>
                              {result.commission_avis && (
                                <span className="text-xs text-gray-400">({result.commission_avis})</span>
                              )}
                            </div>
                          )}
                          {result.rapporteur && (
                            <div className="flex items-center gap-1.5">
                              <Gavel className="h-4 w-4 text-orange-500" />
                              <span>{result.rapporteur}</span>
                            </div>
                          )}
                        </div>
                      )}

                      {/* Détails du vote */}
                      {(result.vote_pour !== null && result.vote_pour !== undefined) && (
                        <div className="flex flex-wrap gap-3 text-xs mb-4">
                          <span className="inline-flex items-center px-2 py-1 rounded bg-green-50 text-green-700">
                            ✓ Pour: {result.vote_pour}
                          </span>
                          {result.vote_contre !== null && result.vote_contre !== undefined && (
                            <span className="inline-flex items-center px-2 py-1 rounded bg-red-50 text-red-700">
                              ✗ Contre: {result.vote_contre}
                            </span>
                          )}
                          {result.vote_abstentions !== null && result.vote_abstentions !== undefined && (
                            <span className="inline-flex items-center px-2 py-1 rounded bg-gray-100 text-gray-700">
                              ○ Abstentions: {result.vote_abstentions}
                            </span>
                          )}
                          {result.membres_en_exercice && (
                            <span className="inline-flex items-center px-2 py-1 rounded bg-blue-50 text-blue-700">
                              Effectif: {result.membres_en_exercice}
                            </span>
                          )}
                        </div>
                      )}
                    </CardContent>
                    
                    <CardFooter className="pt-0">
                      {result.url && (
                        <a 
                          href={result.url} 
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
