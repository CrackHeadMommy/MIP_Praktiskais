# LD1:
# Lietas, kas obligāti jābūt kodā pēc PD1 norādēm:
# izvēlēties, kurš uzsāk spēli: cilvēks vai dators;
# izvēlēties, kuru algoritmu izmantos dators konkrētajā spēles reizē: Minimaksa algoritmu vai Alfa-beta algoritmu;
# izpildīt gājienus un redzēt izmaiņas spēles laukumā pēc gājienu (gan cilvēka, gan datora) izpildes;
# uzsākt spēli atkārtoti pēc kārtējās spēles pabeigšanas.

# obligāti ir jārealizē:
# spēles koka daļas glabāšana datu struktūras veidā (klases, saistītie saraksti, utt.)
# spēles koka ģenerēšana līdz noteiktajam līmenim atkarībā no spēles sarežģītības
# heiristiskā novērtējuma funkcijas izstrāde un tās pielietošana laikā, kad datoram ir jāveic gājiens
# Minimaksa algoritms un Alfa-beta algoritms (abiem ir jābūt realizētiem kā Pārlūkošana uz priekšu pār n-gājieniem)


import algorythms as alg
import random
from dataclasses import dataclass, field
from typing import Optional

import game_state as gs
import game_ui as gui

MIN_SEQUENCE_LENGTH = 15
MAX_SEQUENCE_LENGTH = 25

@dataclass
class GameSession:
    # Glabā spēles sesijas stāvokli. *Priekš GUI*.
    current_state: Optional[gs.GameState] = None
    selected_algorithm: str = "Min-Max"
    tree_depth_limit: int = 2
    latest_tree_root: Optional[gs.GameTreeNode] = None
    status_messages: list[str] = field(default_factory=list)
    initial_sequence_length: int = 0
    slot_values: list[int] = field(default_factory=list)
    slot_taken_by: list[Optional[str]] = field(default_factory=list)
    current_index_to_slot_index: list[int] = field(default_factory=list)


def create_random_number_sequence(sequence_length: int) -> list[int]:
    # Ģenerē sākuma virkni jaunai spēlei.
    return [random.randint(1, 4) for _ in range(sequence_length)]


def is_game_over(game_state: Optional[gs.GameState]) -> bool:
    if game_state is None:
        return False
    return len(game_state.number_sequence) == 0


def get_winner_text(game_state: gs.GameState) -> str:
    if game_state.human_score == game_state.computer_score:
        return "Spēle beigusies. Rezultāts: neizšķirts."
    if game_state.human_score > game_state.computer_score:
        return "Spēle beigusies. Uzvarētājs: cilvēks."
    return "Spēle beigusies. Uzvarētājs: dators."


def add_status_message(game_session: GameSession, message: str) -> None:
    # Pievieno ierakstu žurnālam.
    game_session.status_messages.append(message)


def find_current_index_by_slot(game_session: GameSession, selected_slot_index: int) -> Optional[int]:
    # Atrod, kuram pašreizējās virknes elementam atbilst konkrētā kaste.
    try:
        return game_session.current_index_to_slot_index.index(selected_slot_index)
    except ValueError:
        return None


def mark_taken_slot(game_session: GameSession, current_index: int, taken_by: str) -> None:
    # Atzīmē kurš paņēma konkrēto kasti (cilvēks vai dators).
    if current_index < 0 or current_index >= len(game_session.current_index_to_slot_index):
        return

    removed_slot_index = game_session.current_index_to_slot_index.pop(current_index)
    game_session.slot_taken_by[removed_slot_index] = taken_by


def try_read_integer(value, default_value: int) -> int:
    try:
        return int(value)
    except Exception:
        return default_value


def start_new_game(window, values, game_session: GameSession) -> None:
    # Nolasa iestatījumus no vadības rindas un pārbauda atļautās robežas.
    sequence_length = try_read_integer(values["-SEQUENCE-LENGTH-"], -1)
    tree_depth_limit = try_read_integer(values["-TREE-DEPTH-"], -1)

    if sequence_length < MIN_SEQUENCE_LENGTH or sequence_length > MAX_SEQUENCE_LENGTH:
        gui.show_error("Kļūda: Virknes garumam jābūt no 15 līdz 25.")
        return

    if tree_depth_limit < 1 or tree_depth_limit > 4:
        gui.show_error("Kļūda: Koka dziļumam jābūt no 1 līdz 4.")
        return

    # Nosaka sākuma gājiena veicēju pēc lietotāja izvēles.
    start_player_value = values["-START-PLAYER-"]
    current_turn = "human" if start_player_value == "Cilvēks" else "computer"

    # Izveido jaunu sākuma virkni.
    starting_sequence = create_random_number_sequence(sequence_length)

    game_session.current_state = gs.GameState(
        number_sequence=starting_sequence.copy(),
        human_score=50,
        computer_score=50,
        current_turn=current_turn,
    )
    game_session.selected_algorithm = values["-ALGORITHM-"]
    game_session.tree_depth_limit = tree_depth_limit
    game_session.latest_tree_root = None
    game_session.status_messages = []
    game_session.initial_sequence_length = sequence_length
    game_session.slot_values = starting_sequence.copy()
    game_session.slot_taken_by = [None for _ in range(sequence_length)]
    game_session.current_index_to_slot_index = list(range(sequence_length))

    add_status_message(game_session, f"Sākta jauna spēle. Virknes garums: {sequence_length}.")
    add_status_message(game_session, f"Spēli sāk: {start_player_value}. Algoritms: {game_session.selected_algorithm}.")

    # Ja spēli sāk dators, izpilda gājienu pirms cilvēka pirmā klikšķa.
    make_computer_move_if_needed(game_session)
    gui.update_game_ui(window, game_session, MAX_SEQUENCE_LENGTH)


