import { execFileSync } from 'node:child_process';
import { readFileSync, lstatSync, mkdtempSync, rmSync } from 'node:fs';
import { homedir, tmpdir } from 'node:os';
import { join } from 'node:path';

const run = (command, args, env = {}) => execFileSync(command, args, { encoding: 'utf8', env: { ...process.env, NO_COLOR: '1', ...env } }).trim();
const skills = (...args) => run('npx', ['--yes', 'skills', ...args]);
const inventory = () => {
  const value = JSON.parse(skills('list', '--global', '--json'));
  if (!Array.isArray(value)) throw new Error('Expected global skills inventory array.');
  return value;
};
const lock = () => {
  try { return JSON.parse(readFileSync(join(homedir(), '.agents/.skill-lock.json'), 'utf8')).skills; }
  catch (error) { if (error.code === 'ENOENT') return {}; throw error; }
};
const configured = JSON.parse(process.env.MACRESET_AGENT_SKILLS);
if (!configured || Array.isArray(configured) || typeof configured !== 'object') throw new Error('Expected skills source/name mapping.');
const entries = Object.entries(configured).flatMap(([source, names]) => {
  if (!/^[\w.-]+\/[\w.-]+$/.test(source) || !Array.isArray(names)) throw new Error(`Invalid skill source: ${source}`);
  return names.map(name => {
    if (typeof name !== 'string' || !/^[\w-]+$/.test(name)) throw new Error(`Invalid skill name: ${name}`);
    return [source, name];
  });
});
if (new Set(entries.map(([, name]) => name)).size !== entries.length) throw new Error('Managed skill names must be unique.');
const workspace = mkdtempSync(join(tmpdir(), 'macreset-skill-hash-'));
try {
  const objects = join(workspace, 'objects.git');
  run('git', ['init', '--bare', objects]);
  const hash = name => {
    const path = join(homedir(), '.agents/skills', name);
    try { if (!lstatSync(path).isDirectory()) return ''; }
    catch (error) { if (error.code === 'ENOENT') return ''; throw error; }
    const env = { GIT_INDEX_FILE: join(workspace, `${name}.index`) };
    run('git', [`--git-dir=${objects}`, `--work-tree=${path}`, 'add', '-A'], env);
    return run('git', [`--git-dir=${objects}`, 'write-tree'], env);
  };
  const healthy = (items, metadata, source, name) => {
    const matches = items.filter(item => item.name === name);
    const item = matches[0];
    const entry = metadata[name];
    return matches.length === 1 && item.source === source && item.agents?.includes('Codex') && item.agents?.includes('Cursor')
      && entry?.source === source && typeof entry.skillPath === 'string' && entry.skillPath.length > 0
      && /^[a-f0-9]{40}$/.test(entry.skillFolderHash || '') && hash(name) === entry.skillFolderHash;
  };
  const initial = inventory();
  const metadata = lock();
  for (const [source, name] of entries) {
    if (healthy(initial, metadata, source, name)) {
      const output = skills('update', name, '--global', '--yes');
      console.log(output);
      if (/Failed to check skills from|Failed to update|cannot be checked automatically|No global skills to check/.test(output)
        || (!output.includes(`Updated ${name}`) && !output.includes('All global skills are up to date'))) {
        throw new Error(`Skill update did not confirm success: ${name}`);
      }
    } else {
      const added = JSON.parse(skills('add', source, '--skill', name, '--global', '--agent', 'codex', '--agent', 'cursor', '--yes', '--json'));
      if (!Array.isArray(added) || added.filter(item => item.name === name).length !== 1) throw new Error(`Skill repair failed: ${name}`);
    }
    if (!healthy(inventory(), lock(), source, name)) throw new Error(`Skill postcondition failed: ${source}/${name}`);
  }
} finally {
  rmSync(workspace, { recursive: true, force: true });
}
