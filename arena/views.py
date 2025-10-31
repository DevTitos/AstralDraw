# arena/views.py
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from datetime import timedelta, datetime
import json
from .models import *
from decimal import Decimal
import random
from arena.ai_models import AstralAI

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
    
    # Get leaderboard entries for the selected season
    leaderboard_entries = ArenaLeaderboard.objects.filter(
        season=season
    ).select_related('player', 'player__arena_profile').order_by('position')[:100]
    
    # Get user's rank if not in top 100
    user_rank = None
    if request.user.is_authenticated:
        try:
            user_rank = ArenaLeaderboard.objects.get(
                season=season,
                player=request.user
            )
        except ArenaLeaderboard.DoesNotExist:
            # If user doesn't have a rank this season, create a placeholder
            user_profile = request.user.arena_profile
            user_rank = {
                'position': ArenaLeaderboard.objects.filter(season=season).count() + 1,
                'rating': user_profile.rating,
                'tier': user_profile.get_tier_display(),
                'player': request.user
            }
    
    context = {
        'season': season,
        'leaderboard': leaderboard_entries,
        'user_rank': user_rank,
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

# arena/views.py - Add these tournament views

@login_required
def tournament_list(request):
    """Display all available tournaments"""
    # Active tournaments (currently running)
    active_tournaments = Tournament.objects.filter(
        is_active=True,
        start_time__lte=timezone.now(),
        end_time__gte=timezone.now()
    ).order_by('start_time')
    
    # Upcoming tournaments
    upcoming_tournaments = Tournament.objects.filter(
        is_active=False,
        is_completed=False,
        start_time__gt=timezone.now()
    ).order_by('start_time')
    
    # Completed tournaments
    completed_tournaments = Tournament.objects.filter(
        is_completed=True
    ).order_by('-end_time')[:10]
    
    # Check which tournaments user has joined
    user_participations = TournamentParticipant.objects.filter(
        player=request.user,
        tournament__in=active_tournaments | upcoming_tournaments
    ).values_list('tournament_id', flat=True)
    
    context = {
        'active_tournaments': active_tournaments,
        'upcoming_tournaments': upcoming_tournaments,
        'completed_tournaments': completed_tournaments,
        'user_participations': list(user_participations),
    }
    return render(request, 'arena/tournaments.html', context)

@login_required
@require_http_methods(["POST"])
def join_tournament(request, tournament_id):
    """Join a tournament"""
    try:
        tournament = get_object_or_404(Tournament, id=tournament_id)
        
        # Validation checks
        if tournament.is_completed:
            return JsonResponse({
                "success": False,
                "message": "This tournament has already ended"
            }, status=400)
        
        if tournament.current_players >= tournament.max_players:
            return JsonResponse({
                "success": False,
                "message": "Tournament is full"
            }, status=400)
        
        if timezone.now() > tournament.start_time:
            return JsonResponse({
                "success": False,
                "message": "Tournament has already started"
            }, status=400)
        
        # Check if user already joined
        existing_participation = TournamentParticipant.objects.filter(
            tournament=tournament,
            player=request.user
        ).exists()
        
        if existing_participation:
            return JsonResponse({
                "success": False,
                "message": "You have already joined this tournament"
            }, status=400)
        
        # Check if user has enough ASTRA for entry fee
        if not has_sufficient_balance(request.user, tournament.entry_fee):
            return JsonResponse({
                "success": False,
                "message": f"Insufficient ASTRA balance. Entry fee: {tournament.entry_fee} ASTRA"
            }, status=400)
        
        # Create participation
        participant = TournamentParticipant.objects.create(
            tournament=tournament,
            player=request.user
        )
        
        # Update tournament player count
        tournament.current_players += 1
        tournament.save()
        
        # Deduct entry fee (in real implementation, this would be a blockchain transaction)
        # deduct_astra_balance(request.user, tournament.entry_fee)
        
        return JsonResponse({
            "success": True,
            "message": f"Successfully joined {tournament.name}!",
            "participants_count": tournament.current_players
        })
        
    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": "Failed to join tournament"
        }, status=500)

