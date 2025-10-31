# arena/management/commands/arena_stats.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from arena.models import *
from datetime import timedelta

class Command(BaseCommand):
    help = 'Generate Astral Arena statistics report'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=7, help='Number of days to analyze')

    def handle(self, *args, **options):
        days = options['days']
        since = timezone.now() - timedelta(days=days)
        
        self.stdout.write(f"🌌 Astral Arena Statistics (Last {days} days)")
        self.stdout.write("=" * 50)
        
        # Player statistics
        total_players = ArenaPlayer.objects.count()
        new_players = ArenaPlayer.objects.filter(created_at__gte=since).count()
        
        # Game statistics
        total_games = ArenaGame.objects.filter(created_at__gte=since).count()
        completed_games = ArenaGame.objects.filter(status='completed', created_at__gte=since).count()
        active_games = ArenaGame.objects.filter(status='active').count()
        
        # Financial statistics
        financials = ArenaGame.objects.filter(created_at__gte=since).aggregate(
            total_staked=Sum('stake_amount') * 2,
            total_fees=Sum('platform_fee')
        )
        
        # Tournament statistics
        tournament_stats = Tournament.objects.filter(created_at__gte=since).aggregate(
            total=Count('id'),
            active=Count('id', filter=Q(is_active=True)),
            completed=Count('id', filter=Q(is_completed=True))
        )
        
        self.stdout.write(f"👥 Players: {total_players} total, {new_players} new")
        self.stdout.write(f"🎮 Games: {total_games} total, {completed_games} completed, {active_games} active")
        self.stdout.write(f"💰 Financial: {financials['total_staked'] or 0} ASTRA staked, {financials['total_fees'] or 0} ASTRA fees")
        self.stdout.write(f"🏆 Tournaments: {tournament_stats['total']} total, {tournament_stats['active']} active, {tournament_stats['completed']} completed")
        
        # Top players
        self.stdout.write("\n🏅 Top 5 Players:")
        top_players = ArenaPlayer.objects.order_by('-rating')[:5]
        for i, player in enumerate(top_players, 1):
            self.stdout.write(f"  {i}. {player.user.username} - {player.rating} ({player.tier})")