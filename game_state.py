class GameState:
    __slots__ = ("number_sequence", "player_scores", "current_player", "move_count")

    def __init__(self, number_sequence, player_scores, current_player, move_count):
        self.number_sequence = number_sequence  # [1, 3, 2, ...] Atlikušie skaitļi (1-3) no virknes
        self.player_scores = player_scores      # [50, 50]
        self.current_player = current_player    # 0/1 - Spēlētājs kuram ir gājiens 
        self.move_count = move_count            # cik gājinu jau ir izdarīti


    

    
