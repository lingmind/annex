#!/usr/bin/env node
import { spawn, spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { realpathSync } from 'node:fs';

function systemPython() {
  for (const command of ['python3', 'python']) {
    const check = spawnSync(command, ['-c', 'import sys; sys.exit(sys.version_info < (3, 11))'], { stdio: 'ignore' });
    if (check.status === 0) return command;
  }
  throw new Error('Install Python 3.11 or newer, then retry.');
}

export function run(command, args, capture = false) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, { stdio: capture ? ['ignore', 'pipe', 'inherit'] : 'inherit' });
    let output = '';
    if (capture) child.stdout.on('data', data => { output += data; });
    child.on('error', reject);
    child.on('close', code => code === 0 ? resolve(output.trim()) : reject(new Error(`LingMind setup exited with code ${code}.`)));
  });
}

export function runtimePython() {
  return run(systemPython(), [fileURLToPath(new URL('./agent_runtime.py', import.meta.url))], true);
}

if (process.argv[1] && fileURLToPath(import.meta.url) === realpathSync(process.argv[1])) {
  try {
    const args = process.argv.slice(2);
    if (args.includes('--help') || !args.length) {
      console.log('lingmind-agent --agent codex|workbuddy|doubao|dsh [--environment-code CODE] [--login]');
    } else {
      const python = args.includes('dsh') ? await runtimePython() : systemPython();
      await run(python, [fileURLToPath(new URL('./setup-agent.py', import.meta.url)), ...args]);
    }
  } catch (error) {
    console.error(error.message);
    process.exitCode = 1;
  }
}
