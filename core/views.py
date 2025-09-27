from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Sum, Count, Q
from django.core.cache import cache
from django.views.decorators.cache import cache_page
from django.db import transaction  # Fixed import
import json
import string
import random
import logging

from core.models import UserWallet, Draw, ForgedKey, Alert
from hiero.utils import create_new_account
from hiero.ft import associate_token
from hiero.nft import create_nft, mint_nft, associate_nft, transfer_nft
from hiero.hcs import submit_message

logger = logging.getLogger(__name__)

# Cache timeouts (in seconds)
CACHE_TIMEOUT_SHORT = 300  # 5 minutes
CACHE_TIMEOUT_LONG = 1800  # 30 minutes

def id_generator(size=8, chars=string.ascii_uppercase + string.digits):
    """Optimized random string generator"""
    return ''.join(random.choices(chars, k=size))

def assign_user_wallet(name):
    """Optimized wallet assignment with better error handling"""
    try:
        recipient_id, recipient_private_key, new_account_public_key = create_new_account(name)
        associate_token(recipient_id, recipient_private_key)
        
        return {
            'status': 'success',
            'new_account_public_key': new_account_public_key,
            'recipient_private_key': recipient_private_key,
            'recipient_id': recipient_id
        }
    except Exception as e:
        logger.error(f"Wallet assignment error: {e}")
        return {'status': 'failed', 'error': str(e)}

@require_http_methods(["GET", "POST"])
def register_view(request):
    """Optimized registration view with bulk operations"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == "POST":
        # Use dictionary for faster field access
        post_data = request.POST
        required_fields = ['email', 'first_name', 'last_name', 'password', 'password1']
        
        # Fast field validation
        if not all(post_data.get(field) for field in required_fields):
            messages.warning(request, "All fields are required")
            return redirect('register')
        
        if post_data['password'] != post_data['password1']:
            messages.warning(request, "Password does not match")
            return redirect('register')
        
        email = post_data['email'].lower().strip()  # Normalize email
        
        # Cache user existence check
        cache_key = f"user_exists_{email}"
        if cache.get(cache_key) or User.objects.filter(email=email).exists():
            cache.set(cache_key, True, 300)
            messages.warning(request, "User with this email already exists")
            return redirect('register')
        
        try:
            # Create wallet first (more expensive operation)
            wallet_response = assign_user_wallet(name=f"{post_data['first_name']} {post_data['last_name']}")
            
            if wallet_response['status'] != 'success':
                messages.warning(request, "Wallet creation failed")
                return redirect('register')
            
            # Bulk create user and wallet
            with transaction.atomic():  # Fixed transaction import
                user = User.objects.create_user(
                    username=email,  # Use email as username for faster lookup
                    email=email,
                    first_name=post_data['first_name'],
                    last_name=post_data['last_name'],
                    password=post_data['password']
                )
                
                UserWallet.objects.create(
                    user=user,
                    public_key=wallet_response['new_account_public_key'],
                    private_key=wallet_response['recipient_private_key'],
                    recipient_id=wallet_response['recipient_id']
                )
            
            # Cache the new user
            cache.set(cache_key, True, 300)
            messages.success(request, "Account created successfully")
            return redirect('login')
            
        except Exception as e:
            logger.error(f"Registration error: {e}")
            messages.warning(request, "Registration failed")
            return redirect('register')
    
    return render(request, 'accounts/register.html')

@require_http_methods(["GET", "POST"])
def login_view(request):
    """Optimized login with caching"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        email = request.POST.get('email', '').lower().strip()
        password = request.POST.get('password', '')
        
        if not email or not password:
            messages.warning(request, "All fields are required")
            return redirect('login')
        
        # Cache failed login attempts
        fail_key = f"login_fail_{email}"
        fail_count = cache.get(fail_key, 0)
        
        if fail_count >= 5:
            messages.warning(request, "Too many failed attempts. Try again later.")
            return redirect('login')
        
        # Authenticate using username (which is email)
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            # Prefetch related data in one query
            wallet = UserWallet.objects.only('id').filter(user=user).first()
            if not wallet:
                messages.warning(request, "Wallet not found")
                return redirect('login')
            
            login(request, user)
            cache.delete(fail_key)  # Clear fail counter
            
            # Cache user session data
            cache.set(f"user_{user.id}_wallet", wallet.id, 3600)
            messages.success(request, f"Welcome back, {user.first_name}!")
            return redirect('dashboard')
        else:
            cache.set(fail_key, fail_count + 1, 900)  # 15 minute timeout
            messages.warning(request, "Invalid credentials")
            return redirect('login')
    
    return render(request, 'accounts/auth.html')

