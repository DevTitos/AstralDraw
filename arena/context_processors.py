from arena.models import Challenge, ArenaPlayer

def arena_context(request):
    if request.user.is_authenticated:
        try:
            arena_profile = request.user.arena_profile
            pending_challenges = Challenge.objects.filter(
                opponent=request.user,
                status='pending'
            ).count()
            return {
                'arena_profile': arena_profile,
                'pending_challenges_count': pending_challenges,
            }
        except ArenaPlayer.DoesNotExist:
            pass
    return {}