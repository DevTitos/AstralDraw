from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class GovernanceNFT(models.Model):
    TIER_CHOICES = [
        ('celestial', 'Celestial Board'),
        ('stellar', 'Stellar Assembly'),
        ('cosmic', 'Cosmic Community'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tier = models.CharField(max_length=20, choices=TIER_CHOICES)
    nft_id = models.CharField(max_length=100, unique=True)
    serial_number = models.IntegerField()
    token_id = models.CharField(max_length=50)  # Hedera Token ID
    acquired_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    voting_power = models.IntegerField(default=1)
    
    class Meta:
        db_table = 'governance_nfts'
    
    def __str__(self):
        return f"{self.get_tier_display()} - {self.user.username}"

class GovernanceTopic(models.Model):
    topic_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField()
    created_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'governance_topics'
    
    def __str__(self):
        return f"{self.name} ({self.topic_id})"

class GovernanceProposal(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active Voting'),
        ('passed', 'Passed'),
        ('rejected', 'Rejected'),
        ('implemented', 'Implemented'),
    ]
    
    topic = models.ForeignKey(GovernanceTopic, on_delete=models.CASCADE)
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=500)
    description = models.TextField()
    created_date = models.DateTimeField(auto_now_add=True)
    voting_start = models.DateTimeField()
    voting_end = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    min_approval_percentage = models.IntegerField(default=60)
    hedera_message_id = models.CharField(max_length=100, blank=True, null=True)
    
    class Meta:
        db_table = 'governance_proposals'
        ordering = ['-created_date']
    
    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"

class Vote(models.Model):
    VOTE_CHOICES = [
        ('yes', 'Yes'),
        ('no', 'No'),
        ('abstain', 'Abstain'),
    ]
    
    proposal = models.ForeignKey(GovernanceProposal, on_delete=models.CASCADE)
    voter = models.ForeignKey(User, on_delete=models.CASCADE)
    vote = models.CharField(max_length=10, choices=VOTE_CHOICES)
    voting_power = models.IntegerField(default=1)
    voted_at = models.DateTimeField(auto_now_add=True)
    hedera_transaction_id = models.CharField(max_length=100, blank=True, null=True)
    
    class Meta:
        db_table = 'governance_votes'
        unique_together = ['proposal', 'voter']
    
    def __str__(self):
        return f"{self.voter.username} - {self.vote}"

class NFTMarketplace(models.Model):
    nft = models.ForeignKey(GovernanceNFT, on_delete=models.CASCADE)
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='seller')
    price = models.DecimalField(max_digits=20, decimal_places=2)
    listed_at = models.DateTimeField(auto_now_add=True)
    is_sold = models.BooleanField(default=False)
    sold_at = models.DateTimeField(blank=True, null=True)
    buyer = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='buyer')
    
    class Meta:
        db_table = 'nft_marketplace'
    
    def __str__(self):
        return f"{self.nft.tier} - {self.price} ASTRA"