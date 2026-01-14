import { Filter, Calendar } from 'lucide-react'
import { Label } from './ui/label'
import { Select } from './ui/select'
import { Input } from './ui/input'

interface FiltersProps {
  selectedTheme: string
  onThemeChange: (theme: string) => void
  startDate: string
  onStartDateChange: (date: string) => void
  endDate: string
  onEndDateChange: (date: string) => void
}

const THEMES = [
  { value: 'all', label: 'Toutes les thématiques' },
  { value: 'urbanisme', label: 'Urbanisme' },
  { value: 'etat-civil', label: 'État Civil' },
  { value: 'travaux', label: 'Travaux' },
  { value: 'environnement', label: 'Environnement' },
  { value: 'deliberations', label: 'Délibérations' },
  { value: 'marches-publics', label: 'Marchés Publics' },
  { value: 'autres', label: 'Autres' },
]

export function Filters({
  selectedTheme,
  onThemeChange,
  startDate,
  onStartDateChange,
  endDate,
  onEndDateChange,
}: FiltersProps) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl w-full p-6">
      <h2 className="text-xl font-semibold text-[#212121] mb-6 flex items-center gap-2">
        <Filter className="h-5 w-5 text-gray-600" aria-hidden="true" />
        Filtres
      </h2>
      <div className="space-y-6">
        <div className="space-y-3">
          <Label htmlFor="theme-filter" className="text-sm font-medium text-[#212121]">
            Thématique
          </Label>
          <Select
            id="theme-filter"
            value={selectedTheme}
            onChange={(e) => onThemeChange(e.target.value)}
            aria-label="Filtrer par thématique"
            className="rounded-lg border-gray-300 w-full"
          >
            {THEMES.map((theme) => (
              <option key={theme.value} value={theme.value}>
                {theme.label}
              </option>
            ))}
          </Select>
        </div>

        <div className="space-y-4">
          <div className="flex items-center gap-2 text-sm font-medium text-[#212121]">
            <Calendar className="h-4 w-4 text-gray-600" aria-hidden="true" />
            <span>Période</span>
          </div>
          
          <div className="space-y-3">
            <Label htmlFor="start-date" className="text-sm font-medium text-[#212121]">
              Date de début
            </Label>
            <Input
              id="start-date"
              type="date"
              value={startDate}
              onChange={(e) => onStartDateChange(e.target.value)}
              aria-label="Sélectionner la date de début"
              className="rounded-lg border-gray-300 text-sm w-full"
            />
          </div>

          <div className="space-y-3">
            <Label htmlFor="end-date" className="text-sm font-medium text-[#212121]">
              Date de fin
            </Label>
            <Input
              id="end-date"
              type="date"
              value={endDate}
              onChange={(e) => onEndDateChange(e.target.value)}
              aria-label="Sélectionner la date de fin"
              min={startDate}
              className="rounded-lg border-gray-300 text-sm w-full"
            />
          </div>
        </div>
      </div>
    </div>
  )
}
