import React, { useEffect, useRef } from 'react'
import MapComponent from './MapComponent'
import StreetsList from './StreetsList'

function DeedCard({ deed }) {
  // Flatten geolocation data for easier access
  const geo = deed.geolocation || {}
  const validCount = geo.validated_streets?.length || 0
  const invalidCount = geo.invalid_streets?.length || 0
  const confidence = geo.cluster_center_lat ? geo.confidence : 0

  // Create a flattened deed object for MapComponent and other children
  const flatDeed = {
    deed_id: deed.deed_id,
    county: deed.county,
    primary_town: geo.primary_town,
    cluster_center_lat: geo.cluster_center_lat,
    cluster_center_lon: geo.cluster_center_lon,
    final_address: geo.final_address,
    cluster_radius_miles: geo.cluster_radius_miles,
    confidence: geo.confidence,
    validated_streets: geo.validated_streets || [],
    invalid_streets: geo.invalid_streets || [],
  }

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
        <MapComponent deed={flatDeed} />

        <div className="info-panels">
          <div className="info-panel">
            <div className="panel-header">✓ Validated Streets ({validCount})</div>
            <StreetsList
              streets={flatDeed.validated_streets}
              isValid={true}
            />
          </div>

          <div className="info-panel">
            <div className="panel-header">✗ Invalid Streets ({invalidCount})</div>
            <StreetsList
              streets={flatDeed.invalid_streets}
              isValid={false}
            />
          </div>

          {flatDeed.cluster_center_lat && (
            <div className="location-info">
              <h4>📍 Final Location</h4>
              <div className="location-detail">
                <strong>Town:</strong> {flatDeed.primary_town}
              </div>
              <div className="location-detail">
                <strong>Address:</strong> {flatDeed.final_address || 'N/A'}
              </div>
              <div className="location-detail">
                <strong>Coordinates:</strong>{' '}
                {flatDeed.cluster_center_lat.toFixed(6)}, {flatDeed.cluster_center_lon.toFixed(6)}
              </div>
              <div className="location-detail">
                <strong>Cluster Radius:</strong> {flatDeed.cluster_radius_miles?.toFixed(2)} miles
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
