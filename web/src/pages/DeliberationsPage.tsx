import { useState, useEffect } from 'react'
import { Pagination } from '../components/Pagination'
import { FileText, Calendar, ChevronRight, LayoutGrid, LayoutList, ExternalLink } from 'lucide-react'
import { searchApi, type SearchResult } from '../services/api'

const RESULTS_PER_PAGE = 25

export function DeliberationsPage() {
  const [results, setResults] = useState<SearchResult[]>([])
  const [totalResults, setTotalResults] = useState(0)
  const [currentPage, setCurrentPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [viewMode, setViewMode] = useState<'table' | 'cards'>('table')

  const totalPages = Math.ceil(totalResults / RESULTS_PER_PAGE)

  useEffect(() => {
    fetchDeliberations()
  }, [currentPage])

  const fetchDeliberations = async () => {
    setLoading(true)
    try {
      const response = await searchApi.search({
        limit: RESULTS_PER_PAGE,
        skip: (currentPage - 1) * RESULTS_PER_PAGE
      })
      setResults(response.results)
      setTotalResults(response.total)
    } catch (err) {
      console.error('Erreur lors du chargement des délibérations:', err)
    } finally {
      setLoading(false)
    }
  }

  const formatDate = (dateString: string | undefined) => {
    if (!dateString) return '-'
    try {
      return new Date(dateString).toLocaleDateString('fr-FR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
      })
    } catch {
      return dateString
    }
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <div className="flex items-center justify-between mb-2">
          <h1 className="text-2xl font-bold text-gray-900">Délibérations</h1>
          <div className="flex items-center gap-2">
            <div className="flex items-center bg-gray-100 rounded-lg p-1">
              <button
                onClick={() => setViewMode('table')}
                className={`p-2 rounded-md transition-colors ${
                  viewMode === 'table' ? 'bg-white shadow-sm text-indigo-600' : 'text-gray-500 hover:text-gray-700'
                }`}
                title="Vue tableau"
              >
                <LayoutList className="w-4 h-4" />
              </button>
              <button
                onClick={() => setViewMode('cards')}
                className={`p-2 rounded-md transition-colors ${
                  viewMode === 'cards' ? 'bg-white shadow-sm text-indigo-600' : 'text-gray-500 hover:text-gray-700'
                }`}
                title="Vue cartes"
              >
                <LayoutGrid className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
        <p className="text-gray-600">
          Consultez l'ensemble des {totalResults > 0 && <span className="font-semibold">{totalResults}</span>} délibérations du Conseil régional
        </p>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-indigo-600"></div>
        </div>
      ) : viewMode === 'table' ? (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200">
                  <th className="text-left px-6 py-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                    Objet
                  </th>
                  <th className="text-left px-6 py-4 text-xs font-semibold text-gray-500 uppercase tracking-wider w-32">
                    Date
                  </th>
                  <th className="text-right px-6 py-4 text-xs font-semibold text-gray-500 uppercase tracking-wider w-20">
                    Action
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {results.map((result, index) => (
                  <tr key={result._id} className={`hover:bg-gray-50 transition-colors ${index % 2 === 0 ? 'bg-white' : 'bg-gray-50/30'}`}>
                    <td className="px-6 py-4">
                      <div className="flex items-start gap-3">
                        <div className="p-2 bg-indigo-50 rounded-lg flex-shrink-0">
                          <FileText className="w-4 h-4 text-indigo-600" />
                        </div>
                        <div className="min-w-0">
                          <p className="font-medium text-gray-900 line-clamp-2">
                            {result.delib_objet || result.filename}
                          </p>
                          {result.delib_numero && (
                            <p className="text-xs text-gray-500 mt-1">N°{result.delib_numero}</p>
                          )}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2 text-sm text-gray-600">
                        <Calendar className="w-4 h-4 text-gray-400" />
                        {formatDate(result.date)}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-right">
                      {result.url ? (
                        <a
                          href={result.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 text-indigo-600 hover:text-indigo-800 transition-colors"
                        >
                          <ExternalLink className="w-4 h-4" />
                        </a>
                      ) : (
                        <ChevronRight className="w-4 h-4 text-gray-300" />
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          
          <Pagination
            currentPage={currentPage}
            totalPages={totalPages}
            onPageChange={setCurrentPage}
            totalResults={totalResults}
            resultsPerPage={RESULTS_PER_PAGE}
          />
        </div>
      ) : (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {results.map((result) => (
              <div
                key={result._id}
                className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md transition-all hover:border-indigo-200"
              >
                <div className="flex items-start gap-4">
                  <div className="p-3 bg-indigo-50 rounded-xl flex-shrink-0">
                    <FileText className="w-5 h-5 text-indigo-600" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold text-gray-900 line-clamp-2 mb-2">
                      {result.delib_objet || result.filename}
                    </h3>
                    <div className="flex flex-wrap items-center gap-3 text-sm text-gray-500">
                      <span className="flex items-center gap-1">
                        <Calendar className="w-3.5 h-3.5" />
                        {formatDate(result.date)}
                      </span>
                    </div>
                    <div className="flex items-center justify-end mt-4">
                      {result.url && (
                        <a
                          href={result.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1.5 text-sm font-medium text-indigo-600 hover:text-indigo-800 transition-colors"
                        >
                          Voir
                          <ExternalLink className="w-3.5 h-3.5" />
                        </a>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <Pagination
              currentPage={currentPage}
              totalPages={totalPages}
              onPageChange={setCurrentPage}
              totalResults={totalResults}
              resultsPerPage={RESULTS_PER_PAGE}
            />
          </div>
        </div>
      )}
    </div>
  )
}
