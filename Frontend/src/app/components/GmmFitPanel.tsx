import React, { useMemo, useState } from 'react'
import apiClient from '../../services/api'
import GreenButton from './GreenButton'
import SectionHeader from './SectionHeader'

type GmmFitPanelProps = {
  dataIds: string[]
  onFitComplete?: () => void
}

type FitResult = {
  dataId: string
  gmmIds: string[]
  nModels: number
}

const GmmFitPanel: React.FC<GmmFitPanelProps> = ({ dataIds, onFitComplete }) => {
  const [maxComponents, setMaxComponents] = useState(10)
  const [numComponents, setNumComponents] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [results, setResults] = useState<FitResult[]>([])

  const selectedCount = dataIds?.length ?? 0

  const parsedNumComponents = useMemo(() => {
    const trimmed = numComponents.trim()
    if (!trimmed) return null
    const parsed = Number(trimmed)
    if (!Number.isFinite(parsed) || parsed <= 0) return null
    return Math.floor(parsed)
  }, [numComponents])

  const handleFit = async () => {
    if (!dataIds || dataIds.length === 0) {
      setError('No data IDs selected. Select one or more data_ids from the sidebar.')
      return
    }

    setLoading(true)
    setError(null)
    setResults([])

    try {
      const collected: FitResult[] = []

      for (const dataId of dataIds) {
        const payload: Record<string, unknown> = {
          data_id: dataId,
          max_components: maxComponents,
        }
        if (parsedNumComponents !== null) {
          payload.num_components = parsedNumComponents
        }

        const response = await apiClient.post('/gmm/fit', payload)
        collected.push({
          dataId,
          gmmIds: response?.gmm_ids ?? [],
          nModels: response?.n_models ?? 0,
        })
      }

      setResults(collected)
      if (onFitComplete) onFitComplete()
    } catch (fitErr: any) {
      setError(fitErr?.message ?? String(fitErr))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="gmm-fit-panel">
      <SectionHeader
        mainText="Fit Gaussian Mixture Models"
        subText="Use selected data_ids to fit GMMs. New gmm_ids will appear in the sidebar after fitting."
      />

      <div className="gmm-fit-panel__controls">
        <label className="field">
          <span className="field__label">Max Components</span>
          <input
            className="field__input"
            type="number"
            min={1}
            max={25}
            value={maxComponents}
            onChange={(e) => setMaxComponents(Math.max(1, Math.min(25, Number(e.target.value || 1))))}
          />
        </label>

        <label className="field">
          <span className="field__label">Fixed Components (optional)</span>
          <input
            className="field__input"
            type="number"
            min={1}
            max={25}
            value={numComponents}
            onChange={(e) => setNumComponents(e.target.value)}
            placeholder="Leave empty for model selection"
          />
        </label>
      </div>

      <div className="gmm-fit-panel__actions">
        <GreenButton onClick={handleFit} disabled={loading || selectedCount === 0}>
          {loading ? 'Fitting...' : 'Fit Selected Data'}
        </GreenButton>
        <div className="gmm-fit-panel__selected">{selectedCount} data_ids selected</div>
      </div>

      {error && <div className="gmm-fit-panel__error">{error}</div>}

      {results.length > 0 && (
        <div className="gmm-fit-panel__results">
          <div className="gmm-fit-panel__results-title">Fit Results</div>
          {results.map((result) => (
            <div key={result.dataId} className="gmm-fit-panel__result-row">
              <div>
                <strong>{result.dataId}</strong> ({result.nModels} model{result.nModels === 1 ? '' : 's'})
              </div>
              <div className="gmm-fit-panel__chips">
                {result.gmmIds.map((id) => (
                  <span key={id} className="gmm-fit-panel__chip">{id}</span>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default GmmFitPanel
