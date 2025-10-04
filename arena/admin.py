from django.contrib import admin
from .models import *

@admin.register(ArenaPlayer)
class ArenaPlayerAdmin(admin.ModelAdmin):
    list_display = ['user', 'tier', 'rating', 'games_played', 'games_won', 'win_streak']
    list_filter = ['tier', 'created_at']
    search_fields = ['user__username']

@admin.register(ArenaGame)
class ArenaGameAdmin(admin.ModelAdmin):
    list_display = ['game_id', 'mode', 'status', 'player1', 'player2', 'stake_amount', 'winner', 'created_at']
    list_filter = ['mode', 'status', 'created_at']
    search_fields = ['game_id', 'player1__username', 'player2__username']

@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    list_display = ['name', 'tournament_type', 'entry_fee', 'total_prize_pool', 'is_active', 'start_time']
    list_filter = ['tournament_type', 'is_active']

@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    list_display = ['challenger', 'opponent', 'stake_amount', 'status', 'created_at', 'expires_at']
    list_filter = ['status', 'created_at']

@admin.register(ArenaLeaderboard)
class ArenaLeaderboardAdmin(admin.ModelAdmin):
    list_display = ['season', 'player', 'position', 'rating', 'win_rate']
    list_filter = ['season']