def logout_view(request):
    """Optimized logout with cache cleanup"""
    user_id = request.user.id
    logout(request)
    # Cleanup user-specific cache
    cache.delete_many([f"user_{user_id}_wallet", f"user_{user_id}_keys"])
    return redirect("login")

@cache_page(300)  # Cache for 5 minutes
def landing(request):
    """Optimized landing page with selective field loading"""
    cache_key = "landing_page_data"
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return render(request, 'landing.html', cached_data)
    
    # Use only() to load only necessary fields
    active_draws = Draw.objects.filter(
        status__in=[Draw.DrawStatus.UPCOMING, Draw.DrawStatus.ACTIVE]
    ).only('id', 'title', 'prize_pool', 'draw_datetime').order_by('draw_datetime')[:3]
    
    recent_winners = Draw.objects.filter(
        status=Draw.DrawStatus.ENDED,
        winner_wallet__isnull=False
    ).select_related('winner_wallet__user').only(
        'title', 'prize_pool', 'draw_datetime', 'winner_wallet__user__first_name'
    )[:5]
    
    # Use aggregate with specific fields
    stats = Draw.objects.aggregate(
        total_draws=Count('id'),
        total_prizes=Sum('prize_pool')
    )
    stats['active_players'] = UserWallet.objects.count()
    
    context = {
        'active_draws': active_draws,
        'recent_winners': recent_winners,
        'stats': stats,
    }
    
    cache.set(cache_key, context, 300)
    return render(request, 'landing.html', context)

@login_required
def dashboard(request):
    """Optimized dashboard with efficient queries"""
    user_id = request.user.id
    cache_key = f"dashboard_{user_id}"
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return render(request, 'dash.html', cached_data)
    
    # Get or create wallet efficiently
    user_wallet = UserWallet.objects.get(
        user_id=user_id,
    )
    cosmic_users = UserWallet.objects.all().count()
    keys_forged = ForgedKey.objects.all().count()
    # User's active keys with efficient query
    user_keys = ForgedKey.objects.filter(
        user_wallet=user_wallet
    ).select_related('draw').only(
        'id', 'serial_number', 'created_at', 'draw__title', 'draw__status'
    ).order_by('-created_at')[:10]
    # Active draws user can participate in
    active_draws = Draw.objects.filter(
        status__in=["upcoming", "active"],
    )[:10]
    total_prizes = Draw.objects.get(status='active').prize_pool
    all_draws = Draw.objects.all()
    # User's winning history
    user_wins = Draw.objects.filter(
        winner_wallet=user_wallet
    ).only('title', 'prize_pool', 'draw_datetime').order_by('-draw_datetime')[:5]
    
    context = {
        'user_wallet': user_wallet,
        'user_keys': user_keys,
        'active_draws': active_draws,
        'user_wins': user_wins,
        'next_draw': active_draws.first() if active_draws else None,
        'all_draws':all_draws,
        'cosmic_users':cosmic_users,
        'keys_forged':keys_forged,
        'total_prizes':total_prizes
    }
    
    cache.set(cache_key, context, 120)  # 2 minute cache
    return render(request, 'dash.html', context)

