import { execFileSync, spawnSync } from 'node:child_process';
import { accessSync, constants, mkdirSync, readFileSync, writeFileSync, renameSync, chmodSync, copyFileSync, rmSync, existsSync } from 'node:fs';
import { homedir, userInfo } from 'node:os';
import { join } from 'node:path';

const env = process.env;
const model = env.MACRESET_LOCAL_LLM_MODEL;
const context = Number(env.MACRESET_LOCAL_LLM_CONTEXT);
if (typeof model !== 'string' || !model.length || !Number.isSafeInteger(context) || context <= 0) {
  throw new Error('local_llm_model must be nonempty and local_llm_context_length a positive integer.');
}
const packages = JSON.parse(env.MACRESET_PI_PACKAGES);
if (!Array.isArray(packages) || packages.some(p => typeof p !== 'string' || !p.length)) {
  throw new Error('pi_packages must be a JSON array of nonempty strings.');
}
for (const key of ['MACRESET_PI_PROVIDER', 'MACRESET_PI_MODEL', 'MACRESET_PI_THINKING']) {
  if (!env[key]) throw new Error(`${key} must be nonempty.`);
}
const home = homedir();
const ollama = join(env.HOMEBREW_PREFIX, 'bin/ollama');
accessSync(ollama, constants.X_OK);
const domain = `gui/${userInfo().uid}`;
const service = `${domain}/com.macreset.ollama`;
const run = (command, args, options = {}) => execFileSync(command, args, { stdio: 'inherit', ...options });
function inspectService(label) {
  const result = spawnSync('launchctl', ['print', `${domain}/${label}`], { encoding: 'utf8' });
  if (result.error) throw result.error;
  if (result.status === 0) return result.stdout;
  if (/could not find service/i.test(result.stderr)) return null;
  throw new Error(`Cannot inspect ${label}: ${result.stderr}`);
}
// Keep the existing label: native mise agents rename it and risk competing servers.
const loaded = inspectService('com.macreset.ollama');
for (const label of ['homebrew.mxcl.ollama', 'dev.mise.ollama']) {
  if (inspectService(label) !== null) throw new Error(`Another Ollama service (${label}) is loaded; resolve its ownership before retrying.`);
}
async function tags() {
  const response = await fetch('http://127.0.0.1:11434/api/tags', { signal: AbortSignal.timeout(5000) });
  if (!response.ok) throw new Error(`Ollama API returned ${response.status}`);
  const data = await response.json();
  if (!Array.isArray(data.models)) throw new Error('Ollama API returned an invalid model inventory.');
  return data.models;
}
if (loaded === null) {
  try {
    const response = await fetch('http://127.0.0.1:11434/api/tags', { signal: AbortSignal.timeout(5000) });
    await response.body?.cancel();
    throw new Error('Port 11434 already responds without the managed Ollama job; stop the other server before retrying.');
  } catch (error) {
    if (error.cause?.code !== 'ECONNREFUSED') throw error;
  }
}
const xml = value => String(value).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&apos;' }[c]));
const plist = join(home, 'Library/LaunchAgents/com.macreset.ollama.plist');
const log = join(home, 'Library/Logs/macreset-ollama.log');
const content = `<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>Label</key><string>com.macreset.ollama</string>
<key>ProgramArguments</key><array><string>${xml(ollama)}</string><string>serve</string></array>
<key>EnvironmentVariables</key><dict><key>OLLAMA_HOST</key><string>127.0.0.1:11434</string><key>OLLAMA_CONTEXT_LENGTH</key><string>${context}</string></dict>
<key>RunAtLoad</key><true/><key>KeepAlive</key><true/>
<key>StandardOutPath</key><string>${xml(log)}</string><key>StandardErrorPath</key><string>${xml(log)}</string>
</dict></plist>
`;
mkdirSync(join(home, 'Library/LaunchAgents'), { recursive: true, mode: 0o755 });
mkdirSync(join(home, 'Library/Logs'), { recursive: true, mode: 0o755 });
const old = existsSync(plist) ? readFileSync(plist, 'utf8') : null;
const changed = old !== content;
if (changed) {
  const temporary = `${plist}.${process.pid}.tmp`;
  try {
    writeFileSync(temporary, content, { mode: 0o644 });
    run('plutil', ['-lint', temporary]);
    renameSync(temporary, plist);
  } finally { rmSync(temporary, { force: true }); }
}
let models;
try {
  if (changed && loaded !== null) run('launchctl', ['bootout', service]);
  if (changed || loaded === null) run('launchctl', ['bootstrap', domain, plist]);
  else if (!/state = running/.test(loaded)) run('launchctl', ['kickstart', service]);
  for (let attempt = 0; attempt < 12; attempt++) {
    try {
      models = await tags();
      if (!/state = running/.test(inspectService('com.macreset.ollama') || '')) throw new Error('Managed Ollama job is not running.');
      break;
    } catch (error) {
      if (attempt === 11) throw error;
      await new Promise(resolve => setTimeout(resolve, 2000));
    }
  }
} catch (error) {
  // Restore a previously managed service if replacing its settings fails.
  if (changed && old !== null) {
    if (inspectService('com.macreset.ollama') !== null) run('launchctl', ['bootout', service]);
    writeFileSync(plist, old, { mode: 0o644 });
    if (loaded !== null) run('launchctl', ['bootstrap', domain, plist]);
  }
  throw error;
}
if (!models.some(entry => entry.name === model)) {
  run(ollama, ['pull', model], { env: { ...env, OLLAMA_HOST: '127.0.0.1:11434' } });
  if (!(await tags()).some(entry => entry.name === model)) throw new Error(`Ollama did not retain model ${model}.`);
}
const supportedPi = [join(home, '.pi/agent/bin/pi'), join(home, '.local/bin/pi'), join(env.HOMEBREW_PREFIX, 'bin/pi')];
if (!supportedPi.some(path => existsSync(path))) {
  run('npm', ['install', '--global', '--ignore-scripts', '@earendil-works/pi-coding-agent'], { env: { ...env, NPM_CONFIG_PREFIX: join(home, '.local') } });
  if (!supportedPi.some(path => existsSync(path))) throw new Error('Pi installation did not create a supported executable.');
}
const directory = join(home, '.pi/agent');
mkdirSync(directory, { recursive: true, mode: 0o700 });
chmodSync(directory, 0o700);
function configure(name, value) {
  const path = join(directory, name);
  const text = `${JSON.stringify(value, null, 2)}\n`;
  if (existsSync(path) && readFileSync(path, 'utf8') === text) { chmodSync(path, 0o600); return; }
  if (existsSync(path)) {
    const backup = `${path}.${Date.now()}.${process.pid}.bak`;
    copyFileSync(path, backup, constants.COPYFILE_EXCL);
    chmodSync(backup, 0o600);
  }
  const temporary = `${path}.${process.pid}.tmp`;
  try {
    writeFileSync(temporary, text, { mode: 0o600 });
    chmodSync(temporary, 0o600);
    renameSync(temporary, path);
  } finally { rmSync(temporary, { force: true }); }
}
configure('models.json', { providers: { ollama: { baseUrl: 'http://127.0.0.1:11434/v1', api: 'openai-completions', apiKey: 'ollama', models: [{ id: model, contextWindow: context }] } } });
configure('settings.json', { defaultProvider: env.MACRESET_PI_PROVIDER, defaultModel: env.MACRESET_PI_MODEL, defaultThinkingLevel: env.MACRESET_PI_THINKING, packages });
