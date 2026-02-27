#!/usr/bin/env node
/**
 * Renders all v2 HTML diagrams to high-quality PNGs using Puppeteer.
 * Output: output/png/<filename>.png at 2x device scale for crisp PowerPoint slides.
 */

import puppeteer from 'puppeteer';
import { readdir, mkdir } from 'fs/promises';
import { join, basename, extname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = fileURLToPath(new URL('.', import.meta.url));
const OUTPUT_DIR = join(__dirname, '..', 'output');
const PNG_DIR = join(OUTPUT_DIR, 'png');

// Viewport matches the v2 presentation target: 4K at 125% scaling
const VIEWPORT_WIDTH = 3072;
const VIEWPORT_HEIGHT = 1590;
// 2x device scale factor for crisp rendering on high-DPI displays / print
const DEVICE_SCALE = 2;

async function main() {
  await mkdir(PNG_DIR, { recursive: true });

  const files = (await readdir(OUTPUT_DIR))
    .filter(f => f.endsWith('-v2.html'))
    .sort();

  console.log(`Found ${files.length} v2 HTML files to render.\n`);

  const browser = await puppeteer.launch({
    headless: true,
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-gpu',
      '--font-render-hinting=none',
    ],
  });

  for (const file of files) {
    const htmlPath = join(OUTPUT_DIR, file);
    const pngName = basename(file, extname(file)) + '.png';
    const pngPath = join(PNG_DIR, pngName);

    console.log(`Rendering: ${file} ...`);

    const page = await browser.newPage();
    await page.setViewport({
      width: VIEWPORT_WIDTH,
      height: VIEWPORT_HEIGHT,
      deviceScaleFactor: DEVICE_SCALE,
    });

    // Use file:// protocol so relative icon paths resolve correctly
    const fileUrl = `file:///${htmlPath.replace(/\\/g, '/')}`;
    await page.goto(fileUrl, { waitUntil: 'networkidle0', timeout: 30000 });

    // Give JS-drawn elements (SVG arrows, animations) time to settle
    await new Promise(r => setTimeout(r, 1500));

    await page.screenshot({
      path: pngPath,
      fullPage: false, // Capture only the viewport (no scroll)
      type: 'png',
    });

    await page.close();
    console.log(`  -> ${pngName} (${VIEWPORT_WIDTH * DEVICE_SCALE}x${VIEWPORT_HEIGHT * DEVICE_SCALE}px)`);
  }

  await browser.close();
  console.log(`\nDone! ${files.length} PNGs saved to output/png/`);
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});