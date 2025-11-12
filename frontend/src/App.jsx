import React, { useState, useEffect } from 'react'
import DeedCard from './components/DeedCard'
import './index.css'

function App() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      setError(null)

      // Load from public folder (copy data there using sync-data.js)
      const response = await fetch('/step5_final_integrated.json')

      if (!response.ok) {
        throw new Error(
          'Data file not found. Run: node sync-data.js from the frontend folder'
        )
      }

      const jsonData = await response.json()
      setData(jsonData)
    } catch (err) {
      setError(err.message)
      console.error('Error loading data:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container">
      <header>
        <h1>🗺️ Deed Geocoding Results</h1>
        {data?.metadata?.quality_report && (
          <div className="header-stats">
            <div className="stat-card">
              <div className="stat-label">Total Deeds</div>
              <div className="stat-value">{data.metadata.quality_report.total_deeds}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Geocoded</div>
              <div className="stat-value">{data.metadata.quality_report.geocoded_count}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Success Rate</div>
              <div className="stat-value">{data.metadata.quality_report.geocoded_rate}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">With Streets</div>
              <div className="stat-value">{data.metadata.quality_report.with_streets_count}</div>
            </div>
          </div>
        )}
      </header>

      <main className="deed-grid">
        {loading && <div className="loading">Loading data...</div>}

        {error && (
          <div className="error">
            <h3>Error Loading Data</h3>
            <p>{error}</p>
            <p style={{ marginTop: '8px', fontSize: '12px' }}>
              Make sure you've run <code>python -m deeds_pipeline.step5_integration</code> first.
            </p>
          </div>
        )}

        {!loading && !error && (!data?.deeds || data.deeds.length === 0) && (
          <div className="no-data">
            <h2>No deed data found</h2>
            <p>Run the pipeline steps first to generate data.</p>
          </div>
        )}

        {!loading && !error && data?.deeds && (
          data.deeds.map((deed, index) => (
            <DeedCard key={deed.deed_id || index} deed={deed} />
          ))
        )}
      </main>
    </div>
  )
}

export default App
