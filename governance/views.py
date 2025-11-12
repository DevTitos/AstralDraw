from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db import transaction
from django.core.cache import cache
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
import json
import logging
from .models import GovernanceNFT, GovernanceTopic, GovernanceProposal, Vote, NFTMarketplace
from hiero.governance import submit_message, mint_nft, associate_nft
from core.models import UserWallet
from hiero.ft import fund_pool
from hiero.mirror_node import get_balance

logger = logging.getLogger(__name__)

class GovernanceConfig:
    """Configuration constants for governance system"""
    NFT_PRICES = {
        'celestial': 10000,
        'stellar': 1000, 
        'cosmic': 100
    }
    NFT_LIMITS = {
        'celestial': 10,
        'stellar': 1000,
        'cosmic': 10000
    }
    VOTING_POWER = {
        'celestial': 10,
        'stellar': 2,
        'cosmic': 1
    }
    VOTING_DURATION_DAYS = 7
    MIN_PROPOSAL_TITLE_LENGTH = 5
    MAX_PROPOSAL_TITLE_LENGTH = 200
    MIN_PROPOSAL_DESC_LENGTH = 10
    MAX_PROPOSAL_DESC_LENGTH = 2000
    RATE_LIMITS = {
        'create_proposal': {'limit': 3, 'timeout': 3600},  # 3 per hour
        'cast_vote': {'limit': 10, 'timeout': 300},       # 10 per 5 minutes
        'purchase_nft': {'limit': 5, 'timeout': 3600},    # 5 per hour
    }

def rate_limit_check(user_id, action):
    """Check if user has exceeded rate limits for an action"""
    limit_config = GovernanceConfig.RATE_LIMITS.get(action, {'limit': 5, 'timeout': 300})
    key = f"rate_limit:{action}:{user_id}"
    count = cache.get(key, 0)
    
    if count >= limit_config['limit']:
        return True
    cache.set(key, count + 1, limit_config['timeout'])
    return False

def validate_proposal_data(data):
    """Validate proposal creation data"""
    required_fields = ['topic_id', 'title', 'description']
    for field in required_fields:
        if not data.get(field):
            raise ValueError(f"Missing required field: {field}")
    
    title = data['title'].strip()
    description = data['description'].strip()
    
    if len(title) < GovernanceConfig.MIN_PROPOSAL_TITLE_LENGTH:
        raise ValueError(f"Title must be at least {GovernanceConfig.MIN_PROPOSAL_TITLE_LENGTH} characters")
    
    if len(title) > GovernanceConfig.MAX_PROPOSAL_TITLE_LENGTH:
        raise ValueError(f"Title cannot exceed {GovernanceConfig.MAX_PROPOSAL_TITLE_LENGTH} characters")
    
    if len(description) < GovernanceConfig.MIN_PROPOSAL_DESC_LENGTH:
        raise ValueError(f"Description must be at least {GovernanceConfig.MIN_PROPOSAL_DESC_LENGTH} characters")
    
    if len(description) > GovernanceConfig.MAX_PROPOSAL_DESC_LENGTH:
        raise ValueError(f"Description cannot exceed {GovernanceConfig.MAX_PROPOSAL_DESC_LENGTH} characters")
    
    return {
        'topic_id': data['topic_id'],
        'title': title,
        'description': description
    }

def validate_vote_data(data):
    """Validate vote data"""
    if not data.get('vote'):
        raise ValueError("Missing vote choice")
    
    vote_choice = data['vote'].lower()
    if vote_choice not in ['yes', 'no']:
        raise ValueError("Vote must be 'yes' or 'no'")
    
    return vote_choice

