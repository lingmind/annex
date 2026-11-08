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

// Host diagnostics only show this message, so carry the child's own reason with it.
function cause(stderr) {
  const line = stderr.split('\n').map(text => text.trim()).filter(Boolean).pop();
  return line ? ` ${line.length > 300 ? `${line.slice(0, 297)}...` : line}` : '';
}

export function run(command, args, capture = false) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, { stdio: capture ? ['ignore', 'pipe', 'pipe'] : ['inherit', 'inherit', 'pipe'] });
    let output = '';
    let errors = '';
    if (capture) child.stdout.on('data', data => { output += data; });
    child.stderr.on('data', data => { errors += data; process.stderr.write(data); });
    child.on('error', reject);
    child.on('close', code => code === 0 ? resolve(output.trim()) : reject(new Error(`LingMind setup exited with code ${code}.${cause(errors)}`)));
  });
}

let runtimePreparation;

export function runtimePython() {
  // Both DSH components share one bootstrap, including the first-run venv creation.
  runtimePreparation ??= run(systemPython(), [fileURLToPath(new URL('./agent_runtime.py', import.meta.url))], true)
    .catch(error => {
      runtimePreparation = undefined;
      throw error;
    });
  return runtimePreparation;
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
