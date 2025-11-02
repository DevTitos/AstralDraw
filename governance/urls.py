from django.urls import path
from . import views

urlpatterns = [
    path('api/governance/proposals/create/', views.create_proposal, name='create_proposal'),
    path('api/governance/proposals/<int:proposal_id>/vote/', views.cast_vote, name='cast_vote'),
    path('api/governance/proposals/<int:proposal_id>/results/', views.get_proposal_results, name='proposal_results'),
    path('api/governance/nft/purchase/<str:tier>/', views.purchase_nft, name='purchase_nft'),
    path('api/governance/nft/<int:nft_id>/list/', views.list_nft_for_sale, name='list_nft'),
    path('api/governance/stats/', views.governance_stats, name='governance_stats'),
]