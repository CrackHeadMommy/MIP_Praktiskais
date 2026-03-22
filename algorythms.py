# algorithms.py
# Minimax + Alpha-Beta meklēšana uz priekšu pār n-gājieniem
# ar heiristisko novērtējumu un statistiku (ģenerētās/novērtētās virsotnes, laiks).

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Optional, Tuple, List

import game_state as gs


@dataclass
class SearchStats:
    generated_nodes: int = 0   # cik mezglu izveidots (iesk. sakni)
    evaluated_nodes: int = 0   # cik reizes pielietota heiristika (vai terminālais novērtējums)


@dataclass
class SearchResult:
    best_child: Optional[gs.GameTreeNode]
    best_score: float
    stats: SearchStats
    elapsed_ms: float


def is_terminal_state(state: gs.GameState) -> bool:
    return len(state.number_sequence) == 0


def terminal_score(state: gs.GameState) -> int:
    # Gala rezultāts no datora skatpunkta
    return state.computer_score - state.human_score


def immediate_delta_for_removed_value(current_turn: str, removed_value: int) -> int:
    """
    Aprēķina momentāno izmaiņu (computer_score - human_score) pēc viena gājiena,
    ja pašreizējais gājiena veicējs noņem removed_value.

    current_turn == "computer":
        1 -> -1 (dators zaudē punktu)
        2 ->  0
        3 -> +1 (cilvēks zaudē punktu)
    current_turn == "human":
        1 -> +1 (cilvēks zaudē punktu)
        2 ->  0
        3 -> -1 (dators zaudē punktu)
    """
    if current_turn == "computer":
        if removed_value == 3:
            return +1
        if removed_value == 2:
            return 0
        return -1  # 1
    else:
        if removed_value == 1:
            return +1
        if removed_value == 2:
            return 0
        return -1  # 3


def heuristic_evaluate(state: gs.GameState) -> float:
    """
    Heiristika: pašreizējais punktu starpības stāvoklis +
    aptuvenā nākotnes ietekme (katrs spēlētājs ņem sev izdevīgāko: 3 > 2 > 1).
    Greedy simulācija ir emulēta ar formūlām, bez cikla.
    """
    diff = state.computer_score - state.human_score

    # saskaita atlikušos skaitļus
    c1 = c2 = c3 = 0
    for v in state.number_sequence:
        if v == 1:
            c1 += 1
        elif v == 2:
            c2 += 1
        else:
            c3 += 1

    turn = state.current_turn
    total_moves = c1 + c2 + c3

    # saskaita, cik palika izdevīgo gājienu 
    # (koeficientus var mainīt, jo tam ir aptuvēna nozīme)
    diff += 0.3 * c3
    diff -= 0.1 * c2
    diff -= 0.3 * c1

    # ņem vērā kas veic gājienu un cik skaitļu palika
    if turn == "computer":
        diff += 0.1 * total_moves
        computer_first = True
    else:
        diff -= 0.1 * total_moves
        computer_first = False

    # greedy simulācija, ņemot vērā papildus aprēķinus (optimizēta)
    # diff = greedy_simulation(diff, c1, c2, c3, turn)

    """
    Šeit es mēģināju optimizācijai greedy simulācijas vietā izmantot formūlas, 
    lai nebūtu cikla (tagad ir O(1) sarežģītība, instead of O(n)), jo spēle pašlaik ir pietiekami vienkārša. 
    Greedy ciklu (mazliet pamainīto uz atsevišķo funkciju) atstāju ka komentāru
    """
    
    # skaita, cik skaitļu paņems spēlētājs, kas veic pirmo gājienu, ja skaitļu rinda ir nepara
    def split_count(total: int, first: bool) -> Tuple[int, int]:
        half = total // 2
        if total % 2 == 0:
            return half, half
        else:
            return half + 1 if first else half, half if first else half + 1

    comp_3, hum_3 = split_count(c3, computer_first)
    comp_1, hum_1 = split_count(c1, computer_first)

    diff += comp_3 - hum_3
    diff -= comp_1 - hum_1

    return float(diff)

"""
def greedy_simulation(diff: float, c1: int, c2: int, c3: int, turn: str) -> float:
    #šī greedy funkcija ir labāk piemerota lielākam tree depth (3-4)
    
    computer_turn = (turn == "computer")

    while (c1 + c2 + c3) > 0:
        if c3 > 0:
            take = c3
            c3 = 0
            if computer_turn:
                diff += take
            else:
                diff -= take
        elif c2 > 0:
            take = c2
            c2 = 0
        elif c1 > 0:
            take = c1
            c1 = 0
            if computer_turn:
                diff -= take
            else:
                diff += take

        computer_turn = False

    return diff
"""

