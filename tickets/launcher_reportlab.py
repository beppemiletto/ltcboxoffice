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

evento_datetime = datetime(2023,7,4,21,00, tzinfo=cambiano)

ticket = TicketPrinter(
    save_path = 'media/tickets',
    numero="C20230714.008.058",
    show="L'omo la fomna e la mort E LE MIRABOLANTI MERAVIGLIE ",
    evento_datetime=evento_datetime, 
    seat= "C03" ,
    ingresso= "Intero" ,
    price = 10.00)

filename = ticket.build_background()

ticket.write_text()

img = ticket.make_qrcode(user='beppe.miletto@gmail.com', event=8)

ticket.draw_qrcode(img_path=img)

print(filename)

