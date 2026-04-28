import React, { useEffect, useRef, useState } from 'react'
import apiClient from '../../services/api'
import GreenButton from './GreenButton'
import SectionHeader from './SectionHeader'

type GMMParams = {
  gmm_id: string
  weights: number[]
  means: number[][]
  covariances: number[][][]
}

const X_MIN = -50
const X_MAX = 50
const Y_MIN = 0
const Y_MAX = 250

function multivariateNormalPdf(x: number[], mean: number[], cov: number[][]) {
  // 2D multivariate normal pdf
  const det = cov[0][0] * cov[1][1] - cov[0][1] * cov[1][0]
  if (det <= 0) return 0
  const inv00 = cov[1][1] / det
  const inv01 = -cov[0][1] / det
  const inv10 = -cov[1][0] / det
  const inv11 = cov[0][0] / det
  const dx0 = x[0] - mean[0]
  const dx1 = x[1] - mean[1]
  const mahal = dx0 * (inv00 * dx0 + inv01 * dx1) + dx1 * (inv10 * dx0 + inv11 * dx1)
  const norm = 1 / (2 * Math.PI * Math.sqrt(det))
  return norm * Math.exp(-0.5 * mahal)
}

function computeDensityGrid(params: GMMParams, w: number, h: number) {
  const { weights, means, covariances } = params
  const nx = w
  const ny = h
  const xs = new Float64Array(nx)
  const ys = new Float64Array(ny)
  for (let i = 0; i < nx; i++) xs[i] = X_MIN + (i / (nx - 1)) * (X_MAX - X_MIN)
  for (let j = 0; j < ny; j++) ys[j] = Y_MIN + (j / (ny - 1)) * (Y_MAX - Y_MIN)

  const density = new Float64Array(nx * ny)
  let vmin = Infinity
  let vmax = -Infinity
  for (let j = 0; j < ny; j++) {
    for (let i = 0; i < nx; i++) {
      const x = xs[i]
      const y = ys[j]
      let val = 0
      for (let k = 0; k < weights.length; k++) {
        val += weights[k] * multivariateNormalPdf([x, y], means[k], covariances[k])
      }
      density[j * nx + i] = val
      if (val > 0 && val < vmin) vmin = val
      if (val > vmax) vmax = val
    }
  }

  if (!isFinite(vmin) || !isFinite(vmax) || vmax <= 0) {
    vmin = 1e-12
    vmax = 1e-6
  }

  return { density, nx, ny, vmin, vmax }
}

function colormapCoolWarm(t: number) {
  // simple approximation between blue and red
  const r = Math.max(0, Math.min(255, Math.round(255 * t)))
  const g = Math.max(0, Math.min(255, Math.round(255 * (1 - Math.abs(t - 0.5) * 2))))
  const b = Math.max(0, Math.min(255, Math.round(255 * (1 - t))))
  return [r, g, b]
}

