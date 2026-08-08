from django.test import Client, SimpleTestCase, override_settings

from toolbox.processors import run_tool
from toolbox.registry import TOOLS, get_tool


@override_settings(ROOT_URLCONF='stackbox.urls')
class StackBoxTests(SimpleTestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)

    def test_tool_catalog_size(self):
        self.assertGreaterEqual(len(TOOLS), 70)

    def test_processor_coverage(self):
        from toolbox.processors import PROCESSORS

        for tool in TOOLS:
            self.assertIn(tool.slug, PROCESSORS)

    def test_home_ok(self):
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'StackBox')

    def test_tool_page_ok(self):
        res = self.client.get('/tools/json-format/')
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'JSON 格式化')

    def test_api_json_format(self):
        # fetch csrf
        self.client.get('/tools/json-format/')
        csrf = self.client.cookies['csrftoken'].value
        res = self.client.post(
            '/api/tools/json-format/',
            data='{"action":"minify","text":"{\\"a\\":1}"}',
            content_type='application/json',
            HTTP_X_CSRFTOKEN=csrf,
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['result'], '{"a":1}')

    def test_processors_smoke(self):
        samples = [
            ('json-format', 'format', '{"a":1}', '', {}),
            ('base64', 'encode', 'x', '', {}),
            ('hash', 'hash', 'x', '', {'algo': 'sha256'}),
            ('json-sql', 'insert', '[{"id":1}]', '', {'table': 't'}),
            ('xml-format', 'format', '<a><b>1</b></a>', '', {}),
            ('slugify', 'slugify', 'Hello World', '', {}),
            ('random', 'int', '1-10', '', {'count': '2'}),
        ]
        for slug, action, text, text_b, opts in samples:
            with self.subTest(slug=slug):
                self.assertIsNotNone(get_tool(slug))
                result = run_tool(slug, action, text, opts, text_b=text_b)
                self.assertTrue(result.get('ok', True), result)
                self.assertIn('result', result)
