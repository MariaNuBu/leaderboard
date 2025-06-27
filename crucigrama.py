
import streamlit as st
import pandas as pd
import csv
from datetime import datetime
import os
from supabase import create_client, Client

# --- 1. Definición de Datos y Configuración Inicial ---

# Diccionario original con las pistas
DICCIONARIO_PISTAS = {
    "Mechanical Turk": "Access to an on-demand global workforce to quickly complete data transformation microtasks at low cost, streamlining the overall process by decomposing workflows into discrete tasks",
    "Ground Truth": "Service that uses Mechanical Turk and other data processing methods to streamline the data preparation process even further",
    "Data Wrangler": "Visual, code-free tool for data preprocessing and feature engineering that integrates with AWS data sources. Streamlines data ingestion through a visual interface to profile, understand, clean, and transform data using built-in recipes.",
    "Feature Store": "Managed repository for storing, sharing, and managing features used for ML models.",
    "AWS GLUE": "Fully anaged extract, transform, and load (ETL) service that makes it convenient to prepare and load data for analytics",
    "AWS Glue Data Catalog": "Central repository to store metadata for all of your structured and semi-structured data assets across various data sources."
}

# Limpiamos las claves para usarlas como respuestas (sin espacios, mayúsculas)
RESPUESTAS_LIMPIAS = {
    "MECHANICALTURK": DICCIONARIO_PISTAS["Mechanical Turk"],
    "GROUNDTRUTH": DICCIONARIO_PISTAS["Ground Truth"],
    "DATAWRANGLER": DICCIONARIO_PISTAS["Data Wrangler"],
    "FEATURESTORE": DICCIONARIO_PISTAS["Feature Store"],
    "AWSGLUE": DICCIONARIO_PISTAS["AWS GLUE"],
    "DATACATALOG": DICCIONARIO_PISTAS["AWS Glue Data Catalog"]
}

# --- 2. Diseño Manual del Crucigrama ---
puzzle_layout = [
    (6, 1, 'horizontal', 1, 'MECHANICALTURK'),
    (6, 9, 'vertical', 3, 'AWSGLUE'),
    (0, 2, 'vertical', 2, 'FEATURESTORE'),
    (5, 5, 'vertical', 4, 'DATAWRANGLER'),
    (3, 0, 'horizontal', 5, 'DATACATALOG'),
    (16, 4, 'horizontal', 6, 'GROUNDTRUTH')
]

GRID_ROWS = 18
GRID_COLS = 18
SCORE_FILE = "score_crucigrama.csv"
# --- 3. Funciones Auxiliares ---
    

