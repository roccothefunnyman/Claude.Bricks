#!/usr/bin/env node
/**
 * Renders all v2 HTML diagrams to cropped PNGs using Puppeteer.
 * Measures the actual content bounding box on each page and clips to that area
 * with padding, so PNGs contain only the diagram — no empty background.
 * Output: output/png/<filename>-cropped.png at 2x device scale.
 */

import puppeteer from 'puppeteer';
import { readdir, mkdir } from 'fs/promises';
import { join, basename, extname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = fileURLToPath(new URL('.', import.meta.url));
const OUTPUT_DIR = join(__dirname, '..', 'output');
const PNG_DIR = join(OUTPUT_DIR, 'png');

// Viewport large enough to contain all content without clipping
const VIEWPORT_WIDTH = 3072;
const VIEWPORT_HEIGHT = 1590;
const DEVICE_SCALE = 2;
// Padding around the content in CSS pixels
const PADDING = 32;

async function main() {
  await mkdir(PNG_DIR, { recursive: true });

  const files = (await readdir(OUTPUT_DIR))
    .filter(f => f.endsWith('-v2.html'))
    .sort();

  console.log(`Found ${files.length} v2 HTML files to render (cropped).\n`);

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
    const pngName = basename(file, extname(file)) + '-cropped.png';
    const pngPath = join(PNG_DIR, pngName);

    console.log(`Rendering: ${file} ...`);

    const page = await browser.newPage();
    await page.setViewport({
      width: VIEWPORT_WIDTH,
      height: VIEWPORT_HEIGHT,
      deviceScaleFactor: DEVICE_SCALE,
    });

    const fileUrl = `file:///${htmlPath.replace(/\\/g, '/')}`;
    await page.goto(fileUrl, { waitUntil: 'networkidle0', timeout: 30000 });

    // Give JS-drawn elements (SVG arrows, animations) time to settle
    await new Promise(r => setTimeout(r, 1500));

    // Make body and html backgrounds transparent so PNG alpha channel is clear
    await page.evaluate(() => {
      document.documentElement.style.background = 'transparent';
      document.body.style.background = 'transparent';
    });

    // Measure the bounding box of all visible content
    const contentBox = await page.evaluate(() => {
      // Get all elements that have actual rendered size
      const all = document.body.querySelectorAll('*');
      let minX = Infinity, minY = Infinity, maxX = 0, maxY = 0;
      let found = false;

      for (const el of all) {
        const style = window.getComputedStyle(el);
        // Skip invisible elements
        if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') continue;
        // Skip the body and html themselves (they fill the viewport)
        if (el.tagName === 'BODY' || el.tagName === 'HTML') continue;
        // Skip SVG internals (defs, markers, etc.) — they report 0,0 bounds
        if (el.closest('svg') && el.tagName !== 'svg') continue;

        const rect = el.getBoundingClientRect();
        if (rect.width === 0 || rect.height === 0) continue;

        found = true;
        minX = Math.min(minX, rect.left);
        minY = Math.min(minY, rect.top);
        maxX = Math.max(maxX, rect.right);
        maxY = Math.max(maxY, rect.bottom);
      }

      if (!found) return null;
      return { x: minX, y: minY, width: maxX - minX, height: maxY - minY };
    });

    if (!contentBox) {
      console.log(`  -> SKIPPED (no visible content found)`);
      await page.close();
      continue;
    }

    // Add padding, clamped to viewport bounds
    const clip = {
      x: Math.max(0, contentBox.x - PADDING),
      y: Math.max(0, contentBox.y - PADDING),
      width: Math.min(VIEWPORT_WIDTH - Math.max(0, contentBox.x - PADDING),
                      contentBox.width + PADDING * 2),
      height: Math.min(VIEWPORT_HEIGHT - Math.max(0, contentBox.y - PADDING),
                       contentBox.height + PADDING * 2),
    };

    await page.screenshot({
      path: pngPath,
      type: 'png',
      clip: clip,
      omitBackground: true, // Transparent where body bg was
    });

    const actualW = Math.round(clip.width * DEVICE_SCALE);
    const actualH = Math.round(clip.height * DEVICE_SCALE);
    console.log(`  -> ${pngName} (${actualW}x${actualH}px, clipped from ${Math.round(contentBox.x)},${Math.round(contentBox.y)})`);

    await page.close();
  }

  await browser.close();
  console.log(`\nDone! Cropped PNGs saved to output/png/`);
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});