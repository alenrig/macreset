import { execFileSync, spawnSync } from 'node:child_process';
import { arch, homedir } from 'node:os';
import { isAbsolute } from 'node:path';

const mise = process.env.MACRESET_MISE || 'mise';
const brew = process.env.MACRESET_BREW;
if (!brew) throw new Error('Homebrew environment is missing; run the apps task.');
const run = (bin, args) => execFileSync(bin, args, { stdio: 'inherit' });
const capture = (bin, args) => execFileSync(bin, args, { encoding: 'utf8' });
const status = () => JSON.parse(capture(mise, ['bootstrap', 'packages', 'status', '--json']));
const words = value => (value || '').split(/\s+/).filter(Boolean);
const validCask = name => /^[a-zA-Z0-9@+_.\/-]+$/.test(name) && !name.startsWith('-');
const removals = words(process.env.MACRESET_CASK_REMOVE);
const masRemovals = words(process.env.MACRESET_MAS_REMOVE);
if (!removals.every(validCask) || !masRemovals.every(id => /^\d+$/.test(id))) throw new Error('Invalid app removal inventory.');
let appdir = process.env.MISE_BREW_CASK_OPT_APPDIR || '/Applications';
if (appdir.startsWith('~/')) appdir = `${homedir()}/${appdir.slice(2)}`;
if (!isAbsolute(appdir) || appdir === '/' || appdir.split('/').includes('..')) throw new Error('Application directory must be absolute, non-root, without ..');
const upgrade = process.env.MACRESET_MAS_UPGRADE_ALL || 'false';
if (!['true', 'false'].includes(upgrade)) throw new Error('MACRESET_MAS_UPGRADE_ALL must be true or false.');

// Both commands must succeed: authentication/indexing errors are not missing apps.
run('mas', ['version']);
console.error('App Store work requires an Apple Account signed in to App Store, existing purchases and Spotlight indexing; authentication prompts may follow.');
const installedMas = () => new Set(capture('mas', ['list']).split('\n').map(line => line.match(/^\s*(\d+)\s/)?.[1]).filter(Boolean));
let masIds = installedMas();
let brewCasks = new Set(capture(brew, ['list', '--cask']).trim().split(/\s+/).filter(Boolean));
const token = name => name.split('/').at(-1);
const inventory = status();
for (const manager of ['brew-cask', 'mas']) {
  const entries = inventory[manager]?.packages;
  if (!Array.isArray(entries)) throw new Error(`Expected native ${manager} inventory.`);
  for (const entry of entries) {
    const name = entry.package;
    if (!(manager === 'mas' ? /^\d+$/.test(name) : validCask(name))) throw new Error(`Invalid ${manager} package: ${name}`);
    if (entry.desired_state !== 'present' || entry.requested_version !== 'latest') throw new Error(`${manager}:${name}: only present/latest is supported.`);
    if ((manager === 'mas' ? masRemovals.includes(name) : removals.some(item => token(item) === token(name)))) throw new Error(`App is both installed and removed: ${name}`);
  }
}
for (const name of removals) {
  if (brewCasks.has(token(name))) run(brew, ['uninstall', '--cask', name]);
}
for (const id of masRemovals) {
  if (masIds.has(id)) run('mas', ['uninstall', id]);
}

for (const manager of ['brew-cask', 'mas']) {
  for (const entry of inventory[manager].packages) {
    const name = entry.package;
    if (manager === 'mas') {
      run(mise, ['bootstrap', 'packages', 'apply', `mas:${name}`]);
      if (!installedMas().has(name)) throw new Error(`App Store app ${name} is missing after installation; check account and Spotlight.`);
      continue;
    }
    // Native casks always use /opt/homebrew; preserve Intel/custom-prefix ownership.
    const cliOnly = arch() === 'x64' || process.env.HOMEBREW_PREFIX !== '/opt/homebrew';
    if (!cliOnly && entry.managed_by === 'unknown') throw new Error(`Unknown cask ownership for ${name}; repair receipts before rerunning.`);
    if (brewCasks.has(token(name)) && entry.managed_by !== 'mise') {
      console.error(`Keeping Homebrew-owned cask: ${name}; maintenance upgrades it through Homebrew.`);
      continue;
    }
    let fallback = cliOnly;
    if (!fallback) {
      const result = spawnSync(mise, ['bootstrap', 'packages', 'apply', `brew-cask:${name}`], { encoding: 'utf8' });
      process.stdout.write(result.stdout || '');
      process.stderr.write(result.stderr || '');
      if (result.error) throw result.error;
      if (result.status !== 0) {
        fallback = /unsupported artifact type|unsupported (?:cask |Homebrew )?feature|formula uses /i.test(result.stderr || '');
        if (!fallback) throw new Error(`Native cask install failed for ${name}; review ownership/conflict/authentication errors before rerunning.`);
      }
    }
    if (fallback) {
      console.error(`Homebrew CLI fallback for ${name}: native architecture/prefix or artifact support gap.`);
      run(brew, ['install', '--cask', '--adopt', `--appdir=${appdir}`, name]);
      run(brew, ['list', '--cask', name]);
      brewCasks.add(token(name));
    } else {
      const final = status()['brew-cask']?.packages.find(item => item.package === name);
      if (final?.state !== 'installed') throw new Error(`Cask ${name} is missing after native installation.`);
    }
  }
}
if (upgrade === 'true') run('mas', ['upgrade']);
masIds = installedMas();
brewCasks = new Set(capture(brew, ['list', '--cask']).trim().split(/\s+/).filter(Boolean));
if (masRemovals.some(id => masIds.has(id)) || removals.some(name => brewCasks.has(token(name)))) throw new Error('Explicit application removals did not converge.');
