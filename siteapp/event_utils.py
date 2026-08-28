from django.db.models import Q
from django.utils import timezone


def event_time_split(queryset=None):
    """Dzieli wydarzenia na nadchodzące/trwające i minione (po dacie zakończenia, a w jej braku po dacie startu)."""
    from .models import Event

    if queryset is None:
        queryset = Event.objects.all()

    today = timezone.now().date()
    is_past = Q(end_date__lt=today) | (Q(end_date__isnull=True) & Q(start_date__lt=today))
    past = queryset.filter(is_past).order_by('-start_date')
    upcoming = queryset.exclude(is_past).order_by('start_date')
    return upcoming, past
