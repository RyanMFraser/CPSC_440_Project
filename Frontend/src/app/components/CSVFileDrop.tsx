import React, { useRef, useState, DragEvent } from 'react'
import apiClient from '../../services/api'
import GreenButton from './GreenButton'

type UploadStatus = 'idle' | 'parsing' | 'uploading' | 'success' | 'error'

function parseCSV(content: string) {
  const lines = content.split(/\r?\n/).filter((l) => l.trim() !== '')
  if (lines.length === 0) return []
  const header = lines[0].split(',').map((h) => h.trim().replace(/^"|"$/g, ''))
  const rows = lines.slice(1).map((line) => {
    // naive CSV split (doesn't handle escaped commas in quotes)
    const cols = line.split(',').map((c) => c.trim().replace(/^"|"$/g, ''))
    const obj: Record<string, any> = {}
    for (let i = 0; i < header.length; i++) {
      obj[header[i]] = cols[i] ?? ''
    }
    return obj
  })
  return rows
}

const CSVFileDrop: React.FC = () => {
  const fileInputRef = useRef<HTMLInputElement | null>(null)
  const [dragActive, setDragActive] = useState(false)
  const [status, setStatus] = useState<UploadStatus>('idle')
  const [message, setMessage] = useState<string | null>(null)
  const [gmmId, setGmmId] = useState('data id here no spaces')
  const [writeMode, setWriteMode] = useState<'overwrite' | 'append'>('append')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [transformedRows, setTransformedRows] = useState<any[] | null>(null)

  const onFiles = (file: File) => {
    setStatus('parsing')
    setMessage(null)
    try {
      const reader = new FileReader()
      reader.onload = (e) => {
        const text = e.target?.result as string
        const rows = parseCSV(text)

        // Basic transform: ensure X and Y are numbers and Club exists
        const transformed = rows.map((r: any, i: number) => ({
          X: Number(r.X ?? r.x ?? r.x_coord ?? r['X coord'] ?? 0),
          Y: Number(r.Y ?? r.y ?? r.y_coord ?? r['Y coord'] ?? 0),
          Club: String(r.Club ?? r.club ?? r['Club'] ?? '').trim(),
        }))

        setSelectedFile(file)
        setTransformedRows(transformed)
        setStatus('idle')
        setMessage(`Loaded ${transformed.length} rows. Click Upload to send to ${gmmId}.`)
      }
      reader.readAsText(file)
    } catch (err: any) {
      setStatus('error')
      setMessage(err?.message ?? String(err))
    }
  }

  const handleUpload = async () => {
    if (!transformedRows) {
      setMessage('No file loaded. Please select a CSV file first.')
      return
    }

    setStatus('uploading')
    try {
      await apiClient.post('/data/upload', {
        gmm_id: gmmId,
        rows: transformedRows,
        write_mode: writeMode,
      })

      setStatus('success')
      setMessage(`Uploaded ${transformedRows.length} rows to ${gmmId}`)
      setSelectedFile(null)
      setTransformedRows(null)
    } catch (err: any) {
      setStatus('error')
      setMessage(err?.message ?? String(err))
    }
  }

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    const file = e.dataTransfer.files?.[0]
    if (file) onFiles(file)
  }

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(true)
  }

  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
  }

  const handleClick = () => {
    fileInputRef.current?.click()
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) onFiles(file)
  }

  return (
    <div className="csv-drop__container" style={{ width: '100%' }}>
      <div className="csv-drop__form">
        <div className="field-row">
          <label className="field">
            <span className="field__label">Dataset ID</span>
            <input className="field__input" value={gmmId} onChange={(e) => setGmmId(e.target.value)} />
          </label>

          <label className="field">
            <span className="field__label">Write Mode</span>
            <select className="field__select" value={writeMode} onChange={(e) => setWriteMode(e.target.value as any)}>
              <option value="overwrite">overwrite</option>
              <option value="append">append</option>
            </select>
          </label>
        </div>

        <div
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onClick={handleClick}
          role="button"
          tabIndex={0}
          className={`csv-drop__area ${dragActive ? 'is-dragging' : ''}`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv,text/csv"
            style={{ display: 'none' }}
            onChange={handleFileChange}
          />

          <div className="csv-drop__message">
            <div className="csv-drop__title">Drag & drop a CSV file here</div>
            <div className="csv-drop__subtitle">or click to select</div>
            <div className="csv-drop__hint">Expected columns: <code>X</code>, <code>Y</code>, <code>Club</code></div>
          </div>
        </div>

        <div className="csv-drop__status">
          <strong>Status:</strong> {status}
          {message && <div className="csv-drop__message-text">{message}</div>}
          {transformedRows && (
            <div className="csv-drop__upload">
              <GreenButton onClick={handleUpload} disabled={status === 'uploading'}>
                {status === 'uploading' ? 'Uploading...' : 'Upload CSV'}
              </GreenButton>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default CSVFileDrop
