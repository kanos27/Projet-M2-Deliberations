import { Search } from 'lucide-react'
import { Button } from './ui/button'
import { Input } from './ui/input'

interface SearchBarProps {
  value: string
  onChange: (value: string) => void
  onSearch: () => void
  resultsCount?: number
}

export function SearchBar({ value, onChange, onSearch, resultsCount }: SearchBarProps) {
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSearch()
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      onChange('')
    }
  }

  return (
    <form 
      onSubmit={handleSubmit} 
      className="w-full"
      role="search"
      aria-label="Recherche de délibérations"
    >
      <div className="flex gap-2 items-end">
        <div className="flex-1">
          <label 
            htmlFor="search-input" 
            className="block text-sm font-medium text-gray-700 mb-2"
          >
            Rechercher une délibération
          </label>
          <Input
            id="search-input"
            type="search"
            inputMode="search"
            autoComplete="off"
            autoCorrect="off"
            spellCheck={false}
            placeholder="Rechercher une délibération (titre, référence, mots-clés...)"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onKeyDown={handleKeyDown}
            className="w-full text-base h-12"
            aria-describedby="search-hint"
          />
          <p id="search-hint" className="sr-only">
            Saisissez votre recherche puis appuyez sur Entrée ou cliquez sur Rechercher. Appuyez sur Échap pour effacer.
          </p>
        </div>
        <Button 
          type="submit" 
          size="lg"
          className="focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-indigo-400 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700"
        >
          <Search className="h-5 w-5 mr-2" aria-hidden="true" />
          Rechercher
        </Button>
      </div>
      
      <div 
        role="status" 
        aria-live="polite" 
        aria-atomic="true"
        className="sr-only"
      >
        {resultsCount !== undefined && (
          resultsCount === 0 
            ? 'Aucun résultat trouvé' 
            : `${resultsCount} résultat${resultsCount > 1 ? 's' : ''} trouvé${resultsCount > 1 ? 's' : ''}`
        )}
      </div>
    </form>
  )
}
