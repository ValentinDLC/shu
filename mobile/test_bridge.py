import json
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from unittest.mock import patch

import dev_server


class YouTubeUrlTests(unittest.TestCase):
    def test_accepts_youtube_and_short_links(self):
        self.assertTrue(dev_server.is_youtube_url('https://www.youtube.com/watch?v=abc'))
        self.assertTrue(dev_server.is_youtube_url('https://youtu.be/abc'))
        self.assertTrue(dev_server.is_youtube_url('https://music.youtube.com/watch?v=abc'))

    def test_rejects_non_youtube_and_unsafe_urls(self):
        for value in (
            'http://youtube.com/watch?v=abc',
            'https://youtube.com.example.org/watch?v=abc',
            'https://example.com/watch?v=abc',
            'file:///etc/passwd',
            'https://user:pass@youtube.com/watch?v=abc',
            'https://youtube.com:8443/watch?v=abc',
            'not a url',
        ):
            with self.subTest(value=value):
                self.assertFalse(dev_server.is_youtube_url(value))

    def test_title_is_safe_and_bounded(self):
        self.assertEqual(dev_server.safe_title('Cours: Intro/Partie?'), 'Cours_ Intro_Partie_')
        self.assertLessEqual(len(dev_server.safe_title('x' * 300)), 160)

    def test_download_options_limit_duration_and_playlists(self):
        fake_info = {}
        class FakeYDL:
            def __init__(self, options):
                self.options = options
            def __enter__(self):
                return self
            def __exit__(self, *_args):
                return False
            def extract_info(self, _url, download):
                self.assert_download = download
                output = Path(self.options['outtmpl'].replace('.%(ext)s', '.mp3'))
                output.write_bytes(b'mp3-data')
                fake_info['filter'] = self.options['match_filter']
                return {'title': 'A/B'}
        with tempfile.TemporaryDirectory() as directory, patch.object(dev_server.yt_dlp, 'YoutubeDL', FakeYDL):
            audio_path, title = dev_server.download_youtube_audio('https://youtu.be/abc', Path(directory))
            self.assertEqual(audio_path.read_bytes(), b'mp3-data')
            self.assertEqual(title, 'A_B')
            self.assertTrue(fake_info['filter']({'duration': 3 * 60 * 60 + 1}, incomplete=False))
            self.assertIsNone(fake_info['filter']({'duration': 60}, incomplete=False))


class ApiErrorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original_token = dev_server.ACCESS_TOKEN
        dev_server.ACCESS_TOKEN = 'test-session-token'
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), dev_server.BridgeHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f'http://127.0.0.1:{cls.server.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)
        dev_server.ACCESS_TOKEN = cls.original_token

    def post(self, url, token=None):
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        request = Request(self.base + '/api/youtube-audio', data=json.dumps({'url': url}).encode(), headers=headers, method='POST')
        try:
            with urlopen(request, timeout=3) as response:
                return response.status, response.read()
        except HTTPError as error:
            return error.code, error.read()

    def test_missing_access_code_is_rejected(self):
        status, body = self.post('https://youtu.be/abc')
        self.assertEqual(status, 401)
        self.assertIn('non autorisée', json.loads(body)['error'])

    def test_non_youtube_url_is_rejected_before_download(self):
        with patch.object(dev_server, 'download_youtube_audio') as download:
            status, body = self.post('https://example.com/video', 'test-session-token')
        self.assertEqual(status, 400)
        self.assertIn('YouTube', json.loads(body)['error'])
        download.assert_not_called()

    def test_invalid_request_body_is_rejected(self):
        request = Request(self.base + '/api/youtube-audio', data=b'{bad json', headers={
            'Content-Type': 'application/json', 'Authorization': 'Bearer test-session-token'
        }, method='POST')
        with self.assertRaises(HTTPError) as context:
            urlopen(request, timeout=3)
        self.assertEqual(context.exception.code, 400)


if __name__ == '__main__':
    unittest.main()
