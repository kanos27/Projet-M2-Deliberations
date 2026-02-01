import { Filter, Calendar, User, Vote, Users2, RotateCcw } from 'lucide-react'
import { Label } from './ui/label'
import { Select } from './ui/select'
import { Input } from './ui/input'
import { Button } from './ui/button'
import { useEffect, useState } from 'react'
import { searchApi, type FilterOptions } from '../services/api'

interface FiltersProps {
  voteResultat: string
  onVoteResultatChange: (value: string) => void
  commission: string
  onCommissionChange: (value: string) => void
  startDate: string
  onStartDateChange: (date: string) => void
  endDate: string
  onEndDateChange: (date: string) => void
  person: string
  onPersonChange: (name: string) => void
  onReset: () => void
}

export function Filters({
  voteResultat,
  onVoteResultatChange,
  commission,
  onCommissionChange,
  startDate,
  onStartDateChange,
  endDate,
  onEndDateChange,
  person,
  onPersonChange,
  onReset,
}: FiltersProps) {
  const [filterOptions, setFilterOptions] = useState<FilterOptions>({
    vote_resultats: [],
    commissions: [],
    avis_commissions: [],
    lieux: [],
    buckets: []
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const loadFilterOptions = async () => {
      try {
        setLoading(true)
        const options = await searchApi.getFilterOptions()
        setFilterOptions(options)
      } catch (error) {
        console.error('Erreur lors du chargement des options de filtres:', error)
      } finally {
        setLoading(false)
      }
    }
    loadFilterOptions()
  }, [])

  const hasActiveFilters = voteResultat !== 'all' || 
                          commission !== 'all' ||
                          startDate !== '' || 
                          endDate !== '' || 
                          person !== ''

  return (
    <div className="bg-white border border-gray-200 rounded-xl w-full p-6 shadow-sm">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-[#212121] flex items-center gap-2">
          <Filter className="h-5 w-5 text-blue-600" aria-hidden="true" />
          Filtres
        </h2>
        {hasActiveFilters && (
          <Button
            onClick={onReset}
            variant="ghost"
            size="sm"
            className="text-xs text-gray-600 hover:text-gray-900 flex items-center gap-1"
          >
            <RotateCcw className="h-3 w-3" />
            Réinitialiser
          </Button>
        )}
      </div>

      {loading ? (
        <div className="space-y-4 animate-pulse">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="space-y-2">
              <div className="h-4 bg-gray-200 rounded w-1/3"></div>
              <div className="h-10 bg-gray-100 rounded"></div>
            </div>
          ))}
        </div>
      ) : (
        <div className="space-y-5">
          {/* Résultat du vote */}
          <div className="space-y-2">
            <Label htmlFor="vote-filter" className="text-sm font-medium text-[#212121] flex items-center gap-2">
              <Vote className="h-4 w-4 text-green-600" />
              Résultat du vote
            </Label>
            <Select
              id="vote-filter"
              value={voteResultat}
              onChange={(e) => onVoteResultatChange(e.target.value)}
              aria-label="Filtrer par résultat de vote"
              className="rounded-lg border-gray-300 w-full"
            >
              <option value="all">Tous les résultats</option>
              {filterOptions.vote_resultats.map((vote) => (
                <option key={vote} value={vote}>
                  {vote}
                </option>
              ))}
            </Select>
          </div>

          {/* Commission */}
          <div className="space-y-2">
            <Label htmlFor="commission-filter" className="text-sm font-medium text-[#212121] flex items-center gap-2">
              <Users2 className="h-4 w-4 text-purple-600" />
              Commission
            </Label>
            <Select
              id="commission-filter"
              value={commission}
              onChange={(e) => onCommissionChange(e.target.value)}
              aria-label="Filtrer par commission"
              className="rounded-lg border-gray-300 w-full"
            >
              <option value="all">Toutes les commissions</option>
              {filterOptions.commissions.map((comm) => (
                <option key={comm} value={comm}>
                  {comm}
                </option>
              ))}
            </Select>
          </div>

          {/* Période */}
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-sm font-medium text-[#212121]">
              <Calendar className="h-4 w-4 text-red-600" aria-hidden="true" />
              <span>Période</span>
            </div>
            
            <div className="grid grid-cols-2 gap-2">
              <div className="space-y-1">
                <Label htmlFor="start-date" className="text-xs text-gray-500">
                  Du
                </Label>
                <Input
                  id="start-date"
                  type="date"
                  value={startDate}
                  onChange={(e) => onStartDateChange(e.target.value)}
                  aria-label="Date de début"
                  className="rounded-lg border-gray-300 text-sm w-full"
                />
              </div>

              <div className="space-y-1">
                <Label htmlFor="end-date" className="text-xs text-gray-500">
                  Au
                </Label>
                <Input
                  id="end-date"
                  type="date"
                  value={endDate}
                  onChange={(e) => onEndDateChange(e.target.value)}
                  aria-label="Date de fin"
                  min={startDate}
                  className="rounded-lg border-gray-300 text-sm w-full"
                />
              </div>
            </div>
          </div>

          {/* Recherche de personne */}
          <div className="space-y-2">
            <Label htmlFor="person-filter" className="text-sm font-medium text-[#212121] flex items-center gap-2">
              <User className="h-4 w-4 text-cyan-600" />
              Membre (présent/absent)
            </Label>
            <Input
              id="person-filter"
              type="text"
              value={person}
              onChange={(e) => onPersonChange(e.target.value)}
              placeholder="Nom du membre..."
              aria-label="Rechercher un membre"
              className="rounded-lg border-gray-300 text-sm w-full"
            />
            <p className="text-xs text-gray-400">
              Recherche dans les membres présents et absents
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