def get_user_wallet(user):
    """Get user's wallet or return error response"""
    try:
        return UserWallet.objects.get(user=user)
    except UserWallet.DoesNotExist:
        logger.warning(f"User {user.id} attempted action without wallet")
        return None

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def create_proposal(request):
    """Create a new governance proposal"""
    try:
        # Rate limiting check
        if rate_limit_check(request.user.id, 'create_proposal'):
            return JsonResponse({
                'success': False,
                'error': 'Rate limit exceeded. Please wait before creating another proposal.'
            }, status=429)
        
        data = json.loads(request.body)
        validated_data = validate_proposal_data(data)
        
        # Check if user has governance NFT
        user_nft = GovernanceNFT.objects.filter(user=request.user, is_active=True).first()
        if not user_nft:
            logger.warning(f"User {request.user.id} attempted to create proposal without NFT")
            return JsonResponse({
                'success': False,
                'error': 'Governance NFT required to create proposals'
            }, status=403)
        
        # Get topic
        topic = get_object_or_404(GovernanceTopic, topic_id=validated_data['topic_id'])
        
        # Create proposal
        with transaction.atomic():
            proposal = GovernanceProposal.objects.create(
                topic=topic,
                creator=request.user,
                title=validated_data['title'],
                description=validated_data['description'],
                voting_start=timezone.now(),
                voting_end=timezone.now() + timezone.timedelta(days=GovernanceConfig.VOTING_DURATION_DAYS)
            )
            
            # Submit to Hedera
            message = f"PROPOSAL:{proposal.id}:{request.user.id}:{validated_data['title']}"
            hedera_result = submit_message(message, topic.topic_id)
            
            if hedera_result['status'] == 'success':
                proposal.hedera_message_id = str(hedera_result['topic'])
                proposal.status = "active"
                proposal.save()
                
                logger.info(f"Proposal {proposal.id} created by user {request.user.id}")
                
                return JsonResponse({
                    'success': True,
                    'proposal_id': proposal.id,
                    'hedera_message_id': proposal.hedera_message_id,
                    'message': 'Proposal created and recorded on Hedera'
                })
            else:
                proposal.delete()
                logger.error(f"Hedera submission failed for proposal by user {request.user.id}: {hedera_result}")
                return JsonResponse({
                    'success': False,
                    'error': 'Failed to record proposal on blockchain'
                }, status=500)
                
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON from user {request.user.id}")
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except ValueError as e:
        logger.warning(f"Validation error for user {request.user.id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
    except Exception as e:
        logger.error(f"Unexpected error in create_proposal for user {request.user.id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def cast_vote(request, proposal_id):
    """Cast a vote on a proposal"""
    try:
        # Rate limiting check
        if rate_limit_check(request.user.id, 'cast_vote'):
            return JsonResponse({
                'success': False,
                'error': 'Rate limit exceeded. Please wait before voting again.'
            }, status=429)
        
        data = json.loads(request.body)
        vote_choice = validate_vote_data(data)
        
        proposal = get_object_or_404(GovernanceProposal, id=proposal_id)
        
        # Check if voting is active
        if proposal.status != 'active':
            return JsonResponse({
                'success': False,
                'error': 'Voting is not active for this proposal'
            }, status=400)
        
        if timezone.now() > proposal.voting_end:
            proposal.status = 'ended'
            proposal.save()
            return JsonResponse({
                'success': False,
                'error': 'Voting period has ended'
            }, status=400)
        
        # Check if user has already voted
        existing_vote = Vote.objects.filter(proposal=proposal, voter=request.user).first()
        if existing_vote:
            return JsonResponse({
                'success': False,
                'error': 'You have already voted on this proposal'
            }, status=400)
        
        # Get user's voting power
        user_nft = GovernanceNFT.objects.filter(user=request.user, is_active=True).first()
        if not user_nft:
            return JsonResponse({
                'success': False,
                'error': 'Governance NFT required to vote'
            }, status=403)
        
        voting_power = user_nft.voting_power
        
        # Create vote
        with transaction.atomic():
            vote = Vote.objects.create(
                proposal=proposal,
                voter=request.user,
                vote=vote_choice,
                voting_power=voting_power
            )
            
            # Submit to Hedera
            message = f"VOTE:{proposal.id}:{request.user.username}:{vote_choice}:{voting_power}"
            hedera_result = submit_message(message, proposal.topic.topic_id)
            
            if hedera_result['status'] == 'success':
                vote.hedera_transaction_id = str(hedera_result['topic'])
                vote.save()
                
                # Update proposal status if needed
                update_proposal_status(proposal)
                
                logger.info(f"Vote cast by user {request.user.id} on proposal {proposal.id}")
                
                return JsonResponse({
                    'success': True,
                    'vote_id': vote.id,
                    'hedera_transaction_id': vote.hedera_transaction_id,
                    'message': 'Vote recorded on blockchain'
                })
            else:
                vote.delete()
                logger.error(f"Hedera submission failed for vote by user {request.user.id}: {hedera_result}")
                return JsonResponse({
                    'success': False,
                    'error': 'Failed to record vote on blockchain'
                }, status=500)
                
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON from user {request.user.id} for voting")
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except ValueError as e:
        logger.warning(f"Validation error in vote from user {request.user.id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
    except Exception as e:
        logger.error(f"Unexpected error in cast_vote for user {request.user.id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
@login_required
@transaction.atomic
def purchase_nft(request, tier):
    """Purchase a governance NFT"""
    try:
        # Rate limiting check
        if rate_limit_check(request.user.id, 'purchase_nft'):
            return JsonResponse({
                'success': False,
                'error': 'Rate limit exceeded. Please wait before purchasing another NFT.'
            }, status=429)
        
        tier = tier.lower()
        price = GovernanceConfig.NFT_PRICES.get(tier)
        if not price:
            return JsonResponse({
                'success': False,
                'error': 'Invalid NFT tier'
            }, status=400)
        
        # Get user wallet
        user_wallet = get_user_wallet(request.user)
        if not user_wallet:
            return JsonResponse({
                'success': False,
                'error': 'Hedera Wallet not initiated, try again later!'
            }, status=400)
        
        # Check balance
        try:
            astra_bal = get_balance(user_wallet.recipient_id)
        except Exception as e:
            logger.error(f"Balance check failed for user {request.user.id}: {str(e)}")
            astra_bal = 0
            
        if astra_bal < price:
            return JsonResponse({
                'success': False,
                'error': f'Insufficient balance. Need {price} ASTRA, have {astra_bal} ASTRA'
            }, status=400)
        
        # Check availability
        existing_count = GovernanceNFT.objects.filter(tier=tier, is_active=True).count()
        max_count = GovernanceConfig.NFT_LIMITS.get(tier, 0)
        
        if existing_count >= max_count:
            return JsonResponse({
                'success': False,
                'error': 'No NFTs available for this tier'
            }, status=400)
        
        # Check if user already has an NFT of this tier
        existing_user_nft = GovernanceNFT.objects.filter(user=request.user, tier=tier, is_active=True).first()
        if existing_user_nft:
            return JsonResponse({
                'success': False,
                'error': f'You already own a {tier} NFT'
            }, status=400)
        
        # Mint NFT on Hedera
        token_ids = {
            'celestial': '0.0.7174407',
            'stellar': '0.0.7174419',
            'cosmic': '0.0.7181084'
        }
        
        token_id = token_ids.get(tier)
        if not token_id:
            return JsonResponse({
                'success': False,
                'error': 'Invalid token configuration'
            }, status=500)
            
        metadata = json.dumps({
            "tier": tier,
            "owner": user_wallet.recipient_id,
            "timestamp": str(timezone.now()),
        })
        print(token_id)
        mint_result = mint_nft(token_id, metadata)
        
        if mint_result['status'] == 'success':
            # Associate NFT with user's wallet
            assc = associate_nft(
                account_id=user_wallet.recipient_id, 
                token_id=token_id, 
                account_private_key=user_wallet.decrypt_key(), 
                nft_id=mint_result['message']
            )
            
            if assc['status'] == 'success':
                # Create NFT record
                nft = GovernanceNFT.objects.create(
                    user=request.user,
                    tier=tier,
                    nft_id=str(mint_result['message']),
                    serial_number=mint_result['serial'],
                    token_id=token_id,
                    voting_power=GovernanceConfig.VOTING_POWER.get(tier, 1)
                )

                # Deduct balance 
                transfer = fund_pool(
                    recipient_id=user_wallet.recipient_id, 
                    amount=price, 
                    account_private_key=user_wallet.decrypt_key()
                )
                
                if transfer['status'] == 'failed':
                    logger.error(f"Balance transfer failed for user {request.user.id}: {transfer}")
                    return JsonResponse({
                        'success': False,
                        'error': f'Payment processing failed: {transfer.get("message", "Unknown error")}'
                    }, status=500)

                logger.info(f"NFT purchased by user {request.user.id}: {tier} tier")
                
                return JsonResponse({
                    'success': True,
                    'nft_id': nft.id,
                    'hedera_nft_id': nft.nft_id,
                    'serial_number': nft.serial_number,
                    'tier': nft.tier,
                    'voting_power': nft.voting_power,
                    'message': f'Successfully purchased {tier} NFT'
                })
            else:
                logger.error(f"NFT association failed for user {request.user.id}: {assc}")
                return JsonResponse({
                    'success': False,
                    'error': f'NFT Association failed: {assc.get("message", "Unknown error")}'
                }, status=500)
        else:
            logger.error(f"NFT minting failed for user {request.user.id}: {mint_result}")
            return JsonResponse({
                'success': False,
                'error': f'NFT minting failed: {mint_result.get("message", "Unknown error")}'
            }, status=500)
                
    except Exception as e:
        logger.error(f"Unexpected error in purchase_nft for user {request.user.id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error during NFT purchase'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def list_nft_for_sale(request, nft_id):
    """List an NFT for sale on marketplace"""
    try:
        data = json.loads(request.body)
        price = data.get('price')
        
        if not price or price <= 0:
            return JsonResponse({
                'success': False,
                'error': 'Valid price is required'
            }, status=400)
        
        nft = get_object_or_404(GovernanceNFT, id=nft_id, user=request.user, is_active=True)
        
        # Check if already listed
        existing_listing = NFTMarketplace.objects.filter(nft=nft, is_sold=False).exists()
        if existing_listing:
            return JsonResponse({
                'success': False,
                'error': 'NFT is already listed for sale'
            }, status=400)
        
        # Create marketplace listing
        listing = NFTMarketplace.objects.create(
            nft=nft,
            seller=request.user,
            price=price
        )
        
        logger.info(f"NFT {nft_id} listed for sale by user {request.user.id} at price {price}")
        
        return JsonResponse({
            'success': True,
            'listing_id': listing.id,
            'price': listing.price,
            'listed_at': listing.created_at,
            'message': 'NFT listed for sale successfully'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f"Error listing NFT {nft_id} by user {request.user.id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to list NFT for sale'
        }, status=500)

@require_http_methods(["GET"])
@login_required
def get_proposal_results(request, proposal_id):
    """Get voting results for a proposal"""
    try:
        proposal = get_object_or_404(GovernanceProposal, id=proposal_id)
        
        votes = Vote.objects.filter(proposal=proposal)
        total_votes = sum(vote.voting_power for vote in votes)
        
        yes_votes = sum(vote.voting_power for vote in votes if vote.vote == 'yes')
        no_votes = sum(vote.voting_power for vote in votes if vote.vote == 'no')
        abstain_votes = sum(vote.voting_power for vote in votes if vote.vote == 'abstain')
        
        yes_percentage = (yes_votes / total_votes * 100) if total_votes > 0 else 0
        no_percentage = (no_votes / total_votes * 100) if total_votes > 0 else 0
        abstain_percentage = (abstain_votes / total_votes * 100) if total_votes > 0 else 0
        
        return JsonResponse({
            'proposal_id': proposal.id,
            'title': proposal.title,
            'status': proposal.status,
            'total_votes': total_votes,
            'yes_votes': yes_votes,
            'no_votes': no_votes,
            'abstain_votes': abstain_votes,
            'yes_percentage': round(yes_percentage, 2),
            'no_percentage': round(no_percentage, 2),
            'abstain_percentage': round(abstain_percentage, 2),
            'approval_threshold': proposal.min_approval_percentage,
            'is_passed': yes_percentage >= proposal.min_approval_percentage,
            'voting_end': proposal.voting_end,
            'unique_voters': votes.values('voter').distinct().count()
        })
        
    except Exception as e:
        logger.error(f"Error getting results for proposal {proposal_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to get proposal results'
        }, status=500)

@require_http_methods(["GET"])
@login_required
def get_user_nfts(request):
    """Get user's governance NFTs"""
    try:
        nfts = GovernanceNFT.objects.filter(user=request.user, is_active=True)
        nft_data = []
        for nft in nfts:
            nft_data.append({
                'id': nft.id,
                'tier': nft.tier,
                'nft_id': nft.nft_id,
                'token_id': nft.token_id,
                'serial_number': nft.serial_number,
                'voting_power': nft.voting_power,
                'purchase_date': nft.acquired_date,
                'is_active': nft.is_active
            })
        
        return JsonResponse({
            'success': True,
            'nfts': nft_data,
            'total_nfts': len(nft_data)
        })
        
    except Exception as e:
        logger.error(f"Error getting NFTs for user {request.user.id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to get user NFTs'
        }, status=500)

@require_http_methods(["GET"])
@login_required
def get_active_proposals(request):
    """Get all active proposals"""
    try:
        proposals = GovernanceProposal.objects.filter(status='active').select_related('creator', 'topic')
        proposal_data = []
        for proposal in proposals:
            # Check if user has voted on this proposal
            user_vote = Vote.objects.filter(proposal=proposal, voter=request.user).first()
            
            proposal_data.append({
                'id': proposal.id,
                'title': proposal.title,
                'description': proposal.description,
                'creator': {
                    'id': proposal.creator.id,
                    'username': proposal.creator.username
                },
                'topic': {
                    'id': proposal.topic.id,
                    'name': proposal.topic.name,
                    'topic_id': proposal.topic.topic_id
                },
                'voting_start': proposal.voting_start,
                'voting_end': proposal.voting_end,
                'min_approval_percentage': proposal.min_approval_percentage,
                'hedera_message_id': proposal.hedera_message_id,
                'created_at': proposal.created_at,
                'has_voted': user_vote is not None,
                'user_vote': user_vote.vote if user_vote else None,
                'total_votes': Vote.objects.filter(proposal=proposal).count()
            })
        
        return JsonResponse({
            'success': True,
            'proposals': proposal_data,
            'total_active': len(proposal_data)
        })
        
    except Exception as e:
        logger.error(f"Error getting active proposals: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to get active proposals'
        }, status=500)

@require_http_methods(["GET"])
@login_required
def get_proposal_detail(request, proposal_id):
    """Get detailed information about a specific proposal"""
    try:
        proposal = get_object_or_404(GovernanceProposal, id=proposal_id)
        user_vote = Vote.objects.filter(proposal=proposal, voter=request.user).first()
        
        proposal_data = {
            'id': proposal.id,
            'title': proposal.title,
            'description': proposal.description,
            'status': proposal.status,
            'creator': {
                'id': proposal.creator.id,
                'username': proposal.creator.username
            },
            'topic': {
                'id': proposal.topic.id,
                'name': proposal.topic.name,
                'topic_id': proposal.topic.topic_id
            },
            'voting_start': proposal.voting_start,
            'voting_end': proposal.voting_end,
            'min_approval_percentage': proposal.min_approval_percentage,
            'hedera_message_id': proposal.hedera_message_id,
            'created_at': proposal.created_date,
            'has_voted': user_vote is not None,
            'user_vote': user_vote.vote if user_vote else None,
            'user_voting_power': user_vote.voting_power if user_vote else 0
        }
        
        return JsonResponse({
            'success': True,
            'proposal': proposal_data
        })
        
    except Exception as e:
        logger.error(f"Error getting proposal {proposal_id} details: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to get proposal details'
        }, status=500)

@require_http_methods(["GET"])
@login_required
def governance_stats(request):
    """Get governance statistics"""
    try:
        total_nfts = GovernanceNFT.objects.filter(is_active=True).count()
        celestial_count = GovernanceNFT.objects.filter(tier='celestial', is_active=True).count()
        stellar_count = GovernanceNFT.objects.filter(tier='stellar', is_active=True).count()
        cosmic_count = GovernanceNFT.objects.filter(tier='cosmic', is_active=True).count()
        
        stats = {
            'success': True,
            'nft_stats': {
                'celestial': {
                    'available': GovernanceConfig.NFT_LIMITS['celestial'] - celestial_count,
                    'total': GovernanceConfig.NFT_LIMITS['celestial'],
                    'sold': celestial_count
                },
                'stellar': {
                    'available': GovernanceConfig.NFT_LIMITS['stellar'] - stellar_count,
                    'total': GovernanceConfig.NFT_LIMITS['stellar'],
                    'sold': stellar_count
                },
                'cosmic': {
                    'available': GovernanceConfig.NFT_LIMITS['cosmic'] - cosmic_count,
                    'total': GovernanceConfig.NFT_LIMITS['cosmic'],
                    'sold': cosmic_count
                }
            },
            'proposal_stats': {
                'active': GovernanceProposal.objects.filter(status='active').count(),
                'passed': GovernanceProposal.objects.filter(status='passed').count(),
                'rejected': GovernanceProposal.objects.filter(status='rejected').count(),
                'total': GovernanceProposal.objects.count()
            },
            'voting_stats': {
                'total_votes': Vote.objects.count(),
                'total_voters': Vote.objects.values('voter').distinct().count(),
                'total_voting_power': sum(vote.voting_power for vote in Vote.objects.all())
            },
            'user_stats': {
                'has_nft': GovernanceNFT.objects.filter(user=request.user, is_active=True).exists(),
                'user_votes': Vote.objects.filter(voter=request.user).count(),
                'user_voting_power': sum(nft.voting_power for nft in GovernanceNFT.objects.filter(user=request.user, is_active=True))
            }
        }
        
        return JsonResponse(stats)
        
    except Exception as e:
        logger.error(f"Error getting governance stats: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to get governance statistics'
        }, status=500)

