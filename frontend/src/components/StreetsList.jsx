import React from 'react'

function StreetsList({ streets, isValid }) {
  if (!streets || streets.length === 0) {
    return (
      <ul className="streets-list">
        <li style={{ color: '#6b7280' }}>None</li>
      </ul>
    )
  }

  return (
    <ul className="streets-list">
      {isValid ? (
        // Validated streets with full info
        streets.map((street, idx) => (
          <li key={idx} className="street-valid">
            <span className="street-icon">📍</span>
            <div>
              <strong>{street.street_name}</strong>
              <br />
              <small style={{ color: '#666' }}>{street.town}</small>
            </div>
          </li>
        ))
      ) : (
        // Invalid streets - just the name
        streets.map((street, idx) => (
          <li key={idx} className="street-invalid">
            <span className="street-icon">❌</span>
            {typeof street === 'string' ? street : street.street_name}
          </li>
        ))
      )}
    </ul>
  )
}

export default StreetsList
