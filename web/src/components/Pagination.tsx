import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from 'lucide-react'

interface PaginationProps {
  currentPage: number
  totalPages: number
  onPageChange: (page: number) => void
  totalResults: number
  resultsPerPage: number
}

export function Pagination({ currentPage, totalPages, onPageChange, totalResults, resultsPerPage }: PaginationProps) {
  const startResult = (currentPage - 1) * resultsPerPage + 1
  const endResult = Math.min(currentPage * resultsPerPage, totalResults)

  const getPageNumbers = () => {
    const pages: (number | string)[] = []
    const showPages = 5 

    if (totalPages <= showPages) {
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i)
      }
    } else {
      if (currentPage <= 3) {
        for (let i = 1; i <= 4; i++) pages.push(i)
        pages.push('...')
        pages.push(totalPages)
      } else if (currentPage >= totalPages - 2) {
        pages.push(1)
        pages.push('...')
        for (let i = totalPages - 3; i <= totalPages; i++) pages.push(i)
      } else {
        pages.push(1)
        pages.push('...')
        for (let i = currentPage - 1; i <= currentPage + 1; i++) pages.push(i)
        pages.push('...')
        pages.push(totalPages)
      }
    }

    return pages
  }

  if (totalPages <= 1) return null

  return (
    <div className="flex items-center justify-between border-t border-gray-200 bg-white px-6 py-4 rounded-b-xl">
      <div className="flex-1 hidden sm:block">
        <p className="text-sm text-gray-700">
          Affichage de <span className="font-semibold">{startResult}</span> à{' '}
          <span className="font-semibold">{endResult}</span> sur{' '}
          <span className="font-semibold">{totalResults}</span> résultat{totalResults > 1 ? 's' : ''}
        </p>
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={() => onPageChange(1)}
          disabled={currentPage === 1}
          className="p-2 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          aria-label="Première page"
        >
          <ChevronsLeft className="h-4 w-4" />
        </button>

        <button
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage === 1}
          className="p-2 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          aria-label="Page précédente"
        >
          <ChevronLeft className="h-4 w-4" />
        </button>

        <div className="hidden sm:flex items-center gap-1">
          {getPageNumbers().map((page, index) => (
            page === '...' ? (
              <span key={`ellipsis-${index}`} className="px-3 py-2 text-gray-500">
                ...
              </span>
            ) : (
              <button
                key={page}
                onClick={() => onPageChange(page as number)}
                className={`px-3 py-2 rounded-lg font-medium transition-colors ${
                  currentPage === page
                    ? 'bg-indigo-600 text-white'
                    : 'text-gray-700 hover:bg-gray-100 border border-gray-300'
                }`}
              >
                {page}
              </button>
            )
          ))}
        </div>

        <span className="sm:hidden px-3 py-2 text-sm text-gray-700">
          Page {currentPage} / {totalPages}
        </span>

        <button
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage === totalPages}
          className="p-2 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          aria-label="Page suivante"
        >
          <ChevronRight className="h-4 w-4" />
        </button>

        <button
          onClick={() => onPageChange(totalPages)}
          disabled={currentPage === totalPages}
          className="p-2 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          aria-label="Dernière page"
        >
          <ChevronsRight className="h-4 w-4" />
        </button>
      </div>
    </div>
  )
}
