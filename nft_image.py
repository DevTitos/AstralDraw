from PIL import Image, ImageDraw, ImageFont
import random
import hashlib
import qrcode
from datetime import datetime

class CleanCosmicTicket:
    def __init__(self):
        # Optimized size for clarity
        self.width = 800
        self.height = 1200
        self.colors = {
            'background': (8, 12, 36),  # Dark space blue
            'primary': (138, 43, 226),  # Vibrant purple
            'accent': (255, 215, 0),    # Gold
            'text': (255, 255, 255),    # White
            'numbers_bg': (30, 144, 255), # Royal blue
            'highlight': (50, 205, 50),  # Lime green
            'danger': (255, 69, 0)      # Red-orange
        }
        
    def generate_ticket_data(self, owner_name):
        """Generate all ticket data"""
        ticket_id = f"AST{random.randint(10000, 99999)}"
        base_numbers = sorted(random.sample(range(1, 100), 6))
        
        # Generate NEBULA variations
        variations = {}
        for i in range(6):
            var_numbers = base_numbers.copy()
            while True:
                new_num = random.randint(1, 99)
                if new_num not in var_numbers:
                    var_numbers[i] = new_num
                    break
            variations[f"NEB-{i+1}"] = sorted(var_numbers)
        
        verification_hash = hashlib.sha256(
            f"{ticket_id}{owner_name}{base_numbers}".encode()
        ).hexdigest()[:16].upper()
        
        return {
            'ticket_id': ticket_id,
            'owner': owner_name.upper(),
            'base_numbers': base_numbers,
            'variations': variations,
            'verification_hash': verification_hash,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M")
        }
    
    def create_clean_ticket(self, owner_name):
        """Create a clean, readable ticket"""
        # Create image with dark background
        img = Image.new('RGB', (self.width, self.height), self.colors['background'])
        draw = ImageDraw.Draw(img)
        
        # Try to load a font, fallback to default
        try:
            title_font = ImageFont.truetype("arial.ttf", 36)
            header_font = ImageFont.truetype("arial.ttf", 28)
            normal_font = ImageFont.truetype("arial.ttf", 22)
            small_font = ImageFont.truetype("arial.ttf", 18)
        except:
            # Scale default font for better visibility
            title_font = ImageFont.load_default()
            header_font = ImageFont.load_default()
            normal_font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
        # Generate data
        data = self.generate_ticket_data(owner_name)
        
        # ===== HEADER SECTION =====
        header_bg = [0, 0, self.width, 120]
        draw.rectangle(header_bg, fill=self.colors['primary'])
        
        # Title
        draw.text(
            (self.width//2, 60), 
            "ASTRAL DRAW COSMIC LOTTERY", 
            fill=self.colors['accent'], 
            font=title_font, 
            anchor="mm"
        )
        
        # ===== OWNER INFO SECTION =====
        y_position = 150
        draw.text(
            (50, y_position), 
            f"OWNER: {data['owner']}", 
            fill=self.colors['text'], 
            font=header_font
        )
        
        draw.text(
            (50, y_position + 40), 
            f"TICKET: {data['ticket_id']}", 
            fill=self.colors['accent'], 
            font=normal_font
        )
        
        draw.text(
            (50, y_position + 70), 
            f"ISSUED: {data['timestamp']}", 
            fill=self.colors['text'], 
            font=small_font
        )
        
        # ===== MAIN NUMBERS SECTION =====
        y_position += 130
        draw.text(
            (self.width//2, y_position), 
            "LUCKY NUMBERS", 
            fill=self.colors['accent'], 
            font=header_font, 
            anchor="mm"
        )
        
        # Draw number circles
        y_position += 50
        number_size = 60
        spacing = (self.width - (6 * number_size)) // 7
        
        for i, number in enumerate(data['base_numbers']):
            x = spacing + (i * (number_size + spacing))
            
            # Draw number circle
            draw.ellipse(
                [x, y_position, x + number_size, y_position + number_size],
                fill=self.colors['numbers_bg'],
                outline=self.colors['accent'],
                width=3
            )
            
            # Draw number
            draw.text(
                (x + number_size//2, y_position + number_size//2),
                f"{number:02d}",
                fill=self.colors['text'],
                font=header_font,
                anchor="mm"
            )
        
        # ===== NEBULA VARIATIONS SECTION =====
        y_position += 120
        draw.text(
            (self.width//2, y_position), 
            "NEBULA CONVERGENCE", 
            fill=self.colors['accent'], 
            font=header_font, 
            anchor="mm"
        )
        
        y_position += 40
        
        # Draw variations in a clean grid
        variation_height = 80
        for i, (nebula, numbers) in enumerate(data['variations'].items()):
            row = i // 2  # 2 columns
            col = i % 2
            
            x_start = 50 + (col * (self.width // 2 - 50))
            y_start = y_position + (row * variation_height)
            
            # Variation background
            draw.rounded_rectangle(
                [x_start, y_start, x_start + 350, y_start + 60],
                radius=10,
                fill=(30, 30, 60),
                outline=self.colors['primary'],
                width=2
            )
            
            # Variation title
            draw.text(
                (x_start + 10, y_start + 15),
                nebula,
                fill=self.colors['accent'],
                font=small_font
            )
            
            # Find and highlight changed number
            changed_idx = None
            for idx, (base_num, var_num) in enumerate(zip(data['base_numbers'], numbers)):
                if base_num != var_num:
                    changed_idx = idx
                    break
            
            # Draw variation numbers
            num_spacing = 280 // 6
            for idx, num in enumerate(numbers):
                num_x = x_start + 20 + (idx * num_spacing)
                
                if idx == changed_idx:
                    # Highlight changed number
                    draw.ellipse(
                        [num_x - 12, y_start + 35, num_x + 12, y_start + 55],
                        fill=self.colors['highlight']
                    )
                    draw.text(
                        (num_x, y_start + 45),
                        f"{num:02d}",
                        fill=self.colors['background'],
                        font=small_font,
                        anchor="mm"
                    )
                else:
                    draw.text(
                        (num_x, y_start + 45),
                        f"{num:02d}",
                        fill=self.colors['text'],
                        font=small_font,
                        anchor="mm"
                    )
        
        # ===== VERIFICATION SECTION =====
        y_position += 180  # Adjust based on variations
        
        # QR Code
        qr_data = f"{data['ticket_id']}|{data['owner']}|{data['verification_hash']}"
        qr = qrcode.QRCode(version=1, box_size=4, border=2)
        qr.add_data(qr_data)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color=self.colors['accent'], back_color=self.colors['background'])
        qr_img = qr_img.resize((120, 120))
        
        img.paste(qr_img, (self.width - 150, y_position))
        
        # Verification text
        draw.text(
            (50, y_position + 30),
            "VERIFICATION:",
            fill=self.colors['accent'],
            font=normal_font
        )
        
        draw.text(
            (50, y_position + 60),
            data['verification_hash'],
            fill=self.colors['text'],
            font=small_font
        )
        
        # ===== FOOTER =====
        footer_y = self.height - 50
        draw.text(
            (self.width//2, footer_y),
            "OFFICIAL NFT TICKET - DO NOT DUPLICATE",
            fill=self.colors['danger'],
            font=small_font,
            anchor="mm"
        )
        
        return img, data

# ULTRA SIMPLE VERSION - MAXIMUM VISIBILITY
def create_ultra_clear_ticket(owner_name):
    """Create extremely clear and visible ticket"""
    width, height = 600, 800
    img = Image.new('RGB', (width, height), (0, 0, 50))  # Dark blue background
    draw = ImageDraw.Draw(img)
    
    # Colors that POP
    colors = {
        'gold': (255, 215, 0),
        'white': (255, 255, 255),
        'green': (0, 255, 0),
        'red': (255, 0, 0),
        'purple': (128, 0, 128)
    }
    
    # Generate simple data
    ticket_id = f"AST{random.randint(1000, 9999)}"
    numbers = sorted(random.sample(range(1, 100), 6))
    
    # HEADER - BIG AND BOLD
    draw.rectangle([0, 0, width, 80], fill=colors['purple'])
    draw.text((width//2, 40), "COSMIC LOTTERY", fill=colors['gold'], anchor="mm", font=ImageFont.load_default())
    
    # OWNER INFO
    draw.text((20, 100), f"OWNER: {owner_name.upper()}", fill=colors['white'], font=ImageFont.load_default())
    draw.text((20, 130), f"TICKET: {ticket_id}", fill=colors['gold'], font=ImageFont.load_default())
    
    # MAIN NUMBERS - HUGE AND CLEAR
    draw.text((width//2, 180), "LUCKY NUMBERS", fill=colors['gold'], anchor="mm", font=ImageFont.load_default())
    
    # Big number circles
    for i, num in enumerate(numbers):
        x = 50 + (i * 90)
        # Big circles
        draw.ellipse([x, 220, x+70, 290], fill=colors['green'], outline=colors['gold'], width=3)
        # Big numbers
        draw.text((x+35, 255), f"{num:02d}", fill=(0, 0, 0), anchor="mm", font=ImageFont.load_default())
    
    # NEBULA VARIANTS - SIMPLE DISPLAY
    draw.text((width//2, 350), "NEBULA DRAWS", fill=colors['gold'], anchor="mm", font=ImageFont.load_default())
    
    y_pos = 390
    for i in range(6):
        # Create variation
        var_nums = numbers.copy()
        while True:
            new_num = random.randint(1, 99)
            if new_num not in var_nums:
                var_nums[i] = new_num
                break
        
        row = i // 3
        col = i % 3
        
        x_start = 30 + (col * 190)
        y_start = y_pos + (row * 60)
        
        draw.text((x_start, y_start), f"N{i+1}:", fill=colors['white'], font=ImageFont.load_default())
        
        # Show numbers compactly
        nums_text = " ".join(f"{n:02d}" for n in var_nums)
        draw.text((x_start + 40, y_start), nums_text, fill=colors['green'], font=ImageFont.load_default())
    
    # FOOTER
    draw.text((width//2, height - 30), "OFFICIAL NFT TICKET", fill=colors['red'], anchor="mm", font=ImageFont.load_default())
    
    filename = f"CLEAR_TICKET_{owner_name.replace(' ', '_')}.png"
    img.save(filename)
    print(f"✅ Generated: {filename}")
    return img

# GENERATION FUNCTIONS
def generate_clean_ticket(owner_name):
    """Generate clean version"""
    generator = CleanCosmicTicket()
    img, data = generator.create_clean_ticket(owner_name)
    
    filename = f"CLEAN_TICKET_{data['ticket_id']}.png"
    img.save(filename, quality=100)
    
    print(f"🎫 CLEAN TICKET: {filename}")
    print(f"🔢 Numbers: {data['base_numbers']}")
    return img, data

def generate_ticket_collection():
    """Generate a collection of clear tickets"""
    owners = ["ALICE", "BOB", "CAROL", "DAVE"]
    
    print("🚀 GENERATING CLEAR TICKETS...")
    print("=" * 50)
    
    for owner in owners:
        # Choose which version to generate:
        generate_clean_ticket(owner)      # Clean detailed version
        # create_ultra_clear_ticket(owner)  # Ultra simple version
    
    print("=" * 50)
    print("✅ ALL TICKETS GENERATED SUCCESSFULLY!")

if __name__ == "__main__":
    generate_ticket_collection()
    
    # Test single ultra-clear ticket
    # create_ultra_clear_ticket("TEST_USER")