@login_required
@require_http_methods(["POST"])
def create_tournament(request):
    """Create a new tournament (admin function)"""
    try:
        if not request.user.is_staff:
            return JsonResponse({
                "success": False,
                "message": "Only staff can create tournaments"
            }, status=403)
        
        name = request.POST.get("name")
        tournament_type = request.POST.get("tournament_type")
        entry_fee = Decimal(request.POST.get("entry_fee", 0))
        max_players = int(request.POST.get("max_players", 16))
        start_time = request.POST.get("start_time")
        
        if not all([name, tournament_type, start_time]):
            return JsonResponse({
                "success": False,
                "message": "Missing required fields"
            }, status=400)
        
        # Parse start time
        start_datetime = timezone.make_aware(
            datetime.strptime(start_time, '%Y-%m-%dT%H:%M')
        )
        
        # Calculate end time based on tournament type
        if tournament_type == 'daily':
            end_datetime = start_datetime + timedelta(hours=24)
        elif tournament_type == 'weekly':
            end_datetime = start_datetime + timedelta(days=7)
        elif tournament_type == 'monthly':
            end_datetime = start_datetime + timedelta(days=30)
        else:  # special
            end_datetime = start_datetime + timedelta(hours=6)
        
        # Calculate prize pool (platform adds 50% of total entry fees)
        estimated_prize_pool = (entry_fee * max_players) * Decimal('1.5')
        
        tournament = Tournament.objects.create(
            name=name,
            tournament_type=tournament_type,
            entry_fee=entry_fee,
            max_players=max_players,
            total_prize_pool=estimated_prize_pool,
            start_time=start_datetime,
            end_time=end_datetime,
            is_active=False  # Will become active when start time reached
        )
        
        return JsonResponse({
            "success": True,
            "message": f"Tournament '{name}' created successfully!",
            "tournament_id": tournament.id
        })
        
    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": "Failed to create tournament"
        }, status=500)


@login_required
def tournament_detail(request, tournament_id):
    """Display tournament details and bracket"""
    tournament = get_object_or_404(Tournament, id=tournament_id)
    participants = TournamentParticipant.objects.filter(
        tournament=tournament
    ).select_related('player', 'player__arena_profile').order_by('joined_at')
    
    # Get tournament games (you'll need to implement this logic)
    tournament_games = ArenaGame.objects.filter(
        mode='tournament',
        # Add your tournament game filtering logic here
    ).select_related('player1', 'player2', 'winner').order_by('created_at')
    
    # Check if user is participating
    user_participation = participants.filter(player=request.user).first()
    
    # Calculate prize distribution percentages
    first_prize = "50%"
    second_prize = "30%" 
    third_prize = "20%"
    
    context = {
        'tournament': tournament,
        'participants': participants,
        'tournament_games': tournament_games,
        'user_participation': user_participation,
        'can_join': can_join_tournament(tournament, request.user),
        'first_prize': first_prize,
        'second_prize': second_prize,
        'third_prize': third_prize,
        'now': timezone.now(),
    }
    return render(request, 'arena/tournament_detail.html', context)

@login_required
def my_tournaments(request):
    """Show tournaments the user has joined"""
    user_participations = TournamentParticipant.objects.filter(
        player=request.user
    ).select_related('tournament').order_by('-tournament__start_time')
    
    # Separate into active and completed
    active_participations = [p for p in user_participations if not p.tournament.is_completed]
    completed_participations = [p for p in user_participations if p.tournament.is_completed]
    
    context = {
        'active_participations': active_participations,
        'completed_participations': completed_participations,
    }
    return render(request, 'arena/my_tournaments.html', context)


# Conditional Celery import to avoid errors if Celery isn't installed
try:
    from celery import shared_task
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    # Create a dummy decorator if Celery isn't available
    def shared_task(func):
        return func

# ... your existing models and other views ...

# Tournament management functions
def start_tournament(tournament_id):
    """Start a tournament when its start time is reached"""
    try:
        tournament = Tournament.objects.get(id=tournament_id)
        
        if tournament.is_active or tournament.is_completed:
            return
        
        # Check if we have enough players
        if tournament.current_players < 2:  # Minimum 2 players
            tournament.is_completed = True
            tournament.save()
            # Refund entry fees
            refund_tournament_entries(tournament)
            return
        
        tournament.is_active = True
        tournament.save()
        
        # Create tournament bracket and initial matches
        create_tournament_bracket(tournament)
        
    except Tournament.DoesNotExist:
        pass

def create_tournament_bracket(tournament):
    """Create initial bracket for tournament"""
    participants = TournamentParticipant.objects.filter(tournament=tournament)
    participant_list = list(participants)
    
    # Shuffle participants for random seeding
    random.shuffle(participant_list)
    
    # Create initial matches (this is a simplified version)
    # In a real implementation, you'd create a proper bracket structure
    for i in range(0, len(participant_list), 2):
        if i + 1 < len(participant_list):
            create_tournament_game(
                tournament,
                participant_list[i].player,
                participant_list[i + 1].player
            )

def create_tournament_game(tournament, player1, player2):
    """Create a tournament game"""
    game_id = f"TOURNEY_{tournament.id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
    
    game = ArenaGame.objects.create(
        game_id=game_id,
        mode='tournament',
        player1=player1,
        player2=player2,
        stake_amount=0,  # Tournament games don't have individual stakes
        status='active',
        started_at=timezone.now()
    )
    
    return game

