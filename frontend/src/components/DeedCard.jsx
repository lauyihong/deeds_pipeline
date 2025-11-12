import React, { useEffect, useRef } from 'react'
import MapComponent from './MapComponent'
import StreetsList from './StreetsList'

function DeedCard({ deed }) {
  const validCount = deed.validated_streets?.length || 0
  const invalidCount = deed.invalid_streets?.length || 0
  const confidence = deed.cluster_center_lat ? deed.confidence : 0

  return (
    <div className="deed-card">
      <div className="deed-header">
        <div>
          <div className="deed-title">Deed {deed.deed_id}</div>
          <div className="deed-county">{deed.county}</div>
        </div>
        <div style={{ textAlign: 'right', fontSize: '12px' }}>
          <div>✓ {validCount} validated</div>
          <div>✗ {invalidCount} invalid</div>
        </div>
      </div>

      <div className="deed-content">
        <MapComponent deed={deed} />

        <div className="info-panels">
          <div className="info-panel">
            <div className="panel-header">✓ Validated Streets ({validCount})</div>
            <StreetsList
              streets={deed.validated_streets || []}
              isValid={true}
            />
          </div>

          <div className="info-panel">
            <div className="panel-header">✗ Invalid Streets ({invalidCount})</div>
            <StreetsList
              streets={deed.invalid_streets || []}
              isValid={false}
            />
          </div>

          {deed.cluster_center_lat && (
            <div className="location-info">
              <h4>📍 Final Location</h4>
              <div className="location-detail">
                <strong>Town:</strong> {deed.primary_town}
              </div>
              <div className="location-detail">
                <strong>Address:</strong> {deed.final_address || 'N/A'}
              </div>
              <div className="location-detail">
                <strong>Coordinates:</strong>{' '}
                {deed.cluster_center_lat.toFixed(6)}, {deed.cluster_center_lon.toFixed(6)}
              </div>
              <div className="location-detail">
                <strong>Cluster Radius:</strong> {deed.cluster_radius_miles?.toFixed(2)} miles
              </div>
              <div className="location-detail">
                <strong>Confidence:</strong> {(confidence * 100).toFixed(1)}%
                <div className="confidence-bar">
                  <div className="confidence-fill" style={{ width: `${confidence * 100}%` }}></div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default DeedCard