@login_required
@require_http_methods(["POST"])
def submit_keys(request):
    """Optimized key submission with transaction"""
    try:
        draw_id = request.POST['draw_id']
        key_1 = request.POST['key-1']
        key_2 = request.POST['key-2']
        key_3 = request.POST['key-3']
        key_4 = request.POST['key-4']
        key_5 = request.POST['key-5']
        key_6 = request.POST['key-6']
        if not draw_id and key_1 and key_2 and key_3 and key_4 and key_5 and key_6:
            messages.warning(request, "All Fields are required to initiate Draw Key Forging!")
            return redirect(request.META.get('HTTP_REFERER', '/'))
        draw = get_object_or_404(Draw, id=draw_id)
        
        if not draw.is_active():
            messages.warning(request, "Draw Not Active for Key Forging, try again later!")
            return redirect(request.META.get('HTTP_REFERER', '/'))
        
        user_wallet_id = cache.get(f"user_{request.user.id}_wallet")
        user_wallet = get_object_or_404(UserWallet, user=request.user)
        if not user_wallet_id:
            user_wallet_id = user_wallet.id
            cache.set(f"user_{request.user.id}_wallet", user_wallet_id, 3600)
        
        # Check existing submission using exists() for speed
        if ForgedKey.objects.filter(user_wallet=user_wallet, draw=draw).exists():
            messages.warning(request, "Keys already submitted for this draw!")
            return redirect(request.META.get('HTTP_REFERER', '/'))
        # Payment Comes here
        # Check user Astra balance using Mirror Node
        star_keys = [key_1, key_2, key_3, key_4, key_5, key_6]
        
        with transaction.atomic():
            user_wallet = get_object_or_404(UserWallet, user=request.user)
            # FOrge NFT TIcket
            ticket_metadata = f"title:{draw.title} Convergence - Keys: {star_keys} - User :{user_wallet_id}"
            print(draw.nft_id)
            nft_ = mint_nft(nft_token_id=draw.nft_id, metadata=ticket_metadata)
            if nft_['status'] == 'success':
                assc=associate_nft(account_id=user_wallet.recipient_id, token_id=draw.nft_id, account_private_key=user_wallet.decrypt_key(), nft_id=nft_['message'])
                if assc['status'] == 'success':
                    # Create forged key
                    serial_number = f"AK{draw_id:04d}{user_wallet_id:04d}{nft_['serial']}"
                    forged_key = ForgedKey.objects.create(
                        user_wallet=user_wallet,
                        draw=draw,
                        serial_number=serial_number,
                        star_keys=str(star_keys),
                    )
                    draw.total_tickets_sold += 1
                    draw.save()
                    # CReate HCS Message for immutability
                    submit_message(message=ticket_metadata)
            else:
                messages.warning(request, f"Forging Failed: {nft_['message']}")
                return redirect(request.META.get('HTTP_REFERER', '/'))
        
        # Invalidate relevant caches
        cache.delete_many([f"dashboard_{request.user.id}", f"user_{request.user.id}_keys"])
        
        messages.success(request, "Keys submitted successfully!")
        return redirect(request.META.get('HTTP_REFERER', '/'))
        
    except Exception as e:
        messages.warning(request, f"An Error Occured while Forging your star keys, please try again later: {e}")
        return redirect(request.META.get('HTTP_REFERER', '/'))

@login_required
@require_http_methods(["POST"])
def create_draw(request):
    """Admin view to create new draws"""
    if not request.user.is_staff:
        messages.warning(request, "admin access required!")
        return redirect(request.META.get('HTTP_REFERER', '/'))
    
    try:
        
        title = request.POST['title']
        symbol = request.POST['symbol']
        status = request.POST['status']
        prize_pool = request.POST['prize_pool']
        draw_datetime = request.POST['draw_datetime']
        
        # Validate required fields
        if not title and  symbol and status and prize_pool and draw_datetime:
            messages.warning(request, "All Field are required!")
            return redirect(request.META.get('HTTP_REFERER', '/'))
        
        # Generate winning star keys (6 random numbers 0-9)
        #winning_keys = [random.randint(0, 9) for _ in range(6)]
        # CREATE ASTRAL NFT DRAW
        draw_nft = create_nft(title=title, symbol=symbol)
        if draw_nft['status'] == 'failed':
            messages.warning(request, "Draw creation failed, NFT creation was not successful")
            return redirect(request.META.get('HTTP_REFERER', '/'))
        else:
            draw = Draw.objects.create(
                title=title,
                prize_pool=prize_pool,
                draw_datetime=draw_datetime,
                status=status,
                nft_id=draw_nft['token_id']
            )
            Alert.objects.create(title="New Convergence Launched", content=f"{title} Convergence is now active with {prize_pool} ASTRA prize pool", icon='rocket')
        
        # Clear relevant caches
        cache.delete_many(["platform_stats", "landing_page_data"])
        messages.success(request, f"{draw.title} Convergence Draw created successfully")
        return redirect(request.META.get('HTTP_REFERER', '/'))
        
    except Exception as e:
        messages.warning(request, f"An error occured: {e}")
        return redirect(request.META.get('HTTP_REFERER', '/'))

