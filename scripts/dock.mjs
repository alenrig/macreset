import { execFileSync } from 'node:child_process';
import { existsSync } from 'node:fs';

const removals = JSON.parse(process.env.MACRESET_DOCK_REMOVE || '[]');
const items = JSON.parse(process.env.MACRESET_DOCK_ITEMS || '[]');
if (!Array.isArray(removals) || !removals.every(name => typeof name === 'string' && name && !['all', 'spacer-tiles'].includes(name))) throw new Error('Invalid selective Dock removals.');
if (!Array.isArray(items) || !items.every(item => typeof item.name === 'string' && item.name && typeof item.path === 'string' && item.path.startsWith('/') && Number.isInteger(item.pos) && item.pos > 0)) throw new Error('Invalid Dock persistent items.');
if (new Set(items.map(item => item.name)).size !== items.length || new Set(items.map(item => item.pos)).size !== items.length) throw new Error('Dock names and positions must be unique.');
// Validate every application before changing the Dock; modern macOS moved system apps.
for (const item of items) {
  if (!existsSync(item.path) && item.path.startsWith('/Applications/')) {
    const systemPath = item.path.replace('/Applications/', '/System/Applications/');
    if (existsSync(systemPath)) item.path = systemPath;
  }
  if (!existsSync(item.path)) throw new Error(`Dock application is missing: ${item.path}; install apps before rerunning.`);
}
const run = args => execFileSync('dockutil', args, { stdio: 'inherit' });
const list = () => execFileSync('dockutil', ['--list'], { encoding: 'utf8' }).trim().split('\n').filter(Boolean).map(line => line.split('\t'));
let entries = list();
const presentRemovals = removals.filter(name => entries.some(entry => entry[0] === name));
for (const [index, name] of presentRemovals.entries()) {
  run(['--remove', name, ...(items.length || index < presentRemovals.length - 1 ? ['--no-restart'] : [])]);
}
const normalizedPath = path => decodeURI(path.replace(/^file:\/\//, '')).replace(/\/$/, '');
for (const item of [...items].sort((a, b) => a.pos - b.pos)) {
  const existing = list().find(entry => normalizedPath(entry[1] || '') === normalizedPath(item.path));
  run(['--add', item.path, '--label', item.name, '--replacing', existing?.[0] || item.name, '--position', String(item.pos), '--no-restart']);
}
// Let dockutil restart the Dock using its current macOS-compatible implementation.
if (items.length) run(['--move', items[0].name, '--position', String(items[0].pos)]);
entries = list();
const apps = entries.filter(entry => entry[2] === 'persistent-apps');
for (const item of items) {
  if (apps[item.pos - 1]?.[0] !== item.name) throw new Error(`Dock position did not converge for ${item.name}.`);
}
if (removals.some(name => entries.some(entry => entry[0] === name) && !items.some(item => item.name === name))) throw new Error('Dock removals did not converge.');
