from typing import Any

import FreeSimpleGUI as sg
from typing import Optional

AVAILABLE_BUTTON_COLOR = ("black", "#f0f0f0")
HUMAN_TAKEN_BUTTON_COLOR = ("white", "#2e7d32")
COMPUTER_TAKEN_BUTTON_COLOR = ("white", "#b23a48")
NUMBER_BUTTON_EVENT_PREFIX = "-NUM-"


def show_error(message: str) -> None:
    # Kļūdu paziņojumiem uz GUI.
    sg.popup_error(message)


def is_window_closed_event(event: Any) -> bool:
    # Loga aizvēršanai. (galvenajā ciklā).
    return event == sg.WINDOW_CLOSED


def is_number_button_event(event: Any) -> bool:
    # Atpazīst vai klikšķis ir uz skaitļu kastes.
    return isinstance(event, str) and event.startswith(NUMBER_BUTTON_EVENT_PREFIX)


def parse_slot_index_from_number_event(event_text: str) -> Optional[int]:
    # Atgriež nospiestās skaitļu kastes indeksu.
    try:
        return int(event_text.replace(NUMBER_BUTTON_EVENT_PREFIX, ""))
    except Exception:
        return None


def build_number_button_grid(max_sequence_length: int, max_columns: int = 10) -> list:
    # Sataisa režģi ar kastēm (pogām) pa 10 vienā rindā, lai visas būtu redzamas.
    number_button_grid = []

    for row_start_index in range(0, max_sequence_length, max_columns):
        row_end_index = min(row_start_index + max_columns, max_sequence_length)
        number_buttons = []

        for button_index in range(row_start_index, row_end_index):
            number_buttons.append(
                sg.Button(
                    "",
                    key=f"-NUM-{button_index}",
                    size=(4, 1),
                    disabled=True,
                    visible=False,
                    pad=(2, 6),
                )
            )

        number_button_grid.append(number_buttons)

    return number_button_grid


def format_turn_for_ui(current_turn: str) -> str:
    if current_turn == "human":
        return "Cilvēks"
    if current_turn == "computer":
        return "Dators"
    return "-"


def update_game_ui(window: Any, game_session: Any, max_sequence_length: int) -> None:
    if game_session.current_state is None:
        window["-CURRENT-TURN-"].update("-")
        window["-HUMAN-SCORE-"].update("-")
        window["-COMPUTER-SCORE-"].update("-")

        # Paslēpj visas skaitļu kastes pirms spēles sākuma.
        for button_index in range(max_sequence_length):
            window[f"{NUMBER_BUTTON_EVENT_PREFIX}{button_index}"].update(text="", disabled=True, visible=False)
    else:
        current_state = game_session.current_state
        window["-CURRENT-TURN-"].update(format_turn_for_ui(current_state.current_turn))
        window["-HUMAN-SCORE-"].update(str(current_state.human_score))
        window["-COMPUTER-SCORE-"].update(str(current_state.computer_score))

        # Aktivizē brīvās kastes tieši tad kad cilvēkam ir gājiens.
        human_can_move = current_state.current_turn == "human" and len(current_state.number_sequence) > 0

        # Iet cauri visām skaitļu kastēm un iedod katrai tās stāvokli konkrētajā brīdī:
        # brīva / cilvēka paņemta / datora paņemta.
        for button_index in range(max_sequence_length):
            if button_index < game_session.initial_sequence_length:
                number_value = game_session.slot_values[button_index]
                taken_by = game_session.slot_taken_by[button_index]

                if taken_by == "human":
                    window[f"{NUMBER_BUTTON_EVENT_PREFIX}{button_index}"].update(
                        text=f"{number_value}C",
                        disabled=True,
                        visible=True,
                        button_color=HUMAN_TAKEN_BUTTON_COLOR,
                    )
                elif taken_by == "computer":
                    window[f"{NUMBER_BUTTON_EVENT_PREFIX}{button_index}"].update(
                        text=f"{number_value}D",
                        disabled=True,
                        visible=True,
                        button_color=COMPUTER_TAKEN_BUTTON_COLOR,
                    )
                else:
                    window[f"{NUMBER_BUTTON_EVENT_PREFIX}{button_index}"].update(
                        text=str(number_value),
                        disabled=not human_can_move,
                        visible=True,
                        button_color=AVAILABLE_BUTTON_COLOR,
                    )
            else:
                window[f"{NUMBER_BUTTON_EVENT_PREFIX}{button_index}"].update(text="", disabled=True, visible=False)

    status_text = "\n".join(game_session.status_messages)
    window["-STATUS-LOG-"].update(status_text)


def create_window(max_sequence_length: int):
    # Pirmajā rindā definē spēles parametrus:
    # virknes garumu, sākuma spēlētāju, algoritma tipu un koka dziļumu.
    settings_row = [
        sg.Text("Virknes garums (15-25):"),
        sg.Input("15", size=(5, 1), key="-SEQUENCE-LENGTH-"),

        sg.Text("Spēli sāks:"),
        sg.Combo(["Cilvēks", "Dators"], default_value="Cilvēks", readonly=True, key="-START-PLAYER-"),

        sg.Text("Datora algoritms:"),
        sg.Combo(["Min-Max", "Alfa-Beta"], default_value="Min-Max", readonly=True, key="-ALGORITHM-"),

        sg.Text("Koka dziļums (1-4):"),
        sg.Spin(values=[1, 2, 3, 4], initial_value=2, size=(4, 1), key="-TREE-DEPTH-"),

        # Pogas:
        sg.Button("Sākt spēli", key="-START-GAME-"),

        sg.Button("Restartēt", key="-RESTART-GAME-"),
    ]

    # Rāda rezultātu un kam ir nākamais gājiens.
    score_row = [
        sg.Text("Pašreizējais gājiens:"),
        sg.Text("-", key="-CURRENT-TURN-", size=(10, 1)),
      
        sg.Text("Cilvēka punkti:"),
        sg.Text("-", key="-HUMAN-SCORE-", size=(5, 1)),
      
        sg.Text("Datora punkti:"),
        sg.Text("-", key="-COMPUTER-SCORE-", size=(5, 1)),
    ]

    # Skaitļu kastes
    number_box_area = build_number_button_grid(max_sequence_length)

    # Notikumu žurnāls (jeb "log"):
    status_log_area = [
        sg.Multiline("", size=(100, 10), key="-STATUS-LOG-", disabled=True, autoscroll=True,  expand_x=True, expand_y=True),
    ]

    layout = [
        settings_row,
        [sg.HorizontalSeparator()],
        score_row,
        [sg.Text("")],
        [sg.Text("")],
        *number_box_area,
        status_log_area,
    ]

    return sg.Window("LD1 Spele_42", layout, finalize=True, resizable=True)
