from django.templatetags.static import static
from ltcboxoffice.settings import STATIC_ROOT

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
        static_path = os.path.abspath(os.path.join(STATIC_ROOT, self.save_path))
        img_path = os.path.abspath(os.path.join(static_path, "barcode_img_{}.png".format(barcode_data)))

        try:
            image_barcode = treepoem.generate_barcode(
                barcode_type='code128',
                data=barcode_data, 
                options={'includetext': True, 'includecheck': False, 'includecheckintext': False},
                scale=2
            )
            image_barcode.save(img_path)
            return img_path
        except treepoem.TreepoemError as e:
            logger.error(f"Ghostscript error generating barcode: {e}")
            logger.warning("Ghostscript not installed. Install it with: choco install ghostscript (run as Administrator)")
            # Return a placeholder path - barcode will be generated later when Ghostscript is available
            return f"static/{self.save_path}/barcode_img_{barcode_data}.png"
        except Exception as e:
            logger.error(f"Unexpected error generating barcode: {e}")
            return f"static/{self.save_path}/barcode_img_{barcode_data}.png"
    



