# arena/views.py
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from datetime import timedelta
import json
from .models import *
from decimal import Decimal

@login_required
def arena_lobby(request):
    """Main arena lobby view"""
    player_profile, created = ArenaPlayer.objects.get_or_create(user=request.user)
    
    # Get active tournaments
    active_tournaments = Tournament.objects.filter(
        is_active=True, 
        start_time__lte=timezone.now(),
        end_time__gte=timezone.now()
    )
    
    # Get pending challenges
    pending_challenges = Challenge.objects.filter(
        opponent=request.user,
        status='pending',
        expires_at__gt=timezone.now()
    )
    
    # Get available players for challenges (excluding self)
    available_players = User.objects.filter(
        is_active=True,
        arena_profile__isnull=False
    ).exclude(id=request.user.id)
    
    context = {
        'player_profile': player_profile,
        'active_tournaments': active_tournaments,
        'pending_challenges': pending_challenges,
        'available_players': available_players,
    }
    return render(request, 'arena/lobby.html', context)

@login_required
@require_http_methods(["POST"])
def create_challenge(request):
    """Create a challenge to another player"""
    try:
        opponent_id = request.POST.get("opponent_id")
        stake_amount = Decimal(request.POST.get("stake_amount", 100))
        
        if stake_amount < 100:
            return JsonResponse({
                "success": False, 
                "message": "Minimum stake is 100 ASTRA"
            }, status=400)
        
        opponent = get_object_or_404(User, id=opponent_id)
        
        # Check if player has enough ASTRA
        # This would integrate with your main wallet system
        if not has_sufficient_balance(request.user, stake_amount):
            return JsonResponse({
                "success": False,
                "message": "Insufficient ASTRA balance"
            }, status=400)
        
        # Create challenge
        challenge = Challenge.objects.create(
            challenger=request.user,
            opponent=opponent,
            stake_amount=stake_amount,
            expires_at=timezone.now() + timedelta(seconds=30)
        )
        
        return JsonResponse({
            "success": True,
            "message": "Challenge sent successfully",
            "challenge_id": challenge.id
        })
        
    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": "Failed to create challenge"
        }, status=500)

@login_required
@require_http_methods(["POST"])
def respond_to_challenge(request):
    """Accept or reject a challenge"""
    try:
        challenge_id = request.POST.get("challenge_id")
        action = request.POST.get("action")  # 'accept' or 'reject'
        
        challenge = get_object_or_404(Challenge, id=challenge_id, opponent=request.user)
        
        if challenge.is_expired():
            challenge.status = 'expired'
            challenge.save()
            return JsonResponse({
                "success": False,
                "message": "Challenge has expired"
            }, status=400)
        
        if action == 'accept':
            # Check if opponent has enough ASTRA
            if not has_sufficient_balance(request.user, challenge.stake_amount):
                return JsonResponse({
                    "success": False,
                    "message": "Insufficient ASTRA balance"
                }, status=400)
            
            # Create game from challenge
            game = create_game_from_challenge(challenge)
            challenge.status = 'accepted'
            challenge.game = game
            challenge.save()
            
            return JsonResponse({
                "success": True,
                "message": "Challenge accepted! Game starting...",
                "game_id": game.game_id
            })
            
        elif action == 'reject':
            challenge.status = 'rejected'
            challenge.save()
            return JsonResponse({
                "success": True,
                "message": "Challenge rejected"
            })
            
    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": "Failed to process challenge"
        }, status=500)

@login_required
def game_interface(request, game_id):
    """Main game interface"""
    game = get_object_or_404(ArenaGame, game_id=game_id)
    
    # Check if user is part of this game
    if request.user not in [game.player1, game.player2]:
        return JsonResponse({
            "success": False,
            "message": "Not authorized to view this game"
        }, status=403)
    
    context = {
        'game': game,
        'player_number': 1 if request.user == game.player1 else 2,
    }
    return render(request, 'arena/game_interface.html', context)

@login_required
@require_http_methods(["POST"])
def make_move(request):
    """Process a player's move"""
    try:
        game_id = request.POST.get("game_id")
        from_row = int(request.POST.get("from_row"))
        from_col = int(request.POST.get("from_col"))
        to_row = int(request.POST.get("to_row"))
        to_col = int(request.POST.get("to_col"))
        
        game = get_object_or_404(ArenaGame, game_id=game_id)
        
        # Validate it's the player's turn
        player_number = 1 if request.user == game.player1 else 2
        if game.current_player != player_number:
            return JsonResponse({
                "success": False,
                "message": "Not your turn"
            }, status=400)
        
        # Process the move (this would contain your game logic)
        move_result = process_game_move(game, from_row, from_col, to_row, to_col)
        
        if move_result['success']:
            # Update game state
            game.current_player = 3 - player_number  # Switch players (1->2, 2->1)
            game.turn_number += 1
            
            # Add to move history
            move_history = game.move_history or []
            move_history.append({
                'turn': game.turn_number,
                'player': player_number,
                'from': [from_row, from_col],
                'to': [to_row, to_col],
                'timestamp': timezone.now().isoformat()
            })
            game.move_history = move_history
            
            game.save()
            
            # Check for victory
            victory_check = check_victory_conditions(game)
            if victory_check['game_over']:
                game.complete_game(victory_check['winner'], victory_check['victory_type'])
            
            return JsonResponse({
                "success": True,
                "message": "Move processed successfully",
                "game_state": get_game_state(game),
                "victory": victory_check
            })
        else:
            return JsonResponse({
                "success": False,
                "message": move_result['message']
            }, status=400)
            
    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": "Failed to process move"
        }, status=500)

