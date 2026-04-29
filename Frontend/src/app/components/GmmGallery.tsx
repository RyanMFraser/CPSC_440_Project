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

const GmmGallery: React.FC<{ gmmIds?: string[] }> = ({ gmmIds = [] }) => {
  const [models, setModels] = useState<GMMParams[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [activeIndex, setActiveIndex] = useState(0)

  const hasModels = models.length > 0
  const activeModel = hasModels ? models[activeIndex] : null

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
    } catch (err: any) {
      console.error('Failed fetching GMM params:', err)
      setError(err?.message ?? String(err))
    } finally {
      setLoading(false)
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
                  height={540}
                />
              ) : null}

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
