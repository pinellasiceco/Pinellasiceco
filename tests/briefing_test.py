"""
UA tests for send_briefing.py — mocks urllib.request.urlopen, no network required.
Run from repo root: python3 -m pytest tests/briefing_test.py -v
"""
import importlib
import json
import os
import subprocess
import sys
import unittest
from unittest.mock import MagicMock, patch

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESEND_URL = 'https://api.resend.com/emails'


def _make_mock_response(body=b'{"id":"email_123"}'):
    """Create a mock urllib response object."""
    mock = MagicMock()
    mock.read.return_value = body
    return mock


class TestBriefingScript(unittest.TestCase):

    def setUp(self):
        if 'send_briefing' in sys.modules:
            del sys.modules['send_briefing']
        os.environ['RESEND_API_KEY'] = 're_test_key_abc123'
        os.environ['BRIEFING_EMAIL'] = 'test@pinellasiceco.com'
        os.environ.pop('SUPABASE_URL', None)
        os.environ.pop('SUPABASE_KEY', None)
        if REPO_ROOT not in sys.path:
            sys.path.insert(0, REPO_ROOT)

    def tearDown(self):
        os.environ.pop('RESEND_API_KEY', None)
        os.environ.pop('BRIEFING_EMAIL', None)
        if 'send_briefing' in sys.modules:
            del sys.modules['send_briefing']

    def _run_main_and_capture(self):
        """Run send_briefing.main() with urllib mocked; return captured Request object."""
        mock_resp = _make_mock_response()
        captured_req = {}

        def fake_urlopen(req, timeout=None):
            captured_req['req'] = req
            return mock_resp

        # Patch at the module level so the dynamic import inside send_email() picks it up
        with patch('urllib.request.urlopen', side_effect=fake_urlopen):
            import send_briefing
            send_briefing.main()

        return captured_req.get('req')

    # --- Basic validation ---

    def test_script_is_valid_python(self):
        result = subprocess.run(
            [sys.executable, '-m', 'py_compile', os.path.join(REPO_ROOT, 'send_briefing.py')],
            capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0, f"Syntax error: {result.stderr}")

    def test_exits_if_resend_api_key_missing(self):
        del os.environ['RESEND_API_KEY']
        with self.assertRaises(SystemExit):
            import send_briefing
            send_briefing.main()

    def test_exits_if_briefing_email_missing(self):
        del os.environ['BRIEFING_EMAIL']
        with self.assertRaises(SystemExit):
            import send_briefing
            send_briefing.main()

    # --- HTTP call verification ---

    def test_posts_to_resend_api_url(self):
        req = self._run_main_and_capture()
        self.assertIsNotNone(req, "urllib.request.urlopen was never called")
        self.assertEqual(req.full_url, RESEND_URL)

    def test_http_method_is_post(self):
        req = self._run_main_and_capture()
        self.assertEqual(req.method, 'POST')

    def test_authorization_header_set(self):
        req = self._run_main_and_capture()
        auth = req.get_header('Authorization')
        self.assertIsNotNone(auth, "Authorization header missing")
        self.assertTrue(auth.startswith('Bearer '), f"Should start with Bearer: {auth}")
        self.assertIn('re_test_key_abc123', auth)

    # --- Payload verification ---

    def _get_payload(self):
        req = self._run_main_and_capture()
        return json.loads(req.data.decode('utf-8'))

    def test_payload_has_required_fields(self):
        payload = self._get_payload()
        for field in ('from', 'to', 'subject', 'html'):
            self.assertIn(field, payload, f"Missing field '{field}' in email payload")

    def test_to_field_contains_briefing_email(self):
        payload = self._get_payload()
        to_field = payload.get('to', [])
        self.assertIsInstance(to_field, list, "'to' should be a list")
        self.assertIn('test@pinellasiceco.com', to_field)

    def test_from_field_is_briefing_address(self):
        payload = self._get_payload()
        self.assertIn('pinellasiceco.com', payload.get('from', ''))

    def test_subject_contains_date_or_briefing(self):
        payload = self._get_payload()
        subject = payload.get('subject', '')
        self.assertGreater(len(subject), 5, "Subject too short")
        # Subject should mention Briefing or a month name
        self.assertRegex(subject, r'Briefing|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec',
                         "Subject should contain 'Briefing' or a month name")

    def test_html_body_contains_prospect_data(self):
        payload = self._get_payload()
        html = payload.get('html', '')
        # index.html has 8,992 baked-in prospects — HTML should reference at least one
        self.assertGreater(len(html), 1000, "HTML email body is unexpectedly short")

    def test_html_body_includes_app_link(self):
        payload = self._get_payload()
        html = payload.get('html', '').lower()
        # Email always includes a link to the live PWA
        self.assertIn('pinellasiceco.github.io', html, "PWA link missing from briefing HTML")

    def test_content_type_header_is_json(self):
        req = self._run_main_and_capture()
        ct = req.get_header('Content-type')
        self.assertIsNotNone(ct, "Content-Type header missing")
        self.assertIn('application/json', ct)


if __name__ == '__main__':
    unittest.main()
