import React from 'react'
import CSVUploader from './CSVUploader'

type IdPayload = {
  data_ids?: string[]
  gmm_ids?: string[]
  mdp_ids?: string[]
}

const SelectedItemsPanel: React.FC<{ selected: IdPayload }> = ({ selected }) => {
  const { data_ids = [], gmm_ids = [], mdp_ids = [] } = selected
  return (
    <section style={{ marginTop: 0 }}>
      <h3>Selected Items</h3>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: 12 }}>
        <div>
          <strong>Data IDs</strong>
          <ul>
            {data_ids.map((d) => (
              <li key={d}>{d}</li>
            ))}
            {data_ids.length === 0 && <li style={{ color: '#64748b' }}>None selected</li>}
          </ul>
        </div>

        <div>
          <strong>GMM IDs</strong>
          <ul>
            {gmm_ids.map((d) => (
              <li key={d}>{d}</li>
            ))}
            {gmm_ids.length === 0 && <li style={{ color: '#64748b' }}>None selected</li>}
          </ul>
        </div>

        <div>
          <strong>MDP IDs</strong>
          <ul>
            {mdp_ids.map((d) => (
              <li key={d}>{d}</li>
            ))}
            {mdp_ids.length === 0 && <li style={{ color: '#64748b' }}>None selected</li>}
          </ul>
        </div>
      </div>
    </section>
  )
}

const FrontPage: React.FC<{ selected: IdPayload }> = ({ selected }) => {
  return (
    <div className="frontpage-grid">
      <div className="frontpage__left">
        <CSVUploader />
      </div>

      <div className="frontpage__right">
        <SelectedItemsPanel selected={selected} />
      </div>
    </div>
  )
}

export default FrontPage
