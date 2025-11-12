import React, { useEffect, useRef } from 'react'
import L from 'leaflet'

// Fix for default markers in Leaflet
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
})

function MapComponent({ deed }) {
  const mapRef = useRef(null)
  const mapInstanceRef = useRef(null)

  useEffect(() => {
    if (!deed.cluster_center_lat || !mapRef.current) return

    // Initialize map
    if (mapInstanceRef.current) {
      mapInstanceRef.current.remove()
    }

    const map = L.map(mapRef.current).setView(
      [deed.cluster_center_lat, deed.cluster_center_lon],
      13
    )

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors',
      maxZoom: 19,
    }).addTo(map)

    // Add validated streets as colored markers
    deed.validated_streets?.forEach((street, idx) => {
      const hue = (idx / Math.max(deed.validated_streets.length, 1)) * 240
      L.circleMarker([street.latitude, street.longitude], {
        radius: 8,
        fillColor: `hsl(${hue}, 100%, 50%)`,
        color: '#2c3e50',
        weight: 2,
        opacity: 0.8,
        fillOpacity: 0.7,
      })
        .bindPopup(
          `<b>${street.street_name}</b><br/>` +
          `Town: ${street.town}<br/>` +
          `${street.address}`
        )
        .addTo(map)
    })

    // Add cluster center as red marker
    const redMarkerIcon = L.icon({
      iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
      shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
      iconSize: [25, 41],
      iconAnchor: [12, 41],
      popupAnchor: [1, -34],
      shadowSize: [41, 41],
    })

    L.marker([deed.cluster_center_lat, deed.cluster_center_lon], {
      icon: redMarkerIcon,
    })
      .bindPopup(
        `<b>Property Center</b><br/>` +
        `Town: ${deed.primary_town}<br/>` +
        `Confidence: ${(deed.confidence * 100).toFixed(1)}%`
      )
      .addTo(map)

    // Draw cluster radius circle
    if (deed.cluster_radius_miles > 0) {
      const radiusMeters = deed.cluster_radius_miles * 1609.34
      L.circle([deed.cluster_center_lat, deed.cluster_center_lon], radiusMeters, {
        color: '#e74c3c',
        fill: true,
        fillOpacity: 0.1,
        weight: 2,
        dashArray: '5, 5',
      })
        .bindPopup(`Cluster radius: ${deed.cluster_radius_miles.toFixed(2)} miles`)
        .addTo(map)
    }

    mapInstanceRef.current = map

    // Cleanup
    return () => {
      map.remove()
      mapInstanceRef.current = null
    }
  }, [deed])

  return <div ref={mapRef} className="map-container" />
}

export default MapComponent
