import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export interface Document {
  _id: string
  filename: string
  title?: string
  source: string
  bucket: string
  url?: string
  metadata?: Record<string, unknown>
  created_at: string
}

export interface DocumentsParams {
  source?: string
  skip?: number
  limit?: number
}

export interface SearchResult {
  _id: string
  filename: string
  bucket: string
  delib_id?: string
  delib_numero?: number
  delib_objet?: string
  collectivite?: string
  date?: string
  date_convocation?: string
  decision?: string
  matiere?: string
  url?: string
  // Vote info
  vote_resultat?: string
  vote_pour?: number | null
  vote_contre?: number | null
  vote_abstentions?: number | null
  membres_en_exercice?: number | null
  // Commission info
  commission?: string
  commission_avis?: string
  // Séance info
  seance_lieu?: string
  rapporteur?: string
  // Membres counts
  membres_presents_count?: number
  membres_absents_count?: number
}

export interface SearchParams {
  q?: string
  bucket?: string
  date_from?: string
  date_to?: string
  year?: string
  vote_resultat?: string
  commission?: string
  rapporteur?: string
  person?: string
  skip?: number
  limit?: number
}

export interface SearchResponse {
  total: number
  count: number
  skip: number
  limit: number
  results: SearchResult[]
}

export interface FilterOptions {
  vote_resultats: string[]
  commissions: string[]
  avis_commissions: string[]
  collectivites: string[]
  rapporteurs: string[]
  lieux: string[]
  years: string[]
  buckets: string[]
}

export const documentsApi = {
  /**
   * Récupère la liste des documents
   */
  getDocuments: async (params?: DocumentsParams): Promise<Document[]> => {
    const response = await api.get<Document[]>('/documents', { params })
    return response.data
  },

  /**
   * Récupère un document par son ID
   */
  getDocument: async (id: string): Promise<Document> => {
    const response = await api.get<Document>(`/documents/${id}`)
    return response.data
  },

  /**
   * Récupère la liste des sources disponibles
   */
  getSources: async (): Promise<string[]> => {
    const response = await api.get<string[]>('/sources')
    return response.data
  },
}

export const searchApi = {
  /**
   * Recherche avancée dans les délibérations
   */
  search: async (params: SearchParams): Promise<SearchResponse> => {
    const response = await api.get<SearchResponse>('/search', { params })
    return response.data
  },

  /**
   * Récupère les options de filtres depuis l'API
   */
  getFilterOptions: async (): Promise<FilterOptions> => {
    try {
      const response = await api.get<FilterOptions>('/metadata/filter-options')
      return response.data
    } catch {
      // Fallback si l'endpoint n'existe pas encore
      return {
        vote_resultats: [],
        commissions: [],
        avis_commissions: [],
        collectivites: [],
        rapporteurs: [],
        lieux: [],
        years: [],
        buckets: []
      }
    }
  },

  /**
   * Récupère la liste des collectivités
   */
  getCollectivites: async (): Promise<string[]> => {
    try {
      const options = await searchApi.getFilterOptions()
      return options.collectivites
    } catch {
      return []
    }
  },

  /**
   * Récupère la liste des buckets
   */
  getBuckets: async (): Promise<string[]> => {
    try {
      const response = await api.get<string[]>('/metadata/buckets')
      return response.data
    } catch {
      return []
    }
  }
}

// Types pour les membres
export interface Person {
  civilite?: string
  nom: string
  prenom?: string
}

export interface PeopleResponse {
  count: number
  people: Person[]
}

export interface PersonStats {
  person: string
  bucket: string | null
  total_deliberations: number
  present_count: number
  absent_count: number
  presence_rate: number
}

export const peopleApi = {
  /**
   * Récupère la liste de tous les membres
   */
  getAllPeople: async (bucket?: string): Promise<PeopleResponse> => {
    try {
      const params = bucket ? { bucket } : {}
      const response = await api.get<PeopleResponse>('/metadata/people', { params })
      return response.data
    } catch {
      return { count: 0, people: [] }
    }
  },

  /**
   * Récupère les statistiques d'un membre
   */
  getPersonStats: async (personName: string, bucket?: string): Promise<PersonStats> => {
    const params = bucket ? { bucket } : {}
    const response = await api.get<PersonStats>(`/metadata/people/${encodeURIComponent(personName)}/stats`, { params })
    return response.data
  },

  /**
   * Récupère les délibérations d'un membre
   */
  getPersonDeliberations: async (personName: string, presence?: 'present' | 'absent' | 'any', bucket?: string, skip?: number, limit?: number) => {
    const params: Record<string, any> = {}
    if (presence) params.presence = presence
    if (bucket) params.bucket = bucket
    if (skip) params.skip = skip
    if (limit) params.limit = limit
    const response = await api.get(`/metadata/people/${encodeURIComponent(personName)}/deliberations`, { params })
    return response.data
  }
}

export default api