def make_computer_move_if_needed(game_session: GameSession) -> None:
    # Dators izdara gājienu tikai tad, ja:
    # - spēle ir sākta
    # - ir datora gājiens
    # - spēle nav beigusies
    if game_session.current_state is None:
        return

    if game_session.current_state.current_turn != "computer":
        return

    if is_game_over(game_session.current_state):
        return

    # Ģenerē spēles koka daļu no šobrīdējā stāvokļa (prasība: koks tiek ģenerēts un glabāts datu struktūrā).
    game_session.latest_tree_root = gs.generate_game_tree_from_state(
        starting_state = game_session.current_state,
        depth_limit = game_session.tree_depth_limit,
    )

    if game_session.latest_tree_root is None or len(game_session.latest_tree_root.children) == 0:
        add_status_message(game_session, "Kļūda: Datoram nav derīgu gājienu.")
        return

    selected_algorithm = game_session.selected_algorithm


    # Min-Max / Alfa-Beta (meklēšana uz priekšu pār n-gājieniem + heiristika)
    # alg.choose_best_move atgriež SearchResult ar:
    # - best_child (GameTreeNode)
    # - elapsed_ms, stats.generated_nodes, stats.evaluated_nodes
    result = alg.choose_best_move(
        start_state = game_session.current_state,
        depth_limit = game_session.tree_depth_limit,
        algorithm_name = selected_algorithm,
    )

    chosen_child_node = result.best_child

    if chosen_child_node is None:
        # Ja kaut kas notiek (nevajadzētu), iekrīt uz nejaušo.
        chosen_child_node = random.choice(game_session.latest_tree_root.children)
        algorithm_message = (
            f'Kļūda: "{selected_algorithm}" neatgrieza gājienu, izvēlēts nejaušs gājiens.'
        )
    else:
        algorithm_message = (
            f'Datora algoritms "{selected_algorithm}" izvēlējās gājienu. '
            f'Laiks: {result.elapsed_ms:.2f} ms; '
            f'Ģenerētas virsotnes: {result.stats.generated_nodes}; '
            f'Novērtētas virsotnes: {result.stats.evaluated_nodes}.'
        )

    # Pielieto izvēlēto gājienu spēles sesijai
    removed_current_index = chosen_child_node.removed_index
    removed_value = chosen_child_node.removed_value

    # Atzīmē noņemto elementu UI kartējumā (lai poga kļūst "datora paņemta")
    if removed_current_index is not None:
        mark_taken_slot(game_session, removed_current_index, "computer")

    # Atjaunina spēles stāvokli
    game_session.current_state = chosen_child_node.game_state

    # Žurnāls
    add_status_message(game_session, algorithm_message)
    add_status_message(game_session, f"Dators noņēma skaitli {removed_value}.")

    # Ja spēle beigusies -> uzvarētājs
    if is_game_over(game_session.current_state):
        add_status_message(game_session, get_winner_text(game_session.current_state))


def handle_human_move(window, game_session: GameSession, selected_slot_index: int) -> None:
    if game_session.current_state is None:
        gui.show_error("Kļūda: Vispirms sāc spēli.")
        return

    if game_session.current_state.current_turn != "human":
        gui.show_error("Kļūda: Šobrīd nav cilvēka gājiens.")
        return

    if is_game_over(game_session.current_state):
        gui.show_error('Kļūda: Spēle jau ir beigusies. Spied "Restartēt".')
        return

    # Pārveido nospiestās kastes pozīciju uz indeksu pašreizējā virknē.
    selected_current_index = find_current_index_by_slot(game_session, selected_slot_index)
    if selected_current_index is None:
        gui.show_error("Kļūda: Šis skaitlis jau ir noņemts.")
        return

    # Veic cilvēka gājienu un atzīmē to UI.
    new_state, removed_value = gs.apply_move_to_state(game_session.current_state, selected_current_index)
    mark_taken_slot(game_session, selected_current_index, "human")
    game_session.current_state = new_state

    add_status_message(game_session, f"Cilvēks noņēma skaitli {removed_value}.")

    if is_game_over(game_session.current_state):
        add_status_message(game_session, get_winner_text(game_session.current_state))
        gui.update_game_ui(window, game_session, MAX_SEQUENCE_LENGTH)
        return

    # Uzreiz pēc cilvēka gājiena izpilda datora gājienu.
    make_computer_move_if_needed(game_session)

    if game_session.current_state is not None and is_game_over(game_session.current_state):
        add_status_message(game_session, get_winner_text(game_session.current_state))

    gui.update_game_ui(window, game_session, MAX_SEQUENCE_LENGTH)


def run_game() -> None:
    window = gui.create_window(MAX_SEQUENCE_LENGTH)
    game_session = GameSession()

    gui.update_game_ui(window, game_session, MAX_SEQUENCE_LENGTH)

    while True:
        event, values = window.read()

        if gui.is_window_closed_event(event):
            break

        # Sāk jaunu sesiju ar janiem iestatījumiem.
        if event in ("-START-GAME-", "-RESTART-GAME-"):
            start_new_game(window, values, game_session)

        # Klikšķis uz skaitļa kastes (cilvēka gājiens).
        if gui.is_number_button_event(event):
            selected_slot_index = gui.parse_slot_index_from_number_event(event)
            if selected_slot_index is not None:
                handle_human_move(window, game_session, selected_slot_index)

    window.close()


if __name__ == "__main__":
    run_game()
