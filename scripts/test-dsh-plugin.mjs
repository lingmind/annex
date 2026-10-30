import assert from 'node:assert/strict';
import { mkdtempSync, symlinkSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import { mount } from './dsh-plugin.mjs';

const mounted = [];
const skills = {}, mcp = {};
mount({ plugin: (provider, config) => mounted.push({ provider, config }) }, '/test/python', skills, mcp);
assert.equal(mounted[0].provider, skills);
assert.match(mounted[0].config.customSkillDirs[0], /plugins\/lingmind\/skills$/);
assert.equal(mounted[1].provider, mcp);
assert.equal(mounted[1].config.command, '/test/python');
assert.equal(mounted[1].config.transport, 'stdio');
assert.deepEqual(mounted[1].config.args.slice(1), ['--stdio']);
assert.equal(mounted[1].config.failOnStartupError, true);
if (process.platform !== 'win32') {
  const directory = mkdtempSync(join(tmpdir(), 'lingmind-bin-'));
  try {
    const bin = join(directory, 'lingmind-agent');
    symlinkSync(fileURLToPath(new URL('./agent-cli.mjs', import.meta.url)), bin);
    const result = spawnSync(process.execPath, [bin, '--help'], { encoding: 'utf8' });
    assert.equal(result.status, 0);
    assert.match(result.stdout, /lingmind-agent --agent/);
  } finally {
    rmSync(directory, { recursive: true });
  }
}
console.log('DSH mounts shared Skills and the authenticated stdio transport.');
