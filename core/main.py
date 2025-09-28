import random

def generate_star_convergence_with_mapping(num_stars=6):
    """
    Generate random motion directions for stars that converge
    toward a single random convergent point, and map them to
    integers between 0 and 9.
    
    Args:
        num_stars (int): Number of stars to generate (default = 6)
    
    Returns:
        tuple: (convergent_point, star_data)
               where star_data is a list of dicts with
               star name, direction, and mapped number
    """
    star_names = [
        "Aldebaran", "Theta² Tauri", "Gamma Tauri",
        "Delta¹ Tauri", "Epsilon Tauri", "Hyadum I"
    ]
    
    if num_stars > len(star_names):
        raise ValueError(f"Only {len(star_names)} star names available.")
    
    convergent_point = random.uniform(0, 360)
    star_data = []
    draws = []
    
    for star in star_names[:num_stars]:
        # Random direction around convergent point
        direction = (convergent_point + random.uniform(-10, 10)) % 363
        
        # Distance from convergent point (0–10 roughly)
        distance = abs(direction - convergent_point)
        # Map to 0–9 range (0 = exactly at convergent point, 9 = farthest)
        mapped_number = round((distance / 10) * 9)
        mapped_number = max(0, min(9, mapped_number))  # clamp to [0,9]
        draws.append(mapped_number)
        
        star_data.append({
            "name": star,
            "direction": round(direction, 2),
            "mapped_number": mapped_number
        })
    
    #return round(convergent_point, 2), star_data
    return draws


# Example usage:
#if __name__ == "__main__":
#    cp, stars = generate_star_convergence_with_mapping()
#    print(f"Convergent Point: {cp}°")
#    for s in stars:
#        print(f"{s['name']}: {s['direction']}° -> {s['mapped_number']}")
