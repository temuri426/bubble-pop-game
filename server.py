#!/usr/bin/env python3
"""
Bubble Pop Game custom server.

Serves the game AND lets it read video files from ANY folder path on this PC
(including absolute paths like D:\\YT videos) without any browser file-picker
or upload prompt.

Endpoints:
  GET /                  -> the game (static files from the game directory)
  GET /api/list_videos?folder=<path>
                         -> JSON list of video filenames in <path>
  GET /video?folder=<path>&name=<file>
                         -> streams <file> with HTTP Range support (for seeking)
"""
import os
import re
import json
import subprocess
import tempfile
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

GAME_DIR = os.path.dirname(os.path.abspath(__file__))
VIDEO_EXTS = {'.mp4', '.webm', '.ogg', '.mov', '.m4v', '.mkv', '.avi', '.flv'}

# PowerShell script that opens the native Windows "Browse for Folder" dialog
# and prints the selected absolute path (or nothing if cancelled). Run with
# -STA so the WinForms dialog works reliably.
_FOLDER_PICKER_PS = r"""
Add-Type -AssemblyName System.Windows.Forms -ErrorAction SilentlyContinue
Add-Type -AssemblyName System.Drawing -ErrorAction SilentlyContinue
[System.Windows.Forms.Application]::EnableVisualStyles()

# Win32 helper to force the dialog to the foreground
Add-Type @'
using System;
using System.Runtime.InteropServices;
public class Win32 {
    [DllImport("user32.dll")]
    public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")]
    public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
}
'@

# Create an invisible top-most owner form so the dialog pops in front.
$owner = New-Object System.Windows.Forms.Form
$owner.TopMost = $true
$owner.Opacity = 0
$owner.ShowInTaskbar = $false
$owner.WindowState = [System.Windows.Forms.FormWindowState]::Minimized
[void]$owner.Show()

$d = New-Object System.Windows.Forms.FolderBrowserDialog
$d.Description = 'Select the folder that contains reward videos'
$d.ShowNewFolderButton = $false

# Bring the dialog to the foreground
$result = $d.ShowDialog($owner)
if ($result -eq [System.Windows.Forms.DialogResult]::OK) {
    Write-Output $d.SelectedPath
}
$owner.Dispose()
"""


class BubblePopHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # directory=GAME_DIR makes static file serving resolve from the game folder
        super().__init__(*args, directory=GAME_DIR, **kwargs)

    # ---------- helpers ----------
    def _resolve_folder(self, folder):
        folder = (folder or '').strip()
        if not folder:
            return GAME_DIR
        if os.path.isabs(folder):
            return os.path.normpath(folder)
        return os.path.normpath(os.path.join(GAME_DIR, folder))

    def _send_json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def _list_videos(self, folder):
        abs_folder = self._resolve_folder(folder)
        if not os.path.isdir(abs_folder):
            return {'ok': False, 'error': 'folder not found', 'folder': folder,
                    'resolved': abs_folder, 'videos': []}
        videos = []
        for name in sorted(os.listdir(abs_folder)):
            ext = os.path.splitext(name)[1].lower()
            if ext in VIDEO_EXTS:
                videos.append(name)
        return {'ok': True, 'folder': folder, 'resolved': abs_folder,
                'videos': videos}



    def _pick_folder(self):
        """Open a native Windows 'Browse for Folder' dialog and return the path."""
        try:
            with tempfile.NamedTemporaryFile('w', suffix='.ps1', delete=False, encoding='utf-8') as tf:
                tf.write(_FOLDER_PICKER_PS)
                ps1 = tf.name
            cmd = ['powershell', '-NoProfile', '-STA', '-ExecutionPolicy', 'Bypass', '-File', ps1]
            result = subprocess.run(cmd, capture_output=True, timeout=120)
            os.unlink(ps1)
            out = (result.stdout or '').decode('utf-8', errors='replace').strip()
            if result.returncode == 0 and out:
                # sift for a line that looks like an absolute drive path
                for line in out.splitlines():
                    line = line.strip()
                    if len(line) >= 3 and (line[1:2] == ':' or line.startswith('\\')):
                        return {'ok': True, 'folder': os.path.normpath(line)}
                return {'ok': False, 'error': 'no path selected / cancelled'}
            return {'ok': False, 'error': 'dialog cancelled or failed (rc=%s)' % result.returncode}
        except Exception as e:
            return {'ok': False, 'error': 'folder picker failed: %s' % e}

    def _serve_video(self, file_path):
        size = os.path.getsize(file_path)
        start, end = 0, size - 1
        range_header = self.headers.get('Range')
        status = 200
        if range_header:
            m = re.match(r'bytes=(\d*)-(\d*)', range_header)
            if m and (m.group(1) or m.group(2)):
                if m.group(1):
                    start = int(m.group(1))
                if m.group(2):
                    end = int(m.group(2))
                end = min(end, size - 1)
                status = 206
        length = end - start + 1
        ctype = self.guess_type(file_path) or 'application/octet-stream'
        self.send_response(status)
        self.send_header('Content-Type', ctype)
        self.send_header('Accept-Ranges', 'bytes')
        self.send_header('Content-Length', str(length))
        if status == 206:
            self.send_header('Content-Range', 'bytes %d-%d/%d' % (start, end, size))
        self.end_headers()
        with open(file_path, 'rb') as f:
            f.seek(start)
            remaining = length
            while remaining > 0:
                chunk = f.read(min(65536, remaining))
                if not chunk:
                    break
                self.wfile.write(chunk)
                remaining -= len(chunk)

    # ---------- routing ----------
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        qs = parse_qs(parsed.query)

        if path == '/api/pick_folder':
            self._send_json(self._pick_folder())
            return

        if path == '/api/list_videos':
            folder = qs.get('folder', [''])[0]
            self._send_json(self._list_videos(folder))
            return

        if path == '/video':
            folder = qs.get('folder', [''])[0]
            name = qs.get('name', [''])[0]
            if not name:
                self.send_error(400, 'missing name')
                return
            abs_folder = self._resolve_folder(folder)
            file_path = os.path.normpath(os.path.join(abs_folder, name))
            # Keep the request inside the chosen folder (basic path-traversal guard)
            if not (os.path.abspath(file_path).startswith(os.path.abspath(abs_folder) + os.sep)
                    or os.path.dirname(os.path.abspath(file_path)) == os.path.abspath(abs_folder)):
                self.send_error(403, 'forbidden')
                return
            if not os.path.isfile(file_path):
                self.send_error(404, 'not found')
                return
            self._serve_video(file_path)
            return

        # Everything else -> static game files
        return super().do_GET()

    def do_HEAD(self):
        # SimpleHTTPRequestHandler handles HEAD; delegate for static files.
        super().do_HEAD()

    def log_message(self, fmt, *args):
        # Quiet, but UNCOMMENT the next line for verbose request logging.
        # print('%s %s' % (self.address_string(), fmt % args))
        pass


def main():
    port = 8080
    httpd = ThreadingHTTPServer(('127.0.0.1', port), BubblePopHandler)
    print('Bubble Pop server running at http://localhost:%d' % port)
    print('Game folder: %s' % GAME_DIR)
    print('Press Ctrl+C to stop.')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('\nStopping server...')
        httpd.shutdown()


if __name__ == '__main__':
    main()