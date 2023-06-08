from django.shortcuts import render
from django.http import HttpResponse
from billboard.models import Show
from store.models import Event
from orders.models import OrderEvent
# Tickets document imports
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.rl_config import defaultPageSize
from reportlab.lib.units import inch

def myFirstPage(canvas, doc):
    Title = "Hello world"
    pageinfo = "platypus example"
    PAGE_HEIGHT=defaultPageSize[1]; PAGE_WIDTH=defaultPageSize[0]
    canvas.saveState()
    canvas.setFont('Times-Bold',16)
    canvas.drawCentredString(PAGE_WIDTH/2.0, PAGE_HEIGHT-108, Title)
    canvas.setFont('Times-Roman',9)
    canvas.drawString(inch, 0.75 * inch, "First Page / %s" % pageinfo)
    canvas.restoreState()

def myLaterPages(canvas, doc):
    pageinfo = "platypus example"
    canvas.saveState()
    canvas.setFont('Times-Roman',9)
    canvas.drawString(inch, 0.75 * inch, "Page %d %s" % (doc.page, pageinfo))
    canvas.restoreState()

def go(k):
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate("{}_ticket.pdf".format(k))
    Story = [Spacer(1,2*inch)]
    titolo = 'Biglietto per il posto {}'.format(k)
    style = styles["Heading1"]
    p = Paragraph(titolo, style)
    Story.append(p)
    Story.append(Spacer(1,0.2*inch))
    
    style = styles["Normal"]
    for i in range(10):
       bogustext = ("This is Paragraph number %s. " % i)
       p = Paragraph(bogustext, style)
       Story.append(p)
       Story.append(Spacer(1,0.2*inch))
    doc.build(Story, onFirstPage=myFirstPage, onLaterPages=myLaterPages)

# Create your views here.
def tickets(request):
    show_list = Show.objects.filter(is_in_billboard=True, is_active=True)
    show_dict = dict()
    for show in show_list:
        event_list = Event.objects.filter(show=show)
        show_dict[show.pk] = {
            'show':show,
            'event_list': event_list,
                              }


    context = {
        'show_dict': show_dict,

    }
    return render(request, 'tickets/tickets.html', context)

def event_list(request, event_slug):
    context ={

    }
    return render(request, 'tickets/event-list.html', context)

def print_ticket(request, orderevent):
    ordereventobj = OrderEvent.objects.get(id=orderevent)

    # Tickets document settins
    PAGE_HEIGHT=defaultPageSize[1]; PAGE_WIDTH=defaultPageSize[0]
    styles = getSampleStyleSheet()

    response_str = 'This is the order event to be processed<br>id = {} - {} - {}<br>ricevuto da {} {}<br><br>'.format(
        ordereventobj.pk, 
        ordereventobj.seats_price, 
        ordereventobj.payment,
        ordereventobj.payment.user.first_name,
        ordereventobj.payment.user.last_name
        
        )
    seats_dict = ordereventobj.seats_dict()
    for k, seat in seats_dict.items():
        response_str += 'I am going to print ticket for seat {} <br>'.format(seat[0])
        go(k)

    return HttpResponse(response_str)
    