def update_proposal_status(proposal):
    """Update proposal status based on voting results"""
    try:
        votes = Vote.objects.filter(proposal=proposal)
        total_votes = sum(vote.voting_power for vote in votes)
        
        if total_votes > 0:
            yes_votes = sum(vote.voting_power for vote in votes if vote.vote == 'yes')
            yes_percentage = (yes_votes / total_votes * 100)
            
            if yes_percentage >= proposal.min_approval_percentage:
                proposal.status = 'passed'
            else:
                proposal.status = 'rejected'
            
            proposal.save()
            logger.info(f"Proposal {proposal.id} status updated to {proposal.status}")
            
    except Exception as e:
        logger.error(f"Error updating status for proposal {proposal.id}: {str(e)}")


# views.py - Add these functions

@require_http_methods(["GET"])
@login_required
def get_active_proposals(request):
    """Get all active proposals for the dashboard"""
    try:
        proposals = GovernanceProposal.objects.filter(status='active').select_related('creator', 'topic')
        proposal_data = []
        
        for proposal in proposals:
            # Get vote counts
            votes = Vote.objects.filter(proposal=proposal)
            total_votes = sum(vote.voting_power for vote in votes)
            yes_votes = sum(vote.voting_power for vote in votes if vote.vote == 'yes')
            yes_percentage = (yes_votes / total_votes * 100) if total_votes > 0 else 0
            
            # Check if user has voted
            user_vote = Vote.objects.filter(proposal=proposal, voter=request.user).first()
            
            proposal_data.append({
                'id': proposal.id,
                'title': proposal.title,
                'description': proposal.description,
                'status': proposal.status,
                'voting_start': proposal.voting_start,
                'voting_end': proposal.voting_end,
                'min_approval_percentage': proposal.min_approval_percentage,
                'creator': {
                    'id': proposal.creator.id,
                    'username': proposal.creator.username
                },
                'topic': {
                    'id': proposal.topic.id,
                    'name': proposal.topic.name,
                    'topic_id': proposal.topic.topic_id
                },
                'total_votes': total_votes,
                'yes_percentage': round(yes_percentage, 2),
                'has_voted': user_vote is not None,
                'user_vote': user_vote.vote if user_vote else None,
                'is_urgent': timezone.now() > proposal.voting_end - timezone.timedelta(hours=24)
            })
        
        return JsonResponse({
            'success': True,
            'proposals': proposal_data
        })
        
    except Exception as e:
        logger.error(f"Error getting active proposals: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to load proposals'
        }, status=500)

