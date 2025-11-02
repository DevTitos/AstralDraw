from django.urls import path
from . import views

urlpatterns = [
    # Proposal endpoints
    path('api/governance/proposals/create/', views.create_proposal, name='create_proposal'),
    path('api/governance/proposals/active/', views.get_active_proposals, name='active_proposals'),
    path('api/governance/proposals/<int:proposal_id>/', views.get_proposal_detail, name='proposal_detail'),
    path('api/governance/proposals/<int:proposal_id>/vote/', views.cast_vote, name='cast_vote'),
    path('api/governance/proposals/<int:proposal_id>/results/', views.get_proposal_results, name='proposal_results'),
    
    # NFT endpoints
    path('api/governance/nft/purchase/<str:tier>/', views.purchase_nft, name='purchase_nft'),
    path('api/governance/nft/my-nfts/', views.get_user_nfts, name='user_nfts'),
    path('api/governance/nft/<int:nft_id>/list/', views.list_nft_for_sale, name='list_nft'),
    
    # Stats and info endpoints
    path('api/governance/stats/', views.governance_stats, name='governance_stats'),

    # New URLs for the dashboard
    path('api/governance/proposals/active/', views.get_active_proposals, name='active_proposals'),
    path('api/governance/nft/my-nfts/', views.get_user_nfts, name='user_nfts'),
    path('api/governance/user/activity/', views.get_user_activity, name='user_activity'),
    path('api/governance/nft/available/', views.get_available_nfts, name='available_nfts'),
]