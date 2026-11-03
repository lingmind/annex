import assert from 'node:assert/strict';
import { mkdtempSync, symlinkSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import { EventEmitter } from 'node:events';
import childProcess from 'node:child_process';
import { syncBuiltinESMExports } from 'node:module';
import { mock } from 'node:test';
import { runtimePython } from './agent-cli.mjs';
import { mount, Config } from './dsh-plugin.mjs';

const mounted = [];
const skills = {}, mcp = {};
mount({ plugin: (provider, config) => mounted.push({ provider, config }) }, '/test/python', skills, mcp);
assert.equal(mounted[0].provider, skills);
assert.match(mounted[0].config.customSkillDirs[0], /plugins\/lingmind\/skills$/);
assert.equal(mounted[1].provider, mcp);
assert.equal(mounted[1].config.command, '/test/python');
assert.equal(mounted[1].config.transport, 'stdio');
assert.deepEqual(mounted[1].config.args.slice(1), ['--stdio', '--product', 'lingmind', '--connection', 'lingmind']);
assert.equal(mounted[1].config.failOnStartupError, true);
const operator = [];
mount({ plugin: (provider, config) => operator.push({ provider, config }) }, '/test/python', skills, mcp, 'lingmind-operator');
assert.equal(operator[0].config.providerName, 'lingmind-operator');
assert.match(operator[0].config.customSkillDirs[0], /plugins\/lingmind-operator\/skills$/);
assert.equal(operator[1].config.serverName, 'lingmind-operator');
assert.deepEqual(operator[1].config.args.slice(1), ['--stdio', '--product', 'lingmind-operator', '--connection', 'lingmind']);
assert.throws(() => mount({}, '', skills, mcp, 'unknown'), /Unknown LingMind product/);
const beta = [];
mount({ plugin: (provider, config) => beta.push({ provider, config }) }, '/test/python', skills, mcp, 'lingmind', 'beta');
assert.equal(beta[0].config.providerName, 'lingmind-beta');
assert.equal(beta[1].config.serverName, 'lingmind-beta');
assert.deepEqual(beta[1].config.args.slice(-2), ['--connection', 'beta']);
assert.deepEqual(Config({}).connections, ['lingmind']);
assert.deepEqual(Config({ connections: ['beta', 'sandbox'] }).connections, ['beta', 'sandbox']);
assert.throws(() => Config({ connections: ['../invalid'] }));
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

let preparations = 0;
mock.method(childProcess, 'spawnSync', () => ({ status: 0 }));
mock.method(childProcess, 'spawn', () => {
  preparations++;
  const child = new EventEmitter();
  child.stdout = new EventEmitter();
  process.nextTick(() => {
    child.stdout.emit('data', '/runtime/python\n');
    child.emit('close', preparations === 1 ? 1 : 0);
  });
  return child;
});
syncBuiltinESMExports();
try {
  const first = runtimePython();
  assert.equal(first, runtimePython(), 'concurrent components share the bootstrap');
  await assert.rejects(first, /code 1/);
  const retry = runtimePython();
  assert.notEqual(first, retry, 'a failed bootstrap can be retried');
  assert.equal(retry, runtimePython());
  assert.equal(await retry, '/runtime/python');
  assert.equal(preparations, 2);
} finally {
  mock.restoreAll();
  syncBuiltinESMExports();
}
