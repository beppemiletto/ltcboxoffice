#!/usr/bin/env python3
"""
Utility per trovare l'endpoint corretto della stampante POS USB.
Esegui questo script se la stampante viene trovata ma non stampa nulla.

Uso:
    python check_endpoints.py
"""
import sys

try:
    import usb.core
    import usb.util
except ImportError:
    print("ERRORE: pyusb non installato.")
    print("Installa con: pip install pyusb")
    sys.exit(1)

try:
    import libusb_package
    backend = libusb_package.get_libusb1_backend()
except ImportError:
    backend = None

print("Dispositivi USB trovati:\n")
try:
    devices = list(usb.core.find(find_all=True, backend=backend))
except Exception as e:
    print(f"Errore accesso USB: {e}")
    print("Su Linux: assicurati di aver creato le regole udev o esegui con sudo.")
    sys.exit(1)

if not devices:
    print("Nessun dispositivo USB trovato.")
    sys.exit(0)

for dev in devices:
    try:
        vid = f"0x{dev.idVendor:04x}"
        pid = f"0x{dev.idProduct:04x}"
        name = ""
        try:
            if dev.iProduct:
                name = usb.util.get_string(dev, dev.iProduct)
        except Exception:
            pass
        print(f"Dispositivo: {vid}:{pid}  {name}")
        for cfg in dev:
            for intf in cfg:
                print(f"  Interfaccia {intf.bInterfaceNumber} (class={intf.bInterfaceClass})", end="")
                if intf.bInterfaceClass == 7:
                    print("  ← STAMPANTE")
                else:
                    print()
                for ep in intf:
                    direction = "OUT" if usb.util.endpoint_direction(ep.bEndpointAddress) == usb.util.ENDPOINT_OUT else "IN"
                    ep_type = {0: "CTRL", 2: "BULK", 3: "INT"}.get(usb.util.endpoint_type(ep.bmAttributes), "?")
                    marker = "  ← usa questo come out_ep" if direction == "OUT" and ep_type == "BULK" else ""
                    print(f"    ep=0x{ep.bEndpointAddress:02x}  {direction}  {ep_type}{marker}")
        print()
    except Exception:
        pass
