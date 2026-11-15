import { execFileSync, spawnSync } from 'node:child_process';
import { arch, homedir } from 'node:os';
import { existsSync } from 'node:fs';
import { join } from 'node:path';

const mise = process.env.MACRESET_MISE || 'mise';
const brew = process.env.MACRESET_BREW;
if (!brew) throw new Error('Homebrew environment is missing; run the packages task.');
const status = () => JSON.parse(execFileSync(mise, ['bootstrap', 'packages', 'status', '--json'], { encoding: 'utf8' }));
// Status exposes the merged native inventory, including mise.local.toml overrides.
const formulas = status().brew?.packages;
if (!Array.isArray(formulas)) throw new Error('Expected native brew package inventory.');
for (const entry of formulas) {
  const name = entry.package;
  if (!/^[a-zA-Z0-9@+_.\/-]+$/.test(name) || name.startsWith('-')) throw new Error(`Invalid formula: ${name}`);
  if (entry.desired_state !== 'present' || entry.requested_version !== 'latest') {
    throw new Error(`Formula ${name}: this setup supports present/latest only; remove declarations to stop managing them.`);
  }
  // Native brew supports only the standard Apple Silicon prefix on macOS.
  const cliOnly = arch() === 'x64' || process.env.HOMEBREW_PREFIX !== '/opt/homebrew';
  let fallback = cliOnly;
  if (!fallback) {
    const result = spawnSync(mise, ['bootstrap', 'packages', 'apply', `brew:${name}`], { encoding: 'utf8' });
    process.stdout.write(result.stdout || '');
    process.stderr.write(result.stderr || '');
    if (result.error) throw result.error;
    if (result.status !== 0) {
      // Only documented native-feature gaps permit fallback; network/auth errors stay failures.
      fallback = /formula uses |unsupported (?:Homebrew |formula )?feature/i.test(result.stderr || '');
      if (!fallback) throw new Error(`Native installation failed for ${name} (exit ${result.status}).`);
    }
  }
  if (fallback) {
    console.error(`Homebrew CLI fallback: ${name} (${cliOnly ? 'architecture or prefix unsupported by native brew' : 'unsupported native formula feature'})`);
    execFileSync(brew, ['install', '--formula', name], { stdio: 'inherit' });
  }
  // Homebrew reads the receipts written by both installers; do not infer success from timestamps.
  execFileSync(brew, ['list', '--formula', '--versions', name], { stdio: 'inherit' });
}

// Preserve the legacy role's optional user-owned Bundle extension, not a second repo inventory.
const brewfile = process.env.MACRESET_BREWFILE || join(homedir(), 'Brewfile');
if (existsSync(brewfile)) execFileSync(brew, ['bundle', '--file', brewfile], { stdio: 'inherit' });