def ordered_move_indices(state: gs.GameState) -> List[int]:
    """
    Sakārto gājienus, lai Alpha-Beta labāk griež zarus:
    - ja ir MAX (dators), ejam vispirms uz labākajiem delta
    - ja ir MIN (cilvēks), ejam vispirms uz sliktākajiem delta
    """
    is_max = (state.current_turn == "computer")
    scored = []
    for idx, val in enumerate(state.number_sequence):
        delta = immediate_delta_for_removed_value(state.current_turn, val)
        scored.append((delta, idx))

    # MAX: lielākais delta pirmais, MIN: mazākais delta pirmais
    scored.sort(reverse = is_max)
    return [idx for _, idx in scored]


def make_child_node(parent_state: gs.GameState, index_to_remove: int, stats: SearchStats) -> gs.GameTreeNode:
    child_state, removed_value = gs.apply_move_to_state(parent_state, index_to_remove)
    child_node = gs.GameTreeNode(
        game_state = child_state,
        removed_index = index_to_remove,
        removed_value = removed_value,
    )
    stats.generated_nodes += 1
    return child_node


# -------------------- MINIMAX --------------------

def minimax_choose_move(start_state: gs.GameState, depth_limit: int) -> SearchResult:
    start = perf_counter()
    stats = SearchStats(generated_nodes = 1, evaluated_nodes = 0)
    root = gs.GameTreeNode(game_state = gs.copy_game_state(start_state))

    best_score, best_child = _minimax(root, depth_limit, stats)

    elapsed_ms = (perf_counter() - start) * 1000.0
    return SearchResult(best_child = best_child, best_score = best_score, stats = stats, elapsed_ms = elapsed_ms)


def _minimax(node: gs.GameTreeNode, depth_left: int, stats: SearchStats) -> Tuple[float, Optional[gs.GameTreeNode]]:
    state = node.game_state

    if depth_left <= 0 or is_terminal_state(state):
        stats.evaluated_nodes += 1
        if is_terminal_state(state):
            return float(terminal_score(state)), None
        return heuristic_evaluate(state), None

    is_max = (state.current_turn == "computer")

    if is_max:
        best_val = float("-inf")
        best_child = None
        for idx in ordered_move_indices(state):
            child = make_child_node(state, idx, stats)
            val, _ = _minimax(child, depth_left - 1, stats)
            if val > best_val:
                best_val = val
                best_child = child
        return best_val, best_child
    else:
        best_val = float("+inf")
        best_child = None
        for idx in ordered_move_indices(state):
            child = make_child_node(state, idx, stats)
            val, _ = _minimax(child, depth_left - 1, stats)
            if val < best_val:
                best_val = val
                best_child = child
        return best_val, best_child


# -------------------- ALPHA-BETA --------------------

def alphabeta_choose_move(start_state: gs.GameState, depth_limit: int) -> SearchResult:
    start = perf_counter()
    stats = SearchStats(generated_nodes=1, evaluated_nodes=0)
    root = gs.GameTreeNode(game_state=gs.copy_game_state(start_state))

    best_score, best_child = _alphabeta(root, depth_limit, float("-inf"), float("+inf"), stats)

    elapsed_ms = (perf_counter() - start) * 1000.0
    return SearchResult(best_child=best_child, best_score=best_score, stats=stats, elapsed_ms=elapsed_ms)


def _alphabeta(
    node: gs.GameTreeNode,
    depth_left: int,
    alpha: float,
    beta: float,
    stats: SearchStats 
    ) -> Tuple[float, Optional[gs.GameTreeNode]]:

    state = node.game_state

    if depth_left <= 0 or is_terminal_state(state):
        stats.evaluated_nodes += 1
        if is_terminal_state(state):
            return float(terminal_score(state)), None
        return heuristic_evaluate(state), None

    is_max = (state.current_turn == "computer")

    if is_max:
        best_val = float("-inf")
        best_child = None
        for idx in ordered_move_indices(state):
            child = make_child_node(state, idx, stats)
            val, _ = _alphabeta(child, depth_left - 1, alpha, beta, stats)
            if val > best_val:
                best_val = val
                best_child = child
            alpha = max(alpha, best_val)
            if beta <= alpha:
                break  # pruning
        return best_val, best_child
    else:
        best_val = float("+inf")
        best_child = None
        for idx in ordered_move_indices(state):
            child = make_child_node(state, idx, stats)
            val, _ = _alphabeta(child, depth_left - 1, alpha, beta, stats)
            if val < best_val:
                best_val = val
                best_child = child
            beta = min(beta, best_val)
            if beta <= alpha:
                break  # pruning
        return best_val, best_child


# -------------------- Vienots interfeiss priekš main.py --------------------

def choose_best_move(start_state: gs.GameState, depth_limit: int, algorithm_name: str) -> SearchResult:
    """
    algorithm_name: "Min-Max" vai "Alfa-Beta"
    """
    if algorithm_name == "Min-Max":
        return minimax_choose_move(start_state, depth_limit)
    if algorithm_name == "Alfa-Beta":
        return alphabeta_choose_move(start_state, depth_limit)

    # fallback (ja kāds UI iedeva ko citu)
    return minimax_choose_move(start_state, depth_limit)
