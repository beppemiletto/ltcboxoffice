from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.utils import timezone
from django.utils.formats import date_format
from datetime import datetime, timedelta
import pytz
from store.models import Event
from openpyxl.workbook import Workbook
from openpyxl.styles import PatternFill, Border, Side, Alignment, Protection, Font
import os

# Create your views here.
def user_not_allowed(request):
    messages.error(request,"Sei entrato con utente non di staff. Non puoi operare in Amministrazione (Cassa e SIAE).")
    return render(request, 'accounts/login.html')

@login_required(login_url='login')
def fiscalmgm_main(request):
    if request.user.is_staff:
        now = datetime.now(pytz.timezone('Europe/Rome')) + timedelta(hours=6)
        time_diff = timedelta(days= 365)
        past_events = Event.objects.filter(date_time__lte=now).filter(show__is_active=True).order_by('-date_time')
        
        paginator_past = Paginator(past_events, 10)
        page = request.GET.get('page')
        paged_events = paginator_past.get_page(page)



            
        
        context = {
            'past_events' : paged_events,
        }
                



        # messages.success(request,"Sei entrato con utente di staff! Sei abilitato ad operare.")
        return render(request, 'fiscalmgm/event_list.html', context)
    
@login_required(login_url='login')
def siae(request, event_id):
    if request.user.is_staff:
        now = datetime.now(pytz.timezone('Europe/Rome')) + timedelta(hours=6)
        time_diff = timedelta(days= 365)
        past_events = Event.objects.filter(date_time__lte=now).filter(show__is_active=True).order_by('-date_time')

        curr_event =  Event.objects.get(id = event_id)

        print("{} - number {} will be the one for SIAE reports".format(curr_event,event_id))

        save_path = 'media/siae_reports'
        evnt_date_code = curr_event.date_time.strftime('%Y%m%d')
        evnt_show_slug = curr_event.show.slug
        mod2da_xls_filename = f'{evnt_date_code}_mod2DA_{evnt_show_slug}.xls'
        filename = os.path.join(os.getcwd(), save_path,mod2da_xls_filename)        
        wb = Workbook()
        ws = wb.active
        ws.title = 'mod 2DA'
        ws.page_setup.orientation = ws.ORIENTATION_LANDSCAPE
        ws.page_setup.paperSize = ws.PAPERSIZE_A4
        ws.page_margins.left = 0.25
        ws.page_margins.right = 0.25
        font_normal = Font(name='Arial', size=10,bold=False, italic=False, vertAlign=None, underline='none', strike=False, color='FF000000')
        font_normal09 = Font(name='Arial', size=9,bold=False, italic=False, vertAlign=None, underline='none', strike=False, color='FF000000')
        font_normal11 = Font(name='Arial', size=11,bold=False, italic=False, vertAlign=None, underline='none', strike=False, color='FF000000')
        font_bold = Font(name='Arial', size=10,bold=True, italic=False, vertAlign=None, underline='none', strike=False, color='FF000000')
        font_bold09 = Font(name='Arial', size=9,bold=True, italic=False, vertAlign=None, underline='none', strike=False, color='FF000000')
        font_bold11 = Font(name='Arial', size=11,bold=True, italic=False, vertAlign=None, underline='none', strike=False, color='FF000000')
        al_left_bottom =Alignment(horizontal='left', vertical='bottom', text_rotation=0, wrap_text=False, shrink_to_fit=False, indent=0)
        al_left_center =Alignment(horizontal='left', vertical='center', text_rotation=0, wrap_text=False, shrink_to_fit=False, indent=0)
        al_center_center =Alignment(horizontal='center', vertical='center', text_rotation=0, wrap_text=False, shrink_to_fit=False, indent=0)


        thin = Side(border_style="thin", color="000000")
        double = Side(border_style="double", color="ff0000")
        
        brd_double = Border(left=Side(border_style='double', color='FF000000'),right=Side(border_style='double',color='FF000000'),
                            top=Side(border_style='double',color='FF000000'),bottom=Side(border_style='double',color='FF000000'),
                            diagonal=Side(border_style=None,color='FF000000'),diagonal_direction=0,outline=Side(border_style=None,color='FF000000'),
                            vertical=Side(border_style=None,color='FF000000'),horizontal=Side(border_style=None,color='FF000000')
                            )
        
        ws.HeaderFooter.differentFirst = True
        ws.firstHeader.left.text = "Page &P of &N"
        ws.firstHeader.center.text = "MOD. 2DA"

        # setting the column size
        colnames = ('A','B','C','D','E','F','G','H','I','J')
        for col in colnames:
            ws.column_dimensions[col].width = 10.5

        #Title merged cells
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=10)
        tlc = ws['A1']
        tlc.value = "Prospetto di Liquidazione Diritti d'Autore e quote varie per manifestazioni musicali in genere, teatrali, di danza e letterarie"
        tlc.font = font_bold11
        tlc.alignment = al_center_center

        #SubTitle merged cells
        ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=10)
        tlcs = ws['A2']
        tlcs.value = "(rif. Punto 14 delle condizioni generali del mod. 116)"
        tlcs.font = font_bold11
        tlcs.alignment = al_center_center

        #Titolo Riquadro Manifestazione
        try:
            trm = ws['A3']
            trm.value = "Manifestazione"
            trm.font = font_bold11
            trm.alignment = al_left_bottom

            # Square Manifestazione
            sq_man = ws['A4:J10']
            make_border(sq_man,'double')
            ws['A4'].value = 'Organizzatore:'
            ws['A4'].font = font_normal
            ws['B4'].value = 'Laboratorio Teatrale di Cambiano APS'
            ws['B4'].font = font_bold

            ws['F4'].value = 'Cod.Fiscale/Partita IVA:'
            ws['F4'].font = font_normal
            ws['H4'].value = '09762270016'
            ws['H4'].font = font_bold

            ws['A5'].value = 'Locale:'
            ws['A5'].font = font_normal
            ws['B5'].value = 'Teatro Comunale di Cambiano'
            ws['B5'].font = font_bold

            ws['F5'].value = 'Codice locale:'
            ws['F5'].font = font_normal
            ws['H5'].value = '0050450366484'
            ws['H5'].font = font_bold

            ws['A6'].value = 'Genere Manifestazione:'
            ws['A6'].font = font_normal
            ws['C6'].value = '45 - Prosa Cabaret'
            ws['C6'].font = font_bold

            ws['A7'].value = 'Titolo(1):'
            ws['A7'].font = font_normal
            ws['B7'].value = curr_event.show.shw_title
            ws['B7'].font = font_bold

            ws['F7'].value = 'Autore:'
            ws['F7'].font = font_normal
            ws['H7'].value = curr_event.show.shw_author
            ws['H7'].font = font_bold

            ws['A8'].value = 'Titolo(2):'
            ws['A8'].font = font_normal
            ws['B8'].value = 'ND'
            ws['B8'].font = font_bold

            ws['F8'].value = 'Autore:'
            ws['F8'].font = font_normal
            ws['H8'].value = "ND"
            ws['H8'].font = font_bold

            ws['A9'].value = 'Compagnia:'
            ws['A9'].font = font_normal09
            ws['B9'].value = curr_event.show.shw_theater_company
            ws['B9'].font = font_bold09

            ws['E9'].value = 'Direttore:'
            ws['E9'].font = font_normal09
            ws['F9'].value = curr_event.show.shw_director
            ws['F9'].font = font_bold09
        
            ws['H9'].value = 'Permesso SIAE No:'
            ws['H9'].font = font_normal09
            ws['I9'].value = "123456789123456"
            ws['I9'].font = font_bold09

            ws['A10'].value = 'Data evento:'
            ws['A10'].font = font_normal09

            localtz = timezone.get_current_timezone()
            date_time = curr_event.date_time.astimezone(localtz)
            ws['B10'].value = date_time.strftime('%d/%m/%Y')
            ws['B10'].font = font_bold09

            ws['E10'].value = 'Ora evento:'
            ws['E10'].font = font_normal09
            ws['F10'].value = date_time.strftime('%H:%M')
            ws['F10'].font = font_bold09
        
            ws['H10'].value = 'GG SETT:'
            ws['H10'].font = font_normal09
            ws['I10'].value = date_format(date_time,'l')
            ws['I10'].font = font_bold09
        except:
            print("Riquadro Manifestazione - Possibili dati mancanti")


        #Titolo Riquadro Titoli d'accesso
        try:
            begin_row = 11
            trm = ws['A{}'.format(begin_row+0)]
            trm.value = "Titoli di accesso emessi dai seguenti sistemi:"
            trm.font = font_bold11
            trm.alignment = al_left_bottom
            ws['E{}'.format(begin_row+0)].value = 'Codice:'
            ws['E{}'.format(begin_row+0)].font = font_bold
            make_underline(ws['F{}'.format(begin_row+0)],'thin')

            ws['H{}'.format(begin_row+0)].value = 'Titolare:'
            ws['H{}'.format(begin_row+0)].font = font_bold
            make_underline(ws['I{}:J{}'.format(begin_row+0,begin_row+0)],'thin')
 
            # Square riquadratura
            # sq_man = ws['A{}:J{}'.format(begin_row+1,begin_row+4)]
            # make_border(sq_man,'double')
            ws['A{}'.format(begin_row+1)].value = '(comprensivi della quota abbonamenti):'
            ws['A{}'.format(begin_row+1)].font = font_normal
            ws['E{}'.format(begin_row+1)].value = 'Codice:'
            ws['E{}'.format(begin_row+1)].font = font_bold
            make_underline(ws['F{}'.format(begin_row+1)],'thin')

            ws['H{}'.format(begin_row+1)].value = 'Titolare:'
            ws['H{}'.format(begin_row+1)].font = font_bold
            make_underline(ws['I{}:J{}'.format(begin_row+1,begin_row+1)],'thin')

            ws['E{}'.format(begin_row+2)].value = 'Codice:'
            ws['E{}'.format(begin_row+2)].font = font_bold
            make_underline(ws['F{}'.format(begin_row+2)],'thin')

            ws['H{}'.format(begin_row+2)].value = 'Titolare:'
            ws['H{}'.format(begin_row+2)].font = font_bold
            make_underline(ws['I{}:J{}'.format(begin_row+2,begin_row+2)],'thin')

            ws['E{}'.format(begin_row+3)].value = 'Codice:'
            ws['E{}'.format(begin_row+3)].font = font_bold
            make_underline(ws['F{}'.format(begin_row+3)],'thin')

            ws['H{}'.format(begin_row+3)].value = 'Titolare:'
            ws['H{}'.format(begin_row+3)].font = font_bold
            make_underline(ws['I{}:J{}'.format(begin_row+3,begin_row+3)],'thin')

        except:
            print("Riquadro Titoli di accesso - Possibili dati mancanti")

        #Titolo Riquadro Presenze
        try:
            begin_row = 16
            row = begin_row 

            trp = ws[f'A{row}']
            trp.value = "Presenze:"
            trp.font = font_bold11
            trp.alignment = al_left_bottom
            # Square riquadratura
            sq_rp = ws[f'A{row+1}:C{row+4}']
            make_border(sq_rp,'double')

            trap = ws[f'E{row}']
            trap.value = "Altri proventi:"
            trap.font = font_bold11
            trap.alignment = al_left_bottom
            # Square riquadratura
            sq_rap = ws[f'E{row+1}:J{row+7}']
            make_border(sq_rap,'double')

            row = begin_row + 1

            ws[f'A{row}'].value = 'INGRESSO'
            ws[f'A{row}'].font = font_normal
            make_underline(ws[f'A{row}'],'thin')
            make_rightline(ws[f'A{row}'],'thin')
 
            ws[f'B{row}'].value = 'Incasso lordo'
            ws[f'B{row}'].font = font_normal09
            make_underline(ws[f'B{row}'],'thin')
            make_rightline(ws[f'B{row}'],'thin')

            ws[f'C{row}'].value = 'Incasso netto'
            ws[f'C{row}'].font = font_normal09
            make_underline(ws[f'C{row}'],'thin')
 
        except:
            print("Riquadro Presenze e altri proventi- Possibili dati mancanti")



        wb.save(filename=filename)

        paginator_past = Paginator(past_events, 10)
        page = request.GET.get('page')
        paged_events = paginator_past.get_page(page)



            
        
        context = {
            'past_events' : paged_events,
        }
                



        # messages.success(request,"Sei entrato con utente di staff! Sei abilitato ad operare.")
        return render(request, 'fiscalmgm/event_list.html', context)

    
