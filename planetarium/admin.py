from django.contrib import admin

from .models import (
    PlanetariumDome,
    ShowSession,
    AstronomyShow,
    ShowTheme,
    Reservation,
    Ticket,
)

admin.site.register(PlanetariumDome)
admin.site.register(ShowTheme)
admin.site.register(ShowSession)
admin.site.register(AstronomyShow)
admin.site.register(Reservation)
admin.site.register(Ticket)
