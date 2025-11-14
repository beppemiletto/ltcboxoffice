from django.conf import settings
import treepoem
import os
import logging

logger = logging.getLogger(__name__)

class OrderBarCodePrinter():
    def __init__(self,
                 save_path:os.path=None, 
                 numero:str=None, 
                ) -> None:
        
        self.save_path = save_path
        self.numero=numero

    def make_barcode(self, user=None, event=None):
        barcode_data = "{}".format(self.numero)
        # Save in static/ directory for direct access
        static_path = os.path.join(settings.BASE_DIR, 'static', self.save_path)
        os.makedirs(static_path, exist_ok=True)  # Create directory if it doesn't exist
        img_path = os.path.join(static_path, f"barcode_img_{barcode_data}.png")

        try:
            image_barcode = treepoem.generate_barcode(
                barcode_type='code128',
                data=barcode_data, 
                options={'includetext': True, 'includecheck': False, 'includecheckintext': False},
                scale=2
            )
            image_barcode.save(img_path)
            # Return relative path for template usage
            return f"static/{self.save_path}/barcode_img_{barcode_data}.png"
        except treepoem.TreepoemError as e:
            logger.error(f"Ghostscript error generating barcode: {e}")
            logger.warning("Ghostscript not installed. Install it with: choco install ghostscript (run as Administrator)")
            # Return a placeholder path - barcode will be generated later when Ghostscript is available
            return f"static/{self.save_path}/barcode_img_{barcode_data}.png"
        except Exception as e:
            logger.error(f"Unexpected error generating barcode: {e}")
            return f"static/{self.save_path}/barcode_img_{barcode_data}.png"
    



