from django.urls import path
from . import views

urlpatterns = [
    # Lobby and Navigation
    path('', views.arena_lobby, name='arena_lobby'),
    path('leaderboard/', views.leaderboard, name='arena_leaderboard'),
    path('profile/', views.player_stats, name='arena_profile'),
    path('profile/<str:username>/', views.player_stats, name='arena_player_stats'),
    
    # Challenge System
    path('challenge/create/', views.create_challenge, name='arena_create_challenge'),
    path('challenge/respond/', views.respond_to_challenge, name='arena_respond_challenge'),
    
    # Game Interface
    path('game/<str:game_id>/', views.game_interface, name='arena_game'),
    path('game/move/', views.make_move, name='arena_make_move'),
    path('game/ability/', views.use_ability, name='arena_use_ability'),
    
    # Tournament System
    path('tournaments/', views.tournament_list, name='arena_tournaments'),
    path('tournaments/my/', views.my_tournaments, name='arena_my_tournaments'),
    path('tournament/<int:tournament_id>/', views.tournament_detail, name='tournament_detail'),
    path('tournament/<int:tournament_id>/join/', views.join_tournament, name='arena_join_tournament'),
    path('tournament/create/', views.create_tournament, name='arena_create_tournament'),  # Staff only

    path('practice/', views.practice_lobby, name='arena_practice'),
    path('practice/start/', views.start_practice_game, name='arena_start_practice'),
    path('practice/ai-move/', views.ai_make_move, name='arena_ai_move'),
]