def refund_tournament_entries(tournament):
    """Refund entry fees if tournament doesn't start"""
    participants = TournamentParticipant.objects.filter(tournament=tournament)
    for participant in participants:
        # refund_astra_balance(participant.player, tournament.entry_fee)
        pass

def can_join_tournament(tournament, user):
    """Check if user can join a tournament"""
    if tournament.is_completed or tournament.is_active:
        return False
    
    if tournament.current_players >= tournament.max_players:
        return False
    
    if timezone.now() > tournament.start_time:
        return False
    
    # Check if already joined
    if TournamentParticipant.objects.filter(tournament=tournament, player=user).exists():
        return False
    
    return True

# Celery tasks for tournament management
@shared_task
def check_tournament_starts():
    """Check and start tournaments that should begin"""
    if not CELERY_AVAILABLE:
        return  # Skip if Celery isn't available
    
    now = timezone.now()
    tournaments_to_start = Tournament.objects.filter(
        is_active=False,
        is_completed=False,
        start_time__lte=now,
        start_time__gte=now - timedelta(minutes=5)  # Within last 5 minutes
    )
    
    for tournament in tournaments_to_start:
        start_tournament(tournament.id)

@shared_task
def check_tournament_ends():
    """Check and end tournaments that should be completed"""
    if not CELERY_AVAILABLE:
        return  # Skip if Celery isn't available
    
    now = timezone.now()
    tournaments_to_end = Tournament.objects.filter(
        is_active=True,
        end_time__lte=now
    )
    
    for tournament in tournaments_to_end:
        end_tournament(tournament.id)

def end_tournament(tournament_id):
    """End a tournament and distribute prizes"""
    try:
        tournament = Tournament.objects.get(id=tournament_id)
        tournament.is_active = False
        tournament.is_completed = True
        tournament.save()
        
        # Calculate and distribute prizes
        distribute_tournament_prizes(tournament)
        
    except Tournament.DoesNotExist:
        pass

def distribute_tournament_prizes(tournament):
    """Distribute prizes to tournament winners"""
    # Get final standings (this would be based on tournament results)
    participants = TournamentParticipant.objects.filter(
        tournament=tournament
    ).order_by('position')
    
    prize_distribution = calculate_prize_distribution(tournament)
    
    for participant in participants:
        if participant.position and participant.position in prize_distribution:
            prize_amount = prize_distribution[participant.position]
            participant.prize_won = prize_amount
            participant.save()
            
            # Award prize to player
            # award_astra_prize(participant.player, prize_amount)

def calculate_prize_distribution(tournament):
    """Calculate prize distribution based on tournament type and player count"""
    total_prize_pool = tournament.total_prize_pool
    player_count = tournament.current_players
    
    # Simple distribution: 50% to 1st, 30% to 2nd, 20% to 3rd
    distribution = {
        1: total_prize_pool * Decimal('0.5'),
        2: total_prize_pool * Decimal('0.3'),
        3: total_prize_pool * Decimal('0.2'),
    }
    
    return distribution

# Manual tournament management views (for when Celery isn't available)
@login_required
def manual_tournament_check(request):
    """Manual endpoint to check tournament starts/ends (for development)"""
    if not request.user.is_staff:
        return JsonResponse({"success": False, "message": "Staff only"})
    
    check_tournament_starts()
    check_tournament_ends()
    
    return JsonResponse({"success": True, "message": "Tournament checks completed"})




# arena/views.py - Add these practice mode views
@login_required
def practice_lobby(request):
    """Practice mode lobby where users select AI difficulty"""
    context = {
        'ai_difficulties': [
            {'level': 'beginner', 'name': 'Cosmic Cadet', 'rating': 800, 'description': 'Perfect for learning the basics'},
            {'level': 'intermediate', 'name': 'Stellar Student', 'rating': 1200, 'description': 'Good for developing strategies'},
            {'level': 'advanced', 'name': 'Galactic Guardian', 'rating': 1600, 'description': 'Challenging opponent for experienced players'},
            {'level': 'expert', 'name': 'Quantum Master', 'rating': 2000, 'description': 'Extreme challenge for pros'},
        ]
    }
    return render(request, 'arena/practice_lobby.html', context)

@login_required
@require_http_methods(["POST"])
def start_practice_game(request):
    """Start a new practice game against AI"""
    try:
        difficulty = request.POST.get("difficulty", "beginner")
        
        # Create AI opponent
        ai = AstralAI(difficulty)
        
        # Generate unique game ID
        game_id = f"PRACTICE_{difficulty}_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create practice game
        game = ArenaGame.objects.create(
            game_id=game_id,
            mode='practice',
            player1=request.user,
            player2=None,  # No human player 2
            stake_amount=0,  # Free practice
            status='active',
            started_at=timezone.now(),
            # AI metadata stored in board_state
            board_state={
                'pieces': initialize_practice_board(),
                'special_tiles': initialize_special_tiles(),
                'ai_difficulty': difficulty,
                'ai_name': ai.name,
                'ai_rating': ai.rating
            }
        )
        
        return JsonResponse({
            "success": True,
            "message": f"Practice game started against {ai.name}!",
            "game_id": game.game_id
        })
        
    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": "Failed to start practice game"
        }, status=500)

