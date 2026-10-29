const { spawnSync } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const result = spawnSync(process.execPath, [
  path.join(root, 'node_modules/tailwindcss/lib/cli.js'),
  '-c', 'tailwind.config.cjs', '-i', 'frontend/input.css',
  '-o', 'static/verse/utilities.css', '--minify',
], { cwd: root, stdio: 'inherit' });
if (result.status !== 0) process.exit(result.status || 1);
fs.mkdirSync(path.join(root, 'static/verse/vendor'), { recursive: true });
fs.copyFileSync(path.join(root, 'node_modules/three/build/three.min.js'), path.join(root, 'static/verse/vendor/three.min.js'));
fs.copyFileSync(path.join(root, 'node_modules/three/LICENSE'), path.join(root, 'static/verse/vendor/THREE-LICENSE.txt'));
