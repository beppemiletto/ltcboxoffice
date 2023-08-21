from django.templatetags.static import static
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.colors import *

from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics import renderPDF, renderSVG, renderPM


import qrcode
from datetime import datetime
import pytz
import locale
import os
import cv2


class TicketPrinter():
    def __init__(self,
                 save_path:os.path=None, 
                 evento:str=None,
                 numero:str=None, 
                 show:str=None,
                 evento_datetime:datetime=None,
                 seat:str=None, 
                 ingresso:str=None,
                 price:float=None) -> None:
        
        self.save_path = save_path
        self.evento=evento
        self.numero=numero
        self.show=show

        self.tzhere = pytz.timezone('Europe/Rome')
        self.evento_datetime = evento_datetime.astimezone(self.tzhere)
        self.seat=seat
        self.ingresso=ingresso
        self.price=price
        prefix = self.numero.split('.')[0]
        shw_code = self.numero.split('.')[1]
        serial = self.numero.split('.')[-1]
        self.pdf_filename = f'{self.seat}_Ticket_{prefix}_{shw_code}_{serial}.pdf'
        self.filename = os.path.join(os.getcwd(), self.save_path,self.pdf_filename)

        self.DPI = 203
        self.w = int(140 * mm )
        self.h = int(63 * mm)

        self.win = canvas.Canvas(filename=self.filename,
                                 pagesize=( self.w, self.h),
                                 bottomup=1,
                                 pageCompression=0,
                                 verbosity=0,
                                 encrypt=None)


    def build_background(self):

        w = self.w
        h = self.h 
        image_location = os.path.join(os.getcwd(),'static/images/logos/biglietto.png')
        self.win.drawImage(image_location,0,h*-1 + 15 ,width=w, height=None, mask=None, preserveAspectRatio=True)
  
        return self.filename

    def write_text(self):

        locale.setlocale(locale.LC_ALL,'it_IT.UTF-8')

        w = self.w 
        h = self.h 

        
        #Stampa il numero del biglietto -  
        self.win.setFillColor('black')
        self.win.setFont('Courier-Bold',11)
        x= 0.025 * w
        y = 0.21 * h
        self.win.drawString(x,y,"N.ro: {}".format(self.numero))

        #Stampa il titolo dello spettacolo
        self.win.setFont('Helvetica-Bold',11)
        x= 0.025 * w
        y = 0.45 * h
        self.win.drawString(x,y,self.show)

        #Stampa la data e ora dell'evento
        data_text= "{}".format(self.evento_datetime.strftime("%A %d %B %Y"))
        ora_text= "ore {}".format(self.evento_datetime.strftime("%H %M"))

        self.win.setFont('Helvetica-Oblique',10)
        x= 0.025 * w
        y = 0.35 * h
        self.win.drawString(x,y,data_text)
        y = 0.30 * h
        self.win.drawString(x,y,ora_text)




        #Stampa il posto come fila e numero posto 
        seat_text = "Fila {} Posto {}".format(self.seat[0],self.seat[1:3])
        x = 0.18 * w
        y = 0.68 * h
        self.win.setFont('Courier-Bold',22)
        self.win.drawString(x,y,seat_text)

        #STAMPA CATEGORIA E PREZZO DELL TITOLO DI INGRESSO
        ingresso_text= "Ingresso {} - € {}".format(self.ingresso, self.price)
        x = 0.18 * w
        y =  0.58 * h 
        self.win.setFont('Helvetica',12)
        self.win.drawString(x,y,ingresso_text)

        return(None)
        
    def make_qrcode(self, user=None, event=None):
        static_path = os.path.abspath(os.path.join(os.getcwd(), "static"))
        img_path = os.path.abspath(os.path.join(static_path, "qrcode_img.png"))
        ticket_qrcode = qrcode.QRCode(
              version= 2,
              error_correction=qrcode.ERROR_CORRECT_M,
              box_size=8,
              border=1
         )
        ticket_qrcode.add_data(
             "'user': '{}','seat': '{}','event':{},'number':{}".format(
             user,self.seat, self.evento, self.numero)
             )
        ticket_qrcode.make(fit=True)
        img = ticket_qrcode.make_image(fill_color='black',back_color='white')
        img.save(img_path)

         
        # detector = cv2.QRCodeDetector()
        # reval,point,s_qr = detector.detectAndDecode(cv2.imread(img_path)) 
        # print(reval)
        # exec('mydict = {'+reval+'}')
        # print(point)
        return img_path
    
    
    def draw_qrcode(self, img_path=None):

        w = self.w
        h = self.h
        if img_path is not None:
            x= 0.77 * w
            y = 0.25 * h
            self.win.drawImage(img_path,x,y,width=90, height=90, mask=None , preserveAspectRatio=True)
        
        self.win.showPage()
        self.win.save()




