from django.conf import settings
import qrcode
import os
import logging

logger = logging.getLogger(__name__)

class OrderBarCodePrinter():
    """
    Generatore di QR Code per le prenotazioni.
    Crea QR code contenenti il numero di prenotazione per facile scansione.
    """
    def __init__(self,
                 save_path:os.path=None,
                 numero:str=None,
                ) -> None:

        self.save_path = save_path
        self.numero = numero

    def make_barcode(self, user=None, event=None):
        """
        Genera un QR code per la prenotazione.

        Returns:
            str: Percorso relativo del file QR code generato
        """
        qr_data = "{}".format(self.numero)
        # Save in static/ directory for direct access
        static_path = os.path.join(settings.BASE_DIR, 'static', self.save_path)
        os.makedirs(static_path, exist_ok=True)  # Create directory if it doesn't exist
        img_path = os.path.join(static_path, f"qrcode_img_{qr_data}.png")

        try:
            # Crea QR code con alta correzione errori
            qr = qrcode.QRCode(
                version=1,  # Auto-size
                error_correction=qrcode.constants.ERROR_CORRECT_H,  # Alta correzione errori (30%)
                box_size=10,  # Dimensione di ogni box in pixel
                border=4,  # Spessore del bordo (minimo 4)
            )
            qr.add_data(qr_data)
            qr.make(fit=True)

            # Crea immagine
            img = qr.make_image(fill_color="black", back_color="white")
            img.save(img_path)

            logger.info(f"QR code generato con successo: {qr_data}")
            # Return relative path for template usage
            return f"static/{self.save_path}/qrcode_img_{qr_data}.png"

        except Exception as e:
            logger.error(f"Errore durante la generazione del QR code: {e}")
            # Return a placeholder path
            return f"static/{self.save_path}/qrcode_img_{qr_data}.png"
    



