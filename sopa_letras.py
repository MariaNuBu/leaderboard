import streamlit as st
import random
import string
import csv
from datetime import datetime
import os
import pandas as pd
from supabase import Client, create_client

# --- 1. Game Configuration & Word List ---

# The words provided by the user, cleaned for the game (uppercase, no spaces)
WORDS_TO_FIND = {
    "AWSGLUEDATAQUALITY":"Managed service that helps users continuously monitor and improve the quality of data.",
    "AWSGLUEDATABREW":"Visual data preparation tool that makes it convenient for users to clean and normalize data without code",
    "AMAZONCOMPREHEND":"NLP service that can be used to extract insights and information from unstructured text data.",
    "SAGEMAKERCLARIFY":"Works by assessing models across different dimensions of bias.",
    "AWSKMS":"Create, manage, and use cryptographic keys for data encryption",
    "AWSEBS":"When using Amazon Elastic Compute Cloud (Amazon EC2) instances for ML, it is recommended that you enable it",
}

# Grid configuration
GRID_SIZE = 20 # Increased size to accommodate long words
SCORE_FILE = "score_sopaletras.csv"

DIRECTIONS = {
    "horizontal": (0, 1),
    "vertical": (1, 0),
    "diagonal_down_right": (1, 1),
    "diagonal_up_right": (-1, 1),
    "diagonal_down_left": (1, -1),
    "diagonal_up_left": (-1, -1),
    # To make it harder, you could also include reversed words
    # "horizontal_rev": (0, -1),
    # "vertical_rev": (-1, 0),
}