@login_required
@require_http_methods(["POST"])
def ai_make_move(request):
    """AI makes a move in response to player's move"""
    try:
        game_id = request.POST.get("game_id")
        game = get_object_or_404(ArenaGame, game_id=game_id, player1=request.user)
        
        # Get AI based on game difficulty
        ai_difficulty = game.board_state.get('ai_difficulty', 'beginner')
        ai = AstralAI(ai_difficulty)
        
        # AI makes move
        ai_move = ai.make_move(game.board_state)
        
        if ai_move:
            # Update board with AI's move
            update_board_with_move(game, ai_move, player_number=2)
            
            # AI might use ability
            ability = ai.decide_ability_usage(game.board_state)
            if ability:
                process_ai_ability(game, ability, ai)
            
            # Switch back to player's turn
            game.current_player = 1
            game.save()
            
            return JsonResponse({
                "success": True,
                "message": f"{ai.name} made a move",
                "ai_move": ai_move,
                "ability_used": ability,
                "game_state": get_game_state(game)
            })
        else:
            return JsonResponse({
                "success": False,
                "message": "AI couldn't find a valid move"
            })
            
    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": "AI move failed"
        }, status=500)

def initialize_practice_board():
    """Initialize board for practice game"""
    return {
        'pieces': [
            # Player 1 pieces (bottom)
            {'number': 7, 'type': 'prime', 'player': 1, 'row': 6, 'col': 0},
            {'number': 8, 'type': 'fibonacci', 'player': 1, 'row': 6, 'col': 1},
            {'number': 16, 'type': 'square', 'player': 1, 'row': 6, 'col': 2},
            {'number': 12, 'type': 'composite', 'player': 1, 'row': 6, 'col': 3},
            {'number': 23, 'type': 'prime', 'player': 1, 'row': 7, 'col': 0},  # Core
            {'number': 21, 'type': 'fibonacci', 'player': 1, 'row': 7, 'col': 1},
            {'number': 36, 'type': 'square', 'player': 1, 'row': 7, 'col': 2},
            {'number': 18, 'type': 'composite', 'player': 1, 'row': 7, 'col': 3},
            
            # AI pieces (top) - player 2
            {'number': 41, 'type': 'prime', 'player': 2, 'row': 0, 'col': 4},
            {'number': 55, 'type': 'fibonacci', 'player': 2, 'row': 0, 'col': 5},
            {'number': 64, 'type': 'square', 'player': 2, 'row': 0, 'col': 6},
            {'number': 24, 'type': 'composite', 'player': 2, 'row': 0, 'col': 7},
            {'number': 17, 'type': 'prime', 'player': 2, 'row': 1, 'col': 4},  # Core
            {'number': 13, 'type': 'fibonacci', 'player': 2, 'row': 1, 'col': 5},
            {'number': 49, 'type': 'square', 'player': 2, 'row': 1, 'col': 6},
            {'number': 28, 'type': 'composite', 'player': 2, 'row': 1, 'col': 7},
        ]
    }

def initialize_special_tiles():
    """Initialize special tiles for practice"""
    return {
        '2,2': 'quantum-tile',
        '5,5': 'dark-matter',
        '1,7': 'wormhole',
        '6,1': 'wormhole'
    }

def update_board_with_move(game, move, player_number):
    """Update board state with a move"""
    piece = move['piece']
    to_row, to_col = move['to_pos']
    
    # Update piece position
    for p in game.board_state['pieces']:
        if (p['number'] == piece['number'] and 
            p['player'] == piece['player'] and
            p['type'] == piece['type']):
            p['row'] = to_row
            p['col'] = to_col
            break
    
    # Check for captures
    game.board_state['pieces'] = [
        p for p in game.board_state['pieces'] 
        if not (p['row'] == to_row and p['col'] == to_col and p['player'] != player_number)
    ]
    
    game.save()

def process_ai_ability(game, ability, ai, self):
    """Process AI ability usage"""
    # Simplified ability processing
    if ability == 'quantum_tunnel':
        # AI teleports a random piece
        ai_pieces = [p for p in game.board_state['pieces'] if p['player'] == 2]
        if ai_pieces:
            piece = random.choice(ai_pieces)
            empty_squares = self._find_empty_squares(game.board_state)
            if empty_squares:
                new_pos = random.choice(empty_squares)
                piece['row'], piece['col'] = new_pos