import React, { useState } from 'react'
import apiClient from '../../services/api'
import GreenButton from './GreenButton'
import SectionHeader from './SectionHeader'
import DispersionHeatMap from './DispersionHeatMap'

type GMMParams = {
  gmm_id: string
  weights: number[]
  means: number[][]
  covariances: number[][][]
}

type SamplePointsById = Record<string, number[][]>
type SampleCountById = Record<string, string>
type SampleLoadingById = Record<string, boolean>
type SampleErrorById = Record<string, string | null>

const GmmGallery: React.FC<{ gmmIds?: string[] }> = ({ gmmIds = [] }) => {
  const [models, setModels] = useState<GMMParams[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [activeIndex, setActiveIndex] = useState(0)
  const [samplesById, setSamplesById] = useState<SamplePointsById>({})
  const [sampleCountById, setSampleCountById] = useState<SampleCountById>({})
  const [sampleLoadingById, setSampleLoadingById] = useState<SampleLoadingById>({})
  const [sampleErrorById, setSampleErrorById] = useState<SampleErrorById>({})

  const hasModels = models.length > 0
  const activeModel = hasModels ? models[activeIndex] : null
  const activeGmmId = activeModel?.gmm_id ?? ''
  const activeSampleCount = activeGmmId ? sampleCountById[activeGmmId] ?? '100' : '100'
  const activeSamples = activeGmmId ? samplesById[activeGmmId] ?? [] : []
  const activeSampleLoading = activeGmmId ? sampleLoadingById[activeGmmId] ?? false : false
  const activeSampleError = activeGmmId ? sampleErrorById[activeGmmId] ?? null : null

  const goPrevious = () => {
    if (!hasModels) return
    setActiveIndex((current) => (current - 1 + models.length) % models.length)
  }

  const goNext = () => {
    if (!hasModels) return
    setActiveIndex((current) => (current + 1) % models.length)
  }

  // Do NOT auto-fetch params on selection change. Generate only when user clicks the button.
  const generate = async () => {
    if (!gmmIds || gmmIds.length === 0) {
      setError('No GMM IDs selected')
      return
    }
    setLoading(true)
    setError(null)
    setModels([])
    try {
      const results: GMMParams[] = []
      for (const id of gmmIds) {
        const res = await apiClient.post('/gmm/params', { gmm_id: id })
        results.push({
          gmm_id: res.gmm_id,
          weights: res.weights,
          means: res.means,
          covariances: res.covariances,
        })
      }
      setModels(results)
      setActiveIndex(0)
      setSamplesById({})
      setSampleCountById({})
      setSampleLoadingById({})
      setSampleErrorById({})
    } catch (err: any) {
      console.error('Failed fetching GMM params:', err)
      setError(err?.message ?? String(err))
    } finally {
      setLoading(false)
    }
  }

  const updateSampleCount = (gmmId: string, value: string) => {
    setSampleCountById((current) => ({ ...current, [gmmId]: value }))
  }

  const requestSamples = async (gmmId: string) => {
    const rawCount = sampleCountById[gmmId] ?? '100'
    const parsedCount = Number.parseInt(rawCount, 10)

    if (!Number.isInteger(parsedCount) || parsedCount < 1 || parsedCount > 10000) {
      setSampleErrorById((current) => ({
        ...current,
        [gmmId]: 'Number of samples must be an integer between 1 and 10000.',
      }))
      return
    }

    setSampleLoadingById((current) => ({ ...current, [gmmId]: true }))
    setSampleErrorById((current) => ({ ...current, [gmmId]: null }))

    try {
      const res = await apiClient.post('/gmm/sample', { gmm_id: gmmId, n_samples: parsedCount })
      setSamplesById((current) => ({ ...current, [gmmId]: res.samples ?? [] }))
      setSampleCountById((current) => ({ ...current, [gmmId]: String(parsedCount) }))
    } catch (err: any) {
      console.error(`Failed sampling for ${gmmId}:`, err)
      setSampleErrorById((current) => ({
        ...current,
        [gmmId]: err?.message ?? 'Failed to sample points.',
      }))
    } finally {
      setSampleLoadingById((current) => ({ ...current, [gmmId]: false }))
    }
  }

  return (
    <div className="gmm-gallery">
      <SectionHeader
        mainText="GMM Heatmap Gallery"
        subText="Select one or more GMM IDs on the left, then click Generate Heatmaps to build log-scaled density plots and browse through them here."
      />
      <div className="gmm-gallery__controls">
        <GreenButton onClick={generate} disabled={loading || !gmmIds || gmmIds.length === 0}>
          {loading ? 'Generating...' : 'Generate Heatmaps'}
        </GreenButton>
        <div className="gmm-gallery__selected-count">{gmmIds?.length ?? 0} selected</div>
      </div>

      {error && <div style={{ color: '#b91c1c', marginBottom: 8 }}>{error}</div>}

      {!hasModels ? (
        <div className="gmm-gallery__empty">
          No heatmaps generated yet. Click "Generate Heatmaps" to create images for the selected GMMs.
        </div>
      ) : (
        <>
          <div className="gmm-gallery__carousel">
            <button
              type="button"
              className="gmm-gallery__arrow"
              onClick={goPrevious}
              aria-label="Previous heatmap"
              disabled={models.length < 2}
            >
              ‹
            </button>

            <div className="gmm-gallery__viewer">
              {activeModel ? (
              <DispersionHeatMap
                  gmmId={activeModel.gmm_id}
                  weights={activeModel.weights}
                  means={activeModel.means}
                  covariances={activeModel.covariances}
                  samples={activeSamples}
                  height={540}
                />
              ) : null}

              {activeModel ? (
                <div className="gmm-gallery__sample-controls">
                  <label htmlFor={`sample-count-${activeModel.gmm_id}`} className="gmm-gallery__sample-label">
                    Num samples
                  </label>
                  <input
                    id={`sample-count-${activeModel.gmm_id}`}
                    className="gmm-gallery__sample-input"
                    type="number"
                    min={1}
                    max={10000}
                    step={1}
                    value={activeSampleCount}
                    onChange={(e) => updateSampleCount(activeModel.gmm_id, e.target.value)}
                    disabled={activeSampleLoading}
                  />
                  <GreenButton
                    onClick={() => requestSamples(activeModel.gmm_id)}
                    disabled={activeSampleLoading}
                  >
                    {activeSampleLoading ? 'Sampling...' : 'Sample'}
                  </GreenButton>
                  <div className="gmm-gallery__sample-count-note">
                    {activeSamples.length > 0 ? `${activeSamples.length} sample(s) shown` : 'No samples plotted yet'}
                  </div>
                </div>
              ) : null}

              {activeSampleError ? <div className="gmm-gallery__sample-error">{activeSampleError}</div> : null}

              <div className="gmm-gallery__caption">
                <div className="gmm-gallery__active-id">{activeModel?.gmm_id}</div>
                <div className="gmm-gallery__position">
                  {activeIndex + 1} of {models.length}
                </div>
              </div>
            </div>

            <button
              type="button"
              className="gmm-gallery__arrow"
              onClick={goNext}
              aria-label="Next heatmap"
              disabled={models.length < 2}
            >
              ›
            </button>
          </div>
        </>
      )}
    </div>
  )
}

export default GmmGallery
