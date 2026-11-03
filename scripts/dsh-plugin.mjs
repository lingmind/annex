import { fileURLToPath } from 'node:url';
import z from '@deepseek-ai/schemastery';
import { runtimePython, run } from './agent-cli.mjs';

export const name = 'lingmind';
export const inject = ['tools', 'skills'];
const connectionNamePattern = /^[a-z0-9][a-z0-9_-]{0,22}$/;
export const Config = z.object({
  connections: z.array(z.string().pattern(connectionNamePattern)).default(['lingmind']),
});

export function mount(ctx, python, skillProvider, mcpClient, product = 'lingmind', connection = 'lingmind') {
  if (!['lingmind', 'lingmind-operator'].includes(product)) throw new Error('Unknown LingMind product');
  if (!connectionNamePattern.test(connection)) throw new Error('Invalid LingMind connection name');
  const serverName = connection === 'lingmind' ? product : `${product}-${connection}`;
  const skills = ctx.plugin(skillProvider, {
    providerName: serverName, includeDefaultRoots: false,
    customSkillDirs: [fileURLToPath(new URL(`../plugins/${product}/skills`, import.meta.url))],
  });
  const mcp = ctx.plugin(mcpClient, {
    serverName, transport: 'stdio', command: python,
    env: {}, cwd: fileURLToPath(new URL('../', import.meta.url)),
    toolCallTimeoutMs: 60000, maxInstructionBytes: 32768,
    args: [fileURLToPath(new URL('./agent-oauth.py', import.meta.url)), '--stdio', '--product', product, '--connection', connection],
    failOnStartupError: true,
  });
  return Promise.all([skills, mcp]);
}

export async function activate(ctx, product, connections = ['lingmind']) {
  if (!connections.length || new Set(connections).size !== connections.length) {
    throw new Error('Configure at least one unique LingMind connection');
  }
  const python = await runtimePython();
  const [skills, mcp] = await Promise.all([
    import('@deepseek-ai/dsh-skill-filesystem'), import('@deepseek-ai/dsh-mcp-client'),
  ]);
  // Initial browser grants share a loopback callback port, so authorize accounts in order.
  for (const connection of connections) {
    await run(python, [fileURLToPath(new URL('./agent-oauth.py', import.meta.url)),
      '--connect', '--product', product, '--connection', connection]);
    await mount(ctx, python, skills, mcp, product, connection);
  }
}

export async function apply(ctx, config = { connections: ['lingmind'] }) {
  await activate(ctx, 'lingmind', config.connections);
}
