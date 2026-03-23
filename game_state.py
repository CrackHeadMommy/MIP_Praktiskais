from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class GameState:
    # Glabā vienas spēles stāvokli, ko izmanto gan GUI, gan spēles koks.
    number_sequence: List[int]
    human_score: int
    computer_score: int
    current_turn: str  # "human" vai "computer"


@dataclass
class GameTreeNode:
    # Viens spēles koka mezgls ar stāvokli un bērnu mezgliem.
    game_state: GameState
    removed_index: Optional[int] = None
    removed_value: Optional[int] = None
    children: List["GameTreeNode"] = field(default_factory=list)


def copy_game_state(game_state: GameState) -> GameState:
    # Izveido GameState kopiju.
    return GameState(
        number_sequence=game_state.number_sequence.copy(),
        human_score=game_state.human_score,
        computer_score=game_state.computer_score,
        current_turn=game_state.current_turn,
    )


def get_box_four_score_change(player_score: int) -> int:
    # Ja spēlētāja punkti ir pāra skaitlis, tad +1, ja nepāra, tad -1.
    if player_score % 2 == 0:
        return 1
    return -1


def apply_move_to_state(previous_state: GameState, index_to_remove: int) -> tuple[GameState, int]:
    # Veic vienu gājienu un atgriež jauno stāvokli.
    new_sequence = previous_state.number_sequence.copy()
    removed_value = new_sequence.pop(index_to_remove)

    new_human_score = previous_state.human_score
    new_computer_score = previous_state.computer_score

    # Aprēķina punktus cilvēka gājienam.
    if previous_state.current_turn == "human":
        if removed_value == 1:
            new_human_score -= 1
        elif removed_value == 2:
            new_human_score -= 1
            new_computer_score -= 1
        elif removed_value == 3:
            new_computer_score -= 1
        elif removed_value == 4:
            # 4. kaste ietekmē tikai to spēlētāju, kurš to paņem.
            new_human_score += get_box_four_score_change(previous_state.human_score)
        next_turn = "computer"
    # Aprēķina punktus datora gājienam.
    else:
        if removed_value == 1:
            new_computer_score -= 1
        elif removed_value == 2:
            new_human_score -= 1
            new_computer_score -= 1
        elif removed_value == 3:
            new_human_score -= 1
        elif removed_value == 4:
            # Ja datoram punkti ir pāra skaitlis, dators iegūst +1, citādi -1.
            new_computer_score += get_box_four_score_change(previous_state.computer_score)
        next_turn = "human"

    next_state = GameState(
        number_sequence=new_sequence,
        human_score=new_human_score,
        computer_score=new_computer_score,
        current_turn=next_turn,
    )
    return next_state, removed_value


def generate_game_tree_from_state(starting_state: GameState, depth_limit: int) -> GameTreeNode:
    # Ģenerē spēles koka daļu līdz norādītajam dziļumam.
    # Dod algoritmu funkcijām gatavu datu struktūru.
    root_node = GameTreeNode(game_state = copy_game_state(starting_state))
    _generate_children_recursively(root_node, depth_limit)
    return root_node


def _generate_children_recursively(parent_node: GameTreeNode, depth_left: int) -> None:
    # Veido visus iespējamos gājienus no dotā mezgla līdz depth_left robežai.
    if depth_left <= 0:
        return
    if len(parent_node.game_state.number_sequence) == 0:
        return

    # Iterē cauri atlikušās number_sequence virknes indeksiem, lai izveidotu katru iespējamo bērnu mezglu.
    for index_to_remove in range(len(parent_node.game_state.number_sequence)):
        child_state, removed_value = apply_move_to_state(parent_node.game_state, index_to_remove)
        child_node = GameTreeNode(
            game_state=child_state,
            removed_index=index_to_remove,
            removed_value=removed_value,
        )
        parent_node.children.append(child_node)
        _generate_children_recursively(child_node, depth_left - 1)
