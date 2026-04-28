import { useState, useEffect } from 'react'
import apiClient from './services/api'
import CSVUploader from './app/components/CSVUploader'
import ModelSidebar from './app/components/ModelSidebar'
import FrontPage from './app/components/FrontPage'
import './App.css'

function App() {
  const [backendStatus, setBackendStatus] = useState('checking')
  const [error, setError] = useState(null)

  // Check if backend is running on component mount
  useEffect(() => {
    const checkBackend = async () => {
      try {
        await apiClient.healthCheck()
        setBackendStatus('connected')
        setError(null)
      } catch (err) {
        setBackendStatus('disconnected')
        setError(err.message)
      }
    }

    checkBackend()
    // Optionally check every 10 seconds
    const interval = setInterval(checkBackend, 10000)
    return () => clearInterval(interval)
  }, [])

  // selection state: allow multiple selections per category
  const [selected, setSelected] = useState({ data_ids: [], gmm_ids: [], mdp_ids: [] })

  const toggleSelected = (category, id) => {
    setSelected((prev) => {
      const prevList = prev[category] ?? []
      const exists = prevList.includes(id)
      const nextList = exists ? prevList.filter((x) => x !== id) : [...prevList, id]
      return { ...prev, [category]: nextList }
    })
  }

  return (
    <div className="app-container">
      <header>
        <h1>Golf Shot Analysis Frontend</h1>
        <p>Backend Status: <strong style={{ color: backendStatus === 'connected' ? 'green' : 'red' }}>
          {backendStatus === 'checking' && '⏳ Checking...'}
          {backendStatus === 'connected' && '✅ Connected'}
          {backendStatus === 'disconnected' && '❌ Disconnected'}
        </strong></p>
        {error && <p style={{ color: 'red', fontSize: '0.9em' }}>Error: {error}</p>}
      </header>

      <main className="app-main">
        <ModelSidebar selected={selected} onToggle={toggleSelected} />

        <div className="app-main__content">

          <FrontPage selected={selected} />

        </div>
      </main>

    </div>
  )
}

export default App
