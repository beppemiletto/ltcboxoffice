from django.templatetags.static import static
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.colors import *

from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics import renderPDF, renderSVG, renderPM


import qrcode
from datetime import datetime
import os
import cv2

# d = Drawing(400,200)
# d_prop = d.getProperties()

# rect = (Rect(50,50,300,100,fillColor=colors.yellow))
# r_prop = rect.getProperties()
# d.add(rect)
# d.add(String(150,100, 'Hello World', fontSize=18, fillColor=colors.red))
# d.add(String(180,86, 'Special characters !@#$%^&*()',
#              fillColor=colors.red))
# renderPDF.drawToFile(d,'example.pdf', 'My First Drawing PDF ticket number stu ca', autoSize=0 )
# renderSVG.drawToFile(d,'example2.svg', 'My First Drawing SVG ticket number stu ca', autoSize=0  )
# renderPM.drawToFile(d,'example2.png','PNG')



# print('Well done!')
# exit(0)

class TicketPrinter():
    def __init__(self,
                 save_path:os.path=None, 
                 location_text:str=None, 
                 location_logo:os.path=None,
                 company_logo: os.path=None,
                 evento:str=None,
                 numero:str=None, 
                 show:str=None,
                 evento_datetime:datetime=None,
                 seat:str=None, 
                 ingresso:str=None,
                 price:float=None) -> None:
        self.save_path = save_path
        self.location = location_text
        self.location_logo = location_logo
        self.company_logo = company_logo
        self.evento=evento
        self.numero=numero
        self.show=show
        self.evento_datetime= evento_datetime
        self.seat=seat
        self.ingresso=ingresso
        self.price=price
        prefix = self.numero.split('.')[0]
        shw_code = self.numero.split('.')[1]
        serial = self.numero.split('.')[-1]
        self.pdf_filename = f'{self.seat}_Ticket_{prefix}_{shw_code}_{serial}.pdf'
        self.filename = os.path.join(os.getcwd(), self.save_path,self.pdf_filename)

        self.DPI = 300
        self.w = int(140 * mm )
        self.h = int(64 * mm)

        self.win = canvas.Canvas(filename=self.filename,
                                 pagesize=( self.w, self.h),
                                 bottomup=1,
                                 pageCompression=0,
                                 verbosity=0,
                                 encrypt=None)


    def build_background(self):

        w = self.w * mm / 2.83
        h = self.h * mm / 2.83
        # self.win.setProperties({'background':colors.antiquewhite})

        lefmost_polygon = self.win.beginPath()
        lefmost_polygon.moveTo(0, 0)
        points = [(int(0.22 * w),0), 
                  (int(0.35 * w),int(0.5 * h)), 
                  (int(0.22 *w),int(1.0 * h)),
                  (int(0 *w),int(1.0 * h)),
                  (0,0),]
        for point in points:
            lefmost_polygon.lineTo(point[0],point[1])
        lefmost_polygon.close()
        fillColor = Color(0,0,0, alpha= 0.5)
        self.win.setFillColor(fillColor)
        self.win.setStrokeColor(grey)
        self.win.drawPath(lefmost_polygon, fill=True)

        image_location = os.path.join(os.getcwd(),'static/images/logos/seats_250.png')
        self.win.drawImage(image_location,0,0,width=None, height=None,mask=None, preserveAspectRatio=True)
        # lefmost_img = Image(Point(int(0.175 *w),int(0.5 * h)),'static/seats.png')
        # lefmost_img.draw(self.win)

        
        center_polygon = self.win.beginPath()
        center_polygon.moveTo(int(0.225* w),0)

        points = [
            (int(0.68 * w),0),
            (int(0.85 *w),int(0.5 * h)),
            (int(0.68 *w),int(1.0 * h)),
            (int(0.225 *w),int(1.0 * h)),
            (int(0.355 *w),int(0.5 * h)),
            (int(0.225* w),0),]
       
        for point in points:
            center_polygon.lineTo(point[0],point[1])
        center_polygon.close()
        fillColor = Color(0.25,0.03,0.06, alpha= 1.0)
        self.win.setFillColor(fillColor)
        self.win.setStrokeColor(grey)
        self.win.drawPath(center_polygon, fill=True)

        self.win.setFillColor(brown)
        rightmost_rectangle = self.win.rect(int(0.71 * w),0, int( 1.0 * w),int(1.0 * h), fill=True )

   
        return self.filename

    def write_text(self):

        w = self.w * mm / 2.83
        h = self.h * mm / 2.83
        text = "Test Text for fonts"
        x = 0.35 * w
        y = h - 0.15 * h
        self.win.setFillColor(white)
        # for font in self.win.getAvailableFonts():
        #     self.win.setFont(font,8)
        #     self.win.drawString(x,y,text)
        #     self.win.setFont('Helvetica',8)
        #     self.win.drawRightString(x-4,y,font+' : ')
        #     y -=10

             



        self.win.setFillColor(white)
        if self.location_logo is None: 
            self.win.setFont('Helvetica-Bold',5)
            x= 0.25 * w
            y = h - 0.15 * h
            self.win.drawRightString(x,y,self.location)


        # self.win.setFont('Helvetica-Bold',8)
        # x= 0.25 * w
        # y = 0.25 * h
        # self.win.drawRightString(x,y,self.season)

        self.win.setFont('Courier-Bold',8)
        x= 0.23 * w
        y = h - 0.92 * h
        self.win.drawRightString(x,y,"N.ro: {}".format(self.numero))

        self.win.setFont('Helvetica-Bold',10)
        x= 0.3 * w
        y = 0.85 * h
        self.win.drawString(x,y,self.show)

        data_text= "{}".format(self.evento_datetime.strftime("%A %d %B %Y"))
        ora_text= "ore {}".format(self.evento_datetime.strftime("%H %M"))

        self.win.setFont('Helvetica-Oblique',9)
        x= 0.325 * w
        y = 0.75 * h
        self.win.drawString(x,y,data_text)
        y = 0.7 * h
        self.win.drawString(x,y,ora_text)





        seat_text = "Fila {} Numero {}".format(self.seat[0],self.seat[1:3])
        x = 0.10 * w
        y = 0.35 * h
        self.win.setFont('Courier-Bold',24)
        self.win.drawString(x,y,seat_text)

        ingresso_text= "Ingresso {} - € {}".format(self.ingresso, self.price)
        x = 0.3 * w
        y =  0.15 * h 
        self.win.setFont('Helvetica',11)
        self.win.drawString(x,y,ingresso_text)


        self.win.setFont('Courier-Bold',8)
        x= 0.95 * w
        y = 0.08 * h
        self.win.drawRightString(x,y,"N.ro: {}".format(self.numero))


        return(None)
        

    def draw_logos(self):
        w = self.w
        h = self.h


        if self.location_logo is not None:
            image_location = os.path.join(os.getcwd(),self.location_logo)

            x= 0.05 * w
            y = 0.75 * h
            self.win.drawImage(image_location,x,y,width=70, height=50, mask=None , preserveAspectRatio=True)
        if self.company_logo is not None:
            image_location = os.path.join(os.getcwd(),self.company_logo)
            x= 0.05 * w
            y = 0.475 * h
            self.win.drawImage(image_location,x,y,width=70, height=50, mask=None , preserveAspectRatio=True)

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
            x= 0.73 * w
            y = 0.35 * h
            self.win.drawImage(img_path,x,y,width=100, height=100, mask=None , preserveAspectRatio=True)
        
        self.win.showPage()
        self.win.save()




