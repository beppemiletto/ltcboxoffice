#!/usr/bin/env python3
"""
ESC/POS Print Bridge — da eseguire sul PC client con stampante USB o di rete.

Legge la configurazione da print_bridge.json nella stessa directory.
Esempi di configurazione:

  USB (predefinito):
    {"type": "usb", "vendor": "0x0483", "product": "0x5840", "out_ep": 3, "interface": 0}

  Stampante di rete:
    {"type": "network", "host": "192.168.1.50", "port": 9100}

Se print_bridge.json non esiste vengono usati i valori predefiniti USB.

Dipendenze:
    pip install pyusb   (solo per modalità USB)

Permessi USB su Linux:
    sudo cp 99-escpos.rules /etc/udev/rules.d/
    sudo udevadm control --reload-rules && sudo udevadm trigger
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os
import signal
import socket
import sys

# ── Configurazione ─────────────────────────────────────────────────────────────
PORT = 9100
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'print_bridge.json')
DEFAULT_CONFIG = {
    "type": "usb",
    "vendor": "0x0483",
    "product": "0x5840",
    "out_ep": 3,
    "interface": 0,
}
# ──────────────────────────────────────────────────────────────────────────────

CONFIG = {}


def load_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return DEFAULT_CONFIG.copy()


def reload_config():
    global CONFIG
    CONFIG.clear()
    CONFIG.update(load_config())


reload_config()


def _usb_ids() -> tuple[int, int]:
    vendor = CONFIG.get('vendor', '0x0483')
    product = CONFIG.get('product', '0x5840')
    return (
        int(vendor, 16) if isinstance(vendor, str) else vendor,
        int(product, 16) if isinstance(product, str) else product,
    )


def check_printer() -> bool:
    if CONFIG.get('type') == 'network':
        host = CONFIG.get('host', 'localhost')
        port = int(CONFIG.get('port', 9100))
        try:
            with socket.create_connection((host, port), timeout=2):
                return True
        except OSError:
            return False
    else:
        try:
            import usb.core
            vid, pid = _usb_ids()
            return usb.core.find(idVendor=vid, idProduct=pid) is not None
        except Exception:
            return False


def scan_usb_devices() -> list:
    """Elenca tutti i dispositivi USB connessi (per configurazione guidata)."""
    try:
        import usb.core
        import usb.util
        devices = []
        for dev in usb.core.find(find_all=True):
            entry = {
                "vendor":       f"0x{dev.idVendor:04x}",
                "product":      f"0x{dev.idProduct:04x}",
                "manufacturer": None,
                "product_name": None,
            }
            try:
                if dev.iManufacturer:
                    entry["manufacturer"] = usb.util.get_string(dev, dev.iManufacturer)
            except Exception:
                pass
            try:
                if dev.iProduct:
                    entry["product_name"] = usb.util.get_string(dev, dev.iProduct)
            except Exception:
                pass
            devices.append(entry)
        return devices
    except Exception as exc:
        print(f"[scan] Errore enumerazione USB: {exc}", file=sys.stderr)
        return []


def save_config(new_cfg: dict):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(new_cfg, f, indent=2)
    reload_config()
    print(f"[bridge] Configurazione aggiornata: {new_cfg}")


def send_to_printer(raw_bytes: bytes) -> None:
    if CONFIG.get('type') == 'network':
        host = CONFIG.get('host', 'localhost')
        port = int(CONFIG.get('port', 9100))
        with socket.create_connection((host, port), timeout=10) as s:
            s.sendall(raw_bytes)
    else:
        import usb.core
        import usb.util
        vid, pid = _usb_ids()
        out_ep = CONFIG.get('out_ep', 3)
        interface = CONFIG.get('interface', 0)
        dev = usb.core.find(idVendor=vid, idProduct=pid)
        if dev is None:
            raise RuntimeError(f"Stampante USB {vid:04x}:{pid:04x} non trovata")
        if dev.is_kernel_driver_active(interface):
            dev.detach_kernel_driver(interface)
        dev.set_configuration()
        usb.util.claim_interface(dev, interface)
        try:
            dev.write(out_ep, raw_bytes)
        finally:
            usb.util.release_interface(dev, interface)


class BridgeHandler(BaseHTTPRequestHandler):

    def _cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Private-Network", "true")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors_headers()
        self.end_headers()

    def do_GET(self):
        if self.path == "/status":
            ok = check_printer()
            body = json.dumps({
                "printer": "ok" if ok else "not_found",
                "type": CONFIG.get('type', 'usb'),
            }).encode()
            self._json_response(200, body)

        elif self.path == "/config":
            body = json.dumps(dict(CONFIG)).encode()
            self._json_response(200, body)

        elif self.path == "/scan":
            devices = scan_usb_devices()
            body = json.dumps(devices).encode()
            self._json_response(200, body)

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        data = self.rfile.read(length)

        if self.path == "/print":
            try:
                send_to_printer(data)
                self._json_response(200, b'{"result":"ok"}')
            except Exception as exc:
                body = json.dumps({"result": "error", "message": str(exc)}).encode()
                print(f"[ERRORE STAMPA] {exc}", file=sys.stderr)
                self._json_response(500, body)

        elif self.path == "/configure":
            try:
                new_cfg = json.loads(data)
                save_config(new_cfg)
                ok = check_printer()
                body = json.dumps({
                    "result": "ok",
                    "printer": "ok" if ok else "not_found",
                    "config": dict(CONFIG),
                }).encode()
                self._json_response(200, body)
            except Exception as exc:
                body = json.dumps({"result": "error", "message": str(exc)}).encode()
                self._json_response(500, body)

        else:
            self.send_response(404)
            self.end_headers()

    def _json_response(self, code: int, body: bytes):
        self.send_response(code)
        self._cors_headers()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        print(f"[bridge] {self.address_string()} {fmt % args}")


def main():
    server = HTTPServer(("localhost", PORT), BridgeHandler)
    ptype = CONFIG.get('type', 'usb')

    print(f"ESC/POS Bridge avviato su http://localhost:{PORT}")
    print(f"  Tipo: {ptype}")

    if ptype == 'network':
        host = CONFIG.get('host', 'localhost')
        port = CONFIG.get('port', 9100)
        print(f"  Stampante di rete: {host}:{port}")
        print(f"  Raggiungibile: {'SI' if check_printer() else 'NO — verifica IP e rete'}")
    else:
        vid, pid = _usb_ids()
        print(f"  Stampante USB: {vid:04x}:{pid:04x}")
        print(f"  Trovata: {'SI' if check_printer() else 'NO — verifica USB e permessi'}")

    if os.path.exists(CONFIG_FILE):
        print(f"  Config: {CONFIG_FILE}")
    else:
        print(f"  Config: predefinita USB (crea {CONFIG_FILE} per personalizzare)")

    print("  Premi Ctrl+C per fermare.\n")

    def _shutdown(sig, frame):
        print("\nBridge fermato.")
        server.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    server.serve_forever()


if __name__ == "__main__":
    main()
