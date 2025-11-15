"""
Import subscriptions data from Excel file
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime
from subscriptions.models import SubscriptionType, Subscription, SubscriptionUsage
from accounts.models import Account
from orders.models import Payment
from store.models import Event
import openpyxl


class Command(BaseCommand):
    help = 'Import subscriptions from Abbonamenti2025-26.xlsx'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='Abbonamenti2025-26.xlsx',
            help='Path to Excel file'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        
        self.stdout.write(f"Importing from {file_path}...")
        
        # Prima creo i tipi abbonamento
        self.create_subscription_types()
        
        # Poi importo gli abbonamenti venduti
        try:
            wb = openpyxl.load_workbook(file_path)
            self.import_sheet(wb, '4 rid', 'R4')
            self.import_sheet(wb, '4 int', 'I4')
            self.import_sheet(wb, '8 rid', 'R8')
            self.import_sheet(wb, '8 int', 'I8')
            wb.close()
            
            self.stdout.write(self.style.SUCCESS('✓ Import completed'))
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'✗ File not found: {file_path}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Error: {e}'))

    def create_subscription_types(self):
        """Crea i 4 tipi di abbonamento base"""
        types_data = [
            {
                'name': 'Abbonamento 8 ingressi interi',
                'code_prefix': 'I8',
                'type': 'FULL',
                'price': 60.00,
                'discount_percent': 25.00,
                'max_events': 8,
            },
            {
                'name': 'Abbonamento 8 ingressi ridotti',
                'code_prefix': 'R8',
                'type': 'REDUCED',
                'price': 42.00,
                'discount_percent': 25.00,
                'max_events': 8,
            },
            {
                'name': 'Abbonamento 4 ingressi interi',
                'code_prefix': 'I4',
                'type': 'FULL',
                'price': 32.00,
                'discount_percent': 20.00,
                'max_events': 4,
            },
            {
                'name': 'Abbonamento 4 ingressi ridotti',
                'code_prefix': 'R4',
                'type': 'REDUCED',
                'price': 23.00,
                'discount_percent': 17.86,
                'max_events': 4,
            },
        ]
        
        for data in types_data:
            sub_type, created = SubscriptionType.objects.get_or_create(
                code_prefix=data['code_prefix'],
                defaults=data
            )
            if created:
                self.stdout.write(f"  ✓ Created: {sub_type.name}")
            else:
                self.stdout.write(f"  - Exists: {sub_type.name}")

    def import_sheet(self, workbook, sheet_name, code_prefix):
        """Importa abbonamenti da un foglio specifico"""
        try:
            sheet = workbook[sheet_name]
        except KeyError:
            self.stdout.write(f"  ⚠ Sheet '{sheet_name}' not found, skipping")
            return
        
        sub_type = SubscriptionType.objects.get(code_prefix=code_prefix)
        self.stdout.write(f"\nImporting {sheet_name} ({code_prefix}):")
        
        # Prima riga dati è la 5 (dopo header)
        for row_idx, row in enumerate(sheet.iter_rows(min_row=5, values_only=True), start=1):
            # row = [Numero, Codice, Venduto il, Nome, Cognome, email, telefono, Pagamento, Data1, Data2, Data3, Data4/8]
            if not row[1]:  # Codice abbonamento vuoto = riga vuota
                break
            
            numero = row[0]
            codice = row[1]
            venduto_il = row[2]
            nome = row[3]
            cognome = row[4]
            email = row[5]
            telefono = row[6]
            pagamento = row[7]
            
            # Date utilizzo (4 o 8 colonne)
            date_utilizzo = [row[8 + i] for i in range(sub_type.max_events) if len(row) > 8 + i]
            
            if not nome or not cognome:
                continue
            
            # Trova o crea utente
            user = self.get_or_create_user(nome, cognome, email, telefono)
            
            # Crea payment record
            if isinstance(venduto_il, datetime):
                sold_date = venduto_il.date()
            else:
                try:
                    sold_date = datetime.strptime(str(venduto_il), '%d/%m/%Y').date()
                except:
                    sold_date = timezone.now().date()
            
            payment = Payment.objects.create(
                user=user,
                payment_id=f'SUB_{codice}',
                payment_method=str(pagamento) if pagamento else 'contanti',
                amount_paid=str(sub_type.price),
                status='COMPLETED'
            )
            
            # Crea abbonamento
            subscription = Subscription.objects.create(
                subscription_number=codice,
                user=user,
                subscription_type=sub_type,
                payment=payment,
                valid_from=sold_date,
                events_included=sub_type.max_events,
                events_used=0,
                status='ACTIVE'
            )
            
            # Crea utilizzi
            for date_val in date_utilizzo:
                if date_val:
                    self.create_usage(subscription, date_val, user)
            
            self.stdout.write(f"  ✓ {codice}: {nome} {cognome} - {subscription.events_used}/{subscription.events_included} eventi usati")

    def get_or_create_user(self, nome, cognome, email, telefono):
        """Trova o crea un utente"""
        # Cerca prima per email
        if email:
            try:
                return Account.objects.get(email=email)
            except Account.DoesNotExist:
                pass
        
        # Crea nuovo utente
        username = f"{nome.lower()}.{cognome.lower()}"[:150]
        # Assicura username unico
        base_username = username
        counter = 1
        while Account.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        
        user = Account.objects.create_user(
            username=username,
            email=email or f"{username}@example.com",
            first_name=nome,
            last_name=cognome,
            password=Account.objects.make_random_password()
        )
        user.phone_number = telefono or ''
        user.save()
        
        return user

    def create_usage(self, subscription, date_val, validated_by):
        """Crea un record di utilizzo"""
        # Converti data
        if isinstance(date_val, datetime):
            usage_date = date_val
        else:
            try:
                usage_date = datetime.strptime(str(date_val), '%d/%m/%Y')
            except:
                return
        
        # Trova evento nella data (se esiste)
        event = Event.objects.filter(date_time__date=usage_date.date()).first()
        
        if event:
            # Crea utilizzo
            SubscriptionUsage.objects.create(
                subscription=subscription,
                event=event,
                seat='TBD',  # Posto da assegnare dopo
                used_by=validated_by
            )
