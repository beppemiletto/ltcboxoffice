from __future__ import absolute_import, unicode_literals
from celery import shared_task
#imports needed for the functions
from django.conf import settings
from django.template.loader import get_template
from .models import Ticket
from datetime import datetime
import pytz
import os


def delTicket(pdf_path=None):
    #Logic to send an email here ........
    res = None
    print(pdf_path, ' is the path of PDF file to be deleted passed')
    try:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
            res = True
    except PermissionError:
        print(f'No permission on {pdf_path}')
        res = False
    except FileNotFoundError:
        print(f'No file {pdf_path} found' )
        res = False
    
    return res

@shared_task()
def scheduledTask():
    #Get Subscriptions
    now = datetime.now(pytz.timezone('Europe/Rome'))
    obsolete_tickets = Ticket.objects.all()
    for tkt in obsolete_tickets:
        event_date = tkt.orderevent.event.date_time
        if event_date < now:
            pdf_path = tkt.pdf_path
            tkt.delete()
            res = delTicket(pdf_path=pdf_path)
            if res is not None:
                if res:
                    print(f'Ticket {pdf_path} removed ')
                else:
                    print(f'Ticket {pdf_path} not removed check error above ')
            else:
                print(f'Ticket {pdf_path} not removed UNKNOWN ERROR')

