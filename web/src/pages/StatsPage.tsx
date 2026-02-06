import { useState, useEffect } from 'react'
import {
  FileText,
  Database,
  Calendar,
  RefreshCw,
  Loader2,
  BarChart3,
  Clock,
  AlertCircle,
  Users,
  User,
  TrendingUp,
  CheckCircle2,
  XCircle,
  Search,
  ChevronDown,
  ChevronUp,
  ExternalLink
} from 'lucide-react'
import { peopleApi, type Person, type PersonStats } from '../services/api'

const API_BASE = 'http://localhost:8000'

interface StatsData {
  totalDocuments: number
  totalMetadata: number
  documentsBySource: Record<string, number>
  recentDocuments: Array<{
    _id: string
    filename: string
    title?: string
    source: string
    created_at: string
  }>
  metadataByYear: Record<string, number>
}

interface MemberWithStats extends Person {
  stats?: PersonStats
  loading?: boolean
}

type TabType = 'overview' | 'members'

export function StatsPage() {
  const [activeTab, setActiveTab] = useState<TabType>('overview')
  const [stats, setStats] = useState<StatsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  const [members, setMembers] = useState<MemberWithStats[]>([])
  const [membersLoading, setMembersLoading] = useState(false)
  const [memberSearch, setMemberSearch] = useState('')
  const [expandedMember, setExpandedMember] = useState<string | null>(null)
  const [memberDeliberations, setMemberDeliberations] = useState<any[]>([])
  const [sortBy, setSortBy] = useState<'name' | 'presence'>('presence')

  useEffect(() => {
    fetchStats()
  }, [])

  useEffect(() => {
    if (activeTab === 'members' && members.length === 0) {
      fetchMembers()
    }
  }, [activeTab])

  const fetchStats = async () => {
    setLoading(true)
    setError(null)
    try {
      const [docsRes, countRes, recentRes, filterRes] = await Promise.all([
        fetch(`${API_BASE}/documents?limit=1000`),
        fetch(`${API_BASE}/metadata/count`),
        fetch(`${API_BASE}/documents?limit=10`),
        fetch(`${API_BASE}/metadata/filter-options`)
      ])

      const docs = docsRes.ok ? await docsRes.json() : []
      const countData = countRes.ok ? await countRes.json() : { count: 0 }
      const recentDocs = recentRes.ok ? await recentRes.json() : []
      const filterOptions = filterRes.ok ? await filterRes.json() : { years: [] }

      const bySource: Record<string, number> = {}
      docs.forEach((doc: any) => {
        const source = doc.source || 'inconnu'
        bySource[source] = (bySource[source] || 0) + 1
      })

      const byYear: Record<string, number> = {}
      if (filterOptions.years && Array.isArray(filterOptions.years)) {
        const yearCounts = await Promise.all(
          filterOptions.years.slice(0, 10).map(async (year: string) => {
            const res = await fetch(`${API_BASE}/search?year=${year}&limit=1`)
            const data = res.ok ? await res.json() : { total: 0 }
            return { year, count: data.total }
          })
        )
        yearCounts.forEach(({ year, count }) => {
          if (count > 0) byYear[year] = count
        })
      }

      setStats({
        totalDocuments: docs.length,
        totalMetadata: countData.count,
        documentsBySource: bySource,
        recentDocuments: recentDocs.slice(0, 10),
        metadataByYear: byYear
      })
    } catch (err) {
      console.error('Erreur:', err)
      setError('Impossible de charger les statistiques')
    }
    setLoading(false)
  }

  const fetchMembers = async () => {
    setMembersLoading(true)
    try {
      const response = await peopleApi.getAllPeople()
      const membersWithoutStats: MemberWithStats[] = response.people.map(p => ({
        ...p,
        loading: true
      }))
      setMembers(membersWithoutStats)
      
      const batchSize = 10
      for (let i = 0; i < membersWithoutStats.length; i += batchSize) {
        const batch = membersWithoutStats.slice(i, i + batchSize)
        const statsPromises = batch.map(async (member) => {
          try {
            const stats = await peopleApi.getPersonStats(member.nom)
            return { nom: member.nom, stats }
          } catch {
            return { nom: member.nom, stats: null }
          }
        })
        
        const batchResults = await Promise.all(statsPromises)
        
        setMembers(prev => prev.map(m => {
          const result = batchResults.find(r => r.nom === m.nom)
          if (result) {
            return { ...m, stats: result.stats || undefined, loading: false }
          }
          return m
        }))
      }
    } catch (err) {
      console.error('Erreur chargement membres:', err)
    }
    setMembersLoading(false)
  }

  const loadMemberDeliberations = async (memberName: string) => {
    if (expandedMember === memberName) {
      setExpandedMember(null)
      setMemberDeliberations([])
      return
    }
    
    setExpandedMember(memberName)
    try {
      const response = await peopleApi.getPersonDeliberations(memberName, 'any', undefined, 0, 5)
      setMemberDeliberations(response.results || [])
    } catch (err) {
      console.error('Erreur chargement délibérations:', err)
      setMemberDeliberations([])
    }
  }

  const getPresenceColor = (rate: number) => {
    if (rate >= 90) return 'text-emerald-600 bg-emerald-50'
    if (rate >= 70) return 'text-amber-600 bg-amber-50'
    return 'text-red-600 bg-red-50'
  }

  const getPresenceBarColor = (rate: number) => {
    if (rate >= 90) return 'bg-emerald-500'
    if (rate >= 70) return 'bg-amber-500'
    return 'bg-red-500'
  }

  const formatMemberName = (member: Person) => {
    const parts = [member.civilite, member.prenom, member.nom].filter(Boolean)
    return parts.join(' ')
  }

  const filteredMembers = members
    .filter(m => {
      if (!memberSearch) return true
      const fullName = formatMemberName(m).toLowerCase()
      return fullName.includes(memberSearch.toLowerCase())
    })
    .sort((a, b) => {
      if (sortBy === 'name') {
        return (a.nom || '').localeCompare(b.nom || '')
      }
      const rateA = a.stats?.presence_rate ?? 0
      const rateB = b.stats?.presence_rate ?? 0
      return rateB - rateA
    })

  if (loading) {
    return (
      <div className="p-8 pt-24 flex items-center justify-center h-full">
        <div className="flex items-center gap-3 text-gray-500">
          <Loader2 className="w-6 h-6 animate-spin" />
          <span>Chargement des statistiques...</span>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-8 pt-24">
        <div className="bg-red-50 border border-red-200 rounded-xl p-6 flex items-center gap-4">
          <AlertCircle className="w-6 h-6 text-red-500" />
          <div>
            <p className="font-medium text-red-800">{error}</p>
            <p className="text-sm text-red-600">Vérifiez que l'API est bien démarrée</p>
          </div>
          <button
            onClick={fetchStats}
            className="ml-auto px-4 py-2 bg-red-100 hover:bg-red-200 text-red-700 rounded-lg transition-colors"
          >
            Réessayer
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="p-8 pt-24">
      <header className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Statistiques</h1>
            <p className="text-gray-600">Vue d'ensemble des données et des membres</p>
          </div>
          <button
            onClick={() => {
              fetchStats()
              if (activeTab === 'members') fetchMembers()
            }}
            className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            Actualiser
          </button>
        </div>
      </header>

      <div className="flex gap-2 mb-8 border-b border-gray-200">
        <button
          onClick={() => setActiveTab('overview')}
          className={`px-4 py-3 font-medium text-sm transition-colors relative ${
            activeTab === 'overview'
              ? 'text-indigo-600'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          <div className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4" />
            Vue d'ensemble
          </div>
          {activeTab === 'overview' && (
            <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-indigo-600" />
          )}
        </button>
        <button
          onClick={() => setActiveTab('members')}
          className={`px-4 py-3 font-medium text-sm transition-colors relative ${
            activeTab === 'members'
              ? 'text-indigo-600'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          <div className="flex items-center gap-2">
            <Users className="w-4 h-4" />
            Membres
            {members.length > 0 && (
              <span className="ml-1 px-2 py-0.5 text-xs bg-gray-100 text-gray-600 rounded-full">
                {members.length}
              </span>
            )}
          </div>
          {activeTab === 'members' && (
            <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-indigo-600" />
          )}
        </button>
      </div>

      {activeTab === 'overview' ? (
        <>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div className="bg-white rounded-xl p-6 shadow-lg border border-gray-100">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-3 bg-indigo-100 rounded-lg">
                  <FileText className="w-6 h-6 text-indigo-600" />
                </div>
                <span className="text-gray-500">Documents PDF</span>
              </div>
              <p className="text-3xl font-bold text-gray-900">{stats?.totalDocuments || 0}</p>
              <p className="text-sm text-gray-500 mt-1">fichiers stockés</p>
            </div>

            <div className="bg-white rounded-xl p-6 shadow-lg border border-gray-100">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-3 bg-green-100 rounded-lg">
                  <Database className="w-6 h-6 text-green-600" />
                </div>
                <span className="text-gray-500">Métadonnées</span>
              </div>
              <p className="text-3xl font-bold text-gray-900">{stats?.totalMetadata || 0}</p>
              <p className="text-sm text-gray-500 mt-1">délibérations indexées</p>
            </div>

            <div className="bg-white rounded-xl p-6 shadow-lg border border-gray-100">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-3 bg-amber-100 rounded-lg">
                  <BarChart3 className="w-6 h-6 text-amber-600" />
                </div>
                <span className="text-gray-500">Taux de conversion</span>
              </div>
              <p className="text-3xl font-bold text-gray-900">
                {stats?.totalDocuments ? Math.round((stats.totalMetadata / stats.totalDocuments) * 100) : 0}%
              </p>
              <p className="text-sm text-gray-500 mt-1">documents convertis</p>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white rounded-xl p-6 shadow-lg border border-gray-100">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <Database className="w-5 h-5 text-gray-400" />
                Documents par source
              </h3>
              {Object.keys(stats?.documentsBySource || {}).length > 0 ? (
                <div className="space-y-3">
                  {Object.entries(stats?.documentsBySource || {}).map(([source, count]) => (
                    <div key={source} className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="w-2 h-2 bg-indigo-500 rounded-full"></div>
                        <span className="text-gray-700 capitalize">{source}</span>
                      </div>
                      <div className="flex items-center gap-3">
                        <div className="w-32 bg-gray-100 rounded-full h-2">
                          <div
                            className="bg-indigo-500 h-2 rounded-full"
                            style={{ width: `${(count / (stats?.totalDocuments || 1)) * 100}%` }}
                          />
                        </div>
                        <span className="text-sm font-medium text-gray-900 w-12 text-right">{count}</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500 text-sm">Aucune donnée disponible</p>
              )}
            </div>

            <div className="bg-white rounded-xl p-6 shadow-lg border border-gray-100">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <Calendar className="w-5 h-5 text-gray-400" />
                Délibérations par année
              </h3>
              {Object.keys(stats?.metadataByYear || {}).length > 0 ? (
                <div className="space-y-3">
                  {Object.entries(stats?.metadataByYear || {})
                    .sort(([a], [b]) => b.localeCompare(a))
                    .map(([year, count]) => (
                      <div key={year} className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                          <span className="text-gray-700">{year}</span>
                        </div>
                        <div className="flex items-center gap-3">
                          <div className="w-32 bg-gray-100 rounded-full h-2">
                            <div
                              className="bg-green-500 h-2 rounded-full"
                              style={{ width: `${(count / (stats?.totalMetadata || 1)) * 100}%` }}
                            />
                          </div>
                          <span className="text-sm font-medium text-gray-900 w-12 text-right">{count}</span>
                        </div>
                      </div>
                    ))}
                </div>
              ) : (
                <p className="text-gray-500 text-sm">Aucune donnée disponible</p>
              )}
            </div>
          </div>

          <div className="mt-6 bg-white rounded-xl p-6 shadow-lg border border-gray-100">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <Clock className="w-5 h-5 text-gray-400" />
              Documents récents
            </h3>
            {(stats?.recentDocuments?.length || 0) > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-100">
                      <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Fichier</th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Source</th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Date d'ajout</th>
                    </tr>
                  </thead>
                  <tbody>
                    {stats?.recentDocuments.map((doc) => (
                      <tr key={doc._id} className="border-b border-gray-50 hover:bg-gray-50">
                        <td className="py-3 px-4">
                          <div className="flex items-center gap-2">
                            <FileText className="w-4 h-4 text-gray-400" />
                            <span className="text-sm text-gray-900 truncate max-w-xs">
                              {doc.title || doc.filename}
                            </span>
                          </div>
                        </td>
                        <td className="py-3 px-4">
                          <span className="text-sm text-gray-600 capitalize">{doc.source}</span>
                        </td>
                        <td className="py-3 px-4">
                          <span className="text-sm text-gray-500">
                            {new Date(doc.created_at).toLocaleDateString('fr-FR', {
                              day: 'numeric',
                              month: 'short',
                              year: 'numeric'
                            })}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-gray-500 text-sm">Aucun document récent</p>
            )}
          </div>
        </>
      ) : (
        <div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
              <div className="flex items-center gap-3">
                <div className="p-2.5 bg-indigo-100 rounded-lg">
                  <Users className="w-5 h-5 text-indigo-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-gray-900">{members.length}</p>
                  <p className="text-xs text-gray-500">Membres total</p>
                </div>
              </div>
            </div>
            <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
              <div className="flex items-center gap-3">
                <div className="p-2.5 bg-emerald-100 rounded-lg">
                  <TrendingUp className="w-5 h-5 text-emerald-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-gray-900">
                    {members.filter(m => (m.stats?.presence_rate ?? 0) >= 90).length}
                  </p>
                  <p className="text-xs text-gray-500">Présence ≥ 90%</p>
                </div>
              </div>
            </div>
            <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
              <div className="flex items-center gap-3">
                <div className="p-2.5 bg-amber-100 rounded-lg">
                  <CheckCircle2 className="w-5 h-5 text-amber-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-gray-900">
                    {members.filter(m => {
                      const rate = m.stats?.presence_rate ?? 0
                      return rate >= 70 && rate < 90
                    }).length}
                  </p>
                  <p className="text-xs text-gray-500">Présence 70-90%</p>
                </div>
              </div>
            </div>
            <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
              <div className="flex items-center gap-3">
                <div className="p-2.5 bg-red-100 rounded-lg">
                  <XCircle className="w-5 h-5 text-red-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-gray-900">
                    {members.filter(m => (m.stats?.presence_rate ?? 0) < 70).length}
                  </p>
                  <p className="text-xs text-gray-500">Présence &lt; 70%</p>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100 mb-6">
            <div className="flex flex-col sm:flex-row gap-4">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Rechercher un membre..."
                  value={memberSearch}
                  onChange={(e) => setMemberSearch(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                />
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setSortBy('presence')}
                  className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                    sortBy === 'presence'
                      ? 'bg-indigo-100 text-indigo-700'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  Trier par présence
                </button>
                <button
                  onClick={() => setSortBy('name')}
                  className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                    sortBy === 'name'
                      ? 'bg-indigo-100 text-indigo-700'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  Trier par nom
                </button>
              </div>
            </div>
          </div>

          {membersLoading && members.length === 0 ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-6 h-6 animate-spin text-indigo-600" />
              <span className="ml-3 text-gray-600">Chargement des membres...</span>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
              {filteredMembers.map((member) => {
                const isExpanded = expandedMember === member.nom
                const presenceRate = member.stats?.presence_rate ?? 0
                
                return (
                  <div
                    key={`${member.nom}-${member.prenom}`}
                    className={`bg-white rounded-xl shadow-sm border transition-all duration-200 ${
                      isExpanded ? 'border-indigo-300 ring-2 ring-indigo-100' : 'border-gray-100 hover:border-gray-200'
                    }`}
                  >
                    <div className="p-5">
                      <div className="flex items-start justify-between mb-4">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-full flex items-center justify-center text-white font-semibold text-sm">
                            {member.prenom?.[0] || ''}{member.nom?.[0] || ''}
                          </div>
                          <div>
                            <h4 className="font-semibold text-gray-900">
                              {member.prenom} {member.nom}
                            </h4>
                            {member.civilite && (
                              <p className="text-xs text-gray-500">{member.civilite}</p>
                            )}
                          </div>
                        </div>
                        {member.loading ? (
                          <Loader2 className="w-4 h-4 animate-spin text-gray-400" />
                        ) : (
                          <span className={`px-2.5 py-1 rounded-full text-xs font-semibold ${getPresenceColor(presenceRate)}`}>
                            {presenceRate.toFixed(1)}%
                          </span>
                        )}
                      </div>

                      {member.stats && !member.loading && (
                        <>
                          <div className="mb-4">
                            <div className="flex justify-between text-xs text-gray-500 mb-1">
                              <span>Taux de présence</span>
                              <span>{member.stats.present_count} / {member.stats.total_deliberations}</span>
                            </div>
                            <div className="w-full bg-gray-100 rounded-full h-2">
                              <div
                                className={`h-2 rounded-full transition-all duration-500 ${getPresenceBarColor(presenceRate)}`}
                                style={{ width: `${presenceRate}%` }}
                              />
                            </div>
                          </div>

                          <div className="grid grid-cols-3 gap-2 text-center">
                            <div className="bg-gray-50 rounded-lg p-2">
                              <p className="text-lg font-bold text-gray-900">{member.stats.total_deliberations}</p>
                              <p className="text-xs text-gray-500">Séances</p>
                            </div>
                            <div className="bg-emerald-50 rounded-lg p-2">
                              <p className="text-lg font-bold text-emerald-600">{member.stats.present_count}</p>
                              <p className="text-xs text-emerald-600">Présent</p>
                            </div>
                            <div className="bg-red-50 rounded-lg p-2">
                              <p className="text-lg font-bold text-red-600">{member.stats.absent_count}</p>
                              <p className="text-xs text-red-600">Absent</p>
                            </div>
                          </div>

                          <button
                            onClick={() => loadMemberDeliberations(member.nom)}
                            className="w-full mt-4 flex items-center justify-center gap-2 py-2 text-sm text-indigo-600 hover:text-indigo-800 hover:bg-indigo-50 rounded-lg transition-colors"
                          >
                            {isExpanded ? (
                              <>
                                <ChevronUp className="w-4 h-4" />
                                Masquer les délibérations
                              </>
                            ) : (
                              <>
                                <ChevronDown className="w-4 h-4" />
                                Voir les délibérations récentes
                              </>
                            )}
                          </button>
                        </>
                      )}
                    </div>

                    {isExpanded && memberDeliberations.length > 0 && (
                      <div className="border-t border-gray-100 p-4 bg-gray-50 rounded-b-xl">
                        <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-3">
                          Dernières délibérations
                        </p>
                        <div className="space-y-2">
                          {memberDeliberations.map((delib: any, idx: number) => (
                            <div
                              key={idx}
                              className="bg-white rounded-lg p-3 text-sm border border-gray-100"
                            >
                              <div className="flex items-start justify-between gap-2">
                                <p className="text-gray-900 font-medium line-clamp-2 flex-1">
                                  {delib.full_metadata?.deliberation?.objet || delib.filename}
                                </p>
                                {delib.full_metadata?.deliberation?.url_document && (
                                  <a
                                    href={delib.full_metadata.deliberation.url_document}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-indigo-600 hover:text-indigo-800 flex-shrink-0"
                                  >
                                    <ExternalLink className="w-4 h-4" />
                                  </a>
                                )}
                              </div>
                              <p className="text-xs text-gray-500 mt-1">
                                {delib.full_metadata?.deliberation?.date
                                  ? new Date(delib.full_metadata.deliberation.date).toLocaleDateString('fr-FR', {
                                      day: 'numeric',
                                      month: 'long',
                                      year: 'numeric'
                                    })
                                  : 'Date inconnue'}
                              </p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )}

          {filteredMembers.length === 0 && !membersLoading && (
            <div className="text-center py-12">
              <User className="w-12 h-12 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500">Aucun membre trouvé</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
