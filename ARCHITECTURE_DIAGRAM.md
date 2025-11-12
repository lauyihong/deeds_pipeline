# Architecture Diagram & Data Flow

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      DEEDS PIPELINE                             │
│                   (Data Processing)                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐    │
│  │ Step 1   │→→→│ Step 2   │→→→│ Step 3   │→→→│ Step 4   │    │
│  │Reformat  │   │ OCR      │   │ Scraper  │   │ Geocode  │    │
│  └──────────┘   └──────────┘   └──────────┘   └────┬─────┘    │
│                                                      │           │
│                                         ┌────────────▼────────┐ │
│                                         │   Step 5            │ │
│                                         │ Integration &       │ │
│                                         │ Export (Clean!)     │ │
│                                         └────────────┬────────┘ │
│                                                      │           │
└──────────────────────────────────────────────────────┼───────────┘
                                                       │
                    ┌──────────────────────────────────┼───────────────────┐
                    │                                  │                   │
          ┌─────────▼────────┐            ┌──────────▼──────┐   ┌────────▼─────┐
          │ JSON Output      │            │ CSV Output      │   │ (New!)       │
          │ Full nested data │            │ Flattened data  │   │ Frontend App │
          └─────────┬────────┘            └─────────────────┘   │              │
                    │                                            │              │
                    └────────────────────────┬───────────────────┘              │
                                             │                                  │
                    ┌────────────────────────▼────────────────────┐            │
                    │ Frontend Application (React)                │            │
                    │ Separate repository/folder                  │            │
                    ├─────────────────────────────────────────────┤            │
                    │  App.jsx                                    │            │
                    │  ├─ DeedCard.jsx                            │            │
                    │  │  ├─ MapComponent.jsx  (Leaflet)          │            │
                    │  │  └─ StreetsList.jsx                      │            │
                    │  └─ index.css                               │            │
                    │                                              │            │
                    │ Reads data from:                            │            │
                    │ ../output/step5_final_integrated.json       │            │
                    └────────────────────────┬────────────────────┘            │
                                             │                                  │
                    ┌────────────────────────▼────────────────────┐            │
                    │ Browser Visualization                       │            │
                    ├─────────────────────────────────────────────┤            │
                    │ • Interactive maps with markers             │            │
                    │ • Geocoding statistics                      │            │
                    │ • Valid/invalid street lists                │            │
                    │ • Cluster visualization                     │            │
                    │ • Responsive design                         │            │
                    │ • Real-time updates on data change          │            │
                    └─────────────────────────────────────────────┘            │
                                                                                │
                                                 ┌──────────────────────────────┘
                                                 │
                                    Local File System or HTTP Server
```

## Component Tree

```
App
├── Header
│   └── Stats Cards (4)
│       ├── Total Deeds
│       ├── Geocoded Count
│       ├── Success Rate
│       └── With Streets
│
└── DeedGrid (for each deed)
    ├── DeedCard (deed_id)
    │   ├── Header
    │   │   └── Deed ID + County
    │   │
    │   └── Content (2 columns)
    │       ├── MapComponent
    │       │   └── Leaflet Map
    │       │       ├── Tile Layer (OSM)
    │       │       ├── Circle Markers (streets)
    │       │       ├── Center Marker (red)
    │       │       └── Radius Circle
    │       │
    │       └── InfoPanels
    │           ├── StreetsList (validated)
    │           ├── StreetsList (invalid)
    │           └── LocationInfo
    │               ├── Town
    │               ├── Address
    │               ├── Coordinates
    │               ├── Radius
    │               └── Confidence Bar
    │
    └── (repeat for each deed)