# ---------- Supabase init ----------
# Lee credenciales seguras desde st.secrets
SUPABASE_URL: str = st.secrets["supabase"]["url"]
SUPABASE_KEY: str = st.secrets["supabase"]["key"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

TABLE_NAME = "scores_crucigrama"  # nombre de la tabla que creaste
# -----------------------------------

def inicializar_estado():
    """Inicializa el estado de la sesión si no existe."""
    if 'grid_state' in st.session_state:
        return
    
    st.session_state.grid_state = [['' for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]
    st.session_state.user_answers = {f"{item[3]}_{item[2]}": "" for item in puzzle_layout}
    st.session_state.correct_answers = {f"{item[3]}_{item[2]}": False for item in puzzle_layout}
    st.session_state.fails = 0
    st.session_state.player_present = False


def generar_cuadricula_html(grid_data):
    """Genera el HTML para mostrar la cuadrícula del crucigrama."""
    active_cells = set()
    cell_numbers = {}

    for r_start, c_start, direction, number, word in puzzle_layout:
        cell_numbers[(r_start, c_start)] = number
        if direction == 'horizontal':
            for i in range(len(word)):
                active_cells.add((r_start, c_start + i))
        else:
            for i in range(len(word)):
                active_cells.add((r_start + i, c_start))
    
    html = "<style> .grid-table { border-collapse: collapse; } .grid-cell { border: 1px solid black; width: 35px; height: 35px; text-align: center; vertical-align: middle; font-size: 18px; position: relative; } .cell-number { position: absolute; top: 1px; left: 1px; font-size: 10px; color: #333; } .black-cell { background-color: #444; }</style>"
    html += "<table class='grid-table'>"
    for r in range(GRID_ROWS):
        html += "<tr>"
        for c in range(GRID_COLS):
            cell_content = grid_data[r][c]
            number_html = f"<span class='cell-number'>{cell_numbers.get((r,c), '')}</span>" if (r, c) in cell_numbers else ""
            if (r, c) in active_cells:
                html += f"<td class='grid-cell'>{number_html}{cell_content}</td>"
            else:
                html += "<td class='grid-cell black-cell'></td>"
        html += "</tr>"
    html += "</table>"
    return html

def revisar_respuestas():
    """Compara las respuestas del usuario (leídas desde session_state) con las correctas."""
    for r_start, c_start, direction, number, word in puzzle_layout:
        key = f"{number}_{direction}"
        # Lee la respuesta del usuario directamente del session_state
        user_answer= st.session_state.user_answers[key].upper().replace(" ", "")
        #user_answer = st.session_state.user_answers[key].upper().replace(" ", "")
        print('Revisando:', key, 'Respuesta del usuario:', user_answer, 'Palabra correcta:', word)

        if user_answer == word:
            st.session_state.correct_answers[key] = True
            # Llenar la cuadrícula con la palabra correcta
            if direction == 'horizontal':
                for i, char in enumerate(word):
                    st.session_state.grid_state[r_start][c_start + i] = char
            else: # vertical
                for i, char in enumerate(word):
                    st.session_state.grid_state[r_start + i][c_start] = char
        else:
            st.session_state.fails += 1
            st.warning(f"Respuesta incorrecta para {key}. Inténtalo de nuevo.")
   

def persist_score() -> None:
    """Guarda la puntuación del jugador en Supabase."""
    player = st.session_state.get("player_name", "").strip()
    if not player:
        return

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    intentos = st.session_state.fails + len(DICCIONARIO_PISTAS)

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


# --- 4. Renderizado de la App en Streamlit ---
def mostrar_crucigrama():
    st.set_page_config( 
        page_title = "Modulo 1.2",
        page_icon= "🧩",
        layout="wide", 
        initial_sidebar_state="expanded"
    )
    st.title("🧩 Crucigrama de Servicios de Datos de AWS")
    st.markdown("Completa el crucigrama con los nombres de los servicios de AWS basándote en las pistas. ¡No uses espacios!")

    inicializar_estado()
    # ---- Sidebar (nombre) ----
    if not st.session_state.player_present:
        with st.sidebar:
            st.header("👤 Jugador")
            jugador = st.text_input("Ingresa tu nombre", key="player_name")
            if st.button("🚀 Empezar Juego"):
                if not jugador:
                    st.error("Por favor, ingresa tu nombre antes de comenzar.")
                    return
                else:
                    st.session_state.player_present = True
                    print('jugador', jugador)
                    print('jugador presente', st.session_state.player_present)
                    st.rerun()
        return
    with st.sidebar:
        st.markdown("---")
        st.subheader("Instrucciones⌨️")
        st.markdown(
            "1. Haz clic en un **❓** para revelar una definición.\n"
            "2. Elige el servicio correcto de la lista.\n"
            "3. Repite hasta acertar todas las definiciones."
        )
    col1, col2 = st.columns([2, 1.5])

    with col1:
        st.header("Crucigrama")
        grid_html = generar_cuadricula_html(st.session_state.grid_state)
        st.markdown(grid_html, unsafe_allow_html=True)

    with col2:
        st.header("Pistas")
        
        with st.form("answers_form"):
            st.subheader("Horizontales")
            for r, c, direction, num, word in sorted(puzzle_layout, key=lambda x: x[3]):
                if direction == 'horizontal':
                    key = f"{num}_{direction}"
                    pista = RESPUESTAS_LIMPIAS[word]
                    icono = "✅" if st.session_state.correct_answers.get(key, False) else ""
                    st.session_state.user_answers[key] = st.text_input(
                        label=f"**{num}.** {pista} {icono}",
                        key=f"user_answers.{key}"
                    )

            st.subheader("Verticales")
            for r, c, direction, num, word in sorted(puzzle_layout, key=lambda x: x[3]):
                if direction == 'vertical':
                    key = f"{num}_{direction}"
                    pista = RESPUESTAS_LIMPIAS[word]
                    icono = "✅" if st.session_state.correct_answers.get(key, False) else ""
                    st.session_state.user_answers[key] = st.text_input(
                        label=f"**{num}.** {pista} {icono}",
                        key=f"user_answers.{key}"
                    )
            
            submit_button = st.form_submit_button(label='Revisar Respuestas')

    if submit_button:
        revisar_respuestas()
        st.rerun()
        if all(st.session_state.correct_answers.values()):
            st.balloons()
            st.success("¡Felicidades! ¡Has completado el crucigrama correctamente!")
            persist_score()

        else:
            st.info("Algunas respuestas correctas se han añadido a la cuadrícula. ¡Sigue intentándolo!")
        st.rerun()

    if st.button("Reiniciar Juego"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        inicializar_estado()
        st.rerun()

        # ---- Tabla de puntuaciones ----
    st.markdown("---")
    st.subheader("🏆 Tabla de puntuaciones")
    st.table(load_scores())
