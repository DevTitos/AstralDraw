from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json
from .models import GovernanceNFT, GovernanceTopic, GovernanceProposal, Vote, NFTMarketplace
from hiero.governance import submit_message, mint_nft, associate_nft
from core.models import UserWallet
from hiero.ft import fund_pool
from hiero.mirror_node import get_balance

@csrf_exempt
@login_required
def create_proposal(request):
    """Create a new governance proposal"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            topic_id = data.get('topic_id')
            title = data.get('title')
            description = data.get('description')
            
            # Check if user has governance NFT
            user_nft = GovernanceNFT.objects.filter(user=request.user, is_active=True).first()
            if not user_nft:
                return JsonResponse({
                    'success': False,
                    'error': 'Governance NFT required to create proposals'
                })
            
            # Get topic
            topic = get_object_or_404(GovernanceTopic, topic_id=topic_id)
            
            # Create proposal
            proposal = GovernanceProposal.objects.create(
                topic=topic,
                creator=request.user,
                title=title,
                description=description,
                voting_start=timezone.now(),
                voting_end=timezone.now() + timezone.timedelta(days=7)
            )
            
            # Submit to Hedera
            message = f"PROPOSAL:{proposal.id}:{request.user.username}:{title}"
            hedera_result = submit_message(message, topic_id)
            
            if hedera_result['status'] == 'success':
                proposal.hedera_message_id = str(hedera_result['topic'])
                proposal.save()
                
                return JsonResponse({
                    'success': True,
                    'proposal_id': proposal.id,
                    'message': 'Proposal created and recorded on Hedera'
                })
            else:
                proposal.delete()
                return JsonResponse({
                    'success': False,
                    'error': 'Failed to record proposal on blockchain'
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })

@csrf_exempt
@login_required
def cast_vote(request, proposal_id):
    """Cast a vote on a proposal"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            vote_choice = data.get('vote')
            
            proposal = get_object_or_404(GovernanceProposal, id=proposal_id)
            
            # Check if voting is active
            if proposal.status != 'active':
                return JsonResponse({
                    'success': False,
                    'error': 'Voting is not active for this proposal'
                })
            
            if timezone.now() > proposal.voting_end:
                return JsonResponse({
                    'success': False,
                    'error': 'Voting period has ended'
                })
            
            # Check if user has already voted
            existing_vote = Vote.objects.filter(proposal=proposal, voter=request.user).first()
            if existing_vote:
                return JsonResponse({
                    'success': False,
                    'error': 'You have already voted on this proposal'
                })
            
            # Get user's voting power
            user_nft = GovernanceNFT.objects.filter(user=request.user, is_active=True).first()
            voting_power = user_nft.voting_power if user_nft else 1
            
            # Create vote
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
                
                return JsonResponse({
                    'success': True,
                    'message': 'Vote recorded on blockchain'
                })
            else:
                vote.delete()
                return JsonResponse({
                    'success': False,
                    'error': 'Failed to record vote on blockchain'
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })

