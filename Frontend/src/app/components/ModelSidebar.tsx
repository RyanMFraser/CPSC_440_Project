import { useEffect, useState } from 'react'
import apiClient from '../../services/api'
import CollapsibleListSection from './CollapsibleListSection'

type IdPayload = {
  data_ids?: string[]
  gmm_ids?: string[]
  mdp_ids?: string[]
}

type ModelSidebarProps = {
  selected?: IdPayload
  onToggle?: (category: keyof IdPayload, id: string) => void
  refreshKey?: number
}

function ModelSidebar({ selected = { data_ids: [], gmm_ids: [], mdp_ids: [] }, onToggle, refreshKey = 0 }: ModelSidebarProps) {
  const [ids, setIds] = useState<IdPayload>({ data_ids: [], gmm_ids: [], mdp_ids: [] })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let isMounted = true

    const fetchIds = async () => {
      try {
        setLoading(true)
        const response = (await apiClient.getIds()) as IdPayload
        if (isMounted) {
          setIds({
            data_ids: response.data_ids ?? [],
            gmm_ids: response.gmm_ids ?? [],
            mdp_ids: response.mdp_ids ?? [],
          })
          setError(null)
        }
      } catch (fetchError: any) {
        console.error('apiClient.getIds failed:', fetchError)
        // Try a direct fetch fallback to get more details / recover
        try {
          const base = import.meta.env.VITE_API_URL || 'http://localhost:8000'
          const res = await fetch(`${base}/ids`, { method: 'GET', mode: 'cors' })
          if (!res.ok) throw new Error(`Fallback GET failed: ${res.status} ${res.statusText}`)
          const json = await res.json()
          if (isMounted) {
            setIds({
              data_ids: json.data_ids ?? [],
              gmm_ids: json.gmm_ids ?? [],
              mdp_ids: json.mdp_ids ?? [],
            })
            setError(null)
          }
        } catch (fallbackErr: any) {
          console.error('Fallback fetch /ids failed:', fallbackErr)
          if (isMounted) {
            setError((fetchError && fetchError.message) || (fallbackErr && fallbackErr.message) || 'Failed to load IDs')
          }
        }
      } finally {
        if (isMounted) {
          setLoading(false)
        }
      }
    }

    fetchIds()

    return () => {
      isMounted = false
    }
  }, [refreshKey])

  return (
    <aside className="model-sidebar">
      <div className="model-sidebar__header">
        <h2>Model Library</h2>
        <p>Click a category to expand or collapse its IDs.</p>
      </div>

      <div className="model-sidebar__sections">
        <CollapsibleListSection
          title="Datasets"
          category="data_ids"
          items={ids.data_ids ?? []}
          selected={selected.data_ids ?? []}
          count={ids.data_ids?.length ?? 0}
          loading={loading}
          error={error}
          onToggle={(cat, id) => onToggle && onToggle('data_ids', id)}
        />
        <CollapsibleListSection
          title="Fitted Clubs"
          category="gmm_ids"
          items={ids.gmm_ids ?? []}
          selected={selected.gmm_ids ?? []}
          count={ids.gmm_ids?.length ?? 0}
          loading={loading}
          error={error}
          onToggle={(cat, id) => onToggle && onToggle('gmm_ids', id)}
        />
        <CollapsibleListSection
          title="Solved Holes"
          category="mdp_ids"
          items={ids.mdp_ids ?? []}
          selected={selected.mdp_ids ?? []}
          count={ids.mdp_ids?.length ?? 0}
          loading={loading}
          error={error}
          onToggle={(cat, id) => onToggle && onToggle('mdp_ids', id)}
        />
      </div>
    </aside>
  )
}

export default ModelSidebar