```

## Data Flow Diagram

```
┌────────────────────────────────────────────────────────────┐
│ step5_final_integrated.json (10 KB)                        │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ {                                                    │   │
│ │   metadata: {                                        │   │
│ │     total_deeds: 2,                                  │   │
│ │     quality_report: {                                │   │
│ │       geocoded_count: 2,                             │   │
│ │       geocoding_rate: "100%",                        │   │
│ │       ...                                            │   │
│ │     }                                                │   │
│ │   },                                                 │   │
│ │   deeds: [                                           │   │
│ │     {                                                │   │
│ │       deed_id: "5767",                               │   │
│ │       county: "Middlesex County",                    │   │
│ │       primary_town: "Dracut",                        │   │
│ │       geolocation: {                                 │   │
│ │         validated_streets: [...],                    │   │
│ │         invalid_streets: [...],                      │   │
│ │         cluster_center_lat: 42.686,                  │   │
│ │         cluster_center_lon: -71.363,                 │   │
│ │         final_address: "...",                        │   │
│ │         cluster_radius_miles: 1.82,                  │   │
│ │         confidence: 0.82                             │   │
│ │       }                                              │   │
│ │     },                                               │   │
│ │     ...                                              │   │
│ │   ]                                                  │   │
│ │ }                                                    │   │
│ └──────────────────────────────────────────────────────┘   │
└────────────────────────────────┬─────────────────────────────┘
                                  │
                    ┌─────────────▼──────────────┐
                    │ App.jsx fetch()            │
                    │ Loads & parses JSON        │
                    └─────────────┬──────────────┘
                                  │
                    ┌─────────────▼──────────────┐
                    │ renderHeaderStats()        │
                    │ Show quality_report data   │
                    └────────────────────────────┘
                                  │
                    ┌─────────────▼──────────────┐
                    │ renderDeedCards()          │
                    │ Map over deeds array       │
                    └─────────────┬──────────────┘
                                  │
                    ┌─────────────▼──────────────────────┐
                    │ DeedCard Component (for each deed) │
                    ├────────────────────────────────────┤
                    │                                    │
                    │ MapComponent                       │
                    │ ├─ L.map() initialization          │
                    │ ├─ Add tile layer                  │
                    │ ├─ Draw street markers             │
                    │ ├─ Add center marker               │
                    │ └─ Draw radius circle              │
                    │                                    │
                    │ StreetsList (validated)            │
                    │ ├─ Filter: street_valid = true     │
                    │ └─ Render with icons               │
                    │                                    │
                    │ StreetsList (invalid)              │
                    │ ├─ Filter: invalid_streets         │
                    │ └─ Render with icons               │
                    │                                    │
                    │ LocationInfo                       │
                    │ ├─ Display town                    │
                    │ ├─ Show address                    │
                    │ ├─ Show coordinates                │
                    │ ├─ Show radius                     │
                    │ └─ Confidence bar                  │
                    │                                    │
                    └────────────────────────────────────┘
                                  │
                    ┌─────────────▼──────────────┐
                    │ Browser Rendering          │
                    │ Interactive Visualization  │
                    └────────────────────────────┘
```

## File Relationships

```
PIPELINE
├── deeds_pipeline/
│   ├── step1_json_reformat.py
│   ├── step2_ocr_extraction.py
│   ├── step3_scraper.py
│   ├── step4_geolocation.py
│   ├── step5_integration.py ◄─────────┐
│   │                                   │ WRITES DATA
│   └── config.py                       │
│                                       │
├── output/                             │
│   ├── step1_reformatted_by_deed_id.json
│   ├── step2_ocr_extracted.json
│   ├── step3_scraper_data.json
│   ├── step4_geolocation.json
│   ├── step5_final_integrated.json ◄──┘
│   └── step5_final_integrated.csv
│
├── frontend/ ◄──────────────────────────────────┐
│   ├── src/                                     │ READS DATA
│   │   ├── App.jsx ─────────┐                  │
│   │   │                    └────────────────┬──┘
│   │   ├── components/
│   │   │   ├── DeedCard.jsx
│   │   │   ├── MapComponent.jsx
│   │   │   └── StreetsList.jsx
│   │   └── index.css
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
│
└── Documentation/
    ├── README.md
    ├── VISUALIZATION_GUIDE.md
    ├── FRONTEND_QUICKSTART.md
    ├── IMPLEMENTATION_SUMMARY.md
    └── ARCHITECTURE_DIAGRAM.md (this file)
```

## Technology Stack

```
PIPELINE:
├─ Python 3.8+
├─ pandas (data processing)
├─ httpx (async HTTP)
└─ Logging

FRONTEND:
├─ React 18.2.0
├─ Vite (build tool)
├─ Leaflet 1.9.4 (maps)
├─ CSS3 (styling)
└─ ES6 JavaScript

VISUALIZATION:
├─ Leaflet Maps
├─ OpenStreetMap Tiles
└─ Responsive Web Design
```

## Deployment Options

### Option 1: Local Development
```
Terminal 1: npm run dev
           (frontend on localhost:3000)

Terminal 2: python -m deeds_pipeline.step5_integration
           (when data needs update)
```

### Option 2: Static Hosting
```
npm run build
# Upload dist/ to GitHub Pages, Netlify, Vercel, etc.
# Access via domain name with no server needed
```

### Option 3: Server with Backend API
```
# Could add Flask/FastAPI backend to serve JSON
# Frontend makes API call instead of local file read
# Easy to add authentication, caching, etc.
```

## Performance Characteristics

```
Pipeline:
├─ Step 5: ~100ms per deed
├─ Depends on: Network (geocoding API calls)
└─ Total: ~500ms for 2 deeds

Frontend:
├─ Load JSON: ~50ms
├─ Parse & render: ~200ms
├─ Map initialization: ~300ms per map
└─ Total: ~2-3s for 2 deeds (mostly map initialization)

Browser:
├─ Initial load: ~3-4s
├─ Interactions: <100ms
└─ Maps are lazy-loaded on demand
```

## Summary

This architecture provides:
✅ Clean separation between data and presentation
✅ Easy to maintain and update
✅ Scalable for future enhancements
✅ Professional UI with React
✅ No server needed for basic use
✅ Flexible deployment options
