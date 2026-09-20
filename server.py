#!/usr/bin/env python3
"""Simple server with no-cache headers so the preview always gets fresh code."""
from http.server import SimpleHTTPRequestHandler, HTTPServer

class NoCacheHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

if __name__ == '__main__':
    HTTPServer(('0.0.0.0', 8080), NoCacheHandler).serve_forever()
