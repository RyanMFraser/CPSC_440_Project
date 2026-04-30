import React from 'react'
import CSVUploader from './CSVUploader'
import GmmFitPanel from './GmmFitPanel'
import GmmGallery from './GmmGallery'
import MdpPolicyPanel from './MdpPolicyPanel'

type IdPayload = {
  data_ids?: string[]
  gmm_ids?: string[]
  mdp_ids?: string[]
}

const FrontPage: React.FC<{ selected: IdPayload; onFitComplete?: () => void }> = ({ selected, onFitComplete }) => {
  return (
    <div className="frontpage-grid">
      <div className="frontpage__left">
        <CSVUploader />
        <div style={{ marginTop: 12 }}>
          <GmmFitPanel dataIds={selected?.data_ids ?? []} onFitComplete={onFitComplete} />
        </div>
      </div>

      <div className="frontpage__right">
        
        <div style={{ marginTop: 12 }}>
          <GmmGallery gmmIds={selected?.gmm_ids ?? []} />
        </div>

        <div style={{ marginTop: 12 }}>
          <MdpPolicyPanel mdpIds={selected?.mdp_ids ?? []} />
        </div>
      </div>
    </div>
  )
}

export default FrontPage