@require_http_methods(["GET"])
@login_required
def get_user_nfts(request):
    """Get user's governance NFTs"""
    try:
        nfts = GovernanceNFT.objects.filter(user=request.user, is_active=True)
        nft_data = []
        for nft in nfts:
            nft_data.append({
                'id': nft.id,
                'tier': nft.tier,
                'nft_id': nft.nft_id,
                'token_id': nft.token_id,
                'serial_number': nft.serial_number,
                'voting_power': nft.voting_power,
                'purchase_date': nft.acquired_date,
                'is_active': nft.is_active
            })
        
        return JsonResponse({
            'success': True,
            'nfts': nft_data
        })
        
    except Exception as e:
        logger.error(f"Error getting user NFTs: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to get user NFTs'
        }, status=500)

@require_http_methods(["GET"])
@login_required
def get_user_activity(request):
    """Get user's voting activity"""
    try:
        votes = Vote.objects.filter(voter=request.user).select_related('proposal', 'proposal__topic')
        vote_data = []
        
        for vote in votes:
            # Calculate proposal result
            proposal_votes = Vote.objects.filter(proposal=vote.proposal)
            total_votes = sum(v.voting_power for v in proposal_votes)
            yes_votes = sum(v.voting_power for v in proposal_votes if v.vote == 'yes')
            yes_percentage = (yes_votes / total_votes * 100) if total_votes > 0 else 0
            passed = yes_percentage >= vote.proposal.min_approval_percentage
            
            vote_data.append({
                'id': vote.id,
                'proposal_id': vote.proposal.id,
                'proposal_title': vote.proposal.title,
                'topic_name': vote.proposal.topic.name,
                'vote': vote.vote,
                'voting_power': vote.voting_power,
                'voted_at': vote.voted_at,
                'proposal_passed': passed
            })
        
        return JsonResponse({
            'success': True,
            'votes': vote_data
        })
        
    except Exception as e:
        logger.error(f"Error getting user activity: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to get user activity'
        }, status=500)

