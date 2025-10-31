# arena/ai_models.py
import random
from django.utils import timezone
from decimal import Decimal
from .models import ArenaGame

class AstralAI:
    DIFFICULTY_LEVELS = {
        'beginner': {'rating': 800, 'name': 'Cosmic Cadet'},
        'intermediate': {'rating': 1200, 'name': 'Stellar Student'}, 
        'advanced': {'rating': 1600, 'name': 'Galactic Guardian'},
        'expert': {'rating': 2000, 'name': 'Quantum Master'}
    }
    
    def __init__(self, difficulty='beginner'):
        self.difficulty = difficulty
        self.rating = self.DIFFICULTY_LEVELS[difficulty]['rating']
        self.name = self.DIFFICULTY_LEVELS[difficulty]['name']
        self.personality = self._get_personality()
    
    def _get_personality(self):
        """Define AI playing style based on difficulty"""
        personalities = {
            'beginner': {
                'aggression': 0.3,
                'defense': 0.7,
                'risk_taking': 0.2,
                'ability_usage': 0.1
            },
            'intermediate': {
                'aggression': 0.5,
                'defense': 0.5,
                'risk_taking': 0.4,
                'ability_usage': 0.3
            },
            'advanced': {
                'aggression': 0.6,
                'defense': 0.4,
                'risk_taking': 0.6,
                'ability_usage': 0.5
            },
            'expert': {
                'aggression': 0.8,
                'defense': 0.2,
                'risk_taking': 0.8,
                'ability_usage': 0.7
            }
        }
        return personalities[self.difficulty]
    
    def make_move(self, game_state):
        """AI decides and makes a move"""
        valid_moves = self._get_valid_moves(game_state)
        
        if not valid_moves:
            return None
            
        # Score each possible move
        scored_moves = []
        for move in valid_moves:
            score = self._evaluate_move(move, game_state)
            scored_moves.append((move, score))
        
        # Sort by score (highest first)
        scored_moves.sort(key=lambda x: x[1], reverse=True)
        
        # Add some randomness based on difficulty
        top_moves = scored_moves[:max(3, len(scored_moves)//2)]
        if random.random() < self.personality['risk_taking']:
            # Occasionally choose a risky move
            chosen_move = random.choice(top_moves[:2])[0] if len(top_moves) >= 2 else top_moves[0][0]
        else:
            # Usually choose the best move
            chosen_move = top_moves[0][0]
            
        return chosen_move
    
    def _get_valid_moves(self, game_state):
        """Get all valid moves for AI pieces"""
        valid_moves = []
        board = game_state['board']
        
        for piece in board['pieces']:
            if piece['player'] == 2:  # AI is always player 2
                moves = self._calculate_piece_moves(piece, board)
                for move in moves:
                    valid_moves.append({
                        'piece': piece,
                        'from_pos': [piece['row'], piece['col']],
                        'to_pos': move,
                        'type': 'move'
                    })
        
        return valid_moves
    
    def _calculate_piece_moves(self, piece, board):
        """Calculate valid moves for a specific piece"""
        moves = []
        piece_type = piece['type']
        row, col = piece['row'], piece['col']
        
        if piece_type == 'prime':
            # Diagonal and knight moves
            directions = [(-1,-1), (-1,1), (1,-1), (1,1),  # Diagonal
                         (-2,-1), (-2,1), (2,-1), (2,1),   # Knight
                         (-1,-2), (-1,2), (1,-2), (1,2)]
        elif piece_type == 'fibonacci':
            # Orthogonal moves (1 and 2 squares)
            directions = [(-2,0), (2,0), (0,-2), (0,2),
                         (-1,0), (1,0), (0,-1), (0,1)]
        elif piece_type == 'square':
            # Jump moves (2 squares in any direction)
            directions = [(-2,-2), (-2,0), (-2,2),
                         (0,-2), (0,2),
                         (2,-2), (2,0), (2,2)]
        else:  # composite
            # Standard queen moves
            directions = [(-1,-1), (-1,0), (-1,1),
                         (0,-1), (0,1),
                         (1,-1), (1,0), (1,1)]
        
        for dr, dc in directions:
            new_row, new_col = row + dr, col + dc
            if 0 <= new_row < 8 and 0 <= new_col < 8:
                # Check if square is occupied by friendly piece
                if not self._is_friendly_piece(new_row, new_col, board):
                    moves.append([new_row, new_col])
        
        return moves
    
    def _is_friendly_piece(self, row, col, board):
        """Check if position has a friendly piece"""
        for piece in board['pieces']:
            if piece['row'] == row and piece['col'] == col and piece['player'] == 2:
                return True
        return False
    
    def _evaluate_move(self, move, game_state):
        """Evaluate how good a move is (higher score = better)"""
        score = 0
        piece = move['piece']
        to_row, to_col = move['to_pos']
        
        # Base score for moving
        score += 10
        
        # Check for captures
        captured_piece = self._get_piece_at(to_row, to_col, game_state['board'])
        if captured_piece and captured_piece['player'] == 1:  # Human player
            piece_value = self._get_piece_value(captured_piece)
            score += piece_value * 50  # Big bonus for captures
        
        # Check if moving toward human core
        human_core = self._get_human_core(game_state['board'])
        if human_core:
            distance_before = abs(piece['row'] - human_core['row']) + abs(piece['col'] - human_core['col'])
            distance_after = abs(to_row - human_core['row']) + abs(to_col - human_core['col'])
            if distance_after < distance_before:
                score += 20
        
        # Check special tiles
        tile_type = self._get_tile_type(to_row, to_col, game_state['board'])
        if tile_type == 'quantum-tile':
            score += 15
        elif tile_type == 'dark-matter':
            score -= 10
        
        # Personality adjustments
        if self.personality['aggression'] > 0.6:
            # Aggressive AI prefers attacking moves
            if captured_piece:
                score *= 1.5
        else:
            # Defensive AI prefers safe moves
            if not self._is_square_safe(to_row, to_col, game_state['board']):
                score *= 0.5
        
        return score
    
    def _get_piece_value(self, piece):
        """Assign values to different piece types"""
        values = {'prime': 4, 'fibonacci': 3, 'square': 3, 'composite': 2}
        return values.get(piece['type'], 1)
    
    def _get_piece_at(self, row, col, board):
        """Get piece at specific position"""
        for piece in board['pieces']:
            if piece['row'] == row and piece['col'] == col:
                return piece
        return None
    
    def _get_human_core(self, board):
        """Find human player's reality core"""
        for piece in board['pieces']:
            if piece['player'] == 1 and piece['number'] in [17, 23]:  # Core pieces
                return piece
        return None
    
    def _get_tile_type(self, row, col, board):
        """Get type of special tile at position"""
        tile_key = f"{row},{col}"
        return board.get('special_tiles', {}).get(tile_key)
    
    def _is_square_safe(self, row, col, board):
        """Check if square is safe from immediate capture"""
        # Simplified safety check
        for piece in board['pieces']:
            if piece['player'] == 1:  # Human pieces
                moves = self._calculate_piece_moves(piece, board)
                if [row, col] in moves:
                    return False
        return True
    
    def decide_ability_usage(self, game_state):
        """Decide if and which ability to use"""
        if random.random() > self.personality['ability_usage']:
            return None
            
        abilities = ['singularity', 'temporal_loop', 'quantum_tunnel', 'reality_anchor']
        # Simple ability selection logic
        return random.choice(abilities) if random.random() < 0.3 else None