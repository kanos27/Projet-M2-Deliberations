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

export default api
