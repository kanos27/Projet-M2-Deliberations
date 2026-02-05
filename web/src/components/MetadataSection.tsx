import { useState } from 'react'
import { FileText, Calendar, MapPin, Building2, Hash, Users2, Gavel, Landmark, ChevronDown, Scale, Users } from 'lucide-react'
import type { SearchResult } from '../services/api'

interface MetadataSectionProps {
  result: SearchResult
  variant?: 'detailed' | 'compact'
}

export function MetadataSection({ result, variant = 'detailed' }: MetadataSectionProps) {
  const [showConsiderants, setShowConsiderants] = useState(false)
  const [showMembres, setShowMembres] = useState(false)

  const formatDate = (dateString: string | undefined) => {
    if (!dateString) return 'Date non disponible'
    try {
      return new Date(dateString).toLocaleDateString('fr-FR', {
        day: 'numeric',
        month: 'long',
        year: 'numeric'
      })
    } catch {
      return dateString
    }
  }

  const formatDateShort = (dateString: string | undefined) => {
    if (!dateString) return '-'
    try {
      return new Date(dateString).toLocaleDateString('fr-FR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
      })
    } catch {
      return dateString
    }
  }

  if (variant === 'compact') {
    return (
      <div className="grid grid-cols-1 gap-4 text-sm">
        {/* Informations générales */}
        <div className="space-y-2">
          {result.collectivite && (
            <div className="flex items-start gap-2">
              <Building2 className="h-4 w-4 text-gray-400 mt-0.5 flex-shrink-0" />
              <div>
                <span className="text-gray-500">Collectivité:</span>
                <span className="ml-1 text-gray-700">{result.collectivite}</span>
                {result.coll_siret && (
                  <span className="ml-1 text-xs text-gray-400">(SIRET: {result.coll_siret})</span>
                )}
              </div>
            </div>
          )}
          {result.delib_id && (
            <div className="flex items-start gap-2">
              <Hash className="h-4 w-4 text-gray-400 mt-0.5 flex-shrink-0" />
              <div>
                <span className="text-gray-500">ID:</span>
                <span className="ml-1 text-gray-700 font-mono text-xs">{result.delib_id}</span>
              </div>
            </div>
          )}
          {result.commission && (
            <div className="flex items-start gap-2">
              <Users2 className="h-4 w-4 text-gray-400 mt-0.5 flex-shrink-0" />
              <div>
                <span className="text-gray-500">Commission:</span>
                <span className="ml-1 text-gray-700">{result.commission}</span>
                {result.commission_date_reunion && (
                  <span className="ml-1 text-xs text-gray-400">(réunie le {formatDateShort(result.commission_date_reunion)})</span>
                )}
              </div>
            </div>
          )}
          {result.rapporteur && (
            <div className="flex items-start gap-2">
              <Gavel className="h-4 w-4 text-gray-400 mt-0.5 flex-shrink-0" />
              <div>
                <span className="text-gray-500">Rapporteur:</span>
                <span className="ml-1 text-gray-700">{result.rapporteur}</span>
              </div>
            </div>
          )}
          {result.seance_lieu && (
            <div className="flex items-start gap-2">
              <MapPin className="h-4 w-4 text-gray-400 mt-0.5 flex-shrink-0" />
              <div>
                <span className="text-gray-500">Lieu:</span>
                <span className="ml-1 text-gray-700">{result.seance_lieu}</span>
              </div>
            </div>
          )}
        </div>

        {/* Vote */}
        {(result.vote_pour !== null || result.vote_contre !== null) && (
          <div className="bg-gray-50 rounded-lg p-3 space-y-2">
            <div className="flex flex-wrap gap-3">
              {result.vote_pour !== null && result.vote_pour !== undefined && (
                <span className="text-sm">
                  <span className="text-gray-500">Pour:</span>
                  <span className="ml-1 font-medium text-emerald-600">{result.vote_pour}</span>
                </span>
              )}
              {result.vote_contre !== null && result.vote_contre !== undefined && (
                <span className="text-sm">
                  <span className="text-gray-500">Contre:</span>
                  <span className="ml-1 font-medium text-red-600">{result.vote_contre}</span>
                </span>
              )}
              {result.vote_abstentions !== null && result.vote_abstentions !== undefined && (
                <span className="text-sm">
                  <span className="text-gray-500">Abstentions:</span>
                  <span className="ml-1 font-medium text-gray-600">{result.vote_abstentions}</span>
                </span>
              )}
            </div>
            {result.vote_resultat && (
              <div className="pt-2 border-t border-gray-200">
                <span className="text-sm text-gray-500">Résultat:</span>
                <span className="ml-1 text-sm font-medium text-indigo-600">{result.vote_resultat}</span>
              </div>
            )}
          </div>
        )}

        {/* Prefecture info */}
        {result.prefecture_date_publication && (
          <div className="text-xs text-gray-500 flex items-center gap-1">
            <Landmark className="h-3 w-3" />
            <span>Publié en préfecture le {formatDateShort(result.prefecture_date_publication)}</span>
          </div>
        )}
      </div>
    )
  }

  // Detailed variant (4 sections)
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-sm">
        {/* Informations générales */}
        <div className="space-y-2">
          <h4 className="font-medium text-gray-700 text-xs uppercase tracking-wide mb-3">Informations générales</h4>
          {result.collectivite && (
            <div className="flex items-start gap-2">
              <Building2 className="h-4 w-4 text-gray-400 mt-0.5 flex-shrink-0" />
              <div>
                <span className="text-gray-500">Collectivité:</span>
                <span className="ml-1 text-gray-700">{result.collectivite}</span>
              </div>
            </div>
          )}
          {result.coll_siret && (
            <div className="flex items-start gap-2">
              <Hash className="h-4 w-4 text-gray-400 mt-0.5 flex-shrink-0" />
              <div>
                <span className="text-gray-500">SIRET:</span>
                <span className="ml-1 text-gray-700 font-mono text-xs">{result.coll_siret}</span>
              </div>
            </div>
          )}
          {result.delib_id && (
            <div className="flex items-start gap-2">
              <FileText className="h-4 w-4 text-gray-400 mt-0.5 flex-shrink-0" />
              <div>
                <span className="text-gray-500">ID Délibération:</span>
                <span className="ml-1 text-gray-700 font-mono text-xs">{result.delib_id}</span>
              </div>
            </div>
          )}
          {result.decision && (
            <div className="flex items-start gap-2">
              <FileText className="h-4 w-4 text-gray-400 mt-0.5 flex-shrink-0" />
              <div>
                <span className="text-gray-500">Décision:</span>
                <span className="ml-1 text-gray-700 font-mono text-xs break-all">{result.decision}</span>
              </div>
            </div>
          )}
          {result.date_convocation && (
            <div className="flex items-start gap-2">
              <Calendar className="h-4 w-4 text-gray-400 mt-0.5 flex-shrink-0" />
              <div>
                <span className="text-gray-500">Convocation:</span>
                <span className="ml-1 text-gray-700">{formatDate(result.date_convocation)}</span>
              </div>
            </div>
          )}
          {result.seance_lieu && (
            <div className="flex items-start gap-2">
              <MapPin className="h-4 w-4 text-gray-400 mt-0.5 flex-shrink-0" />
              <div>
                <span className="text-gray-500">Lieu:</span>
                <span className="ml-1 text-gray-700">{result.seance_lieu}</span>
              </div>
            </div>
          )}
        </div>

        {/* Commission & Rapporteur */}
        <div className="space-y-2">
          <h4 className="font-medium text-gray-700 text-xs uppercase tracking-wide mb-3">Commission & Rapporteur</h4>
          {result.commission && (
            <div className="flex items-start gap-2">
              <Users2 className="h-4 w-4 text-gray-400 mt-0.5 flex-shrink-0" />
              <div>
                <span className="text-gray-500">Commission:</span>
                <span className="ml-1 text-gray-700">{result.commission}</span>
                {result.commission_avis && (
                  <span className="ml-1 text-xs text-gray-400">({result.commission_avis})</span>
                )}
              </div>
            </div>
          )}
          {result.commission_date_reunion && (
            <div className="flex items-start gap-2">
              <Calendar className="h-4 w-4 text-gray-400 mt-0.5 flex-shrink-0" />
              <div>
                <span className="text-gray-500">Date de réunion:</span>
                <span className="ml-1 text-gray-700">{formatDate(result.commission_date_reunion)}</span>
              </div>
            </div>
          )}
          {result.rapporteur && (
            <div className="flex items-start gap-2">
              <Gavel className="h-4 w-4 text-gray-400 mt-0.5 flex-shrink-0" />
              <div>
                <span className="text-gray-500">Rapporteur:</span>
                <span className="ml-1 text-gray-700">{result.rapporteur}</span>
              </div>
            </div>
          )}
          {result.matiere && (
            <div className="flex items-start gap-2">
              <FileText className="h-4 w-4 text-gray-400 mt-0.5 flex-shrink-0" />
              <div>
                <span className="text-gray-500">Matière:</span>
                <span className="ml-1 text-gray-700">{result.matiere}</span>
              </div>
            </div>
          )}

          {/* Prefecture info */}
          {(result.prefecture_id || result.prefecture_date_publication) && (
            <div className="mt-4 pt-3 border-t border-gray-100">
              <h5 className="font-medium text-gray-600 text-xs uppercase tracking-wide mb-2">Préfecture</h5>
              {result.prefecture_id && (
                <div className="flex items-start gap-2">
                  <Landmark className="h-4 w-4 text-gray-400 mt-0.5 flex-shrink-0" />
                  <div>
                    <span className="text-gray-500">ID:</span>
                    <span className="ml-1 text-gray-700 font-mono text-xs">{result.prefecture_id}</span>
                  </div>
                </div>
              )}
              {result.prefecture_date_envoi && (
                <div className="text-xs text-gray-500 mt-1">
                  Envoyé: {formatDateShort(result.prefecture_date_envoi)}
                </div>
              )}
              {result.prefecture_date_reception && (
                <div className="text-xs text-gray-500">
                  Reçu: {formatDateShort(result.prefecture_date_reception)}
                </div>
              )}
              {result.prefecture_date_publication && (
                <div className="text-xs text-gray-500">
                  Publié: {formatDateShort(result.prefecture_date_publication)}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Détails du vote */}
        <div className="space-y-2">
          <h4 className="font-medium text-gray-700 text-xs uppercase tracking-wide mb-3">Détails du vote</h4>
          <div className="bg-white rounded-lg p-3 border border-gray-200 space-y-2">
            {(result.vote_effectif || result.membres_en_exercice) && (
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Membres en exercice</span>
                <span className="font-medium text-gray-700">{result.vote_effectif || result.membres_en_exercice}</span>
              </div>
            )}
            {result.membres_presents_count !== undefined && (
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Présents</span>
                <span className="font-medium text-gray-700">{result.membres_presents_count}</span>
              </div>
            )}
            {result.membres_absents_count !== undefined && result.membres_absents_count > 0 && (
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Absents</span>
                <span className="font-medium text-gray-700">{result.membres_absents_count}</span>
              </div>
            )}
            {result.vote_reel && (
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Votants</span>
                <span className="font-medium text-gray-700">{result.vote_reel}</span>
              </div>
            )}
            <div className="border-t border-gray-100 my-2"></div>
            {result.vote_pour !== null && result.vote_pour !== undefined && (
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Pour</span>
                <span className="font-medium text-emerald-600">{result.vote_pour}</span>
              </div>
            )}
            {result.vote_contre !== null && result.vote_contre !== undefined && (
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Contre</span>
                <span className="font-medium text-red-600">{result.vote_contre}</span>
              </div>
            )}
            {result.vote_abstentions !== null && result.vote_abstentions !== undefined && (
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Abstentions</span>
                <span className="font-medium text-gray-600">{result.vote_abstentions}</span>
              </div>
            )}
            {result.vote_resultat && (
              <>
                <div className="border-t border-gray-100 my-2"></div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Résultat</span>
                  <span className="font-medium text-indigo-600">{result.vote_resultat}</span>
                </div>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Contexte juridique - Section dépliable */}
      {(result.contexte_juridique || result.contenu_textuel) && (
        <div className="border-t border-gray-100 pt-4">
          <button
            onClick={() => setShowConsiderants(!showConsiderants)}
            className="flex items-center gap-2 text-sm font-medium text-gray-700 hover:text-gray-900 transition-colors w-full text-left"
          >
            <Scale className="h-4 w-4 text-gray-400" />
            <span>Contexte juridique et considérants</span>
            <ChevronDown className={`h-4 w-4 text-gray-400 ml-auto transition-transform duration-200 ${showConsiderants ? 'rotate-180' : ''}`} />
          </button>

          {showConsiderants && (
            <div className="mt-4 space-y-4 animate-in slide-in-from-top-2 duration-200">
              {result.contexte_juridique && (
                <div className="bg-gray-50 rounded-lg p-4">
                  <h5 className="font-medium text-gray-700 text-xs uppercase tracking-wide mb-2">Contexte juridique</h5>
                  <p className="text-sm text-gray-600 whitespace-pre-wrap leading-relaxed max-h-64 overflow-y-auto">
                    {result.contexte_juridique}
                  </p>
                </div>
              )}
              {result.contenu_textuel && (
                <div className="bg-gray-50 rounded-lg p-4">
                  <h5 className="font-medium text-gray-700 text-xs uppercase tracking-wide mb-2">Contenu textuel</h5>
                  <p className="text-sm text-gray-600 whitespace-pre-wrap leading-relaxed max-h-64 overflow-y-auto">
                    {result.contenu_textuel}
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Membres présents et absents - Section dépliable */}
      {((result.membres_presents && result.membres_presents.length > 0) || (result.membres_absents && result.membres_absents.length > 0)) && (
        <div className="border-t border-gray-100 pt-4">
          <button
            onClick={() => setShowMembres(!showMembres)}
            className="flex items-center gap-2 text-sm font-medium text-gray-700 hover:text-gray-900 transition-colors w-full text-left"
          >
            <Users className="h-4 w-4 text-gray-400" />
            <span>
              Membres ({result.membres_presents?.length || 0} présent{(result.membres_presents?.length || 0) > 1 ? 's' : ''}, {result.membres_absents?.length || 0} absent{(result.membres_absents?.length || 0) > 1 ? 's' : ''})
            </span>
            <ChevronDown className={`h-4 w-4 text-gray-400 ml-auto transition-transform duration-200 ${showMembres ? 'rotate-180' : ''}`} />
          </button>

          {showMembres && (
            <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4 animate-in slide-in-from-top-2 duration-200">
              {result.membres_presents && result.membres_presents.length > 0 && (
                <div className="bg-emerald-50 rounded-lg p-4">
                  <h5 className="font-medium text-emerald-700 text-xs uppercase tracking-wide mb-3 flex items-center gap-2">
                    <Users className="h-4 w-4" />
                    Présents ({result.membres_presents.length})
                  </h5>
                  <ul className="text-sm text-emerald-800 space-y-1 max-h-48 overflow-y-auto">
                    {result.membres_presents.map((membre, index) => (
                      <li key={index} className="pl-2 border-l-2 border-emerald-200">
                        {membre}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {result.membres_absents && result.membres_absents.length > 0 && (
                <div className="bg-gray-50 rounded-lg p-4">
                  <h5 className="font-medium text-gray-700 text-xs uppercase tracking-wide mb-3 flex items-center gap-2">
                    <Users className="h-4 w-4" />
                    Absents ({result.membres_absents.length})
                  </h5>
                  <ul className="text-sm text-gray-600 space-y-1 max-h-48 overflow-y-auto">
                    {result.membres_absents.map((membre, index) => (
                      <li key={index} className="pl-2 border-l-2 border-gray-200">
                        {membre}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