# ---------- Supabase init ----------
# Lee credenciales seguras desde st.secrets
SUPABASE_URL: str = st.secrets["supabase"]["url"]
SUPABASE_KEY: str = st.secrets["supabase"]["key"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

TABLE_NAME = "scores_sopa_letras"  # nombre de la tabla que creaste

# --- 2. Core Game Logic Functions ---

def persist_score() -> None:
    """Guarda la puntuación del jugador en Supabase."""
    player = st.session_state.get("player_name", "").strip()
    if not player:
        return

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    intentos = st.session_state.fails + len(WORDS_TO_FIND)

    data = {
        "Jugador": player,
        "Intentos": intentos,
        "Fecha": now,
    }

    # Inserta el registro
    try:
        supabase.table(TABLE_NAME).insert(data).execute()
    except Exception as e:
        st.error(f"No se pudo guardar la puntuación: {e}")

def load_scores() -> pd.DataFrame:
    """Carga todas las puntuaciones ordenadas por menos intentos."""
    try:
        resp = supabase.table(TABLE_NAME).select("*").execute()
    except Exception as e:
        st.error(f"No se pudieron cargar las puntuaciones: {e}")
        return pd.DataFrame(columns=["Jugador", "Intentos", "Fecha"])

    # Si no hay datos todavía
    if not resp.data:
        return pd.DataFrame(columns=["Jugador", "Intentos", "Fecha"])

    df = pd.DataFrame(resp.data)
    df["Jugador"] = df["Jugador"].astype(str)
    return df.sort_values(by="Intentos", ascending=True)


def can_place_word(grid, word, start_row, start_col, direction):
    """Checks if a word can be placed at a specific location without collision."""
    dr, dc = direction
    for i, char in enumerate(word):
        r, c = start_row + i * dr, start_col + i * dc

        # Check grid boundaries
        if not (0 <= r < GRID_SIZE and 0 <= c < GRID_SIZE):
            return False

        # Check for collisions with other letters
        if grid[r][c] != '' and grid[r][c] != char:
            return False
    return True

def place_word(grid, word, direction):
    """Places a single word onto the grid at a valid random location."""
    dr, dc = direction
    placed = False
    max_attempts = 100  # Prevent infinite loops

    for _ in range(max_attempts):
        # Calculate valid starting positions to ensure the word fits
        start_row = random.randint(0, GRID_SIZE - 1)
        start_col = random.randint(0, GRID_SIZE - 1)

        if can_place_word(grid, word, start_row, start_col, direction):
            # Place the word
            for i, char in enumerate(word):
                r, c = start_row + i * dr, start_col + i * dc
                grid[r][c] = char

            end_row, end_col = start_row + (len(word) - 1) * dr, start_col + (len(word) - 1) * dc
            return {"word": word, "start": (start_row, start_col), "end": (end_row, end_col), "direction": direction}
    
    return None # Could not place the word

def initialize_game():
    """Sets up the entire game board in session_state if it doesn't exist."""
    if 'grid' in st.session_state:
        return # Game already initialized

    grid = [['' for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
    word_locations = {}

    # Try to place each word
    for word in WORDS_TO_FIND:
        # Try different directions for each word if one fails
        direction_keys = list(DIRECTIONS.keys())
        random.shuffle(direction_keys)
        
        placed_info = None
        for dir_key in direction_keys:
            direction = DIRECTIONS[dir_key]
            placed_info = place_word(grid, word, direction)
            if placed_info:
                word_locations[word] = placed_info
                break
        
        if not placed_info:
            st.error(f"Could not place the word: {word}. Try increasing GRID_SIZE or rerunning.")

    # Fill the rest of the grid with random letters
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            if grid[r][c] == '':
                grid[r][c] = random.choice(string.ascii_uppercase)

    # Store everything in the session state
    st.session_state.grid = grid
    st.session_state.word_locations = word_locations
    st.session_state.found_words = set()
    st.session_state.game_over = False
    st.session_state.fails = 0
    st.session_state.player_present = False

def get_highlighted_coords():
    """Returns a set of all (row, col) tuples that should be highlighted."""
    coords = set()
    for word in st.session_state.found_words:
        if word in st.session_state.word_locations:
            info = st.session_state.word_locations[word]
            r, c = info['start']
            dr, dc = info['direction']
            for i in range(len(word)):
                coords.add((r + i * dr, c + i * dc))
    return coords

def generate_grid_html():
    """Generates the HTML for the word search grid with highlighting."""
    highlighted_coords = get_highlighted_coords()
    
    html = """
    <style>
        .grid-container { display: grid; grid-template-columns: repeat(%(size)s, 30px); gap: 2px; }
        .grid-cell {
            width: 30px; height: 30px;
            display: flex; align-items: center; justify-content: center;
            font-family: monospace; font-size: 18px; font-weight: bold;
            border: 1px solid #ddd;
            background-color: #f0f2f6;
            color: #31333F;
        }
        .highlight { background-color: #A3E4D7; color: #145A32; border: 1px solid #145A32; }
    </style>
    <div class="grid-container">
    """ % {"size": GRID_SIZE}

    grid = st.session_state.grid
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            cell_class = "grid-cell highlight" if (r, c) in highlighted_coords else "grid-cell"
            html += f'<div class="{cell_class}">{grid[r][c]}</div>'
    
    html += "</div>"
    return html

def mostrar_sopa_letras():
    # --- 3. Streamlit App UI and Interaction ---

    st.set_page_config(layout="wide", initial_sidebar_state="expanded")
    st.title("🍲 AWS Sopa de letras")
    st.markdown("Find the hidden AWS service names in the grid. They can be horizontal, vertical, or diagonal.")

    # Initialize the game on first run
    initialize_game()

    # --- Main Layout (Sidebar for controls, Main area for grid) ---
    with st.sidebar:
        if not st.session_state.player_present:
            st.header("👤 Jugador")
            jugador = st.text_input("Ingresa tu nombre", key="player_name")
            if st.button("🔄 Nuevo juego"):
                if not jugador:
                    st.error("Por favor, ingresa tu nombre antes de comenzar.")
                    return
                else:
                    st.session_state.player_present = True
                st.rerun()
        if st.session_state.player_present:
            st.header("Words to Find")
            
            # Display the list of words and their found status
            for word, definition in WORDS_TO_FIND.items():
                if word in st.session_state.found_words:
                    st.markdown(f"✅ {word}: {definition}")
                else:
                    st.markdown(f"🤔 **{definition}**")
                    
            st.header("Enter Your Guess")
            
            # Form for user input to prevent reruns on every keystroke
            with st.form("guess_form", clear_on_submit=True):
                user_guess = st.text_input("Type a word and press Enter", "").upper().strip().replace(" ", "")
                submit_button = st.form_submit_button("Check Word")

            if submit_button and user_guess:
                if user_guess in WORDS_TO_FIND:
                    if user_guess not in st.session_state.found_words:
                        st.session_state.found_words.add(user_guess)
                        st.success(f"You found {user_guess}!")
                        # Check for win condition
                        if len(st.session_state.found_words) == len(WORDS_TO_FIND):
                            st.session_state.game_over = True
                    else:
                        st.warning(f"You already found {user_guess}!")
                else:
                    st.error(f"{user_guess} is not in the list.")
                    st.session_state.fails += 1
            
            if st.button("New Game / Reset"):
                # Clear all relevant session state keys to restart
                for key in ['grid', 'word_locations', 'found_words', 'game_over']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
    if st.session_state.player_present:

        # --- Display the Grid ---
        grid_html = generate_grid_html()
        st.markdown(grid_html, unsafe_allow_html=True)

        # --- Win Condition Celebration ---
        if st.session_state.get('game_over', False):
            st.balloons()
            st.success("🎉 Congratulations! You've found all the words! 🎉")
            persist_score()

    # ---- Tabla de puntuaciones ----
    st.markdown("---")
    st.subheader("🏆 Tabla de puntuaciones")
    st.table(load_scores())
