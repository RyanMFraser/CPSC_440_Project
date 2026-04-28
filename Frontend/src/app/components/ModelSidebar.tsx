import { useEffect, useState } from 'react'
import apiClient from '../../services/api'
import CollapsibleListSection from './CollapsibleListSection'

type IdPayload = {
  data_ids?: string[]
  gmm_ids?: string[]
  mdp_ids?: string[]
}

function ModelSidebar() {
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
        if (isMounted) {
          setError(fetchError?.message ?? 'Failed to load IDs')
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
  }, [])

  return (
    <aside className="model-sidebar">
      <div className="model-sidebar__header">
        <h2>Model Library</h2>
        <p>Click a category to expand or collapse its IDs.</p>
      </div>

      <div className="model-sidebar__sections">
        <CollapsibleListSection
          title="data_ids"
          items={ids.data_ids ?? []}
          count={ids.data_ids?.length ?? 0}
          loading={loading}
          error={error}
        />
        <CollapsibleListSection
          title="gmm_ids"
          items={ids.gmm_ids ?? []}
          count={ids.gmm_ids?.length ?? 0}
          loading={loading}
          error={error}
        />
        <CollapsibleListSection
          title="mdp_ids"
          items={ids.mdp_ids ?? []}
          count={ids.mdp_ids?.length ?? 0}
          loading={loading}
          error={error}
        />
      </div>
    </aside>
  )
}

export default ModelSidebar