@login_required(login_url='login')
def casher(request, event_id):
    if request.user.is_staff:
        now = datetime.now(pytz.timezone('Europe/Rome')) + timedelta(hours=6)
        time_diff = timedelta(days= 365)
        past_events = Event.objects.filter(date_time__lte=now).filter(show__is_active=True).order_by('-date_time')

        curr_event =  Event.objects.get(id = event_id)

        print("{} - number {} will be the one for Cash reports".format(curr_event,event_id))
        
        paginator_past = Paginator(past_events, 10)
        page = request.GET.get('page')
        paged_events = paginator_past.get_page(page)



            
        
        context = {
            'past_events' : paged_events,
        }
                



        # messages.success(request,"Sei entrato con utente di staff! Sei abilitato ad operare.")
        return render(request, 'fiscalmgm/event_list.html', context)
    
def make_border(cells_range, style):
    
    r = 0


    rows = len(cells_range)

    for row in cells_range:
        r += 1
        if r == 1:
            c=0
            cols = len(row)
            for cell in row:
                c += 1
                if c == 1:
                    cell.border =  Border(left=Side(border_style=style, color='FF000000'),right=Side(border_style=None,color='FF000000'),
                            top=Side(border_style=style,color='FF000000'),bottom=Side(border_style=None,color='FF000000'),
                            diagonal=Side(border_style=None,color='FF000000'),diagonal_direction=0,outline=Side(border_style=None,color='FF000000'),
                            vertical=Side(border_style=None,color='FF000000'),horizontal=Side(border_style=None,color='FF000000'))
                elif c > 1 and c < cols:
                    cell.border =  Border(left=Side(border_style=None, color='FF000000'),right=Side(border_style=None,color='FF000000'),
                            top=Side(border_style=style,color='FF000000'),bottom=Side(border_style=None,color='FF000000'),
                            diagonal=Side(border_style=None,color='FF000000'),diagonal_direction=0,outline=Side(border_style=None,color='FF000000'),
                            vertical=Side(border_style=None,color='FF000000'),horizontal=Side(border_style=None,color='FF000000'))
                else:
                    cell.border =  Border(left=Side(border_style=None, color='FF000000'),right=Side(border_style=style,color='FF000000'),
                            top=Side(border_style=style,color='FF000000'),bottom=Side(border_style=None,color='FF000000'),
                            diagonal=Side(border_style=None,color='FF000000'),diagonal_direction=0,outline=Side(border_style=None,color='FF000000'),
                            vertical=Side(border_style=None,color='FF000000'),horizontal=Side(border_style=None,color='FF000000'))
        elif r > 1 and r < rows:
            initial_cell = row[0]
            initial_cell.border =  Border(left=Side(border_style=style, color='FF000000'),right=Side(border_style=None,color='FF000000'),
                            top=Side(border_style=None,color='FF000000'),bottom=Side(border_style=None,color='FF000000'),
                            diagonal=Side(border_style=None,color='FF000000'),diagonal_direction=0,outline=Side(border_style=None,color='FF000000'),
                            vertical=Side(border_style=None,color='FF000000'),horizontal=Side(border_style=None,color='FF000000'))
            final_cell = row[-1]
            final_cell.border =  Border(left=Side(border_style=None, color='FF000000'),right=Side(border_style=style,color='FF000000'),
                            top=Side(border_style=None,color='FF000000'),bottom=Side(border_style=None,color='FF000000'),
                            diagonal=Side(border_style=None,color='FF000000'),diagonal_direction=0,outline=Side(border_style=None,color='FF000000'),
                            vertical=Side(border_style=None,color='FF000000'),horizontal=Side(border_style=None,color='FF000000'))
        else:
            c = 0
            for cell in row:
                c += 1
                if c == 1:
                    cell.border =  Border(left=Side(border_style=style, color='FF000000'),right=Side(border_style=None,color='FF000000'),
                            top=Side(border_style=None,color='FF000000'),bottom=Side(border_style=style,color='FF000000'),
                            diagonal=Side(border_style=None,color='FF000000'),diagonal_direction=0,outline=Side(border_style=None,color='FF000000'),
                            vertical=Side(border_style=None,color='FF000000'),horizontal=Side(border_style=None,color='FF000000'))
                elif c > 1 and c < cols:
                    cell.border =  Border(left=Side(border_style=None, color='FF000000'),right=Side(border_style=None,color='FF000000'),
                            top=Side(border_style=None,color='FF000000'),bottom=Side(border_style=style,color='FF000000'),
                            diagonal=Side(border_style=None,color='FF000000'),diagonal_direction=0,outline=Side(border_style=None,color='FF000000'),
                            vertical=Side(border_style=None,color='FF000000'),horizontal=Side(border_style=None,color='FF000000'))
                else:
                    cell.border =  Border(left=Side(border_style=None, color='FF000000'),right=Side(border_style=style,color='FF000000'),
                            top=Side(border_style=None,color='FF000000'),bottom=Side(border_style=style,color='FF000000'),
                            diagonal=Side(border_style=None,color='FF000000'),diagonal_direction=0,outline=Side(border_style=None,color='FF000000'),
                            vertical=Side(border_style=None,color='FF000000'),horizontal=Side(border_style=None,color='FF000000'))

    return

