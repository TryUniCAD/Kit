import { build } from 'esbuild';
import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync } from 'node:fs';

await build({ entryPoints: ['Board.jsx'], bundle: true, minify: true,
  legalComments: 'eof', outfile: '../../../../Documentation/Planning/Generated/Board.js',
  define: { 'process.env.NODE_ENV': '"production"' } });
const paths = ['re/automation/Planning/Board/Board.jsx', 're/automation/Planning/Board/Board.css',
  're/automation/Planning/Board/package.json', 're/automation/Planning/Board/package-lock.json',
  'Documentation/Planning/Generated/Board.js', 'Documentation/Planning/Generated/Board.css'];
writeFileSync('../../../../Documentation/Planning/BundleManifest.json', JSON.stringify(Object.fromEntries(
  paths.map(path => [path, createHash('sha256').update(readFileSync('../../../../' + path)).digest('hex')])
), null, 2) + '\n');
