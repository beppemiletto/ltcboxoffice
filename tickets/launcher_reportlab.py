from reportlab_ticket_printer import TicketPrinter
from datetime import datetime
import pytz
import os
import locale

locale.setlocale(locale.LC_ALL,'it_IT.UTF-8')



def getBaseDir():
    cwd = os.getcwd()
    return cwd 



timezones=pytz.all_timezones
cambiano = pytz.timezone('Europe/Rome')
static_path = os.path.abspath(os.path.join(getBaseDir(), "static"))
location_logo_path = os.path.abspath(os.path.join(static_path, "logo_teatro.png"))
company_logo_path = os.path.abspath(os.path.join(static_path, "logo_ltc_rid.png"))

evento_datetime = datetime(2023,11,4,21,00, tzinfo=cambiano)

ticket = TicketPrinter(
    location_text ='TEATRO COMUNALE DI CAMBIANO',
    location_logo = location_logo_path,
    company_logo =company_logo_path,
                       
                       season="Stagione 2023-2024 ",
                       numero="I20231115001",
                       show="L'omo la fomna e la mort",
                       evento_datetime=evento_datetime, 
                       seat= "C03" ,
                       ingresso= "Intero" ,
                       price= 10.00)

filename = ticket.build_background()

ticket.write_text()

ticket.draw_logos()

img = ticket.make_qrcode(user='beppe.miletto@gmail.com', event=25, orderevent=16897)

ticket.draw_qrcode(img_path=img)

print(filename)
