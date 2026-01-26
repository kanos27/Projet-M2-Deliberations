import { useState } from 'react'
import { SearchBar } from './SearchBar'
import { Filters } from './Filters'

export function SearchPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedTheme, setSelectedTheme] = useState('all')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')

  return (
    <div className="py-8 container mx-auto px-4">
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
        <div className="lg:col-span-5">
          <SearchBar
            value={searchQuery}
            onChange={setSearchQuery}
            onSearch={() => {}}
          />
        </div>

        <aside className="lg:col-span-1">
          <div className="sticky top-8">
            <Filters
              selectedTheme={selectedTheme}
              onThemeChange={setSelectedTheme}
              startDate={startDate}
              onStartDateChange={setStartDate}
              endDate={endDate}
              onEndDateChange={setEndDate}
            />
          </div>
        </aside>
        
        <div className="lg:col-span-4">
          <div className="bg-white border border-gray-200 rounded-xl p-12 text-center">
            <p className="text-gray-500 text-lg">
              Utilisez la barre de recherche et les filtres pour trouver des documents
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
