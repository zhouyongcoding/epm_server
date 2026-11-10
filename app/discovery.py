import json
import socket
import threading

DISCOVERY_PORT = 45871
DISCOVERY_MAGIC = "ENGINEERING_PROJECT_MANAGEMENT"


class DiscoveryResponder:
    def __init__(self, port: int = DISCOVERY_PORT, urls: list[str] | None = None):
        self._port = port
        self._urls = urls or ["http://127.0.0.1:8001"]
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        if self.running:
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._listen_loop, name="discovery-responder", daemon=True
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self._thread = None

    def _listen_loop(self) -> None:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(("", self._port))
            sock.settimeout(1.0)
        except OSError:
            return
        with sock:
            while not self._stop_event.is_set():
                try:
                    data, addr = sock.recvfrom(4096)
                except socket.timeout:
                    continue
                except OSError:
                    return
                try:
                    message = data.decode("utf-8")
                except UnicodeDecodeError:
                    continue
                if message != DISCOVERY_MAGIC:
                    continue
                response = json.dumps({"service": DISCOVERY_MAGIC, "urls": self._urls})
                try:
                    sock.sendto(response.encode("utf-8"), addr)
                except OSError:
                    pass