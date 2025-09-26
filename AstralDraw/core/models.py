from django.db import models
import uuid
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from cryptography.fernet import Fernet
import os
from cryptography.fernet import Fernet
import base64
from dotenv import load_dotenv
import json
from django.utils import timezone
from decimal import Decimal

load_dotenv()

class UserWallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    fiat_balance = models.DecimalField(max_digits=9, decimal_places=2, default=0)
    public_key = models.CharField(max_length=256, blank=True, null=True)
    private_key = models.CharField(max_length=256, blank=True, null=True, editable=False)
    recipient_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        """Encrypt private keys before saving."""
        if self.private_key:
            key_str = str(self.private_key)
            if not key_str.startswith("gAAAA"):  # Avoid double encryption
                self.private_key = self.encrypt_key(key_str)
        super().save(*args, **kwargs)

    def encrypt_key(self, key: str) -> str:
        """
        Encrypt the private key using Fernet.
        """
        try:
            secret_key = os.getenv('SECRET_KEY')
            if not secret_key:
                raise ValueError("Missing SECRET_KEY in environment variables")
            
            key_bytes = secret_key.encode()
            key_base64 = base64.urlsafe_b64encode(key_bytes.ljust(32)[:32])
            f = Fernet(key_base64)
            return f.encrypt(key.encode()).decode()
        except Exception as e:
            raise ValueError(f"Encryption error: {e}")

    def decrypt_key(self) -> str:
        """
        Decrypt the private key using Fernet.
        """
        try:
            secret_key = os.getenv('SECRET_KEY')
            if not secret_key:
                raise ValueError("Missing SECRET_KEY in environment variables")
            
            key_bytes = secret_key.encode()
            key_base64 = base64.urlsafe_b64encode(key_bytes.ljust(32)[:32])
            f = Fernet(key_base64)
            return f.decrypt(self.private_key.encode()).decode()
        except Exception as e:
            raise ValueError(f"Decryption error: {e}")

    def __str__(self):
        return f"{self.user.username} Wallet"


