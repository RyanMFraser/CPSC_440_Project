import React from 'react'
import CSVFileDrop from './CSVFileDrop'
import SectionHeader from './SectionHeader'

const CSVUploader: React.FC = () => {
  return (
    <div className="csv-uploader">
      <div className="csv-uploader__header">
        <SectionHeader
          mainText="Upload Shot Data"
          subText="Import CSV files containing shot data (X, Y, Club)"
        />
      </div>

      <div className="csv-uploader__body">
        <CSVFileDrop />
      </div>
    </div>
  )
}

export default CSVUploader
