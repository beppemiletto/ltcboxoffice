from django.templatetags.static import static
from reportlab.lib.units import mm
from reportlab.lib.colors import *

import treepoem
from datetime import datetime
import pytz
import os
import cv2


class OrderBarCodePrinter():
    def __init__(self,
                 save_path:os.path=None, 
                 evento:str=None,
                 numero:str=None, 
                 show:str=None,
                 evento_datetime:datetime=None,
                 total:float=None) -> None:
        
        self.save_path = save_path
        self.evento=evento
        self.numero=numero
        self.show=show
        self.total = total


    def make_barcode(self, user=None, event=None):
        static_path = os.path.abspath(os.path.join(os.getcwd(), self.save_path))
        img_path = os.path.abspath(os.path.join(static_path, "barcode_img.png"))
        barcode_data = "{} {}".format(self.evento, self.numero)
        image_barcode = treepoem.generate_barcode(barcode_type='code128',data= barcode_data, options={'includetext':True, 'includecheck':False,'includecheckintext': False},scale=2)

        # ticket_qrcode.make(fit=True)
        image_barcode.save(img_path)

         
        # detector = cv2.QRCodeDetector()
        # reval,point,s_qr = detector.detectAndDecode(cv2.imread(img_path)) 
        # print(reval)
        # exec('mydict = {'+reval+'}')
        # print(point)
        return img_path
    



