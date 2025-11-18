from subscriptions.models import Subscription, SubscriptionType
from django.utils import timezone

print(f'Total subscriptions: {Subscription.objects.count()}')
print(f'Subscription types: {SubscriptionType.objects.count()}')

active = Subscription.objects.filter(valid_to__gte=timezone.now(), is_active=True)
print(f'\nActive subscriptions: {active.count()}')

for s in active:
    print(f'  - {s.subscription_number}: {s.user.email} - {s.remaining_events()} events remaining')
