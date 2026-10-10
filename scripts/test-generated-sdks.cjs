// Exercise the built TypeScript client against an in-memory HTTP transport.
const assert = require('node:assert/strict');
const { Configuration, IncidentsApi, ClosedLoopActionsApi, MessagesApi } = require('../generated/typescript/dist');
const calls = [];
const message = { documentId: 'message-1', type: 'incident', title: '事件', content: '已处置', sourceType: 'incident', sourceId: 'incident-1', createdAt: '2026-10-10T00:00:00Z', readAt: null };
const config = new Configuration({
  basePath: 'https://sdk.invalid',
  accessToken: 'sdk-test-token',
  fetchApi: async (url, init) => {
    calls.push({ url: new URL(url), ...init });
    let body = { data: [], meta: { unread: 4, total: 20, pagination: { page: 2, pageSize: 10, total: 1, pageCount: 1 } } };
    if (url.endsWith('/incidents/stats')) body = { generatedAt: '2026-10-10T00:00:00Z', range: { type: 'month', start: '2026-09-10T00:00:00Z', end: '2026-10-10T00:00:00Z', bucket: 'day', tzOffsetMinutes: 0 }, summary: { incidentTotal: 0, openIncidentTotal: 0, overdueIncidentTotal: 0, highSeverityIncidentTotal: 0, closedIncidentTotal: 0, closureRate: 0, averageResolutionHours: null }, categories: { projects: [], spatialZones: [], rules: [] }, trends: { severity: [], types: [], projects: [], spatialZones: [], rules: [] }, recentIncidents: [] };
    if (url.endsWith('/incidents/incident-1')) body = { data: { documentId: 'incident-1', type: 'ai_incident', severity: 'warning', state: 'open' } };
    if (url.endsWith('/closed-loop-actions/action-1')) body = { data: { documentId: 'action-1', type: 'incident_resolved', state: 'succeeded', mode: 'manual', priority: 'normal' } };
    if (url.includes('/messages?')) body.data = [message];
    if (url.endsWith('/read') || url.endsWith('/read-all')) body = { data: { count: 0 } };
    if (url.endsWith('/resolve') || url.endsWith('/ignore')) body = { incidentId: 'incident-1', state: url.endsWith('/resolve') ? 'resolved' : 'ignored', resolvedAt: '2026-10-10T00:00:00Z', resolutionNote: '已处理' };
    if (url.endsWith('/closed-loop/dispatch')) body = { incidentId: 'incident-1', plannedActionIds: [], executedActionIds: [], skippedActionIds: [], failedActionIds: [] };
    return new Response(JSON.stringify(body), { status: init.method === 'POST' && url.includes('/proxy/crux/') ? 201 : 200, headers: { 'Content-Type': 'application/json' } });
  },
});

async function main() {
  const incidents = new IncidentsApi(config);
  const actions = new ClosedLoopActionsApi(config);
  const messages = new MessagesApi(config);
  const cases = [
    [incidents, 'listIncidents', { xRequestedProject: 'project-1', paginationPage: 2, paginationPageSize: 10, filtersState$eq: 'open', filtersPrimaryRuleHitDocumentId$eq: 'hit-1', responsibleForMe: true }, 'GET', '/proxy/radix/api/incidents'],
    [incidents, 'getIncident', { incidentId: 'incident-1' }, 'GET', '/proxy/radix/api/incidents/incident-1'],
    [incidents, 'getIncidentStats', {}, 'GET', '/proxy/radix/api/incidents/stats'],
    [incidents, 'resolveIncident', { incidentId: 'incident-1', disposeIncidentRequest: { note: '已处置', retestResultId: 'retest-1', dispositionEvidenceIds: ['raw-1'] } }, 'POST', '/proxy/crux/api/ai/incidents/incident-1/resolve'],
    [incidents, 'ignoreIncident', { incidentId: 'incident-1', disposeIncidentRequest: { note: '无需处置' } }, 'POST', '/proxy/crux/api/ai/incidents/incident-1/ignore'],
    [actions, 'listClosedLoopActions', { filtersIncidentDocumentId$eq: 'incident-1' }, 'GET', '/proxy/radix/api/closed-loop-actions'],
    [actions, 'getClosedLoopAction', { closedLoopActionId: 'action-1' }, 'GET', '/proxy/radix/api/closed-loop-actions/action-1'],
    [actions, 'dispatchIncidentClosedLoop', { incidentId: 'incident-1', body: {} }, 'POST', '/proxy/crux/api/ai/incidents/incident-1/closed-loop/dispatch'],
    [messages, 'listMessages', { page: 2, pageSize: 10, unread: true, type: 'incident', search: '铁路事件', days: '7' }, 'GET', '/proxy/radix/api/messages'],
    [messages, 'markMessageRead', { messageId: 'message-1' }, 'POST', '/proxy/radix/api/messages/message-1/read'],
    [messages, 'markAllMessagesRead', {}, 'POST', '/proxy/radix/api/messages/read-all'],
  ];
  for (const [api, name, params, method, path] of cases) {
    const result = await api[name](params);
    const request = calls.at(-1);
    assert.equal(request.method, method);
    assert.equal(request.url.pathname, path);
    assert.equal(request.headers.Authorization, 'Bearer sdk-test-token');
    if (name === 'listMessages') {
      assert.equal(result.data[0].readAt, null);
      assert.equal(result.meta.total, 20);
      assert.equal(result.meta.pagination.total, 1);
      assert.equal(request.url.searchParams.get('pageSize'), '10');
      assert.equal(request.url.searchParams.get('unread'), 'true');
      assert.equal(request.url.searchParams.get('search'), '铁路事件');
      assert.equal(request.url.searchParams.get('days'), '7');
      assert.equal(request.headers['X-Requested-Project'], undefined);
    }
    if (name === 'listIncidents') {
      assert.equal(request.headers['X-Requested-Project'], 'project-1');
      assert.equal(request.url.searchParams.get('pagination[page]'), '2');
      assert.equal(request.url.searchParams.get('filters[state][$eq]'), 'open');
      assert.equal(request.url.searchParams.get('filters[primaryRuleHit][documentId][$eq]'), 'hit-1');
    }
    if (name === 'listClosedLoopActions') assert.equal(request.url.searchParams.get('filters[incident][documentId][$eq]'), 'incident-1');
    if (name === 'resolveIncident') assert.deepEqual(JSON.parse(request.body), params.disposeIncidentRequest);
    if (name.startsWith('mark')) {
      assert.equal(request.body, undefined);
      assert.equal(result.data.count, 0);
    }
  }
  console.log('TypeScript: all 11 new requests, auth, filters, request bodies and message responses passed');
}
main().catch(error => { console.error(error); process.exitCode = 1; });
