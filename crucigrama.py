
import streamlit as st
import pandas as pd

# --- 1. Definición de Datos y Configuración Inicial ---

# Diccionario original con las pistas
DICCIONARIO_PISTAS = {
    "Mechanical Turk": "access to an on-demand global workforce to quickly complete data transformation microtasks at low cost, streamlining the overall process by decomposing workflows into discrete tasks",
    "Ground Truth": "service that uses Mechanical Turk and other data processing methods to streamline the data preparation process even further",
    "Data Wrangler": "visual, code-free tool for data preprocessing and feature engineering that integrates with AWS data sources. streamlines data ingestion through a visual interface to profile, understand, clean, and transform data using built-in recipes. It connects to sources, transforms, cleans, and loads data.",
    "Feature Store": "managed repository for storing, sharing, and managing features used for ML models.",
    "AWS GLUE": "fully managed extract, transform, and load (ETL) service that makes it convenient to prepare and load data for analytics",
    "AWS Glue Data Catalog": "central repository to store metadata for all of your structured and semi-structured data assets across various data sources."
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

# --- 3. Funciones Auxiliares ---

def inicializar_estado():
    """Inicializa el estado de la sesión si no existe."""
    if 'grid_state' not in st.session_state:
        st.session_state.grid_state = [['' for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]
        st.session_state.user_answers = {f"{item[3]}_{item[2]}": "" for item in puzzle_layout}
        st.session_state.correct_answers = {f"{item[3]}_{item[2]}": False for item in puzzle_layout}

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
            


# --- 4. Renderizado de la App en Streamlit ---
def mostrar_crucigrama():
    st.set_page_config(layout="wide")
    st.title("🧩 Crucigrama de Servicios de Datos de AWS")
    st.markdown("Completa el crucigrama con los nombres de los servicios de AWS basándote en las pistas. ¡No uses espacios!")

    inicializar_estado()

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
        if all(st.session_state.correct_answers.values()):
            st.balloons()
            st.success("¡Felicidades! ¡Has completado el crucigrama correctamente!")
        else:
            st.info("Algunas respuestas correctas se han añadido a la cuadrícula. ¡Sigue intentándolo!")
        st.rerun()

    if st.button("Reiniciar Juego"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
