import sys
import os
import gzip
import time
import socket
import threading
import queue
import traceback
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Iterable, Union

# ---------- GUI (PySide6) ----------
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QApplication, QWidget, QGridLayout, QLabel, QLineEdit, QPushButton,
    QTextEdit, QFileDialog, QComboBox, QSpinBox, QCheckBox, QHBoxLayout,
    QVBoxLayout, QGroupBox, QRadioButton, QPlainTextEdit
)

# ------------------ Core HTTP Builder ------------------

CRLF = b"\r\n"

@dataclass
class ClientOptions:
    host: str
    port: int
    path: str
    method: str  # POST/PUT/PATCH/DELETE
    keep_alive: bool
    use_chunked: bool
    chunk_size: int
    chunk_ext: str  # e.g. foo=bar
    use_gzip: bool
    use_multipart: bool
    extra_headers: Dict[str, str]
    trailing_headers: Dict[str, str]
    connect_timeout: float = 5.0
    read_timeout: float = 5.0
    fire_and_go: bool = True  # send and do minimal read
    http_version: str = "HTTP/1.1"  # fixed
    # Body mode
    body_text: Optional[bytes] = None
    file_path: Optional[str] = None
    # Multipart fields
    multipart_field_name: str = "file"
    multipart_text_fields: Dict[str, str] = field(default_factory=dict)
    multipart_filename_override: Optional[str] = None


def parse_header_lines(raw: str) -> Dict[str, str]:
    headers: Dict[str, str] = {}
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        if ":" in line:
            k, v = line.split(":", 1)
            headers[k.strip()] = v.strip()
    return headers


def build_request_headers_firstline(opts: ClientOptions, host_header: Optional[str] = None) -> bytearray:
    first = f"{opts.method} {opts.path} {opts.http_version}".encode("ascii")
    buf = bytearray(first + CRLF)
    host_val = host_header if host_header else f"{opts.host}:{opts.port}"
    buf += f"Host: {host_val}".encode("ascii") + CRLF
    # keep-alive
    buf += (b"Connection: keep-alive" if opts.keep_alive else b"Connection: close") + CRLF
    # add extra headers later (caller)
    return buf


def add_header_lines(buf: bytearray, headers: Dict[str, str]):
    for k, v in headers.items():
        # ensure ascii-safe
        line = f"{k}: {v}".encode("utf-8")
        buf += line + CRLF


def gzip_bytes(data: bytes) -> bytes:
    return gzip.compress(data)


