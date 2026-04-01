const esbuild = require('esbuild');
const fs = require('fs');

function inlineUI() {
  const uiTemplate = fs.readFileSync('src/ui.html', 'utf8');
  const uiJs = fs.readFileSync('dist/ui.js', 'utf8');
  const finalHtml = uiTemplate.replace('<!-- INLINE_SCRIPT -->', `<script>${uiJs}</script>`);
  fs.mkdirSync('dist', { recursive: true });
  fs.writeFileSync('dist/ui.html', finalHtml);
}

async function build() {
  // Build code.ts
  await esbuild.build({
    entryPoints: ['src/code.ts'],
    bundle: true,
    outfile: 'dist/code.js',
    target: 'es2015',
    format: 'iife',
  });

  // Build ui.ts
  await esbuild.build({
    entryPoints: ['src/ui.ts'],
    bundle: true,
    outfile: 'dist/ui.js',
    target: 'es2020',
    format: 'iife',
  });

  inlineUI();
  console.log('Build complete!');
}

build().catch(err => { console.error(err); process.exit(1); });
