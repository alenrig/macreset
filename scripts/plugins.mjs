import { execFileSync } from 'node:child_process';
import { existsSync, mkdirSync, mkdtempSync, rmSync, renameSync, readdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';

const run = (command, args, env = {}) => execFileSync(command, args, { encoding: 'utf8', env: { ...process.env, ...env } }).trim();
const latest = async repository => {
  const response = await fetch(`https://github.com/${repository}/releases/latest`, { redirect: 'manual' });
  const location = response.headers.get('location') || '';
  const prefix = `https://github.com/${repository}/releases/tag/v`;
  if (response.status !== 302 || !location.startsWith(prefix) || !/^\d+\.\d+\.\d+$/.test(location.slice(prefix.length))) {
    throw new Error(`Cannot resolve stable release for ${repository}: HTTP ${response.status}`);
  }
  return location.slice(prefix.length);
};
const version = (output, name) => {
  const rows = output.split('\n').filter(line => line.split(/\s+/)[0] === name);
  if (rows.length > 1) throw new Error(`Duplicate plugin inventory: ${name}`);
  if (!rows.length) return '';
  const value = rows[0].split(/\s+/)[1]?.replace(/^v/, '');
  if (!/^\d+\.\d+\.\d+$/.test(value || '')) throw new Error(`Invalid installed version for ${name}`);
  return value;
};

const fluxInventory = run('flux', ['plugin', 'list']);
if (!/^schema\s/m.test(run('flux', ['plugin', 'search', 'schema']))) throw new Error('Flux catalog is missing schema.');
const fluxLatest = await latest('fluxcd/flux-schema');
const fluxInstalled = version(fluxInventory, 'schema');
if (!fluxInstalled) run('flux', ['plugin', 'install', 'schema']);
else if (fluxInstalled !== fluxLatest) run('flux', ['plugin', 'update', 'schema']);
if (version(run('flux', ['plugin', 'list']), 'schema') !== fluxLatest) throw new Error('Flux schema version verification failed.');

const major = run('helm', ['version', '--short']).match(/^v(\d+)\./)?.[1];
if (!['3', '4'].includes(major)) throw new Error('helm-unittest setup supports Helm 3 and 4 only.');
const plugins = run('helm', ['env', 'HELM_PLUGINS']).replace(/^"|"$/g, '');
if (!plugins.startsWith('/')) throw new Error('Expected an absolute HELM_PLUGINS directory.');
const helmInventory = run('helm', ['plugin', 'list']);
const installed = version(helmInventory, 'unittest');
const desired = await latest('helm-unittest/helm-unittest');
mkdirSync(plugins, { recursive: true });
// Inspect metadata as well as CLI inventory; never replace an ambiguous/corrupt installation.
const pluginDirs = readdirSync(plugins, { withFileTypes: true }).filter(entry => entry.isDirectory()).map(entry => join(plugins, entry.name));
const matches = pluginDirs.filter(path => {
  let metadata;
  try { metadata = readFileSync(join(path, 'plugin.yaml'), 'utf8'); }
  catch (error) { if (error.code === 'ENOENT') return false; throw error; }
  return /^name:\s*["']?unittest["']?\s*$/m.test(metadata);
});
if (matches.length !== (installed ? 1 : 0)) throw new Error('Helm unittest inventory disagrees with plugin directories.');
if (installed !== desired) {
  const destination = matches[0] || join(plugins, 'unittest');
  if (!installed && existsSync(destination)) throw new Error(`Refusing to overwrite ${destination}`);
  const workspace = mkdtempSync(join(dirname(plugins), '.macreset-helm-'));
  const staged = join(workspace, 'plugins');
  const env = { HELM_PLUGINS: staged };
  let preserveBackup = false;
  let replaced = false;
  let backup = false;
  try {
    mkdirSync(staged);
    if (major === '4') {
      const gnupg = join(workspace, 'gnupg');
      mkdirSync(gnupg, { mode: 0o700 });
      const response = await fetch('https://raw.githubusercontent.com/helm-unittest/helm-unittest/main/public-key.asc');
      if (!response.ok) throw new Error(`Cannot download helm-unittest signing key: HTTP ${response.status}`);
      const key = join(workspace, 'public-key.asc');
      writeFileSync(key, Buffer.from(await response.arrayBuffer()), { mode: 0o600 });
      run('gpg', ['--batch', '--homedir', gnupg, '--import', key]);
      const keyring = join(workspace, 'pubring.gpg');
      const exported = execFileSync('gpg', ['--batch', '--homedir', gnupg, '--export']);
      if (!exported.length) throw new Error('Empty helm-unittest signing keyring.');
      writeFileSync(keyring, exported, { mode: 0o600 });
      run('helm', ['plugin', 'install', `https://github.com/helm-unittest/helm-unittest/releases/download/v${desired}/unittest-${desired}.tgz`, '--verify=true', '--keyring', keyring], env);
    } else {
      run('helm', ['plugin', 'install', 'https://github.com/helm-unittest/helm-unittest.git', '--version', `v${desired}`], env);
    }
    if (version(run('helm', ['plugin', 'list'], env), 'unittest') !== desired) throw new Error('Staged helm-unittest verification failed.');
    const incoming = readdirSync(staged, { withFileTypes: true }).filter(entry => entry.isDirectory());
    if (incoming.length !== 1) throw new Error('Expected exactly one staged Helm plugin.');
    if (installed) { renameSync(destination, join(workspace, 'previous')); backup = true; }
    renameSync(join(staged, incoming[0].name), destination);
    replaced = true;
    if (version(run('helm', ['plugin', 'list']), 'unittest') !== desired) throw new Error('Installed helm-unittest verification failed.');
  } catch (error) {
    preserveBackup = backup;
    if (replaced) rmSync(destination, { recursive: true, force: true });
    if (backup) {
      try { renameSync(join(workspace, 'previous'), destination); }
      catch (rollbackError) {
        // Keep the backup when rollback itself fails; deleting it would lose the old plugin.
        preserveBackup = true;
        throw new Error(`Helm rollback failed; recover ${workspace}/previous manually: ${rollbackError.message}`, { cause: error });
      }
      backup = false;
      preserveBackup = false;
    }
    throw error;
  } finally {
    if (!preserveBackup) rmSync(workspace, { recursive: true, force: true });
  }
}
if (version(run('helm', ['plugin', 'list']), 'unittest') !== desired) throw new Error('Helm unittest version verification failed.');