@csrf_exempt
@login_required
def purchase_nft(request, tier):
    """Purchase a governance NFT"""
    if request.method == 'POST':
        try:
            # NFT prices
            nft_prices = {
                'celestial': 10000,
                'stellar': 1000,
                'cosmic': 100
            }
            
            price = nft_prices.get(tier)
            if not price:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid NFT tier'
                })
            
            try:
                astra_bal = get_balance(user_wallet.recipient_id)
            except Exception as e:
                astra_bal = 0
            if astra_bal < 100:
                return JsonResponse({
                    'success': False,
                    'error': f'Insufficient balance. Need {price} ASTRA, have {astra_bal} ASTRA'
                })
            # Check availability
            existing_count = GovernanceNFT.objects.filter(tier=tier, is_active=True).count()
            max_counts = {
                'celestial': 10,
                'stellar': 1000,
                'cosmic': 10000
            }
            
            if existing_count >= max_counts.get(tier, 0):
                return JsonResponse({
                    'success': False,
                    'error': 'No NFTs available for this tier'
                })
            
            # Mint NFT on Hedera
            token_ids = {
                'celestial': '0.0.7174407',
                'stellar': '0.0.7174419',
                'cosmic': '0.0.7174420'
            }
            try:
                user_wallet = UserWallet.objects.get(user=request.user)
            except UserWallet.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'Hedera Wallet not initiated, try again later!'
                })
            
            token_id = token_ids.get(tier)
            metadata = json.dumps({
                "tier": tier,
                "owner": user_wallet.recipient_id,
                "timestamp": str(timezone.now()),
                "voting_power": 10 if tier == 'celestial' else (2 if tier == 'stellar' else 1)
            })
            
            mint_result = mint_nft(token_id, metadata)
            
            if mint_result['status'] == 'success':
                # Create NFT record
                nft = GovernanceNFT.objects.create(
                    user=request.user,
                    tier=tier,
                    nft_id=str(mint_result['message']),
                    serial_number=mint_result['serial'],
                    token_id=token_id,
                    voting_power=10 if tier == 'celestial' else (2 if tier == 'stellar' else 1)
                )
                
                # Deduct balance (you'll need to implement this)
                transfer = fund_pool(recipient_id=user_wallet.recipient_id, amount=100, account_private_key=user_wallet.decrypt_key())
                if transfer['status'] == 'failed':
                    return JsonResponse({
                    'success': False,
                    'error': f'NFT minting failed: {mint_result["message"]}'
                })
                # request.user.astra_balance -= price
                # request.user.save()
                
                return JsonResponse({
                    'success': True,
                    'nft_id': nft.nft_id,
                    'serial_number': nft.serial_number,
                    'message': f'Successfully purchased {tier} NFT'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': f'NFT minting failed: {mint_result["message"]}'
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })

@csrf_exempt
@login_required
def list_nft_for_sale(request, nft_id):
    """List an NFT for sale on marketplace"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            price = data.get('price')
            
            nft = get_object_or_404(GovernanceNFT, id=nft_id, user=request.user, is_active=True)
            
            # Check if already listed
            existing_listing = NFTMarketplace.objects.filter(nft=nft, is_sold=False).exists()
            if existing_listing:
                return JsonResponse({
                    'success': False,
                    'error': 'NFT is already listed for sale'
                })
            
            # Create marketplace listing
            listing = NFTMarketplace.objects.create(
                nft=nft,
                seller=request.user,
                price=price
            )
            
            return JsonResponse({
                'success': True,
                'listing_id': listing.id,
                'message': 'NFT listed for sale successfully'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })

def get_proposal_results(request, proposal_id):
    """Get voting results for a proposal"""
    proposal = get_object_or_404(GovernanceProposal, id=proposal_id)
    
    votes = Vote.objects.filter(proposal=proposal)
    total_votes = sum(vote.voting_power for vote in votes)
    
    yes_votes = sum(vote.voting_power for vote in votes if vote.vote == 'yes')
    no_votes = sum(vote.voting_power for vote in votes if vote.vote == 'no')
    
    yes_percentage = (yes_votes / total_votes * 100) if total_votes > 0 else 0
    no_percentage = (no_votes / total_votes * 100) if total_votes > 0 else 0
    
    return JsonResponse({
        'total_votes': total_votes,
        'yes_votes': yes_votes,
        'no_votes': no_votes,
        'yes_percentage': round(yes_percentage, 2),
        'no_percentage': round(no_percentage, 2),
        'approval_threshold': proposal.min_approval_percentage,
        'is_passed': yes_percentage >= proposal.min_approval_percentage
    })

def update_proposal_status(proposal):
    """Update proposal status based on voting results"""
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

@login_required
def governance_stats(request):
    """Get governance statistics"""
    stats = {
        'board_available': 10 - GovernanceNFT.objects.filter(tier='celestial', is_active=True).count(),
        'board_total': 10,
        'assembly_available': 1000 - GovernanceNFT.objects.filter(tier='stellar', is_active=True).count(),
        'assembly_total': 1000,
        'cosmic_available': 10000 - GovernanceNFT.objects.filter(tier='cosmic', is_active=True).count(),
        'cosmic_total': 10000,
        'active_proposals': GovernanceProposal.objects.filter(status='active').count(),
        'total_proposals': GovernanceProposal.objects.count(),
        'total_votes': Vote.objects.count(),
    }
    
    return JsonResponse(stats)