/**
 * Sync data from pipeline output to frontend public folder
 * Run this after step5 completes: node sync-data.js
 */

import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

const sourceFile = path.join(__dirname, '..', 'output', 'step5_final_integrated.json')
const destFile = path.join(__dirname, 'public', 'step5_final_integrated.json')

// Ensure public folder exists
const publicDir = path.dirname(destFile)
if (!fs.existsSync(publicDir)) {
  fs.mkdirSync(publicDir, { recursive: true })
  console.log(`✓ Created public folder: ${publicDir}`)
}

// Copy file
try {
  fs.copyFileSync(sourceFile, destFile)
  console.log(`✓ Data synced successfully`)
  console.log(`  From: ${sourceFile}`)
  console.log(`  To:   ${destFile}`)
} catch (err) {
  if (err.code === 'ENOENT') {
    console.error('❌ Error: step5_final_integrated.json not found')
    console.error('   Make sure you\'ve run: python -m deeds_pipeline.step5_integration')
    process.exit(1)
  } else {
    console.error('❌ Error copying file:', err.message)
    process.exit(1)
  }
}