@login_required
@require_http_methods(["POST"])
def use_ability(request):
    """Use a quantum ability"""
    try:
        game_id = request.POST.get("game_id")
        ability = request.POST.get("ability")
        target_row = request.POST.get("target_row")
        target_col = request.POST.get("target_col")
        
        game = get_object_or_404(ArenaGame, game_id=game_id)
        player_number = 1 if request.user == game.player1 else 2
        
        # Check energy and process ability
        ability_result = process_ability_usage(game, player_number, ability, target_row, target_col)
        
        if ability_result['success']:
            return JsonResponse({
                "success": True,
                "message": f"Used {ability} successfully",
                "energy_remaining": ability_result['energy_remaining'],
                "game_state": get_game_state(game)
            })
        else:
            return JsonResponse({
                "success": False,
                "message": ability_result['message']
            })
            
    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": "Failed to use ability"
        }, status=500)

@login_required
def leaderboard(request):
    """Display arena leaderboard"""
    season = request.GET.get('season', 's1')
    
    leaderboard_entries = ArenaLeaderboard.objects.filter(
        season=season
    ).select_related('player').order_by('position')[:100]
    
    context = {
        'season': season,
        'leaderboard': leaderboard_entries,
    }
    return render(request, 'arena/leaderboard.html', context)

@login_required
def player_stats(request, username=None):
    """View player statistics"""
    if username:
        user = get_object_or_404(User, username=username)
    else:
        user = request.user
    
    profile = get_object_or_404(ArenaPlayer, user=user)
    recent_games = ArenaGame.objects.filter(
        models.Q(player1=user) | models.Q(player2=user),
        status='completed'
    ).order_by('-completed_at')[:10]
    
    context = {
        'profile_user': user,
        'profile': profile,
        'recent_games': recent_games,
    }
    return render(request, 'arena/player_stats.html', context)

# Helper functions (would be in a separate game_logic.py)
def has_sufficient_balance(user, amount):
    """Check if user has sufficient ASTRA balance"""
    # This would integrate with your main wallet system
    # For now, return True for testing
    return True

def create_game_from_challenge(challenge):
    """Create a game instance from a challenge"""
    game_id = f"ARENA_{timezone.now().strftime('%Y%m%d_%H%M%S')}_{challenge.id}"
    
    # Initial board state
    initial_board = initialize_game_board()
    
    game = ArenaGame.objects.create(
        game_id=game_id,
        mode='challenge',
        player1=challenge.challenger,
        player2=challenge.opponent,
        stake_amount=challenge.stake_amount,
        board_state=initial_board,
        status='active',
        started_at=timezone.now()
    )
    
    return game

def initialize_game_board():
    """Initialize the game board with pieces"""
    # This would contain your initial board setup logic
    return {
        'pieces': [
            # Player 1 pieces
            {'number': 7, 'type': 'prime', 'player': 1, 'row': 6, 'col': 0},
            {'number': 8, 'type': 'fibonacci', 'player': 1, 'row': 6, 'col': 1},
            # ... more pieces
        ],
        'special_tiles': {
            '2,2': 'quantum-tile',
            '5,5': 'dark-matter',
            # ... more special tiles
        }
    }

def process_game_move(game, from_row, from_col, to_row, to_col):
    """Process a game move - contains core game logic"""
    # This would contain your complete movement validation and execution logic
    return {'success': True, 'message': 'Move valid'}

def process_ability_usage(game, player_number, ability, target_row, target_col):
    """Process quantum ability usage"""
    # This would contain your ability logic
    return {'success': True, 'energy_remaining': 75, 'message': 'Ability used'}

def check_victory_conditions(game):
    """Check if game should end"""
    # This would contain your victory condition checks
    return {'game_over': False, 'winner': None, 'victory_type': None}

def get_game_state(game):
    """Get current game state for frontend"""
    return {
        'board': game.board_state,
        'current_player': game.current_player,
        'turn_number': game.turn_number,
        'player1_energy': game.player1_energy,
        'player2_energy': game.player2_energy,
        'player1_time': game.player1_time_remaining,
        'player2_time': game.player2_time_remaining,
    }