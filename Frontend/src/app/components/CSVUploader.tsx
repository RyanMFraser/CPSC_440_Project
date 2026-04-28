import React from 'react'
import CSVFileDrop from './CSVFileDrop'

const CSVUploader: React.FC = () => {
  return (
    <div className="csv-uploader">
      <header className="csv-uploader__header">
        <h2>Upload Shot Data</h2>
        <p className="csv-uploader__subtitle">Import CSV files containing shot data (X, Y, Club)</p>
      </header>

      <div className="csv-uploader__body">
        <CSVFileDrop />
      </div>
    </div>
  )
}

export default CSVUploader
