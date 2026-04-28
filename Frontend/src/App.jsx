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
          <section className="hero">
            <h2>Welcome to your React Frontend</h2>
            <p>Edit <code>src/App.jsx</code> to start building your interface.</p>
            <p style={{ fontSize: '0.9em', color: '#666', marginTop: '1em' }}>
              API Base URL: <code>{import.meta.env.VITE_API_URL}</code>
            </p>
          </section>

          <section className="getting-started">
            <h3>Getting Started</h3>
            <ul>
              <li>Use the API client from <code>src/services/api.js</code> to call your backend</li>
              <li>Example: <code>apiClient.get('/endpoint')</code></li>
              <li>Backend running at: <code>http://localhost:8000</code></li>
              <li>View backend API docs at: <code>http://localhost:8000/docs</code></li>
            </ul>
          </section>

          <FrontPage selected={selected} />

          <section className="info">
            <h3>Useful Commands</h3>
            <ul>
              <li><code>npm run dev</code> - Start dev server (port 5173)</li>
              <li><code>npm run build</code> - Build for production</li>
              <li><code>npm run lint</code> - Run ESLint</li>
              <li><code>npm run preview</code> - Preview production build</li>
            </ul>
          </section>
        </div>
      </main>

      <footer>
        <p>Built with React + Vite | Connected to FastAPI Backend</p>
      </footer>
    </div>
  )
}

export default App
