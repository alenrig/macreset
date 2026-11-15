import { execFileSync } from 'node:child_process';
import { arch, homedir } from 'node:os';
import { join } from 'node:path';

const mise = process.env.MACRESET_MISE || 'mise';
const brew = process.env.MACRESET_BREW;
if (!brew) throw new Error('Homebrew environment is missing; run the maintenance task.');
const run = (bin, args, options = {}) => execFileSync(bin, args, { stdio: 'inherit', ...options });
const capture = (bin, args) => execFileSync(bin, args, { encoding: 'utf8' });
const validName = name => typeof name === 'string' && /^[a-zA-Z0-9@+_.\/-]+$/.test(name) && !name.startsWith('-');
const token = name => name.split('/').at(-1);
const inventory = JSON.parse(capture(mise, ['bootstrap', 'packages', 'status', '--json']));
for (const manager of ['brew', 'brew-cask']) {
  if (!Array.isArray(inventory[manager]?.packages)) throw new Error(`Expected native ${manager} inventory.`);
  for (const entry of inventory[manager].packages) {
    if (!validName(entry.package) || entry.desired_state !== 'present' || entry.requested_version !== 'latest') {
      throw new Error(`Invalid ${manager} maintenance request; only present/latest is supported.`);
    }
  }
}
run('vim', ['+PluginUpdate', '+qall']);
run(brew, ['update']);
// Formula receipts are shared: each declared formula gets exactly one upgrade path.
run(process.execPath, ['scripts/packages.mjs', '--upgrade']);
const formulas = new Set(inventory.brew.packages.map(entry => token(entry.package)));
const nativeCasks = new Set();
if (arch() !== 'x64' && process.env.HOMEBREW_PREFIX === '/opt/homebrew') {
  for (const entry of inventory['brew-cask'].packages) {
    if (entry.managed_by === 'unknown') throw new Error(`Unknown cask ownership: ${entry.package}; repair receipts first.`);
    if (entry.managed_by === 'mise') {
      run(mise, ['bootstrap', 'packages', 'upgrade', '--yes', `brew-cask:${entry.package}`]);
      nativeCasks.add(token(entry.package));
    }
  }
}
// Include user/Brewfile packages, excluding those already assigned to native maintenance.
const outdated = JSON.parse(capture(brew, ['outdated', '--json=v2']));
if (!Array.isArray(outdated.formulae) || !Array.isArray(outdated.casks)) throw new Error('Invalid Homebrew outdated inventory.');
for (const [kind, entries, handled] of [['--formula', outdated.formulae, formulas], ['--cask', outdated.casks, nativeCasks]]) {
  for (const entry of entries) {
    const name = entry.full_name || entry.full_token || entry.name || entry.token;
    if (!validName(name)) throw new Error('Invalid Homebrew package name.');
    if (!handled.has(token(name))) run(brew, ['upgrade', kind, name]);
  }
}
run(brew, ['cleanup']);
run(brew, ['outdated']);
run('mo', ['clean']);
run('mo', ['optimize'], { env: { ...process.env, MOLE_ENABLE_DISK_VERIFY: '1' } });
run('mo', ['purge']);
run('sh', ['./upgrade.sh'], { cwd: join(homedir(), '.oh-my-zsh/tools') });
