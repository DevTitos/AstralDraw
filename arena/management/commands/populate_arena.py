# arena/management/commands/populate_arena.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import random
from decimal import Decimal
from arena.models import *

class Command(BaseCommand):
    help = 'Populate Astral Arena with sample data for testing'

    def handle(self, *args, **options):
        self.stdout.write('🌌 Populating Astral Arena with sample data...')
        
        # Create sample users if they don't exist
        sample_users = self.create_sample_users()
        
        # Create sample tournaments
        sample_tournaments = self.create_sample_tournaments()
        
        # Create sample games
        sample_games = self.create_sample_games(sample_users)
        
        # Create sample challenges
        sample_challenges = self.create_sample_challenges(sample_users)
        
        # Create leaderboard entries
        self.create_leaderboard_entries(sample_users)
        
        self.stdout.write(
            self.style.SUCCESS('✅ Successfully populated Astral Arena with sample data!')
        )

    def create_sample_users(self):
        """Create 10 sample users with arena profiles"""
        users_data = [
            {'username': 'quantum_warrior', 'email': 'quantum@astral.com', 'rating': 2450, 'tier': 'quantum'},
            {'username': 'cosmic_master', 'email': 'cosmic@astral.com', 'rating': 2320, 'tier': 'cosmic'},
            {'username': 'stellar_strategist', 'email': 'stellar@astral.com', 'rating': 2180, 'tier': 'stellar'},
            {'username': 'nebula_queen', 'email': 'nebula@astral.com', 'rating': 2050, 'tier': 'galactic'},
            {'username': 'singularity_knight', 'email': 'singularity@astral.com', 'rating': 1950, 'tier': 'galactic'},
            {'username': 'temporal_lord', 'email': 'temporal@astral.com', 'rating': 1850, 'tier': 'nova'},
            {'username': 'quantum_novice', 'email': 'novice@astral.com', 'rating': 1200, 'tier': 'nova'},
            {'username': 'astro_beginner', 'email': 'beginner@astral.com', 'rating': 950, 'tier': 'protostar'},
            {'username': 'cosmic_rookie', 'email': 'rookie@astral.com', 'rating': 750, 'tier': 'protostar'},
            {'username': 'star_cadet', 'email': 'cadet@astral.com', 'rating': 600, 'tier': 'protostar'},
        ]
        
        users = []
        for user_data in users_data:
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={'email': user_data['email'], 'password': 'testpass123'}
            )
            
            if created:
                arena_profile, _ = ArenaPlayer.objects.get_or_create(
                    user=user,
                    defaults={
                        'rating': user_data['rating'],
                        'tier': user_data['tier'],
                        'games_played': random.randint(50, 200),
                        'games_won': random.randint(20, 150),
                        'win_streak': random.randint(0, 10),
                        'max_win_streak': random.randint(5, 25),
                        'total_astra_won': Decimal(random.randint(1000, 50000)),
                        'total_astra_lost': Decimal(random.randint(500, 20000)),
                    }
                )
                users.append(user)
                self.stdout.write(f'👤 Created user: {user.username}')
        
        return users

    def create_sample_tournaments(self):
        """Create sample tournaments"""
        tournaments_data = [
            {
                'name': 'Quantum Grand Prix',
                'tournament_type': 'weekly',
                'entry_fee': Decimal('500'),
                'max_players': 16,
                'start_time': timezone.now() + timedelta(hours=2),
                'end_time': timezone.now() + timedelta(days=7),
            },
            {
                'name': 'Cosmic Clash Daily',
                'tournament_type': 'daily',
                'entry_fee': Decimal('100'),
                'max_players': 8,
                'start_time': timezone.now() + timedelta(hours=1),
                'end_time': timezone.now() + timedelta(hours=24),
            },
            {
                'name': 'Stellar Championship',
                'tournament_type': 'monthly',
                'entry_fee': Decimal('1000'),
                'max_players': 32,
                'start_time': timezone.now() + timedelta(days=1),
                'end_time': timezone.now() + timedelta(days=30),
            },
        ]
        
        tournaments = []
        for tournament_data in tournaments_data:
            tournament, created = Tournament.objects.get_or_create(
                name=tournament_data['name'],
                defaults=tournament_data
            )
            if created:
                tournaments.append(tournament)
                self.stdout.write(f'🏆 Created tournament: {tournament.name}')
        
        return tournaments

    def create_sample_games(self, users):
        """Create sample completed games"""
        if len(users) < 4:
            return []
        
        games_data = [
            {
                'player1': users[0], 'player2': users[1], 'stake_amount': Decimal('1000'),
                'winner': users[0], 'victory_type': 'core_capture', 'mode': 'duel',
                'status': 'completed', 'turn_number': 24,
            },
            {
                'player1': users[2], 'player2': users[3], 'stake_amount': Decimal('500'),
                'winner': users[3], 'victory_type': 'energy_depletion', 'mode': 'ranked',
                'status': 'completed', 'turn_number': 18,
            },
            {
                'player1': users[1], 'player2': users[4], 'stake_amount': Decimal('2000'),
                'winner': users[1], 'victory_type': 'core_capture', 'mode': 'challenge',
                'status': 'completed', 'turn_number': 32,
            },
            {
                'player1': users[5], 'player2': users[6], 'stake_amount': Decimal('100'),
                'winner': users[6], 'victory_type': 'timeout', 'mode': 'duel',
                'status': 'completed', 'turn_number': 12,
            },
            {
                'player1': users[7], 'player2': users[8], 'stake_amount': Decimal('300'),
                'winner': users[7], 'victory_type': 'core_capture', 'mode': 'ranked',
                'status': 'completed', 'turn_number': 28,
            },
        ]
        
        games = []
        for i, game_data in enumerate(games_data):
            game_id = f"SAMPLE_{i+1}_{timezone.now().strftime('%Y%m%d')}"
            
            # Calculate rewards
            total_pot = game_data['stake_amount'] * 2
            platform_fee = total_pot * Decimal('0.10')
            winner_reward = total_pot - platform_fee
            
            game, created = ArenaGame.objects.get_or_create(
                game_id=game_id,
                defaults={
                    **game_data,
                    'platform_fee': platform_fee,
                    'winner_reward': winner_reward,
                    'player1_energy': random.randint(20, 100),
                    'player2_energy': random.randint(20, 100),
                    'player1_time_remaining': random.randint(30, 180),
                    'player2_time_remaining': random.randint(30, 180),
                    'board_state': self.generate_sample_board_state(),
                    'move_history': self.generate_sample_move_history(game_data['turn_number']),
                    'created_at': timezone.now() - timedelta(hours=random.randint(1, 48)),
                    'started_at': timezone.now() - timedelta(hours=random.randint(1, 47)),
                    'completed_at': timezone.now() - timedelta(hours=random.randint(0, 46)),
                }
            )
            if created:
                games.append(game)
                self.stdout.write(f'🎮 Created game: {game.game_id}')
        
        return games

    def create_sample_challenges(self, users):
        """Create sample challenges"""
        if len(users) < 4:
            return []
        
        challenges_data = [
            {
                'challenger': users[1], 'opponent': users[2], 
                'stake_amount': Decimal('800'), 'status': 'pending',
                'expires_at': timezone.now() + timedelta(minutes=15),
            },
            {
                'challenger': users[3], 'opponent': users[0], 
                'stake_amount': Decimal('1500'), 'status': 'accepted',
                'expires_at': timezone.now() + timedelta(minutes=5),
            },
            {
                'challenger': users[4], 'opponent': users[5], 
                'stake_amount': Decimal('200'), 'status': 'rejected',
                'expires_at': timezone.now() - timedelta(minutes=10),
            },
        ]
        
        challenges = []
        for challenge_data in challenges_data:
            challenge, created = Challenge.objects.get_or_create(
                challenger=challenge_data['challenger'],
                opponent=challenge_data['opponent'],
                stake_amount=challenge_data['stake_amount'],
                defaults=challenge_data
            )
            if created:
                challenges.append(challenge)
                self.stdout.write(f'⚡ Created challenge: {challenge.challenger.username} → {challenge.opponent.username}')
        
        return challenges

    def create_leaderboard_entries(self, users):
        """Create leaderboard entries for all seasons"""
        seasons = ['s1', 's2', 's3']
        
        for season in seasons:
            for position, user in enumerate(users[:10], 1):
                profile = user.arena_profile
                win_rate = (profile.games_won / profile.games_played * 100) if profile.games_played > 0 else 0
                
                leaderboard_entry, created = ArenaLeaderboard.objects.get_or_create(
                    season=season,
                    player=user,
                    defaults={
                        'position': position,
                        'rating': profile.rating - random.randint(0, 100),  # Slight variation per season
                        'games_played': profile.games_played,
                        'win_rate': round(win_rate, 2),
                        'astra_won': profile.total_astra_won,
                    }
                )
                if created:
                    self.stdout.write(f'📊 Created leaderboard entry: {user.username} in {season}')

    def generate_sample_board_state(self):
        """Generate a sample board state for completed games"""
        return {
            'pieces': [
                {'number': 7, 'type': 'prime', 'player': 1, 'row': 3, 'col': 4},
                {'number': 23, 'type': 'prime', 'player': 1, 'row': 2, 'col': 5},
                {'number': 8, 'type': 'fibonacci', 'player': 1, 'row': 4, 'col': 3},
                {'number': 16, 'type': 'square', 'player': 2, 'row': 5, 'col': 4},
                {'number': 41, 'type': 'prime', 'player': 2, 'row': 6, 'col': 3},
                {'number': 21, 'type': 'fibonacci', 'player': 2, 'row': 5, 'col': 5},
            ],
            'special_tiles': {
                '2,2': 'quantum-tile',
                '5,5': 'dark-matter',
                '1,7': 'wormhole',
                '6,1': 'wormhole',
            }
        }

    def generate_sample_move_history(self, turn_count):
        """Generate sample move history"""
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