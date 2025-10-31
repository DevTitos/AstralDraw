# arena/admin_dashboard.py
from django.contrib import admin
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from datetime import timedelta
from .models import *

class AstralArenaDashboard(admin.AdminSite):
    def index(self, request, extra_context=None):
        # Get statistics for the dashboard
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        
        # Basic stats
        total_players = ArenaPlayer.objects.count()
        total_games = ArenaGame.objects.count()
        active_games = ArenaGame.objects.filter(status='active').count()
        total_tournaments = Tournament.objects.count()
        active_tournaments = Tournament.objects.filter(is_active=True).count()
        
        # Financial stats
        total_staked = ArenaGame.objects.aggregate(
            total=Sum('stake_amount') * 2
        )['total'] or 0
        total_fees = ArenaGame.objects.aggregate(
            total=Sum('platform_fee')
        )['total'] or 0
        
        # Recent activity
        recent_games = ArenaGame.objects.filter(
            created_at__gte=week_ago
        ).order_by('-created_at')[:10]
        
        # Player growth
        player_growth = ArenaPlayer.objects.filter(
            created_at__gte=week_ago
        ).count()
        
        # Top players
        top_players = ArenaPlayer.objects.order_by('-rating')[:5]
        
        # Tournament status
        upcoming_tournaments = Tournament.objects.filter(
            start_time__gte=timezone.now(),
            is_completed=False
        ).order_by('start_time')[:5]
        
        extra_context = {
            'total_players': total_players,
            'total_games': total_games,
            'active_games': active_games,
            'total_tournaments': total_tournaments,
            'active_tournaments': active_tournaments,
            'total_staked': total_staked,
            'total_fees': total_fees,
            'player_growth': player_growth,
            'recent_games': recent_games,
            'top_players': top_players,
            'upcoming_tournaments': upcoming_tournaments,
        }
        
        return super().index(request, extra_context=extra_context)

# Custom admin view for game analytics
@admin.register(ArenaGame)
class ArenaGameAdmin(admin.ModelAdmin):
    # ... previous ArenaGameAdmin code ...
    
    def changelist_view(self, request, extra_context=None):
        # Add analytics to the changelist view
        response = super().changelist_view(request, extra_context=extra_context)
        
        try:
            # Game statistics
            total_games = ArenaGame.objects.count()
            completed_games = ArenaGame.objects.filter(status='completed').count()
            active_games = ArenaGame.objects.filter(status='active').count()
            
            # Victory type distribution
            victory_stats = ArenaGame.objects.filter(status='completed').values(
                'victory_type'
            ).annotate(
                count=Count('id')
            ).order_by('-count')
            
            # Mode distribution
            mode_stats = ArenaGame.objects.values('mode').annotate(
                count=Count('id')
            ).order_by('-count')
            
            # Recent financial activity
            recent_stakes = ArenaGame.objects.filter(
                created_at__gte=timezone.now() - timedelta(days=1)
            ).aggregate(
                total_staked=Sum('stake_amount') * 2,
                total_fees=Sum('platform_fee')
            )
            
            extra_context = {
                'total_games': total_games,
                'completed_games': completed_games,
                'active_games': active_games,
                'victory_stats': victory_stats,
                'mode_stats': mode_stats,
                'recent_stakes': recent_stakes,
            }
            
            if hasattr(response, 'context_data'):
                response.context_data.update(extra_context)
                
        except Exception as e:
            # Don't break the admin if analytics fail
            pass
            
        return response