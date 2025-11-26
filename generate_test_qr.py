#!/usr/bin/env python
"""
Script per generare QR code di test per debug scanner mobile.

Uso:
    python generate_test_qr.py
    python generate_test_qr.py 00042_000123_000456
    python generate_test_qr.py --batch 5
"""

import qrcode
import os
import sys
from datetime import datetime

def generate_qr_code(code_text, output_path=None):
    """
    Genera un QR code con le stesse impostazioni usate dal sistema.

    Args:
        code_text: Il testo da codificare nel QR
        output_path: Percorso dove salvare l'immagine (default: test_qr_<timestamp>.png)

    Returns:
        str: Percorso del file generato
    """
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"test_qr_{timestamp}.png"

    # Usa le stesse impostazioni di booking/barcode_printer.py
    qr = qrcode.QRCode(
        version=1,  # Auto-size
        error_correction=qrcode.constants.ERROR_CORRECT_H,  # Alta correzione errori (30%)
        box_size=10,  # Dimensione di ogni box in pixel
        border=4,  # Spessore del bordo (minimo 4)
    )

    qr.add_data(code_text)
    qr.make(fit=True)

    # Crea immagine
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(output_path)

    return output_path


def generate_batch_qr_codes(count=5, base_event=1, base_order=1, base_orderevent=1):
    """
    Genera una serie di QR code di test.

    Args:
        count: Numero di QR code da generare
        base_event: ID evento di partenza
        base_order: ID ordine di partenza
        base_orderevent: ID orderevent di partenza

    Returns:
        list: Lista dei percorsi dei file generati
    """
    files = []
    output_dir = "test_qr_codes"

    # Crea directory se non esiste
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for i in range(count):
        event_id = base_event
        order_id = base_order + i
        orderevent_id = base_orderevent + i

        # Formato: event_order_orderevent (00001_000123_000456)
        code = f"{event_id:05d}_{order_id:06d}_{orderevent_id:06d}"
        output_path = os.path.join(output_dir, f"qr_test_{code}.png")

        filepath = generate_qr_code(code, output_path)
        files.append(filepath)

        print(f"✓ Generato: {filepath}")
        print(f"  Codice: {code}")

    return files


def print_usage():
    """Stampa le istruzioni d'uso."""
    print("""
╔════════════════════════════════════════════════════════════════╗
║           Generatore QR Code di Test                          ║
╚════════════════════════════════════════════════════════════════╝

USO:
    python generate_test_qr.py                          # QR singolo con codice di default
    python generate_test_qr.py 00042_000123_000456     # QR singolo con codice specifico
    python generate_test_qr.py --batch 5                # 5 QR code di test
    python generate_test_qr.py --batch 10 --event 2    # 10 QR per evento 2

OPZIONI:
    --batch N       Genera N QR code di test
    --event ID      ID evento (default: 1)
    --order ID      ID ordine iniziale (default: 1)
    --help, -h      Mostra questo aiuto

FORMATO CODICE:
    event_order_orderevent
    00042_000123_000456
    └──┬─┘ └──┬──┘ └──┬──┘
       │      │        └─ OrderEvent ID (6 cifre)
       │      └────────── Order ID (6 cifre)
       └─────────────────── Event ID (5 cifre)

ESEMPI:
    # Genera QR con codice specifico
    python generate_test_qr.py 00001_000100_000200

    # Genera 10 QR code per l'evento 5
    python generate_test_qr.py --batch 10 --event 5

    # Genera 3 QR code partendo dall'ordine 500
    python generate_test_qr.py --batch 3 --order 500

OUTPUT:
    - Singolo: test_qr_<timestamp>.png nella directory corrente
    - Batch: test_qr_codes/qr_test_<codice>.png
""")


def main():
    """Funzione principale."""
    args = sys.argv[1:]

    # Mostra aiuto
    if '--help' in args or '-h' in args or len(args) == 0:
        print_usage()

        # Genera un QR di default per demo
        default_code = "00001_000001_000001"
        print(f"\nGenerazione QR di default con codice: {default_code}\n")
        filepath = generate_qr_code(default_code)
        print(f"✓ QR code generato: {filepath}")
        print(f"\n💡 Apri questo file su un dispositivo e scansionalo con lo scanner mobile!")
        return

    # Modalità batch
    if '--batch' in args:
        try:
            batch_idx = args.index('--batch')
            count = int(args[batch_idx + 1])
        except (IndexError, ValueError):
            print("❌ Errore: --batch richiede un numero")
            print("   Esempio: python generate_test_qr.py --batch 5")
            return

        # Parametri opzionali
        event_id = 1
        order_id = 1

        if '--event' in args:
            try:
                event_idx = args.index('--event')
                event_id = int(args[event_idx + 1])
            except (IndexError, ValueError):
                print("⚠️ Warning: --event invalido, uso default (1)")

        if '--order' in args:
            try:
                order_idx = args.index('--order')
                order_id = int(args[order_idx + 1])
            except (IndexError, ValueError):
                print("⚠️ Warning: --order invalido, uso default (1)")

        print(f"\n🔄 Generazione di {count} QR code di test...")
        print(f"   Evento: {event_id}, Ordine iniziale: {order_id}\n")

        files = generate_batch_qr_codes(count, event_id, order_id, order_id)

        print(f"\n✓ Generati {len(files)} QR code in test_qr_codes/")
        print(f"\n💡 Apri questi file per testarli con lo scanner mobile!")
        return

    # Modalità singolo con codice specifico
    code = args[0]

    # Valida formato
    parts = code.split('_')
    if len(parts) != 3:
        print(f"❌ Errore: Formato codice invalido: {code}")
        print(f"   Formato atteso: event_order_orderevent (es. 00042_000123_000456)")
        return

    try:
        event_id = int(parts[0])
        order_id = int(parts[1])
        orderevent_id = int(parts[2])
    except ValueError:
        print(f"❌ Errore: Il codice deve contenere solo numeri: {code}")
        return

    print(f"\n🔄 Generazione QR code con codice: {code}\n")
    filepath = generate_qr_code(code)

    print(f"✓ QR code generato: {filepath}")
    print(f"  Codice: {code}")
    print(f"  Evento ID: {event_id}")
    print(f"  Ordine ID: {order_id}")
    print(f"  OrderEvent ID: {orderevent_id}")
    print(f"\n💡 Apri questo file su un dispositivo e scansionalo con lo scanner mobile!")


if __name__ == "__main__":
    main()
