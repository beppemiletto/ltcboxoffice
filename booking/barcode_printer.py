from django.templatetags.static import static
from ltcboxoffice.settings import STATIC_ROOT

import treepoem
import os

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

        image_barcode = treepoem.generate_barcode(barcode_type='code128',data= barcode_data, options={'includetext':True, 'includecheck':False,'includecheckintext': False},scale=2)
        image_barcode.save(img_path)

        return img_path
    



