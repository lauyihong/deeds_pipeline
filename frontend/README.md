# Deed Geocoding Visualization Frontend

A simple React + Leaflet frontend for visualizing deed geolocation results from the deeds pipeline.

## Architecture

The frontend is a **separate application** that reads data from the pipeline's step5 output files:
- Reads from: `../output/step5_final_integrated.json`
- No server integration - just static file serving
- Decoupled from the pipeline - can be updated independently

## Project Structure

```
frontend/
├── src/
│   ├── main.jsx              # Entry point
│   ├── App.jsx               # Main app component
│   ├── index.css             # Global styles
│   └── components/
│       ├── DeedCard.jsx      # Deed card component
│       ├── MapComponent.jsx  # Leaflet map
│       └── StreetsList.jsx   # Streets list component
├── index.html                # HTML template
├── vite.config.js           # Vite config
├── package.json             # Dependencies
└── README.md                # This file
```

## Components

### App.jsx
- Main component that loads data from step5 output
- Displays header stats from quality report
- Renders deed cards in a grid

### DeedCard.jsx
- Displays a single deed record
- Shows deed ID, county, street counts
- Integrates map and info panels

### MapComponent.jsx
- Renders interactive Leaflet map
- Shows validated streets as colored markers
- Red marker for cluster center
- Dashed circle for cluster radius

### StreetsList.jsx
- Lists validated or invalid streets
- Shows town info for validated streets
- Simple text for invalid streets

## Setup & Installation

### Prerequisites
- Node.js 16+ and npm

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
npm run dev
```

This will:
1. Start Vite dev server on http://localhost:3000
2. Open browser automatically
3. Hot-reload on file changes

### Build for Production

```bash
npm run build
```

Output goes to `dist/` folder.

## Usage

### Step 1: Run the Pipeline
First, complete the deeds pipeline steps:

```bash
cd ..  # Go to project root
python -m deeds_pipeline.step5_integration
```

This generates:
- `output/step5_final_integrated.json` - Full nested data with geolocation
- `output/step5_final_integrated.csv` - Flattened CSV for analysis

### Step 2: Run the Frontend

```bash
cd frontend
npm install  # Only needed first time
npm run dev
```

The app will:
1. Load the JSON data from `../output/step5_final_integrated.json`
2. Parse geolocation results
3. Display interactive map visualization for each deed

## Data Flow

```
Step 5 Processing
        ↓
step5_final_integrated.json (output/)
        ↓
Frontend Load
        ↓
Parse & Process
        ↓
Render Components
        ↓
Display Maps & Stats
```

## Features

✅ **Interactive Maps**
- Leaflet + OpenStreetMap tiles
- Colored markers for each validated street
- Red center marker for cluster center
- Dashed circle showing cluster radius
- Hover/click for street details

✅ **Data Display**
- Header statistics (total, geocoded, success rate)
- Validated vs invalid street counts
- Town and address information
- Confidence scores with visual bar
- Cluster radius in miles

✅ **Responsive Design**
- Grid layout adapts to screen size
- Mobile-friendly
- Scrollable street lists

✅ **Clean Architecture**
- Separate components
- No hardcoded data
- Reusable pieces
- Easy to extend

## Customization

### Change Styling
Edit `src/index.css` to modify:
- Colors and gradients
- Layout and spacing
- Font sizes
- Map height

### Add Features
Components can easily be extended to:
- Filter deeds by county/town
- Search functionality
- Export capabilities
- Additional statistics
- Custom map styles

### Connect Different Data Source
Update `src/App.jsx` fetch URL to load from:
- API endpoint
- Different file path
- Local storage
- Remote server

## Troubleshooting

### Data Not Loading
1. Check that `../output/step5_final_integrated.json` exists
2. Run `python -m deeds_pipeline.step5_integration` from project root
3. Check browser console for errors
4. Verify CORS if loading from different domain

### Maps Not Showing
1. Check browser console for Leaflet errors
2. Verify internet connection (needs to load tiles from OpenStreetMap)
3. Check that deed has `cluster_center_lat` and `cluster_center_lon`

### Styling Issues
1. Clear browser cache (Ctrl+Shift+Delete or Cmd+Shift+Delete)
2. Restart dev server: `npm run dev`
3. Check that `src/index.css` is properly imported

## Performance

- Maps are lazy-loaded (only render when in viewport)
- Each map cleans up properly on component unmount
- No unnecessary re-renders with React hooks
- Scrollable lists for large datasets

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile browsers (iOS Safari, Chrome Mobile)

## Dependencies

- **react**: UI library
- **react-dom**: React rendering
- **leaflet**: Map library
- **react-leaflet**: React bindings for Leaflet (optional - using vanilla Leaflet for simplicity)
- **vite**: Build tool

## Future Improvements

- Add filtering by county/town
- Search functionality
- Export to GeoJSON
- Dark mode
- Keyboard shortcuts
- Street info modal with full details
- Comparison view for multiple deeds
