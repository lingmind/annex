#!/usr/bin/env python3
"""Exercise generated Python requests and response models without a live environment."""
import inspect
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'generated/python'))
from lingmind_annex import ApiClient, Configuration
from lingmind_annex.api.closed_loop_actions_api import ClosedLoopActionsApi
from lingmind_annex.api.incidents_api import IncidentsApi
from lingmind_annex.api.messages_api import MessagesApi
from lingmind_annex.models.dispose_incident_request import DisposeIncidentRequest
from lingmind_annex.models.message_list_response import MessageListResponse
from lingmind_annex.models.message_read_response import MessageReadResponse


class GeneratedSDKTests(unittest.IsolatedAsyncioTestCase):
    def test_api_groups(self):
        expected = {'Auth', 'Devices', 'Missions', 'RawData', 'RuleHits', 'Incidents', 'ClosedLoopActions', 'Messages'}
        for directory, extension in [('typescript/src/apis', '.ts'), ('java/src/main/java/com/lingmind/annex/api', '.java')]:
            actual = {file.stem.removesuffix('Api') for file in (ROOT / 'generated' / directory).glob('*Api' + extension)}
            self.assertEqual(actual, expected)

    def test_generator_failure_preserves_outputs(self):
        outputs = [ROOT / 'generated' / name / '.openapi-generator/FILES' for name in ['typescript', 'python', 'java']]
        before = [file.read_bytes() for file in outputs]
        for version, expected_exit in [('placeholder', 1), ('7.25.0', 42)]:
            with self.subTest(version=version), tempfile.TemporaryDirectory() as directory:
                generator = Path(directory) / 'openapi-generator-cli'
                generator.write_text(f'#!/bin/sh\nif [ "$1" = version ]; then echo {version}; else exit 42; fi\n')
                generator.chmod(0o755)
                env = {**os.environ, 'PATH': directory + os.pathsep + os.environ['PATH']}
                result = subprocess.run(['bash', str(ROOT / 'scripts/generate-sdks.sh')], env=env, capture_output=True, text=True)
                self.assertEqual(result.returncode, expected_exit)
                self.assertEqual([file.read_bytes() for file in outputs], before)
                self.assertFalse(list((ROOT / 'generated').glob('.sdk-generation.*')))

    async def asyncSetUp(self):
        self.client = ApiClient(Configuration(host='https://sdk.invalid', access_token='sdk-test-token'))

    async def asyncTearDown(self):
        await self.client.close()

    def request(self, api, name, **values):
        serialize = getattr(api(self.client), '_' + name + '_serialize')
        args = {key: None for key in inspect.signature(serialize).parameters}
        args.update(values)
        return serialize(**args)

    async def test_all_new_requests(self):
        cases = [
            (IncidentsApi, 'list_incidents', 'GET', '/proxy/radix/api/incidents', {}),
            (IncidentsApi, 'get_incident', 'GET', '/proxy/radix/api/incidents/incident-1', {'incident_id': 'incident-1'}),
            (IncidentsApi, 'get_incident_stats', 'GET', '/proxy/radix/api/incidents/stats', {}),
            (IncidentsApi, 'resolve_incident', 'POST', '/proxy/crux/api/ai/incidents/incident-1/resolve', {'incident_id': 'incident-1', 'dispose_incident_request': DisposeIncidentRequest(note='已处置', retestResultId='retest-1', dispositionEvidenceIds=['raw-1'])}),
            (IncidentsApi, 'ignore_incident', 'POST', '/proxy/crux/api/ai/incidents/incident-1/ignore', {'incident_id': 'incident-1', 'dispose_incident_request': DisposeIncidentRequest(note='无需处置')}),
            (ClosedLoopActionsApi, 'list_closed_loop_actions', 'GET', '/proxy/radix/api/closed-loop-actions', {}),
            (ClosedLoopActionsApi, 'get_closed_loop_action', 'GET', '/proxy/radix/api/closed-loop-actions/action-1', {'closed_loop_action_id': 'action-1'}),
            (ClosedLoopActionsApi, 'dispatch_incident_closed_loop', 'POST', '/proxy/crux/api/ai/incidents/incident-1/closed-loop/dispatch', {'incident_id': 'incident-1', 'body': {}}),
            (MessagesApi, 'list_messages', 'GET', '/proxy/radix/api/messages', {}),
            (MessagesApi, 'mark_message_read', 'POST', '/proxy/radix/api/messages/message-1/read', {'message_id': 'message-1'}),
            (MessagesApi, 'mark_all_messages_read', 'POST', '/proxy/radix/api/messages/read-all', {}),
        ]
        for api, name, method, path, values in cases:
            with self.subTest(name=name):
                actual, url, headers, body, _ = self.request(api, name, **values)
                self.assertEqual((actual, urlsplit(url).path), (method, path))
                self.assertEqual(headers['Authorization'], 'Bearer sdk-test-token')
                if name == 'resolve_incident':
                    self.assertEqual(body['retestResultId'], 'retest-1')
                    self.assertEqual(body['dispositionEvidenceIds'], ['raw-1'])
                if name.startswith('mark_'):
                    self.assertIsNone(body)

    async def test_bracket_filters_and_project_header(self):
        _, url, headers, _, _ = self.request(IncidentsApi, 'list_incidents', x_requested_project='project-1', pagination_page=2, pagination_page_size=10, filters_state_eq='open', filters_primary_rule_hit_document_id_eq='hit-1', responsible_for_me=True)
        query = parse_qs(urlsplit(url).query)
        self.assertEqual(query['pagination[page]'], ['2'])
        self.assertEqual(query['pagination[pageSize]'], ['10'])
        self.assertEqual(query['filters[state][$eq]'], ['open'])
        self.assertEqual(query['filters[primaryRuleHit][documentId][$eq]'], ['hit-1'])
        self.assertEqual(query['responsibleForMe'], ['true'])
        self.assertEqual(headers['X-Requested-Project'], 'project-1')
        _, url, _, _, _ = self.request(ClosedLoopActionsApi, 'list_closed_loop_actions', filters_incident_document_id_eq='incident-1')
        self.assertEqual(parse_qs(urlsplit(url).query)['filters[incident][documentId][$eq]'], ['incident-1'])

    async def test_message_filters_and_response(self):
        _, url, headers, _, _ = self.request(MessagesApi, 'list_messages', page=2, page_size=10, unread=True, type='incident', search='铁路事件', days='7')
        query = parse_qs(urlsplit(url).query)
        self.assertEqual(query['pageSize'], ['10'])
        self.assertEqual(query['unread'], ['true'])
        self.assertEqual(query['search'], ['铁路事件'])
        self.assertEqual(query['days'], ['7'])
        self.assertNotIn('X-Requested-Project', headers)
        response = MessageListResponse.from_dict({'data': [{'documentId': 'message-1', 'type': 'incident', 'title': '事件', 'content': '已处置', 'sourceType': 'incident', 'sourceId': 'incident-1', 'createdAt': '2026-10-10T00:00:00Z', 'readAt': None}], 'meta': {'unread': 4, 'total': 20, 'pagination': {'page': 2, 'pageSize': 10, 'pageCount': 1, 'total': 1}}})
        self.assertIsNone(response.data[0].read_at)
        self.assertEqual(response.meta.total, 20)
        self.assertEqual(response.meta.pagination.total, 1)
        self.assertEqual(MessageReadResponse.from_dict({'data': {'count': 0}}).data.count, 0)


if __name__ == '__main__':
    unittest.main()