function drawHeatmapToCanvas(canvas: HTMLCanvasElement, params: GMMParams) {
  const dpr = window.devicePixelRatio || 1
  const width = Math.max(200, Math.min(600, Math.floor(canvas.clientWidth)))
  const height = Math.max(200, Math.min(600, Math.floor(canvas.clientHeight)))
  canvas.width = Math.floor(width * dpr)
  canvas.height = Math.floor(height * dpr)
  canvas.style.width = `${width}px`
  canvas.style.height = `${height}px`
  const ctx = canvas.getContext('2d')!
  ctx.scale(dpr, dpr)

  const gridW = 200
  const gridH = 200
  const { density, nx, ny, vmin, vmax } = computeDensityGrid(params, gridW, gridH)

  // prepare image data
  const img = ctx.createImageData(nx, ny)
  const logVmin = Math.log(vmin)
  const logVmax = Math.log(vmax)
  const logRange = logVmax - logVmin || 1

  for (let j = 0; j < ny; j++) {
    for (let i = 0; i < nx; i++) {
      const idx = j * nx + i
      const val = density[idx]
      const logVal = val > 0 ? Math.log(val) : logVmin
      let t = (logVal - logVmin) / logRange
      t = Math.max(0, Math.min(1, t))
      const [r, g, b] = colormapCoolWarm(t)
      const p = (j * nx + i) * 4
      img.data[p] = r
      img.data[p + 1] = g
      img.data[p + 2] = b
      img.data[p + 3] = Math.round(255 * (0.6 * t + 0.2)) // alpha scaled
    }
  }

  // draw image scaled to canvas size
  // create temporary canvas to put image data and scale
  const tmp = document.createElement('canvas')
  tmp.width = nx
  tmp.height = ny
  const tctx = tmp.getContext('2d')!
  tctx.putImageData(img, 0, 0)
  ctx.clearRect(0, 0, width, height)
  // draw scaled heatmap
  ctx.drawImage(tmp, 0, 0, width, height)

  // optionally draw contour-like lines by overlaying thresholds
  const levels = 6
  for (let li = 1; li <= levels; li++) {
    const level = Math.exp(logVmin + (li / (levels + 1)) * logRange)
    ctx.beginPath()
    ctx.strokeStyle = 'rgba(0,0,0,' + (0.15 + li * 0.05) + ')'
    ctx.lineWidth = 1
    // crude contour: draw isocontour by plotting pixels where density crosses level
    // We'll draw small rectangles at threshold crossings to simulate contour lines
    const threshold = level
    const scaleX = width / nx
    const scaleY = height / ny
    for (let j = 0; j < ny - 1; j++) {
      for (let i = 0; i < nx - 1; i++) {
        const v = density[j * nx + i]
        const right = density[j * nx + (i + 1)]
        const down = density[(j + 1) * nx + i]
        if ((v >= threshold && right < threshold) || (v < threshold && right >= threshold) || (v >= threshold && down < threshold) || (v < threshold && down >= threshold)) {
          const cx = i * scaleX
          const cy = j * scaleY
          ctx.rect(cx, cy, Math.max(1, Math.round(scaleX)), Math.max(1, Math.round(scaleY)))
        }
      }
    }
    ctx.stroke()
    ctx.fillStyle = 'rgba(0,0,0,0)'
  }
}

const GmmGallery: React.FC<{ gmmIds?: string[] }> = ({ gmmIds = [] }) => {
  const [models, setModels] = useState<GMMParams[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const canvasesRef = useRef<Record<string, HTMLCanvasElement | null>>({})
  const [activeIndex, setActiveIndex] = useState(0)

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

  useEffect(() => {
    // draw canvases when models change
    models.forEach((m, idx) => {
      const canvas = canvasesRef.current[m.gmm_id]
      if (canvas) drawHeatmapToCanvas(canvas, m)
    })
  }, [models])

  return (
    <div className="gmm-gallery">
      <SectionHeader
        mainText="GMM Heatmap Viewer"
        subText="Generate and browse log-scaled density heatmaps for the selected GMM IDs."
      />
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
        <GreenButton onClick={generate} disabled={loading || !gmmIds || gmmIds.length === 0}>
          {loading ? 'Generating...' : 'Generate Heatmaps'}
        </GreenButton>
        <div style={{ marginLeft: 8, color: '#475569' }}>{gmmIds?.length ?? 0} selected</div>
      </div>

      {error && <div style={{ color: '#b91c1c', marginBottom: 8 }}>{error}</div>}

      {models.length === 0 ? (
        <div style={{ color: '#64748b' }}>No heatmaps generated yet. Click "Generate Heatmaps" to create images for the selected GMMs.</div>
      ) : (
        <>
          <div className="gmm-gallery__viewer">
            <div className="gmm-gallery__title">GMM Heatmap Viewer</div>
            <div className="gmm-gallery__canvas-wrap">
              {models[activeIndex] ? (
                <canvas
                  ref={(el) => (canvasesRef.current[models[activeIndex].gmm_id] = el)}
                  style={{ width: '100%', height: 420, borderRadius: 8, display: 'block' }}
                />
              ) : null}
            </div>
            <div style={{ marginTop: 8, color: '#475569' }}>{models[activeIndex]?.gmm_id}</div>
          </div>

          <div className="gmm-gallery__thumbs">
            {models.map((m, idx) => (
              <button
                key={m.gmm_id}
                type="button"
                className={`gmm-thumb ${idx === activeIndex ? 'is-active' : ''}`}
                onClick={() => setActiveIndex(idx)}
                style={{ border: 'none', background: 'transparent', padding: 6, cursor: 'pointer' }}
              >
                <canvas
                  ref={(el) => (canvasesRef.current[m.gmm_id] = el)}
                  width={120}
                  height={80}
                  style={{ width: 120, height: 80, borderRadius: 6, display: 'block', boxShadow: idx === activeIndex ? '0 4px 10px rgba(2,6,23,0.12)' : 'none' }}
                />
                <div style={{ fontSize: 12, color: '#243b53', marginTop: 6 }}>{m.gmm_id}</div>
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  )
}

export default GmmGallery
