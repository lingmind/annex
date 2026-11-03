import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { mount } from './dsh-plugin.mjs';

if (!process.env.DSH_NODE_MODULES) {
  throw new Error('Set DSH_NODE_MODULES to the target DSH runtime node_modules directory');
}
const require = createRequire(join(process.env.DSH_NODE_MODULES, '__lingmind_test__.cjs'));
const fixture = fileURLToPath(new URL('./fixtures/dsh-mcp-server.mjs', import.meta.url));
const { Context } = require('@deepseek-ai/cordis');
const ctx = new Context();

try {
  await ctx.plugin(require('@deepseek-ai/dsh-system-prompt').default);
  await ctx.plugin(require('@deepseek-ai/dsh-tools').default);
  await ctx.plugin(require('@deepseek-ai/dsh-skill').default);
  const mcp = require('@deepseek-ai/dsh-mcp-client');
  const skills = require('@deepseek-ai/dsh-skill-filesystem');
  // Exercise the real host bridge without opening browser consent or reading live data.
  const adapter = {
    ...mcp,
    async apply(ctx, config) {
      await mcp.apply(ctx, mcp.Config({
        ...config, command: 'node', args: [fixture], reconnect: { enabled: false },
      }));
    },
  };
  const fibers = [];
  const mounting = {
    plugin(provider, config) {
      const fiber = ctx.plugin(provider, config);
      fibers.push(fiber);
      return fiber;
    },
  };
  for (const [product, connection] of [['lingmind', 'beta'], ['lingmind', 'sandbox'], ['lingmind-operator', 'lingmind']]) {
    mount(mounting, 'node', skills, adapter, product, connection);
  }
  await Promise.all(fibers.map(fiber => fiber.await()));
  const catalog = await ctx.skills.list({ cwd: process.cwd() });
  for (const server of ['lingmind-beta', 'lingmind-sandbox', 'lingmind-operator']) {
    assert(ctx.tools.get(`mcp__${server}__read_probe`));
  }
  assert(catalog.some(skill => skill.name === 'lingmind-business-query'));
  assert(catalog.some(skill => skill.name === 'lingmind-operator-observe'));
  assert.equal(catalog.length, 17);
  console.log('Target DSH runtime loaded 17 shared skills and independent Beta, Sandbox and Operator MCP tool namespaces using a local protocol fixture.');
} finally {
  await ctx.fiber.dispose();
}
