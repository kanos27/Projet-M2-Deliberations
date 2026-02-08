import { useState, useRef, useEffect } from 'react'
import { Input } from './input'
import { cn } from '../../lib/utils'

interface AutocompleteProps {
  id?: string
  value: string
  onChange: (value: string) => void
  options: string[]
  placeholder?: string
  className?: string
  loading?: boolean
}

export function Autocomplete({
  id,
  value,
  onChange,
  options,
  placeholder,
  className,
  loading = false,
}: AutocompleteProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [filteredOptions, setFilteredOptions] = useState<string[]>([])
  const [highlightedIndex, setHighlightedIndex] = useState(-1)
  const containerRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (!value || value.length < 2) {
      setFilteredOptions([])
      setIsOpen(false)
      return
    }

    const searchTerm = value.toLowerCase()
    
    // Helper to remove civility prefix for matching
    const removeCivility = (str: string) => 
      str.replace(/^(mme?\.?\s*)/i, '').trim()

    const filtered = options.filter(option => {
      const lowerOption = option.toLowerCase()
      const optionWithoutCivility = removeCivility(lowerOption)
      
      // Match on full string OR on string without civility
      return lowerOption.includes(searchTerm) || 
             optionWithoutCivility.includes(searchTerm)
    }).slice(0, 10) // Limit to 10 suggestions

    setFilteredOptions(filtered)
    setIsOpen(filtered.length > 0)
    setHighlightedIndex(-1)
  }, [value, options])

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onChange(e.target.value)
  }

  const handleOptionClick = (option: string) => {
    onChange(option)
    setIsOpen(false)
    inputRef.current?.blur()
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!isOpen || filteredOptions.length === 0) return

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault()
        setHighlightedIndex(prev =>
          prev < filteredOptions.length - 1 ? prev + 1 : prev
        )
        break
      case 'ArrowUp':
        e.preventDefault()
        setHighlightedIndex(prev => (prev > 0 ? prev - 1 : -1))
        break
      case 'Enter':
        e.preventDefault()
        if (highlightedIndex >= 0) {
          handleOptionClick(filteredOptions[highlightedIndex])
        }
        break
      case 'Escape':
        e.preventDefault()
        setIsOpen(false)
        setHighlightedIndex(-1)
        break
    }
  }

  return (
    <div ref={containerRef} className="relative">
      <Input
        ref={inputRef}
        id={id}
        type="text"
        value={value}
        onChange={handleInputChange}
        onKeyDown={handleKeyDown}
        onFocus={() => {
          if (filteredOptions.length > 0) {
            setIsOpen(true)
          }
        }}
        placeholder={placeholder}
        className={className}
        autoComplete="off"
      />
      
      {loading && (
        <div className="absolute right-3 top-1/2 -translate-y-1/2">
          <div className="h-4 w-4 animate-spin rounded-full border-2 border-gray-300 border-t-indigo-600" />
        </div>
      )}

      {isOpen && filteredOptions.length > 0 && (
        <div className="absolute z-50 mt-1 w-full bg-white border border-gray-200 rounded-lg shadow-lg max-h-60 overflow-auto">
          {filteredOptions.map((option, index) => (
            <div
              key={option}
              onClick={() => handleOptionClick(option)}
              onMouseEnter={() => setHighlightedIndex(index)}
              className={cn(
                'px-3 py-2 cursor-pointer text-sm transition-colors',
                highlightedIndex === index
                  ? 'bg-indigo-50 text-indigo-900'
                  : 'hover:bg-gray-50 text-gray-900'
              )}
            >
              {option}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
