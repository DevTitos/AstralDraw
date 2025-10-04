import uuid
import random
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageFilter

def generate_cosmic_ticket(
    ticket_id=None,
    draw_date=None,
    output_path="cosmic_ticket.png",
    width=1000,
    height=500
):
    """
    Generates a high-quality sci-fi themed lottery ticket with cosmic effects.
    """

    try:
        # --- DATA ---
        ticket_id = ticket_id or str(uuid.uuid4())[:8].upper()
        draw_date = draw_date or datetime.now().strftime("%Y-%m-%d %H:%M")

        # --- BASE IMAGE ---
        img = Image.new("RGB", (width, height), (5, 5, 20))
        draw = ImageDraw.Draw(img)

        # --- COSMIC BACKGROUND: STARS + NEBULA ---
        for _ in range(600):
            x = random.randint(0, width - 1)
            y = random.randint(0, height - 1)
            size = random.choice([1, 2])
            brightness = random.randint(180, 255)
            star_color = (brightness, brightness, brightness)
            draw.ellipse((x, y, x + size, y + size), fill=star_color)

        for _ in range(10):
            x = random.randint(0, width)
            y = random.randint(0, height)
            radius = random.randint(50, 150)
            nebula_color = random.choice([(80, 0, 120), (0, 120, 200), (200, 50, 150)])
            draw.ellipse(
                (x - radius, y - radius, x + radius, y + radius),
                fill=nebula_color,
            )

        img = img.filter(ImageFilter.GaussianBlur(radius=2))

        # --- LOAD FONTS ---
        try:
            title_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 60)
            id_font = ImageFont.truetype("DejaVuSansMono.ttf", 36)
            date_font = ImageFont.truetype("DejaVuSansMono.ttf", 30)
        except:
            title_font = ImageFont.load_default()
            id_font = ImageFont.load_default()
            date_font = ImageFont.load_default()

        # --- TEXT: TITLE ---
        title_text = "ASTRAL DRAW"
        bbox = draw.textbbox((0, 0), title_text, font=title_font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        draw.text(
            ((width - text_width) // 2, 40),
            title_text,
            font=title_font,
            fill=(0, 255, 255)
        )

        # --- TICKET INFO BOX ---
        box_margin = 50
        draw.rectangle(
            [box_margin, height - 200, width - box_margin, height - 50],
            outline=(0, 255, 255),
            width=4,
        )

        draw.text((box_margin + 40, height - 180), f"🎟 Ticket ID: {ticket_id}", font=id_font, fill=(255, 255, 255))
        draw.text((box_margin + 40, height - 120), f"⏳ Draw Date: {draw_date}", font=date_font, fill=(200, 255, 200))

        # --- Glow Layer for Title ---
        glow = img.copy()
        glow_draw = ImageDraw.Draw(glow)
        glow_draw.text(((width - text_width) // 2, 40), title_text, font=title_font, fill=(0, 200, 255))
        glow = glow.filter(ImageFilter.GaussianBlur(8))
        img = Image.blend(glow, img, 0.7)

        img.save(output_path)
        print(f"[✅] Cosmic ticket generated successfully: {output_path}")

    except Exception as e:
        raise RuntimeError(f"Failed to generate cosmic ticket: {e}")


# Example usage
if __name__ == "__main__":
    generate_cosmic_ticket()
