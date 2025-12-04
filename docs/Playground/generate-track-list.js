#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

// Path from docs/Playground to Audio/Tracks (go up two levels, then into Audio/Tracks)
const tracksDir = path.join(__dirname, '../../Audio/Tracks');
const htmlFile = path.join(__dirname, 'index.html');

// Read all .wav files from Tracks directory
const files = fs.readdirSync(tracksDir)
    .filter(file => file.toLowerCase().endsWith('.wav'))
    .sort();

if (files.length === 0) {
    console.log('No WAV files found in Tracks directory');
    process.exit(0);
}

// Read the HTML file
let html = fs.readFileSync(htmlFile, 'utf8');

// Generate the tracks array string
const tracksArray = files.map(file => `            '${file}'`).join(',\n');
const tracksArrayCode = `        const tracks = [\n${tracksArray}\n        ];`;

// Replace the tracks array in the HTML
const tracksRegex = /const tracks = \[[\s\S]*?\];/;
html = html.replace(tracksRegex, tracksArrayCode);

// Write back to file
fs.writeFileSync(htmlFile, html, 'utf8');

console.log(`Updated track list with ${files.length} file(s):`);
files.forEach(file => console.log(`  - ${file}`));

