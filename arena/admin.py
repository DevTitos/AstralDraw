# arena/admin.py (Minimal working version)
from django.contrib import admin
from .models import *

# Basic admin registrations without customizations
admin.site.register(ArenaPlayer)
admin.site.register(ArenaGame)
admin.site.register(Tournament)
admin.site.register(Challenge)
admin.site.register(ArenaLeaderboard)
admin.site.register(TournamentParticipant)