class Draw(models.Model):
    class DrawStatus(models.TextChoices):
        UPCOMING = 'UPCOMING', _('Upcoming')
        ACTIVE = 'ACTIVE', _('Active')
        ENDED = 'ENDED', _('Ended')
        CANCELLED = 'CANCELLED', _('Cancelled')

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    title = models.CharField(max_length=100, help_text="e.g., Nebula-1 Convergence")
    prize_pool = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="Prize pool in ASTRA")
    star_keys = models.TextField(help_text="JSON array of winning star keys [1,2,3,4,5,6]")  # Encrypted storage
    nft_id = models.CharField(max_length=50, blank=True, null=True, help_text="e.g., 0.0.6861467")
    hcs_message_id = models.CharField(max_length=100, blank=True, null=True, help_text="HCS receipt ID")
    status = models.CharField(max_length=10, choices=DrawStatus.choices, default=DrawStatus.UPCOMING)
    draw_datetime = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Draw statistics
    total_tickets_sold = models.PositiveIntegerField(default=0)
    total_prize_distributed = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    winning_ticket_serial = models.CharField(max_length=50, blank=True, null=True)
    winner_wallet = models.ForeignKey(UserWallet, on_delete=models.SET_NULL, null=True, blank=True, related_name='won_draws')
    
    class Meta:
        ordering = ['-draw_datetime']
        indexes = [
            models.Index(fields=['status', 'draw_datetime']),
            models.Index(fields=['uuid']),
        ]

    def save(self, *args, **kwargs):
        """Encrypt star keys before saving."""
        if self.star_keys and not self.star_keys.startswith("gAAAA"):  # Avoid double encryption
            self.star_keys = self.encrypt_data(self.star_keys)
        super().save(*args, **kwargs)

    def encrypt_data(self, data: str) -> str:
        """Encrypt data using Fernet."""
        try:
            secret_key = os.getenv('SECRET_KEY')
            if not secret_key:
                raise ValueError("Missing SECRET_KEY in environment variables")
            
            key_bytes = secret_key.encode()
            key_base64 = base64.urlsafe_b64encode(key_bytes.ljust(32)[:32])
            f = Fernet(key_base64)
            return f.encrypt(data.encode()).decode()
        except Exception as e:
            raise ValueError(f"Encryption error: {e}")

    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt data using Fernet."""
        try:
            secret_key = os.getenv('SECRET_KEY')
            if not secret_key:
                raise ValueError("Missing SECRET_KEY in environment variables")
            
            key_bytes = secret_key.encode()
            key_base64 = base64.urlsafe_b64encode(key_bytes.ljust(32)[:32])
            f = Fernet(key_base64)
            return f.decrypt(encrypted_data.encode()).decode()
        except Exception as e:
            raise ValueError(f"Decryption error: {e}")

    def get_star_keys(self) -> list:
        """Decrypt and return star keys as list."""
        if not self.star_keys:
            return []
        try:
            decrypted = self.decrypt_data(self.star_keys)
            return json.loads(decrypted)
        except (json.JSONDecodeError, ValueError):
            return []

    def set_star_keys(self, keys_list: list):
        """Encrypt and set star keys from list."""
        self.star_keys = self.encrypt_data(json.dumps(keys_list))

    def map_winner(self):
        """
        Search for an exact winner from ForgedKey Model.
        Returns the winning ForgedKey object or None.
        """
        winning_keys = self.get_star_keys()
        if not winning_keys or len(winning_keys) != 6:
            return None
            
        # Find exact match
        exact_match = ForgedKey.objects.filter(
            draw=self,
            star_keys=self.star_keys  # Compare encrypted values for exact match
        ).first()
        
        if exact_match:
            self.winning_ticket_serial = exact_match.serial_number
            self.winner_wallet = exact_match.user_wallet
            self.save()
            return exact_match
        return None

    def map_nearest_winner(self, min_matches=5):
        """
        Search for star keys that contain at least min_matches winning star keys.
        Returns list of ForgedKey objects sorted by match count.
        """
        winning_keys = set(self.get_star_keys())
        if not winning_keys or len(winning_keys) != 6:
            return []
        
        forged_keys = ForgedKey.objects.filter(draw=self)
        matches = []
        
        for fk in forged_keys:
            try:
                ticket_keys = set(fk.get_star_keys())
                match_count = len(winning_keys.intersection(ticket_keys))
                
                if match_count >= min_matches:
                    matches.append({
                        'forged_key': fk,
                        'match_count': match_count,
                        'matched_keys': list(winning_keys.intersection(ticket_keys))
                    })
            except (ValueError, json.JSONDecodeError):
                continue
        
        # Sort by match count (descending)
        matches.sort(key=lambda x: x['match_count'], reverse=True)
        return matches

    def get_draw_statistics(self):
        """Return comprehensive draw statistics."""
        total_tickets = self.forged_keys.count()
        total_prize = self.prize_pool
        
        # Calculate prize distribution if draw has ended
        prize_distribution = {}
        if self.status == self.DrawStatus.ENDED and self.winner_wallet:
            prize_distribution = {
                'jackpot_winner': {
                    'wallet': self.winner_wallet.user.username,
                    'amount': float(self.prize_pool * Decimal('0.7')),  # 70% to winner
                    'ticket_serial': self.winning_ticket_serial
                },
                'secondary_winners': []  # Could be populated from nearest winners
            }
            
            # Add nearest winners (20% divided among top 5 matches)
            nearest_winners = self.map_nearest_winner(min_matches=4)
            if nearest_winners:
                secondary_prize_pool = float(self.prize_pool * Decimal('0.2'))
                prize_per_winner = secondary_prize_pool / min(5, len(nearest_winners))
                
                for i, winner in enumerate(nearest_winners[:5]):
                    prize_distribution['secondary_winners'].append({
                        'wallet': winner['forged_key'].user_wallet.user.username,
                        'amount': prize_per_winner,
                        'match_count': winner['match_count'],
                        'ticket_serial': winner['forged_key'].serial_number
                    })
        
        return {
            'draw_title': self.title,
            'status': self.status,
            'total_tickets_sold': total_tickets,
            'prize_pool': float(self.prize_pool),
            'draw_datetime': self.draw_datetime,
            'winning_keys': self.get_star_keys(),
            'prize_distribution': prize_distribution,
            'nft_id': self.nft_id,
            'hcs_message_id': self.hcs_message_id
        }

    def is_active(self):
        """Check if draw is currently active."""
        return self.status == self.DrawStatus.ACTIVE

    def can_participate(self):
        """Check if users can still participate in this draw."""
        return self.status in [self.DrawStatus.UPCOMING, self.DrawStatus.ACTIVE] and self.draw_datetime > timezone.now()

    def __str__(self):
        return f"{self.title} - {self.get_status_display()} - {self.prize_pool} ASTRA"


class ForgedKey(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user_wallet = models.ForeignKey(UserWallet, on_delete=models.CASCADE, related_name='forged_keys')
    draw = models.ForeignKey(Draw, on_delete=models.CASCADE, related_name='forged_keys')
    star_keys = models.TextField(help_text="JSON array of user's star keys [1,2,3,4,5,6]", blank=True, null=True)  # Encrypted storage
    hcs_message_id = models.CharField(max_length=100, blank=True, null=True, help_text="HCS receipt ID")
    serial_number = models.CharField(max_length=50, unique=True, help_text="Unique mint serial number")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # NFT Metadata
    nft_metadata = models.JSONField(default=dict, blank=True, help_text="NFT metadata storage")
    token_id = models.CharField(max_length=50, blank=True, null=True, help_text="Hedera Token ID")
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['user_wallet', 'draw', 'serial_number']
        indexes = [
            models.Index(fields=['user_wallet', 'draw']),
            models.Index(fields=['serial_number']),
            models.Index(fields=['created_at']),
        ]

    def save(self, *args, **kwargs):
        """Encrypt star keys before saving."""
        if self.star_keys and not self.star_keys.startswith("gAAAA"):  # Avoid double encryption
            self.star_keys = self.encrypt_data(self.star_keys)
        super().save(*args, **kwargs)

    def encrypt_data(self, data: str) -> str:
        """Encrypt data using Fernet."""
        try:
            secret_key = os.getenv('SECRET_KEY')
            if not secret_key:
                raise ValueError("Missing SECRET_KEY in environment variables")
            
            key_bytes = secret_key.encode()
            key_base64 = base64.urlsafe_b64encode(key_bytes.ljust(32)[:32])
            f = Fernet(key_base64)
            return f.encrypt(data.encode()).decode()
        except Exception as e:
            raise ValueError(f"Encryption error: {e}")

    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt data using Fernet."""
        try:
            secret_key = os.getenv('SECRET_KEY')
            if not secret_key:
                raise ValueError("Missing SECRET_KEY in environment variables")
            
            key_bytes = secret_key.encode()
            key_base64 = base64.urlsafe_b64encode(key_bytes.ljust(32)[:32])
            f = Fernet(key_base64)
            return f.decrypt(encrypted_data.encode()).decode()
        except Exception as e:
            raise ValueError(f"Decryption error: {e}")

    def get_star_keys(self) -> list:
        """Decrypt and return star keys as list."""
        if not self.star_keys:
            return []
        try:
            decrypted = self.decrypt_data(self.star_keys)
            return json.loads(decrypted)
        except (json.JSONDecodeError, ValueError):
            return []

    def set_star_keys(self, keys_list: list):
        """Encrypt and set star keys from list."""
        self.star_keys = self.encrypt_data(json.dumps(keys_list))

    def is_winner(self):
        """Check if this key is the exact winner of the draw."""
        if self.draw.status != Draw.DrawStatus.ENDED:
            return False
        return self.draw.winning_ticket_serial == self.serial_number

    def get_match_count(self):
        """Get number of matching keys with draw's winning keys."""
        if self.draw.status != Draw.DrawStatus.ENDED:
            return 0
        
        draw_keys = set(self.draw.get_star_keys())
        user_keys = set(self.get_star_keys())
        return len(draw_keys.intersection(user_keys))

    def generate_nft_metadata(self):
        """Generate NFT metadata for this forged key."""
        star_keys = self.get_star_keys()
        glyphs = ['⟟', '⍙', '⟊', '⊑', '⌇', '⎍', '⏁', '⍀', '⌰', '⋏']
        visual_glyph = ''.join([glyphs[k % len(glyphs)] for k in star_keys[:6]])
        
        metadata = {
            "name": f"Astral Key #{self.serial_number}",
            "description": f"Star Key for {self.draw.title} - Cosmic Convergence NFT",
            "image": f"https://astraldraw.com/api/nft-image/{self.uuid}/",
            "attributes": [
                {
                    "trait_type": "Convergence",
                    "value": self.draw.title
                },
                {
                    "trait_type": "Serial Number",
                    "value": self.serial_number
                },
                {
                    "trait_type": "Star Keys",
                    "value": str(star_keys)
                },
                {
                    "trait_type": "Cosmic Glyph",
                    "value": visual_glyph
                },
                {
                    "trait_type": "Forged Date",
                    "value": self.created_at.isoformat()
                },
                {
                    "trait_type": "Rarity",
                    "value": self.calculate_rarity()
                }
            ]
        }
        
        self.nft_metadata = metadata
        self.save()
        return metadata

    def calculate_rarity(self):
        """Calculate rarity based on star key patterns."""
        keys = self.get_star_keys()
        if not keys:
            return "Common"
        
        # Simple rarity calculation based on key patterns
        unique_keys = len(set(keys))
        if unique_keys == 6:
            return "Rare"
        elif len([k for k in keys if k % 2 == 0]) == 6:  # All even
            return "Epic"
        elif len([k for k in keys if k % 2 != 0]) == 6:  # All odd
            return "Epic"
        elif len(set(keys)) == 1:  # All same number
            return "Legendary"
        else:
            return "Common"

    def __str__(self):
        return f"Key #{self.serial_number} for {self.draw.title} - {self.user_wallet.user.username}"
