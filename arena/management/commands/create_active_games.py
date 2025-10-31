# arena/management/commands/create_active_games.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
from arena.models import *
import random
from datetime import timedelta

class Command(BaseCommand):
    help = 'Create some active games for demonstration'

    def handle(self, *args, **options):
        self.stdout.write('🎮 Creating active games...')
        
        try:
            # Get some users
            users = User.objects.all()[:4]
            if len(users) < 2:
                self.stdout.write('❌ Need at least 2 users to create active games')
                return

            # Create active games
            active_games_data = [
                {
                    'player1': users[0], 'player2': users[1], 
                    'stake_amount': Decimal('750'), 'mode': 'duel', 'status': 'active',
                    'current_player': 1, 'turn_number': 8,
                },
                {
                    'player1': users[2], 'player2': users[3], 
                    'stake_amount': Decimal('1200'), 'mode': 'ranked', 'status': 'active',
                    'current_player': 2, 'turn_number': 15,
                },
            ]
            
            for i, game_data in enumerate(active_games_data):
                game_id = f"LIVE_{i+1}_{timezone.now().strftime('%H%M%S')}"
                
                game, created = ArenaGame.objects.get_or_create(
                    game_id=game_id,
                    defaults={
                        **game_data,
                        'player1_energy': 85,
                        'player2_energy': 70,
                        'player1_time_remaining': 142,
                        'player2_time_remaining': 156,
                        'board_state': self.generate_active_board_state(),
                        'move_history': self.generate_active_move_history(game_data['turn_number']),
                        'created_at': timezone.now() - timedelta(minutes=10),
                        'started_at': timezone.now() - timedelta(minutes=9),
                    }
                )
                if created:
                    self.stdout.write(f'🎲 Created active game: {game.game_id}')

        except Exception as e:
            self.stdout.write(f'❌ Error creating active games: {e}')

    def generate_active_board_state(self):
        return {
            'pieces': [
                {'number': 7, 'type': 'prime', 'player': 1, 'row': 6, 'col': 2},
                {'number': 23, 'type': 'prime', 'player': 1, 'row': 7, 'col': 1},
                {'number': 8, 'type': 'fibonacci', 'player': 1, 'row': 6, 'col': 1},
                {'number': 16, 'type': 'square', 'player': 1, 'row': 7, 'col': 2},
                {'number': 41, 'type': 'prime', 'player': 2, 'row': 1, 'col': 5},
                {'number': 17, 'type': 'prime', 'player': 2, 'row': 0, 'col': 4},
                {'number': 21, 'type': 'fibonacci', 'player': 2, 'row': 1, 'col': 4},
                {'number': 64, 'type': 'square', 'player': 2, 'row': 0, 'col': 5},
            ],
            'special_tiles': {
                '2,2': 'quantum-tile',
                '5,5': 'dark-matter',
            }
        }

    def generate_active_move_history(self, turn_count):
        moves = []
        for turn in range(1, turn_count + 1):
            moves.append({
                'turn': turn,
                'player': 1 if turn % 2 == 1 else 2,
                'from': [random.randint(0, 7), random.randint(0, 7)],
                'to': [random.randint(0, 7), random.randint(0, 7)],
                'timestamp': (timezone.now() - timedelta(minutes=turn_count - turn)).isoformat(),
            })
        return moves