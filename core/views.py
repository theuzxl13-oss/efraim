from django.shortcuts import render
from django.utils import timezone

from .models import Congregation, Event, Minute


def home(request):
    proximos_eventos = Event.objects.filter(published=True, event_date__gte=timezone.now()).order_by(
        "event_date"
    )[:3]
    ultimas_atas = Minute.objects.filter(published=True).order_by("-meeting_date")[:3]
    return render(
        request,
        "core/home.html",
        {"proximos_eventos": proximos_eventos, "ultimas_atas": ultimas_atas},
    )


def _congregation_filter(request, queryset):
    congregacao_id = request.GET.get("congregacao")
    if congregacao_id and congregacao_id.isdigit():
        queryset = queryset.filter(congregation_id=congregacao_id)
    return queryset


def eventos(request):
    agora = timezone.now()
    qs = Event.objects.filter(published=True).select_related("congregation")
    qs = _congregation_filter(request, qs)
    proximos = qs.filter(event_date__gte=agora).order_by("event_date")
    passados = qs.filter(event_date__lt=agora).order_by("-event_date")
    return render(
        request,
        "core/eventos.html",
        {
            "proximos_eventos": proximos,
            "eventos_passados": passados,
            "congregacoes": Congregation.objects.all(),
            "congregacao_selecionada": request.GET.get("congregacao", ""),
        },
    )


def atas(request):
    qs = Minute.objects.filter(published=True).select_related("congregation").order_by("-meeting_date")
    qs = _congregation_filter(request, qs)
    return render(
        request,
        "core/atas.html",
        {
            "atas": qs,
            "congregacoes": Congregation.objects.all(),
            "congregacao_selecionada": request.GET.get("congregacao", ""),
        },
    )
