import { fileURLToPath } from 'node:url';
import { runtimePython, run } from './agent-cli.mjs';

export const name = 'lingmind';
export const inject = ['tools', 'skills'];

export function mount(ctx, python, skillProvider, mcpClient) {
  ctx.plugin(skillProvider, {
    providerName: 'lingmind', includeDefaultRoots: false,
    customSkillDirs: [fileURLToPath(new URL('../plugins/lingmind/skills', import.meta.url))],
  });
  ctx.plugin(mcpClient, {
    serverName: 'lingmind', transport: 'stdio', command: python,
    env: {}, cwd: fileURLToPath(new URL('../', import.meta.url)),
    toolCallTimeoutMs: 60000, maxInstructionBytes: 32768,
    args: [fileURLToPath(new URL('./agent-oauth.py', import.meta.url)), '--stdio'],
    failOnStartupError: true,
  });
}

export async function apply(ctx) {
  const python = await runtimePython();
  // Complete initial browser consent before the MCP client's initialize timeout starts.
  await run(python, [fileURLToPath(new URL('./agent-oauth.py', import.meta.url)), '--connect']);
  const [skills, mcp] = await Promise.all([
    import('@deepseek-ai/dsh-skill-filesystem'), import('@deepseek-ai/dsh-mcp-client'),
  ]);
  mount(ctx, python, skills, mcp);
}
