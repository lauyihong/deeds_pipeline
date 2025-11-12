# Frontend Setup Fix - Data Syncing

## Problem
The frontend was trying to load data from a relative path that didn't work with Vite dev server.

## Solution
We now use a **sync script** to copy data from pipeline output to the frontend's public folder.

## How It Works Now

### Step 1: Run Pipeline
```bash
python -m deeds_pipeline.step5_integration
```
Creates: `output/step5_final_integrated.json`

### Step 2: Start Frontend (includes auto-sync)
```bash
cd frontend
npm install      # First time only
npm run dev      # Automatically syncs data!
```

The `npm run dev` command now:
1. Runs `npm run sync` to copy data
2. Starts Vite dev server
3. Opens browser

### Step 3: View Results
Opens http://localhost:3000 automatically with your visualization!

## What Changed

### Files Modified
- ✅ `App.jsx` - Updated fetch path to `/step5_final_integrated.json`
- ✅ `package.json` - Added sync script and auto-sync to dev

### Files Created
- ✅ `sync-data.js` - Copies data from output to public folder
- ✅ `public/` - Directory where Vite serves static files

### New Workflow
```
Step 5 Output                  Frontend
    ↓                             ↓
output/                       frontend/
  step5_...json    --sync→      public/
                              step5_...json
                                  ↓
                            Vite serves it
                                  ↓
                           Browser loads
```

## Manual Sync (if needed)

If data gets out of sync, manually sync:
```bash
cd frontend
npm run sync
```

## Troubleshooting

### Error: "Data file not found"
Run sync manually: `npm run sync`

### Dev server won't start
Make sure you ran: `npm install`

### Data is stale
After running step5 again, the dev server will auto-sync on next start.

Or manually sync: `npm run sync`

## Updated Scripts

```json
"scripts": {
  "sync": "node sync-data.js",           // Copy data to public
  "dev": "npm run sync && vite",         // Sync then start server
  "build": "vite build",                 // Build for production
  "preview": "vite preview"              // Preview build
}
```

## Now Ready to Go!

Your frontend is now properly set up to load data. Just run:

```bash
cd frontend
npm run dev
```

That's it! Enjoy your visualization 🎉