@require_http_methods(["GET"])
@login_required
def get_available_nfts(request):
    """Get available NFTs for purchase"""
    try:
        # NFT configuration
        nft_config = {
            'celestial': {
                'name': 'Celestial Board NFT',
                'price': 10000,
                'voting_power': 10,
                'max_supply': 10,
                'token_id': '0.0.7174407'
            },
            'stellar': {
                'name': 'Stellar Assembly NFT', 
                'price': 1000,
                'voting_power': 2,
                'max_supply': 1000,
                'token_id': '0.0.7174419'
            },
            'cosmic': {
                'name': 'Cosmic Community NFT',
                'price': 100,
                'voting_power': 1,
                'max_supply': 10000,
                'token_id': '0.0.7174420'
            }
        }
        
        available_nfts = []
        
        for tier, config in nft_config.items():
            # Count existing NFTs of this tier
            existing_count = GovernanceNFT.objects.filter(tier=tier, is_active=True).count()
            available = config['max_supply'] - existing_count
            
            # Check if user already owns this tier
            user_owns = GovernanceNFT.objects.filter(user=request.user, tier=tier, is_active=True).exists()
            
            available_nfts.append({
                'tier': tier,
                'name': config['name'],
                'price': config['price'],
                'voting_power': config['voting_power'],
                'max_supply': config['max_supply'],
                'available': available,
                'token_id': config['token_id'],
                'user_owns': user_owns,
                'can_purchase': available > 0 and not user_owns
            })
        
        return JsonResponse({
            'success': True,
            'nfts': available_nfts
        })
        
    except Exception as e:
        logger.error(f"Error getting available NFTs: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to get available NFTs'
        }, status=500)