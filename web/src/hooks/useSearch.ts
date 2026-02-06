import { useState, useEffect, useCallback } from 'react'
import { useSearchParams } from 'react-router-dom'
import { searchApi, type SearchResult, type SearchParams } from '../services/api'

const RESULTS_PER_PAGE = 20

export interface SearchState {
  query: string
  voteResultat: string
  commission: string
  year: string
  rapporteur: string
  startDate: string
  endDate: string
  currentPage: number
}

export interface UseSearchReturn {
  // State
  state: SearchState
  results: SearchResult[]
  totalResults: number
  totalPages: number
  loading: boolean
  error: string | null
  
  // Actions
  setQuery: (query: string) => void
  setVoteResultat: (value: string) => void
  setCommission: (value: string) => void
  setYear: (value: string) => void
  setRapporteur: (value: string) => void
  setStartDate: (date: string) => void
  setEndDate: (date: string) => void
  setCurrentPage: (page: number) => void
  performSearch: () => Promise<void>
  resetFilters: () => void
}

export function useSearch(): UseSearchReturn {
  const [searchParams, setSearchParams] = useSearchParams()
  
  const [state, setState] = useState<SearchState>(() => ({
    query: searchParams.get('q') || '',
    voteResultat: searchParams.get('vote_resultat') || 'all',
    commission: searchParams.get('commission') || 'all',
    year: searchParams.get('year') || 'all',
    rapporteur: searchParams.get('rapporteur') || '',
    startDate: searchParams.get('date_from') || '',
    endDate: searchParams.get('date_to') || '',
    currentPage: parseInt(searchParams.get('page') || '1', 10)
  }))
  
  const [results, setResults] = useState<SearchResult[]>([])
  const [totalResults, setTotalResults] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const totalPages = Math.ceil(totalResults / RESULTS_PER_PAGE)

  const syncToUrl = useCallback((newState: SearchState) => {
    const params = new URLSearchParams()
    
    if (newState.query) params.set('q', newState.query)
    if (newState.voteResultat !== 'all') params.set('vote_resultat', newState.voteResultat)
    if (newState.commission !== 'all') params.set('commission', newState.commission)
    if (newState.year !== 'all') params.set('year', newState.year)
    if (newState.rapporteur) params.set('rapporteur', newState.rapporteur)
    if (newState.startDate) params.set('date_from', newState.startDate)
    if (newState.endDate) params.set('date_to', newState.endDate)
    if (newState.currentPage > 1) params.set('page', newState.currentPage.toString())
    
    setSearchParams(params, { replace: true })
  }, [setSearchParams])

  const performSearch = useCallback(async () => {
    setLoading(true)
    setError(null)
    
    try {
      const params: SearchParams = {
        q: state.query || undefined,
        vote_resultat: state.voteResultat !== 'all' ? state.voteResultat : undefined,
        commission: state.commission !== 'all' ? state.commission : undefined,
        year: state.year !== 'all' ? state.year : undefined,
        rapporteur: state.rapporteur || undefined,
        date_from: state.startDate || undefined,
        date_to: state.endDate || undefined,
        limit: RESULTS_PER_PAGE,
        skip: (state.currentPage - 1) * RESULTS_PER_PAGE
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
  }, [state])

  const updateState = useCallback((updates: Partial<SearchState>, resetPage = true) => {
    setState(prev => {
      const newState = {
        ...prev,
        ...updates,
        ...(resetPage && updates.currentPage === undefined ? { currentPage: 1 } : {})
      }
      syncToUrl(newState)
      return newState
    })
  }, [syncToUrl])

  const setQuery = useCallback((query: string) => updateState({ query }), [updateState])
  const setVoteResultat = useCallback((voteResultat: string) => updateState({ voteResultat }), [updateState])
  const setCommission = useCallback((commission: string) => updateState({ commission }), [updateState])
  const setYear = useCallback((year: string) => updateState({ year }), [updateState])
  const setRapporteur = useCallback((rapporteur: string) => updateState({ rapporteur }), [updateState])
  const setStartDate = useCallback((startDate: string) => updateState({ startDate }), [updateState])
  const setEndDate = useCallback((endDate: string) => updateState({ endDate }), [updateState])
  const setCurrentPage = useCallback((currentPage: number) => updateState({ currentPage }, false), [updateState])

  const resetFilters = useCallback(() => {
    const newState: SearchState = {
      query: '',
      voteResultat: 'all',
      commission: 'all',
      year: 'all',
      rapporteur: '',
      startDate: '',
      endDate: '',
      currentPage: 1
    }
    setState(newState)
    syncToUrl(newState)
  }, [syncToUrl])

  useEffect(() => {
    performSearch()
  }, [state.currentPage, state.voteResultat, state.commission, state.year, state.rapporteur, state.startDate, state.endDate])

  return {
    state,
    results,
    totalResults,
    totalPages,
    loading,
    error,
    setQuery,
    setVoteResultat,
    setCommission,
    setYear,
    setRapporteur,
    setStartDate,
    setEndDate,
    setCurrentPage,
    performSearch,
    resetFilters
  }
}
