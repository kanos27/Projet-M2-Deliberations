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

// Raw metadata document from MongoDB
export interface SearchResult {
  _id: string
  filename: string
  bucket: string
  extracted_at?: string
  full_metadata?: {
    deliberation?: {
      id?: string
      numero?: number
      objet?: string
      date?: string
      date_convocation?: string
      url_document?: string
      matiere?: { nom?: string } | string
    }
    collectivite?: { nom?: string; name?: string } | string
    decision?: string
    vote?: {
      resultat?: string
      votes_pour?: number
      votes_contre?: number
      abstentions?: number
      membres_en_exercice?: number
    }
    commission_consultee?: {
      nom?: string
      avis?: string
      date_reunion?: string
    }
    seance?: {
      lieu?: string
      rapporteur?: {
        civilite?: string
        prenom?: string
        nom?: string
      }
    }
    membres_presents?: Array<{ civilite?: string; prenom?: string; nom?: string }>
    membres_absents?: Array<{ civilite?: string; prenom?: string; nom?: string }>
    contenu?: { texte_integral?: string }
    proposition?: { texte?: string }
    references_juridiques?: string[]
    considerants?: string[]
    prefecture?: {
      id?: string
      date_envoi?: string
      date_reception?: string
      date_publication?: string
    }
  }
  scdl_metadata?: {
    COLL_SIRET?: string
    VOTE_EFFECTIF?: number
    VOTE_REEL?: number
    DELIB_OBJET?: string
    DELIB_DATE?: string
  }
}

// Helper to extract flattened fields from raw document
export function extractMetadata(result: SearchResult) {
  const full = result.full_metadata || {}
  const delib = full.deliberation || {}
  const vote = full.vote || {}
  const commission = full.commission_consultee || {}
  const seance = full.seance || {}
  const rapporteur = seance.rapporteur || {}
  const prefecture = full.prefecture || {}
  const scdl = result.scdl_metadata || {}
  const collectivite = full.collectivite
  const matiere = delib.matiere

  return {
    _id: result._id,
    filename: result.filename,
    bucket: result.bucket,
    delib_id: delib.id,
    delib_numero: delib.numero,
    delib_objet: delib.objet || scdl.DELIB_OBJET,
    date: delib.date || scdl.DELIB_DATE,
    date_convocation: delib.date_convocation,
    url: delib.url_document,
    collectivite: typeof collectivite === 'string' ? collectivite : (collectivite?.nom || collectivite?.name || ''),
    matiere: typeof matiere === 'string' ? matiere : (matiere?.nom || ''),
    decision: full.decision,
    vote_resultat: vote.resultat,
    vote_pour: vote.votes_pour,
    vote_contre: vote.votes_contre,
    vote_abstentions: vote.abstentions,
    membres_en_exercice: vote.membres_en_exercice,
    commission: commission.nom,
    commission_avis: commission.avis,
    commission_date_reunion: commission.date_reunion,
    seance_lieu: seance.lieu,
    rapporteur: [rapporteur.civilite, rapporteur.prenom, rapporteur.nom].filter(Boolean).join(' '),
    membres_presents_count: full.membres_presents?.length || 0,
    membres_absents_count: full.membres_absents?.length || 0,
    membres_presents: (full.membres_presents || []).map(m => [m.civilite, m.prenom, m.nom].filter(Boolean).join(' ')),
    membres_absents: (full.membres_absents || []).map(m => [m.civilite, m.prenom, m.nom].filter(Boolean).join(' ')),
    contenu_texte_integral: full.contenu?.texte_integral,
    proposition_texte: full.proposition?.texte,
    references_juridiques: full.references_juridiques || [],
    considerants: full.considerants || [],
    prefecture_id: prefecture.id,
    prefecture_date_envoi: prefecture.date_envoi,
    prefecture_date_reception: prefecture.date_reception,
    prefecture_date_publication: prefecture.date_publication,
    coll_siret: scdl.COLL_SIRET,
    vote_effectif: scdl.VOTE_EFFECTIF,
    vote_reel: scdl.VOTE_REEL,
  }
}

// Flattened result type for components
export type FlatSearchResult = ReturnType<typeof extractMetadata>

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
  matiere_code?: string
  matiere_nom?: string
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
  matieres: Array<{ code: string; nom: string }>
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
   * Recherche avancée dans les délibérations via /metadata
   */
  search: async (params: SearchParams): Promise<SearchResponse> => {
    const response = await api.get<SearchResponse>('/metadata', { params })
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
        buckets: [],
        matieres: []
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