def iter_file_chunks(path: str, chunk_size: int) -> Iterable[bytes]:
    with open(path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            yield chunk


def multipart_iter(
    filespec: Tuple[str, Optional[str], Iterable[bytes]],
    boundary: str,
    text_fields: Dict[str, str],
    filename_override: Optional[str],
    field_name: str,
) -> Iterable[bytes]:
    # text fields
    for k, v in text_fields.items():
        yield f"--{boundary}\r\n".encode()
        yield f'Content-Disposition: form-data; name="{k}"\r\n\r\n'.encode()
        yield v.encode("utf-8")
        yield CRLF
    # file
    file_path, mime, stream_iter = filespec
    filename = filename_override or os.path.basename(file_path)
    mime = mime or "application/octet-stream"
    yield f"--{boundary}\r\n".encode()
    yield f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"\r\n'.encode()
    yield f"Content-Type: {mime}\r\n\r\n".encode()
    for chunk in stream_iter:
        yield chunk
    yield CRLF
    # closing boundary
    yield f"--{boundary}--\r\n".encode()


def calc_iter_length(it: Iterable[bytes]) -> int:
    total = 0
    for part in it:
        total += len(part)
    return total


def clone_iter(it: Iterable[bytes]) -> List[bytes]:
    data = []
    for part in it:
        data.append(part)
    return data


def encode_headers_for_trailer_decl(trailers: Dict[str, str]) -> Optional[str]:
    if not trailers:
        return None
    # Trailer header lists the field-names that will appear in the trailer section
    # e.g. Trailer: Foo, Bar
    return ", ".join(trailers.keys())


class HttpConnection:
    def __init__(self, opts: ClientOptions):
        self.opts = opts
        self.sock: Optional[socket.socket] = None

    def connect(self):
        s = socket.create_connection((self.opts.host, self.opts.port), timeout=self.opts.connect_timeout)
        s.settimeout(self.opts.read_timeout)
        self.sock = s

    def close(self):
        try:
            if self.sock:
                self.sock.close()
        finally:
            self.sock = None

    # Minimal response read: read headers only (or small chunk) then return.
    def _minimal_read_response(self):
        try:
            if not self.sock:
                return
            self.sock.settimeout(0.3)
            data = b""
            # read until header end or timeout
            while b"\r\n\r\n" not in data and len(data) < 65536:
                chunk = self.sock.recv(4096)
                if not chunk:
                    break
                data += chunk
        except Exception:
            pass

    def send_request_content_length(self, body_iter: Iterable[bytes], declared_len: int, is_trailer: bool = False):
        # Build initial headers
        buf = build_request_headers_firstline(self.opts)
        # gzip?
        if self.opts.use_gzip:
            buf += b"Content-Encoding: gzip\r\n"
        # content-length
        buf += f"Content-Length: {declared_len}".encode("ascii") + CRLF
        # trailers not allowed with Content-Length body (HTTP/1.1 allows trailers with chunked only)
        trailer_decl = encode_headers_for_trailer_decl(self.opts.trailing_headers)
        if trailer_decl:
            # Spec-wise, trailers apply with chunked; warn by adding custom header
            buf += b"X-Warning: Trailer headers require chunked encoding\r\n"

        # extra headers
        add_header_lines(buf, self.opts.extra_headers)
        buf += CRLF

        # send headers
        self.sock.sendall(buf)
        # send body
        for part in body_iter:
            self.sock.sendall(part)

        if self.opts.fire_and_go:
            self._minimal_read_response()

    def send_request_chunked(self, body_iter: Iterable[bytes]):
        buf = build_request_headers_firstline(self.opts)
        # Transfer-Encoding: chunked
        buf += b"Transfer-Encoding: chunked\r\n"
        # gzip?
        if self.opts.use_gzip:
            buf += b"Content-Encoding: gzip\r\n"
        # Declare trailers (so we can send trailing headers after 0-chunk)
        trailer_decl = encode_headers_for_trailer_decl(self.opts.trailing_headers)
        if trailer_decl:
            buf += f"Trailer: {trailer_decl}".encode("ascii") + CRLF
        # extra headers
        add_header_lines(buf, self.opts.extra_headers)
        buf += CRLF
        self.sock.sendall(buf)

        ext = ""
        if self.opts.chunk_ext.strip():
            # e.g. ;foo=bar or ;foo
            ce = self.opts.chunk_ext.strip()
            if not ce.startswith(";"):
                ce = ";" + ce
            ext = ce

        # send chunks
        for part in body_iter:
            if not part:
                continue
            size = f"{len(part):X}".encode("ascii")
            self.sock.sendall(size + ext.encode("ascii") + CRLF + part + CRLF)

        # terminating 0-chunk
        self.sock.sendall(b"0" + ext.encode("ascii") + CRLF)

        # Trailing headers (if any)
        for k, v in self.opts.trailing_headers.items():
            line = f"{k}: {v}".encode("utf-8")
            self.sock.sendall(line + CRLF)
        # end of message
        self.sock.sendall(CRLF)

        if self.opts.fire_and_go:
            self._minimal_read_response()

    def perform(self):
        # Prepare body iterator according to options
        if self.opts.use_multipart:
            # multipart form-data stream
            boundary = f"----PyBlastBoundary{int(time.time()*1000)}"
            filespec = (
                self.opts.file_path or "",
                None,
                iter_file_chunks(self.opts.file_path, self.opts.chunk_size) if self.opts.file_path else [self.opts.body_text or b""],
            )
            body_gen = multipart_iter(
                filespec, boundary, self.opts.multipart_text_fields,
                self.opts.multipart_filename_override, self.opts.multipart_field_name
            )

            # possible gzip
            if self.opts.use_gzip:
                # For Content-Length mode we must buffer to know length; for chunked we can stream-compress
                if self.opts.use_chunked:
                    # stream+gzip: simple approach -> buffer (for simplicity & robustness here)
                    data = b"".join(body_gen)
                    gz = gzip_bytes(data)
                    body_iter = [gz]
                    declared_len = len(gz)
                    # Although we chose chunked, we can still send single big chunk(s)
                    if self.opts.use_chunked:
                        self.send_request_chunked(body_iter)
                        return
                else:
                    data = b"".join(body_gen)
                    gz = gzip_bytes(data)
                    self.send_request_content_length([gz], len(gz))
                    return
            else:
                if self.opts.use_chunked:
                    self.send_request_chunked(body_gen)
                    return
                else:
                    # Need content-length -> buffer
                    parts = clone_iter(body_gen)
                    total = sum(len(p) for p in parts)
                    self.send_request_content_length(parts, total)
                    return

            return

        # Non-multipart (raw text or single file)
        if self.opts.file_path:
            if self.opts.use_gzip and not self.opts.use_chunked:
                # need known length -> gzip whole file
                with open(self.opts.file_path, "rb") as f:
                    gz = gzip_bytes(f.read())
                self.send_request_content_length([gz], len(gz))
                return

            if self.opts.use_chunked:
                # optional gzip: for simplicity, if gzip+chunked, gzip whole file first (memory ok for demo)
                if self.opts.use_gzip:
                    with open(self.opts.file_path, "rb") as f:
                        gz = gzip_bytes(f.read())
                    self.send_request_chunked([gz])
                else:
                    self.send_request_chunked(iter_file_chunks(self.opts.file_path, self.opts.chunk_size))
            else:
                # content-length
                file_size = os.path.getsize(self.opts.file_path)
                if self.opts.use_gzip:
                    # handled above
                    pass
                self.send_request_content_length(iter_file_chunks(self.opts.file_path, 8192), file_size)
            return

        # Text body
        body = self.opts.body_text or b""
        if self.opts.use_gzip:
            body = gzip_bytes(body)

        if self.opts.use_chunked:
            self.send_request_chunked([body])
        else:
            self.send_request_content_length([body], len(body))


# ------------------ Worker / Dispatcher ------------------

class SenderWorker(threading.Thread):
    def __init__(self, idx: int, job_q: queue.Queue, log_cb, base_opts: ClientOptions, repeat: int):
        super().__init__(daemon=True)
        self.idx = idx
        self.job_q = job_q
        self.log = log_cb
        self.base_opts = base_opts
        self.repeat = repeat
        self.stop_flag = False

    def run(self):
        try:
            while not self.stop_flag:
                item = None
                try:
                    item = self.job_q.get(timeout=0.3)
                except queue.Empty:
                    break

                file_path_or_text = item
                try:
                    for r in range(self.repeat):
                        opts = self.clone_opts_for_item(file_path_or_text)
                        conn = HttpConnection(opts)
                        if not opts.keep_alive:
                            # one-shot
                            conn.connect()
                            conn.perform()
                            conn.close()
                        else:
                            # try to reuse connection for repeat (basic)
                            conn.connect()
                            try:
                                conn.perform()
                            finally:
                                if not opts.keep_alive:
                                    conn.close()
                                else:
                                    # simple policy: close anyway after one perform to avoid pipeline tangles
                                    conn.close()
                        self.log(f"[T{self.idx}] sent ({r+1}/{self.repeat}): {self.describe_item(file_path_or_text)}")
                finally:
                    self.job_q.task_done()
        except Exception as e:
            self.log(f"[T{self.idx}] ERROR: {e}\n{traceback.format_exc()}")

    def clone_opts_for_item(self, file_path_or_text) -> ClientOptions:
        o = self.base_opts
        new = ClientOptions(
            host=o.host, port=o.port, path=o.path, method=o.method, keep_alive=o.keep_alive,
            use_chunked=o.use_chunked, chunk_size=o.chunk_size, chunk_ext=o.chunk_ext, use_gzip=o.use_gzip,
            use_multipart=o.use_multipart, extra_headers=dict(o.extra_headers),
            trailing_headers=dict(o.trailing_headers),
            connect_timeout=o.connect_timeout, read_timeout=o.read_timeout, fire_and_go=o.fire_and_go,
            http_version=o.http_version, body_text=o.body_text, file_path=o.file_path,
            multipart_field_name=o.multipart_field_name,
            multipart_text_fields=dict(o.multipart_text_fields),
            multipart_filename_override=o.multipart_filename_override,
        )
        if isinstance(file_path_or_text, tuple) and file_path_or_text[0] == "__TEXT__":
            new.file_path = None
            new.body_text = file_path_or_text[1].encode("utf-8")
        else:
            new.file_path = file_path_or_text if file_path_or_text else None
            if not new.file_path:
                new.body_text = o.body_text
        return new

    def describe_item(self, f):
        if isinstance(f, tuple) and f[0] == "__TEXT__":
            return f"text({len(f[1])} chars)"
        elif f:
            return os.path.basename(f)
        return "empty-body"


# ------------------ GUI ------------------

class UploaderGUI(QWidget):
    log_signal = Signal(str)
    done_signal = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("HTTP Blast Uploader (GUI)")
        self.resize(1000, 720)
        self._build_ui()
        self.log_signal.connect(self._append_log)

        self.work_threads: List[SenderWorker] = []

    def _build_ui(self):
        layout = QGridLayout(self)

        # Server box
        srv = QGroupBox("Server")
        g1 = QGridLayout()
        self.ed_host = QLineEdit("127.0.0.1")
        self.ed_port = QSpinBox(); self.ed_port.setRange(1, 65535); self.ed_port.setValue(80)
        self.ed_path = QLineEdit("/upload")
        g1.addWidget(QLabel("Host"), 0, 0); g1.addWidget(self.ed_host, 0, 1)
        g1.addWidget(QLabel("Port"), 1, 0); g1.addWidget(self.ed_port, 1, 1)
        g1.addWidget(QLabel("Path"), 2, 0); g1.addWidget(self.ed_path, 2, 1)
        srv.setLayout(g1)

        # Method & options
        opt = QGroupBox("HTTP Options")
        g2 = QGridLayout()
        self.cb_method = QComboBox(); self.cb_method.addItems(["POST", "PUT", "PATCH", "DELETE"])
        self.keep_alive = QCheckBox("keep-alive"); self.keep_alive.setChecked(True)

        self.use_chunked = QCheckBox("Transfer-Encoding: chunked")
        self.ed_chunk_size = QSpinBox(); self.ed_chunk_size.setRange(1, 10_000_000); self.ed_chunk_size.setValue(65536)
        self.ed_chunk_ext = QLineEdit("")  # e.g. foo=bar or ;foo=bar

        self.use_gzip = QCheckBox("Content-Encoding: gzip")

        g2.addWidget(QLabel("Method"), 0, 0); g2.addWidget(self.cb_method, 0, 1)
        g2.addWidget(self.keep_alive, 0, 2)
        g2.addWidget(self.use_chunked, 1, 0)
        g2.addWidget(QLabel("Chunk size"), 1, 1); g2.addWidget(self.ed_chunk_size, 1, 2)
        g2.addWidget(QLabel("Chunk ext"), 2, 0); g2.addWidget(self.ed_chunk_ext, 2, 1, 1, 2)
        g2.addWidget(self.use_gzip, 3, 0)
        opt.setLayout(g2)

        # Body mode
        body = QGroupBox("Body")
        g3 = QGridLayout()
        self.rb_text = QRadioButton("Text"); self.rb_text.setChecked(True)
        self.rb_file = QRadioButton("File")
        self.rb_multipart = QRadioButton("Multipart (file + fields)")

        self.txt_body = QPlainTextEdit()
        self.ed_file = QLineEdit(); self.btn_file = QPushButton("Browse...")
        self.btn_file.clicked.connect(self._browse_file)

        self.ed_mpart_field = QLineEdit("file")
        self.ed_mpart_textfields = QPlainTextEdit("field1: value1\nfield2: value2")
        self.ed_mpart_filename_override = QLineEdit("")
        g3.addWidget(self.rb_text, 0, 0); g3.addWidget(self.rb_file, 0, 1); g3.addWidget(self.rb_multipart, 0, 2)
        g3.addWidget(QLabel("Text Body"), 1, 0); g3.addWidget(self.txt_body, 1, 1, 1, 2)
        g3.addWidget(QLabel("File Path"), 2, 0); g3.addWidget(self.ed_file, 2, 1); g3.addWidget(self.btn_file, 2, 2)
        g3.addWidget(QLabel("Multipart field name"), 3, 0); g3.addWidget(self.ed_mpart_field, 3, 1)
        g3.addWidget(QLabel("Multipart text fields (k: v)"), 4, 0); g3.addWidget(self.ed_mpart_textfields, 4, 1, 1, 2)
        g3.addWidget(QLabel("Filename override (optional)"), 5, 0); g3.addWidget(self.ed_mpart_filename_override, 5, 1, 1, 2)
        body.setLayout(g3)

        # Headers
        hdr = QGroupBox("Headers")
        g4 = QGridLayout()
        self.ed_headers = QPlainTextEdit("User-Agent: http-blast-uploader/1.0\nPragma: no-cache")
        self.ed_trailers = QPlainTextEdit("X-Trailer: done")
        g4.addWidget(QLabel("Extra headers (one per line, 'K: V')"), 0, 0)
        g4.addWidget(self.ed_headers, 1, 0)
        g4.addWidget(QLabel("Trailing headers (for chunked)"), 2, 0)
        g4.addWidget(self.ed_trailers, 3, 0)
        hdr.setLayout(g4)

        # Run controls
        runb = QGroupBox("Run")
        g5 = QGridLayout()
        self.ed_threads = QSpinBox(); self.ed_threads.setRange(1, 16); self.ed_threads.setValue(4)
        self.ed_repeat = QSpinBox(); self.ed_repeat.setRange(1, 1_000_000); self.ed_repeat.setValue(1)
        self.fire_and_go = QCheckBox("Fire-and-go (read minimal response)"); self.fire_and_go.setChecked(True)
        self.btn_start = QPushButton("Start")
        self.btn_start.clicked.connect(self._start_run)

        g5.addWidget(QLabel("Threads"), 0, 0); g5.addWidget(self.ed_threads, 0, 1)
        g5.addWidget(QLabel("Repeat per item"), 0, 2); g5.addWidget(self.ed_repeat, 0, 3)
        g5.addWidget(self.fire_and_go, 1, 0, 1, 4)
        g5.addWidget(self.btn_start, 2, 0, 1, 4)
        runb.setLayout(g5)

        # Files selection area for batch
        srcb = QGroupBox("Source (Batch)")
        g6 = QGridLayout()
        self.ed_folder = QLineEdit("")
        self.btn_folder = QPushButton("Pick folder (optional)")
        self.btn_folder.clicked.connect(self._browse_folder)
        g6.addWidget(QLabel("Folder w/ files (send each file once)"), 0, 0)
        g6.addWidget(self.ed_folder, 1, 0)
        g6.addWidget(self.btn_folder, 1, 1)
        srcb.setLayout(g6)

        # Log
        self.logview = QTextEdit()
        self.logview.setReadOnly(True)

        # place
        layout.addWidget(srv, 0, 0, 1, 1)
        layout.addWidget(opt, 0, 1, 1, 1)
        layout.addWidget(body, 1, 0, 1, 2)
        layout.addWidget(hdr, 2, 0, 1, 2)
        layout.addWidget(srcb, 3, 0, 1, 2)
        layout.addWidget(runb, 4, 0, 1, 2)
        layout.addWidget(self.logview, 5, 0, 1, 2)

    # ---------- UI helpers ----------
    def _browse_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Pick file")
        if path:
            self.ed_file.setText(path)
            self.rb_file.setChecked(True)

    def _browse_folder(self):
        path = QFileDialog.getExistingDirectory(self, "Pick folder")
        if path:
            self.ed_folder.setText(path)

    def _append_log(self, s: str):
        self.logview.append(s)

    def _log(self, s: str):
        self.log_signal.emit(s)

    # ---------- Run ----------
    def _start_run(self):
        try:
            host = self.ed_host.text().strip()
            port = int(self.ed_port.value())
            path = self.ed_path.text().strip()
            method = self.cb_method.currentText().strip().upper()
            keep_alive = self.keep_alive.isChecked()
            use_chunked = self.use_chunked.isChecked()
            chunk_size = int(self.ed_chunk_size.value())
            chunk_ext = self.ed_chunk_ext.text().strip()
            use_gzip = self.use_gzip.isChecked()

            # body mode
            use_multipart = self.rb_multipart.isChecked()
            is_file = self.rb_file.isChecked()
            is_text = self.rb_text.isChecked()

            text_body = self.txt_body.toPlainText()
            file_path = self.ed_file.text().strip() if is_file or use_multipart else None

            # multipart fields
            m_field = self.ed_mpart_field.text().strip() or "file"
            m_text_fields = parse_header_lines(self.ed_mpart_textfields.toPlainText())
            m_fname_override = self.ed_mpart_filename_override.text().strip() or None

            # headers
            extra_headers = parse_header_lines(self.ed_headers.toPlainText())
            trailing_headers = parse_header_lines(self.ed_trailers.toPlainText())

            # run
            threads = int(self.ed_threads.value())
            repeat = int(self.ed_repeat.value())
            fire_and_go = self.fire_and_go.isChecked()

            # build base options
            base = ClientOptions(
                host=host, port=port, path=path, method=method, keep_alive=keep_alive,
                use_chunked=use_chunked, chunk_size=chunk_size, chunk_ext=chunk_ext,
                use_gzip=use_gzip, use_multipart=use_multipart,
                extra_headers=extra_headers, trailing_headers=trailing_headers,
                fire_and_go=fire_and_go
            )

            if is_text and not use_multipart:
                base.body_text = text_body.encode("utf-8")
                base.file_path = None
            else:
                base.file_path = file_path

            # multipart details
            base.multipart_field_name = m_field
            base.multipart_text_fields = m_text_fields
            base.multipart_filename_override = m_fname_override

            # prepare job queue
            job_q: queue.Queue = queue.Queue()

            # 1) if folder set: enqueue all files
            folder = self.ed_folder.text().strip()
            if folder and os.path.isdir(folder):
                cnt = 0
                for name in os.listdir(folder):
                    p = os.path.join(folder, name)
                    if os.path.isfile(p):
                        job_q.put(p)
                        cnt += 1
                self._log(f"[+] Enqueued {cnt} files from folder.")
            else:
                # 2) single item
                if is_text and not use_multipart:
                    job_q.put(("__TEXT__", text_body))
                elif file_path:
                    job_q.put(file_path)
                else:
                    # empty body
                    job_q.put(None)

            # start threads
            self.work_threads = []
            for i in range(threads):
                thr = SenderWorker(i + 1, job_q, self._log, base, repeat)
                thr.start()
                self.work_threads.append(thr)

            def watcher():
                for t in self.work_threads:
                    t.join()
                self._log("[*] All threads finished.")

            w = threading.Thread(target=watcher, daemon=True)
            w.start()

            self._log(f"Started: {threads} threads, repeat={repeat}, method={method}, "
                      f"{'chunked' if use_chunked else 'content-length'}, "
                      f"{'gzip' if use_gzip else 'no-gzip'}, keep_alive={keep_alive}")

        except Exception as e:
            self._log(f"[!] ERROR: {e}\n{traceback.format_exc()}")

# ---------- Main ----------

def main():
    app = QApplication(sys.argv)
    gui = UploaderGUI()
    gui.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
