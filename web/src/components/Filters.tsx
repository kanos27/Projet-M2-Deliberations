import { Filter, Calendar, User, Vote, Users2, RotateCcw, Gavel, CalendarDays } from 'lucide-react'
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
  year: string
  onYearChange: (value: string) => void
  rapporteur: string
  onRapporteurChange: (value: string) => void
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
  year,
  onYearChange,
  rapporteur,
  onRapporteurChange,
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
    collectivites: [],
    rapporteurs: [],
    lieux: [],
    years: [],
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
                          year !== 'all' ||
                          rapporteur !== '' ||
                          startDate !== '' || 
                          endDate !== '' || 
                          person !== ''

  return (
    <div className="bg-white border border-gray-200 rounded-xl w-full p-5 shadow-sm">
      <div className="flex items-center justify-between mb-5">
        <h2 className="text-base font-semibold text-gray-900 flex items-center gap-2">
          <Filter className="h-4 w-4 text-indigo-600" aria-hidden="true" />
          Filtres
        </h2>
        {hasActiveFilters && (
          <Button
            onClick={onReset}
            className="text-xs text-indigo-600 hover:text-indigo-800 flex items-center gap-1 bg-transparent border-0 cursor-pointer px-2 py-1"
          >
            <RotateCcw className="h-3 w-3" />
            Réinitialiser
          </Button>
        )}
      </div>

      {loading ? (
        <div className="space-y-4 animate-pulse">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="space-y-2">
              <div className="h-3 bg-gray-200 rounded w-1/3"></div>
              <div className="h-9 bg-gray-100 rounded"></div>
            </div>
          ))}
        </div>
      ) : (
        <div className="space-y-4">
          {/* Année */}
          {filterOptions.years.length > 0 && (
            <div className="space-y-1.5">
              <Label htmlFor="year-filter" className="text-xs font-medium text-gray-600 flex items-center gap-1.5">
                <CalendarDays className="h-3.5 w-3.5 text-gray-400" />
                Année
              </Label>
              <Select
                id="year-filter"
                value={year}
                onChange={(e) => onYearChange(e.target.value)}
                className="rounded-lg border-gray-200 text-sm h-9"
              >
                <option value="all">Toutes les années</option>
                {filterOptions.years.map((y) => (
                  <option key={y} value={y}>{y}</option>
                ))}
              </Select>
            </div>
          )}

          {/* Commission */}
          {filterOptions.commissions.length > 0 && (
            <div className="space-y-1.5">
              <Label htmlFor="commission-filter" className="text-xs font-medium text-gray-600 flex items-center gap-1.5">
                <Users2 className="h-3.5 w-3.5 text-gray-400" />
                Commission
              </Label>
              <Select
                id="commission-filter"
                value={commission}
                onChange={(e) => onCommissionChange(e.target.value)}
                className="rounded-lg border-gray-200 text-sm h-9"
              >
                <option value="all">Toutes les commissions</option>
                {filterOptions.commissions.map((comm) => (
                  <option key={comm} value={comm}>{comm}</option>
                ))}
              </Select>
            </div>
          )}

          {/* Résultat du vote */}
          {filterOptions.vote_resultats.length > 0 && (
            <div className="space-y-1.5">
              <Label htmlFor="vote-filter" className="text-xs font-medium text-gray-600 flex items-center gap-1.5">
                <Vote className="h-3.5 w-3.5 text-gray-400" />
                Résultat du vote
              </Label>
              <Select
                id="vote-filter"
                value={voteResultat}
                onChange={(e) => onVoteResultatChange(e.target.value)}
                className="rounded-lg border-gray-200 text-sm h-9"
              >
                <option value="all">Tous les résultats</option>
                {filterOptions.vote_resultats.map((vote) => (
                  <option key={vote} value={vote}>{vote}</option>
                ))}
              </Select>
            </div>
          )}

          {/* Rapporteur */}
          <div className="space-y-1.5">
            <Label htmlFor="rapporteur-filter" className="text-xs font-medium text-gray-600 flex items-center gap-1.5">
              <Gavel className="h-3.5 w-3.5 text-gray-400" />
              Rapporteur
            </Label>
            <Input
              id="rapporteur-filter"
              type="text"
              value={rapporteur}
              onChange={(e) => onRapporteurChange(e.target.value)}
              placeholder="Nom du rapporteur..."
              className="rounded-lg border-gray-200 text-sm h-9"
            />
          </div>

          {/* Période */}
          <div className="space-y-1.5">
            <div className="flex items-center gap-1.5 text-xs font-medium text-gray-600">
              <Calendar className="h-3.5 w-3.5 text-gray-400" />
              <span>Période précise</span>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <Label htmlFor="start-date" className="sr-only">Date de début</Label>
                <Input
                  id="start-date"
                  type="date"
                  value={startDate}
                  onChange={(e) => onStartDateChange(e.target.value)}
                  className="rounded-lg border-gray-200 text-xs h-9"
                  placeholder="Du"
                />
              </div>
              <div>
                <Label htmlFor="end-date" className="sr-only">Date de fin</Label>
                <Input
                  id="end-date"
                  type="date"
                  value={endDate}
                  onChange={(e) => onEndDateChange(e.target.value)}
                  min={startDate}
                  className="rounded-lg border-gray-200 text-xs h-9"
                  placeholder="Au"
                />
              </div>
            </div>
          </div>

          {/* Membre */}
          <div className="space-y-1.5">
            <Label htmlFor="person-filter" className="text-xs font-medium text-gray-600 flex items-center gap-1.5">
              <User className="h-3.5 w-3.5 text-gray-400" />
              Membre présent/absent
            </Label>
            <Input
              id="person-filter"
              type="text"
              value={person}
              onChange={(e) => onPersonChange(e.target.value)}
              placeholder="Nom du membre..."
              className="rounded-lg border-gray-200 text-sm h-9"
            />
          </div>
        </div>
      )}
    </div>
  )
}
