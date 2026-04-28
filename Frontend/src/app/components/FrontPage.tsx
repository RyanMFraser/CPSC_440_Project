import React from 'react'
import CSVUploader from './CSVUploader'
import GmmGallery from './GmmGallery'

type IdPayload = {
  data_ids?: string[]
  gmm_ids?: string[]
  mdp_ids?: string[]
}

const FrontPage: React.FC<{ selected: IdPayload }> = ({ selected }) => {
  return (
    <div className="frontpage-grid">
      <div className="frontpage__left">
        <CSVUploader />
      </div>

      <div className="frontpage__right">
        
        <div style={{ marginTop: 12 }}>
          <GmmGallery gmmIds={selected?.gmm_ids ?? []} />
        </div>
      </div>
    </div>
  )
}

export default FrontPage
