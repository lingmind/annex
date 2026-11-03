import { createInterface } from 'node:readline';

for await (const line of createInterface({ input: process.stdin })) {
  const request = JSON.parse(line);
  if (request.id === undefined) continue;
  let result;
  switch (request.method) {
    case 'initialize':
      result = {
        protocolVersion: request.params.protocolVersion,
        capabilities: { tools: {} },
        serverInfo: { name: 'lingmind-fixture', version: '1.0.0' },
      };
      break;
    case 'tools/list':
      result = { tools: [{
        name: 'read_probe', description: 'Read-only compatibility probe',
        inputSchema: { type: 'object', properties: {} },
      }] };
      break;
    case 'tools/call':
      result = { content: [{ type: 'text', text: 'ok' }] };
      break;
    default:
      result = {};
  }
  process.stdout.write(JSON.stringify({ jsonrpc: '2.0', id: request.id, result }) + '\n');
}