def make_underline(element,style=None):
    try:
        for cell in element[0]:
            styles = get_styles(cell)
            cell.border = Border(left=Side(border_style=styles['left'], color='FF000000'),right=Side(border_style=styles['right'],color='FF000000'),
                            top=Side(border_style=styles['top'],color='FF000000'),bottom=Side(border_style=style,color='FF000000'),
                            diagonal=Side(border_style=styles['diagonal'],color='FF000000'),diagonal_direction=0,outline=Side(border_style=None,color='FF000000'),
                            vertical=Side(border_style=None,color='FF000000'),horizontal=Side(border_style=None,color='FF000000'))

    except:
        styles = get_styles(element)
        element.border =  Border(left=Side(border_style=styles['left'], color='FF000000'),right=Side(border_style=styles['right'],color='FF000000'),
                            top=Side(border_style=styles['top'],color='FF000000'),bottom=Side(border_style=style,color='FF000000'),
                            diagonal=Side(border_style=styles['diagonal'],color='FF000000'),diagonal_direction=0,outline=Side(border_style=None,color='FF000000'),
                            vertical=Side(border_style=None,color='FF000000'),horizontal=Side(border_style=None,color='FF000000'))

    return

def make_rightline(element,style=None):
    try:
        for cell in element[0]:
            styles = get_styles(cell)
            cell.border = Border(left=Side(border_style=styles['left'], color='FF000000'),right=Side(border_style=style,color='FF000000'),
                            top=Side(border_style=styles['top'],color='FF000000'),bottom=Side(border_style=styles['bottom'],color='FF000000'),
                            diagonal=Side(border_style=styles['diagonal'],color='FF000000'),diagonal_direction=0,outline=Side(border_style=None,color='FF000000'),
                            vertical=Side(border_style=None,color='FF000000'),horizontal=Side(border_style=None,color='FF000000'))

    except:
        styles = get_styles(element)
        element.border =  Border(left=Side(border_style=styles['left'], color='FF000000'),right=Side(border_style=style,color='FF000000'),
                            top=Side(border_style=styles['top'],color='FF000000'),bottom=Side(border_style=styles['bottom'],color='FF000000'),
                            diagonal=Side(border_style=styles['diagonal'],color='FF000000'),diagonal_direction=0,outline=Side(border_style=None,color='FF000000'),
                            vertical=Side(border_style=None,color='FF000000'),horizontal=Side(border_style=None,color='FF000000'))

    return

def get_styles(cell):
    styles={}
    styles['left'] = cell.border.left.style
    styles['right'] = cell.border.right.style
    styles['top'] = cell.border.top.style
    styles['bottom'] = cell.border.bottom.style
    styles['diagonal'] = cell.border.diagonal.style

    return styles