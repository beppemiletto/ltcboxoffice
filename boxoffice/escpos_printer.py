from escpos.printer import Usb, Dummy, Network
from django.templatetags.static import static
from ltcboxoffice.settings import BASE_DIR, STATIC_ROOT
import os

class EscPosPrinter(Usb):
    def __init__(self, idVendor, idProduct, timeout=0, in_ep=0x81, out_ep=0x03, *args, **kwargs):
        super().__init__(idVendor, idProduct, timeout, in_ep, out_ep, *args, **kwargs)
        self.static_url_logo = os.path.join(BASE_DIR,STATIC_ROOT,'images/logos/logo_ltc_retinato.png')

    def print_ticket(self, data=None):

        self.image(self.static_url_logo)
        self.set(align='center', font='a',  width=1, height=1)
        self.text('\n')
        self.text(data['numero'])
        self.text('\n')
        self.set(align='right', font='b',  width=2, height=2)
        self.text(data['seat'])
        self.text('\n')
        self.set(align='right', font='a',  width=1, height=1)
        self.text(data['ingresso'])
        self.set(align='center', font='b',  width=3, height=3)
        self.text('\n')
        self.text("Buona visione")
        self.cut(mode=u'FULL')
        return
    def print_ticket_image(self, image = None):
        self.image(image)
        self.cut(mode=u'FULL')


class EscPosDummy(Dummy):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.static_url_logo = os.path.join(BASE_DIR,STATIC_ROOT,'images/logos/logo_ltc_retinato.png')

    def print_ticket(self, data=None):

        self.image(self.static_url_logo)
        # self.set(align='center', font='a',  width=1, height=1)
        # self.text(data['numero'])
        # self.set(align='right', font='b',  width=2, height=2)
        # self.text(data['numero'])
        # self.set(align='right', font='a',  width=1, height=1)
        # self.text(data['numero'])
        # self.set(align='center', font='b',  width=3, height=3)
        self.text("Buona visione")
        self.cut(mode=u'FULL')

        return self.output

class EscPosNetwork(Network):
    def __init__(self, host='localhost', port=9100, timeout=60, *args, **kwargs):
        super().__init__(host, port , timeout, *args, **kwargs)
        self.static_url_logo = os.path.join(BASE_DIR,STATIC_ROOT,'images/logos/logo_ltc.png')

    
    def print_ticket(self, data=None):

        self.image(self.static_url_logo)
        # self.set(align='center', font='a',  width=1, height=1)
        self.text('\n')
        self.text(data['numero'])
        self.text('\n')
        # self.set(align='right', font='b',  width=2, height=2)
        self.text(data['seat'])
        self.text('\n')
        # self.set(align='right', font='a',  width=1, height=1)
        self.text(data['ingresso'])
        # self.set(align='center', font='b',  width=3, height=3)
        self.text('\n')
        self.text("Buona visione")
        self.text('\n')
        self.text('\n')


        return (True)