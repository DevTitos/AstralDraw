# arena/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal

class ArenaPlayer(models.Model):
    TIER_CHOICES = [
        ('protostar', 'Protostar'),
        ('nova', 'Nova'),
        ('galactic', 'Galactic Player'),
        ('stellar', 'Stellar Expert'),
        ('cosmic', 'Cosmic Master'),
        ('quantum', 'Quantum Grandmaster'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='arena_profile')
    rating = models.IntegerField(default=800)
    tier = models.CharField(max_length=20, choices=TIER_CHOICES, default='protostar')
    games_played = models.IntegerField(default=0)
    games_won = models.IntegerField(default=0)
    win_streak = models.IntegerField(default=0)
    max_win_streak = models.IntegerField(default=0)
    total_astra_won = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_astra_lost = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def update_tier(self):
        if self.rating >= 2400:
            self.tier = 'quantum'
        elif self.rating >= 2000:
            self.tier = 'cosmic'
        elif self.rating >= 1600:
            self.tier = 'stellar'
        elif self.rating >= 1200:
            self.tier = 'galactic'
        elif self.rating >= 800:
            self.tier = 'nova'
        else:
            self.tier = 'protostar'
    
    def __str__(self):
        return f"{self.user.username} - {self.tier} ({self.rating})"

class ArenaGame(models.Model):
    GAME_MODES = [
        ('duel', '1v1 Duel'),
        ('tournament', 'Tournament'),
        ('challenge', 'Challenge'),
        ('ranked', 'Ranked Match'),
    ]
    
    STATUS_CHOICES = [
        ('waiting', 'Waiting for Players'),
        ('active', 'Game Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('timeout', 'Timeout'),
    ]
    
    # Game identification
    game_id = models.CharField(max_length=20, unique=True)
    mode = models.CharField(max_length=20, choices=GAME_MODES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='waiting')
    
    # Players
    player1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='arena_games_as_p1')
    player2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='arena_games_as_p2', null=True, blank=True)
    
    # Staking
    stake_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    platform_fee = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    winner_reward = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Game state
    current_player = models.IntegerField(default=1)  # 1 or 2
    turn_number = models.IntegerField(default=1)
    player1_energy = models.IntegerField(default=100)
    player2_energy = models.IntegerField(default=100)
    player1_time_remaining = models.IntegerField(default=180)  # 3 minutes in seconds
    player2_time_remaining = models.IntegerField(default=180)
    
    # Board state (JSON field for flexibility)
    board_state = models.JSONField(default=dict)
    move_history = models.JSONField(default=list)
    
    # Results
    winner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='arena_wins', null=True, blank=True)
    victory_type = models.CharField(max_length=50, blank=True)  # 'core_capture', 'timeout', 'energy_depletion'
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def calculate_rewards(self):
        """Calculate platform fee and winner reward"""
        total_pot = self.stake_amount * 2
        self.platform_fee = Decimal(total_pot) * Decimal('0.10')  # 10% platform fee
        self.winner_reward = Decimal(total_pot) - self.platform_fee
        self.save()
    
    def complete_game(self, winner, victory_type):
        """Mark game as completed and distribute rewards"""
        self.winner = winner
        self.victory_type = victory_type
        self.status = 'completed'
        self.completed_at = timezone.now()
        
        self.calculate_rewards()
        self.save()
        
        # Update player stats
        self.update_player_stats()
    
    def update_player_stats(self):
        """Update ELO ratings and player statistics"""
        player1_profile = self.player1.arena_profile
        player2_profile = self.player2.arena_profile
        
        # Update games played
        player1_profile.games_played += 1
        player2_profile.games_played += 1
        
        # Update win/loss and streaks
        if self.winner == self.player1:
            player1_profile.games_won += 1
            player1_profile.win_streak += 1
            player1_profile.max_win_streak = max(player1_profile.max_win_streak, player1_profile.win_streak)
            player2_profile.win_streak = 0
            
            # Astra transfers
            player1_profile.total_astra_won += self.winner_reward
            player2_profile.total_astra_lost += self.stake_amount
            
        elif self.winner == self.player2:
            player2_profile.games_won += 1
            player2_profile.win_streak += 1
            player2_profile.max_win_streak = max(player2_profile.max_win_streak, player2_profile.win_streak)
            player1_profile.win_streak = 0
            
            # Astra transfers
            player2_profile.total_astra_won += self.winner_reward
            player1_profile.total_astra_lost += self.stake_amount
        
        # Update ELO ratings
        self.update_elo_ratings(player1_profile, player2_profile)
        
        player1_profile.save()
        player2_profile.save()
    
    def update_elo_ratings(self, p1_profile, p2_profile):
        """Update ELO ratings based on game outcome"""
        k_factor = 32
        
        expected_p1 = 1 / (1 + 10 ** ((p2_profile.rating - p1_profile.rating) / 400))
        expected_p2 = 1 / (1 + 10 ** ((p1_profile.rating - p2_profile.rating) / 400))
        
        if self.winner == self.player1:
            actual_p1 = 1
            actual_p2 = 0
        elif self.winner == self.player2:
            actual_p1 = 0
            actual_p2 = 1
        else:  # Draw (shouldn't happen in this game)
            actual_p1 = 0.5
            actual_p2 = 0.5
        
        p1_profile.rating += round(k_factor * (actual_p1 - expected_p1))
        p2_profile.rating += round(k_factor * (actual_p2 - expected_p2))
        
        p1_profile.update_tier()
        p2_profile.update_tier()

class Tournament(models.Model):
    TOURNAMENT_TYPES = [
        ('daily', 'Daily Tournament'),
        ('weekly', 'Weekly Championship'),
        ('monthly', 'Monthly Grand Prix'),
        ('special', 'Special Event'),
    ]
    
    name = models.CharField(max_length=100)
    tournament_type = models.CharField(max_length=20, choices=TOURNAMENT_TYPES)
    entry_fee = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_prize_pool = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    max_players = models.IntegerField(default=16)
    current_players = models.IntegerField(default=0)
    
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_active = models.BooleanField(default=False)
    is_completed = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - {self.tournament_type}"

class TournamentParticipant(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='participants')
    player = models.ForeignKey(User, on_delete=models.CASCADE)
    position = models.IntegerField(null=True, blank=True)  # Final position
    prize_won = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    joined_at = models.DateTimeField(auto_now_add=True)

class Challenge(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
    ]
    
    challenger = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_challenges')
    opponent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_challenges')
    stake_amount = models.DecimalField(max_digits=15, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Resulting game if accepted
    game = models.OneToOneField(ArenaGame, on_delete=models.CASCADE, null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def is_expired(self):
        return timezone.now() > self.expires_at

class ArenaLeaderboard(models.Model):
    SEASON_CHOICES = [
        ('s1', 'Season 1'),
        ('s2', 'Season 2'),
        ('s3', 'Season 3'),
    ]
    
    season = models.CharField(max_length=10, choices=SEASON_CHOICES, default='s1')
    player = models.ForeignKey(User, on_delete=models.CASCADE)
    position = models.IntegerField()
    rating = models.IntegerField()
    games_played = models.IntegerField()
    win_rate = models.DecimalField(max_digits=5, decimal_places=2)
    astra_won = models.DecimalField(max_digits=15, decimal_places=2)
    
    class Meta:
        ordering = ['season', 'position']
        unique_together = ['season', 'player']