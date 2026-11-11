"""Real multipart HTTP and child-process/cache tests, without paid endpoints."""
import base64
from email import policy
from email.parser import BytesParser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import generate_image as g
import prepare_assets as r


class ReferenceInputsTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.refs = []
        for i, color in enumerate(['red', 'green']):
            path = self.root / f'ref-{i}.png'
            Image.new('RGB', (21, 14), color).save(path)
            self.refs.append({'path': path.name, 'role': ['structure only', 'composition only'][i]})
        self.requests = []
        requests = self.requests
        buffer = io.BytesIO()
        Image.new('RGB', (32, 24), 'blue').save(buffer, format='PNG')
        encoded = base64.b64encode(buffer.getvalue()).decode()

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                raw = self.rfile.read(int(self.headers['Content-Length']))
                mime = ('Content-Type: ' + self.headers['Content-Type'] + '\r\n\r\n').encode() + raw
                msg = BytesParser(policy=policy.default).parsebytes(mime)
                requests.append({'path': self.path, 'raw': raw, 'parts': list(msg.iter_parts()),
                                 'authorization': self.headers.get('Authorization')})
                response = json.dumps({'data': [{'b64_json': encoded}]}).encode()
                self.send_response(415 if self.path == '/reject' else 200)
                self.send_header('Content-Length', str(len(response)))
                self.end_headers()
                self.wfile.write(response)

            def log_message(self, *_):
                pass

        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.close_server)
        self.url = f'http://127.0.0.1:{self.server.server_port}'
        env = patch.dict(os.environ, {'ASSET_IMAGE_ENDPOINT': self.url + '/images/generations',
            'ASSET_IMAGE_EDIT_ENDPOINT': '', 'ASSET_IMAGE_MODEL': 'local-image',
            'ASSET_IMAGE_API_KEY': 'private-test-key', 'ASSET_IMAGE_SIZE': '1536x864',
            'ASSET_IMAGE_QUALITY': 'high', 'ASSET_IMAGE_HTTP_PROXY': ''})
        env.start()
        self.addCleanup(env.stop)

    def close_server(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def job(self):
        jobs = r.prepare_jobs(self.root / 'plan.json', {'assets': [{
            'id': 'A', 'prompt': '中文方法图 fixture', 'output': 'output.png',
            'reference_images': self.refs, 'analysis_basis': 'fixture reference input',
            'visual_brief': 'fixture conditioned decoration',
            'prompt_review': 'reference roles reviewed', 'asset_role': 'decoration',
            'generation_mode': 'reference-conditioned', 'page_ids': ['P01'],
            'project_terms': ['fixture', 'method']}]})
        r.configure_jobs(jobs)
        return jobs[0]

    def assert_uploaded(self):
        req = self.requests[-1]
        self.assertEqual('/images/edits', req['path'])
        images = [p for p in req['parts'] if p.get_param('name', header='content-disposition') == 'image[]']
        self.assertEqual(2, len(images))
        for i, part in enumerate(images):
            self.assertEqual((self.root / self.refs[i]['path']).read_bytes(), part.get_payload(decode=True))
            self.assertEqual('image/png', part.get_content_type())
        prompt = next(p for p in req['parts'] if p.get_param('name', header='content-disposition') == 'prompt')
        prompt = prompt.get_payload(decode=True).decode()
        self.assertIn('中文方法图', prompt)
        self.assertLess(prompt.index('Image 1: structure only'), prompt.index('Image 2: composition only'))

    def test_real_uploads_both_transports_with_ordered_roles(self):
        for transport in ['curl', 'urllib']:
            with self.subTest(transport=transport), patch.dict(os.environ, {'ASSET_IMAGE_HTTP_TRANSPORT': transport}):
                if transport == 'curl' and not g.shutil.which('curl.exe' if os.name == 'nt' else 'curl'):
                    continue
                refs = g.resolve_references(self.refs, self.root)
                payload = {'prompt': g.conditioned_prompt('中文方法图', refs), 'n': 1}
                g.request_image(g.reference_endpoint(), 'private-test-key', payload, refs)
                self.assert_uploaded()

    def test_child_metadata_and_cache_preserve_reference_identity(self):
        job = self.job()
        result = r.generate_job(job, self.root / 'unused.env', 20)
        self.assertEqual('generated', result['status'], result)
        self.assert_uploaded()
        meta = json.loads(job['output'].with_suffix('.png.json').read_text(encoding='utf-8'))
        self.assertEqual('reference-conditioned', meta['input_mode'])
        self.assertEqual(job['reference_images'], meta['reference_images'])
        self.assertTrue(r.reusable(job))
        for change in ['role', 'order', 'bytes']:
            with self.subTest(change=change):
                original = job['signature']
                if change == 'role':
                    job['reference_images'][0]['role'] += ' changed'
                elif change == 'order':
                    job['reference_images'].reverse()
                else:
                    Image.new('RGB', (21, 14), 'yellow').save(self.root / self.refs[0]['path'])
                r.configure_jobs([job])
                self.assertNotEqual(original, job['signature'])
                self.assertFalse(r.reusable(job))

    def test_rejected_reference_request_never_falls_back_to_text(self):
        with patch.dict(os.environ, {'ASSET_IMAGE_EDIT_ENDPOINT': self.url + '/reject'}):
            result = r.generate_job(self.job(), self.root / 'unused.env', 20)
        self.assertEqual('failed', result['status'])
        self.assertIn('HTTP 415', result['error'])
        self.assertEqual(['/reject'], [x['path'] for x in self.requests])
        self.assertFalse((self.root / 'output.png').exists())

    def test_missing_invalid_or_unexplained_reference_fails_locally(self):
        for refs in [[{'path': 'missing.png', 'role': 'structure'}], [{'path': 'ref-0.png'}]]:
            with self.assertRaises((ValueError, OSError)):
                g.resolve_references(refs, self.root)
        (self.root / 'bad.png').write_bytes(b'not png')
        with self.assertRaises(OSError):
            g.resolve_references([{'path': 'bad.png', 'role': 'style'}], self.root)
        self.assertEqual([], self.requests)

    def test_custom_routes_need_explicit_edit_route(self):
        self.assertEqual(self.url + '/images/edits', g.reference_endpoint())
        with patch.dict(os.environ, {'ASSET_IMAGE_ENDPOINT': self.url + '/custom'}):
            with self.assertRaisesRegex(SystemExit, 'ASSET_IMAGE_EDIT_ENDPOINT'):
                g.reference_endpoint()
        with patch.dict(os.environ, {'ASSET_IMAGE_EDIT_ENDPOINT': self.url + '/custom-edit'}):
            self.assertEqual(self.url + '/custom-edit', g.reference_endpoint())


if __name__ == '__main__':
    unittest.main()