# Optimized API views with selective field loading
@login_required
def draw_detail(request, draw_id):
    """Optimized draw detail with field selection"""
    draw = get_object_or_404(Draw.objects.only(
        'id', 'title', 'status', 'prize_pool', 'draw_datetime', 'total_tickets_sold', 'winner_wallet_id', 'winning_ticket_serial'
    ), id=draw_id)
    
    
    draw_data = {
        'id': draw.id,
        'title': draw.title,
        'status': draw.status,
        'prize_pool': float(draw.prize_pool),
        'draw_datetime': draw.draw_datetime,
        'total_tickets_sold': draw.total_tickets_sold,
        'can_participate': draw.can_participate(),
    }
    
    if draw.status == Draw.DrawStatus.ENDED:
        draw_data['winning_keys'] = draw.get_star_keys()
        if draw.winner_wallet_id:
            # Efficiently get winner username
            winner_username = User.objects.filter(
                userwallet__id=draw.winner_wallet_id
            ).values_list('username', flat=True).first()
            draw_data['winner'] = {
                'username': winner_username,
                'ticket_serial': draw.winning_ticket_serial
            }
    
    return JsonResponse({'draw': draw_data})

@login_required
def user_keys(request):
    """Optimized user keys with efficient query"""
    cache_key = f"user_{request.user.id}_keys"
    cached_keys = cache.get(cache_key)
    
    if cached_keys:
        return JsonResponse({'keys': cached_keys})
    
    user_wallet = get_object_or_404(UserWallet, user=request.user)
    keys = ForgedKey.objects.filter(
        user_wallet=user_wallet
    ).select_related('draw').only(
        'id', 'serial_number', 'created_at', 'nft_metadata',
        'draw__title', 'draw__status'
    ).order_by('-created_at')[:50]  # Limit results
    
    keys_data = []
    for key in keys:
        keys_data.append({
            'id': key.id,
            'serial_number': key.serial_number,
            'draw_title': key.draw.title,
            'draw_status': key.draw.status,
            'created_at': key.created_at,
            'is_winner': key.is_winner(),
            'match_count': key.get_match_count() if key.draw.status == Draw.DrawStatus.ENDED else None,
        })
    
    cache.set(cache_key, keys_data, 300)
    return JsonResponse({'keys': keys_data})

@cache_page(600)  # Cache for 10 minutes
def platform_stats(request):
    """Optimized platform stats with caching"""
    cache_key = "platform_stats"
    cached_stats = cache.get(cache_key)
    
    if cached_stats:
        return JsonResponse(cached_stats)
    
    # Single query for all stats
    stats = {
        'total_draws': Draw.objects.count(),
        'active_draws': Draw.objects.filter(
            status__in=[Draw.DrawStatus.UPCOMING, Draw.DrawStatus.ACTIVE]
        ).count(),
        'total_prizes': float(Draw.objects.aggregate(Sum('prize_pool'))['prize_pool__sum'] or 0),
        'total_players': UserWallet.objects.count(),
        'keys_forged': ForgedKey.objects.count(),
    }
    
    # Recent winners with efficient query
    recent_winners = list(Draw.objects.filter(
        status=Draw.DrawStatus.ENDED,
        winner_wallet__isnull=False
    ).select_related('winner_wallet__user').values(
        'title', 'prize_pool', 'draw_datetime', 'winner_wallet__user__username'
    )[:5])
    
    result = {'stats': stats, 'recent_winners': recent_winners}
    cache.set(cache_key, result, 600)
    return JsonResponse(result)

# Batch processing optimization for admin functions
@login_required
@require_http_methods(["POST"])
def process_draw(request, draw_id):
    """Optimized draw processing with bulk operations"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Admin access required'})
    
    try:
        draw = get_object_or_404(Draw, id=draw_id)
        
        if draw.status != Draw.DrawStatus.ACTIVE or draw.draw_datetime > timezone.now():
            return JsonResponse({'success': False, 'error': 'Draw cannot be processed'})
        
        # Find winner
        winner = draw.map_winner()
        
        with transaction.atomic():
            if winner:
                prize_amount = draw.prize_pool * 0.7
                # Update draw in single query
                Draw.objects.filter(id=draw_id).update(
                    total_prize_distributed=prize_amount,
                    status=Draw.DrawStatus.ENDED,
                    winner_wallet=winner.user_wallet,
                    winning_ticket_serial=winner.serial_number
                )
            else:
                Draw.objects.filter(id=draw_id).update(status=Draw.DrawStatus.ENDED)
        
        # Clear relevant caches
        cache.delete_many(["platform_stats", "landing_page_data"])
        
        return JsonResponse({
            'success': True,
            'winner': {
                'username': winner.user_wallet.user.username,
                'serial_number': winner.serial_number,
                'prize_amount': float(prize_amount)
            } if winner else None,
            'message': 'Draw processed successfully'
        })
        
    except Exception as e:
        logger.error(f"Draw processing error: {e}")
        return JsonResponse({'success': False, 'error': str(e)})
    
def faqs(request):
    return render(request, 'faqs.html')