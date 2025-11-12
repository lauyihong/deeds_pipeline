# Frontend Quick Start Guide

Get the interactive map visualization running in 2 minutes.

## 1. Run the Pipeline (if not already done)

```bash
# From project root
python -m deeds_pipeline.step5_integration
```

Output:
- ✓ `output/step5_final_integrated.json` (frontend reads this)
- ✓ `output/step5_final_integrated.csv` (for data analysis)

## 2. Install Frontend Dependencies

```bash
cd frontend
npm install
```

First time only - takes ~30 seconds.

## 3. Start the Development Server

```bash
npm run dev
```

Opens http://localhost:3000 in your browser automatically.

## What You'll See

- 🗺️ Interactive map for each deed with all geocoded streets
- 📊 Header statistics (total deeds, geocoded count, success rate)
- 📍 Validated streets marked with colored pins
- ❌ Invalid streets listed separately
- 📌 Red marker showing cluster center (property location)
- 🔴 Dashed circle showing cluster radius
- 📈 Confidence score with visual bar

## Keyboard Shortcuts

| Action | Command |
|--------|---------|
| Start dev server | `npm run dev` |
| Build for production | `npm run build` |
| Preview build | `npm run preview` |

## File Locations

```
Frontend loads data from:
../output/step5_final_integrated.json

Development files in:
./src/
  ├── App.jsx
  ├── index.css
  └── components/
      ├── DeedCard.jsx
      ├── MapComponent.jsx
      └── StreetsList.jsx
```

## Common Tasks

### Modify Colors/Styling
Edit `src/index.css`

### Add a Filter Feature
Create `src/components/FilterBar.jsx` and import in `App.jsx`

### Change Map Tile Provider
Edit `MapComponent.jsx` - line with `L.tileLayer()`

### Deploy to Production
```bash
npm run build
# Upload dist/ folder to your server
```

## Troubleshooting

### Data Not Loading?
```bash
# Make sure step5 was run
python -m deeds_pipeline.step5_integration

# Check file exists
ls output/step5_final_integrated.json
```

### Port 3000 Already in Use?
```bash
npm run dev -- --port 3001
```

### Map Not Displaying?
1. Open browser DevTools (F12)
2. Check Console tab for errors
3. Verify internet connection (needs OpenStreetMap tiles)

## Next Steps

📚 See `frontend/README.md` for detailed documentation
📖 See `VISUALIZATION_GUIDE.md` for architecture overview
🚀 See `QUICKSTART.md` for full pipeline setup

## Tips

✅ Keep dev server running while working - auto-reloads on changes
✅ Open DevTools (F12) to debug components and styles
✅ The frontend watches `../output/` - just refresh browser after running step5 again
✅ No need to restart dev server when pipeline data changes

Enjoy exploring your deed visualization! 🗺️
