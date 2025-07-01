import os
import json
import random
import streamlit as st
import pandas as pd
from typing import Set, List, Dict, Any
from datetime import datetime
from supabase import create_client, Client


# Lee credenciales seguras desde st.secrets
SUPABASE_URL: str = st.secrets["supabase"]["url"]
SUPABASE_KEY: str = st.secrets["supabase"]["key"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

TABLE_NAME = "scores_quiz"  # nombre de la tabla que creaste
# -----------------------------------

# -----------------------------------------------------------------------------
# HELPERS (LÓGICA DE DATOS)
# Estas funciones pueden vivir fuera de la app principal.
# -----------------------------------------------------------------------------

def get_all_topics(root_dir: str = ".") -> List[str]:
    """Recorre *root_dir* y devuelve una lista ordenada de todos los temas únicos."""
    topics: Set[str] = set()
    for dirpath, _, filenames in os.walk(root_dir):
        for fname in filenames:
            if fname.lower().endswith(".json"):
                fpath = os.path.join(dirpath, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as fp:
                        data = json.load(fp)
                    for q in data.get("questions", []):
                        topic = (q.get("topic") or "").strip().lower()
                        if topic:
                            topics.add(topic)
                except Exception as exc:
                    print(f"[WARN] Omitiendo {fpath} durante escaneo de temas: {exc}")
    return sorted(list(topics))

def load_questions(root_dir: str, selected_topics: Set[str]) -> List[Dict[str, Any]]:
    """Recorre *root_dir* y devuelve una lista barajada de preguntas cuyo
    tema está en *selected_topics*."""
    questions: List[Dict] = []
    if not selected_topics:
        return questions
    for dirpath, _, filenames in os.walk(root_dir):
        for fname in filenames:
            if fname.lower().endswith(".json"):
                fpath = os.path.join(dirpath, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as fp:
                        data = json.load(fp)
                    for q in data.get("questions", []):
                        topic = (q.get("topic") or "").strip().lower()
                        if topic in selected_topics:
                            questions.append(q)
                except Exception as exc:
                    print(f"[WARN] Omitiendo {fpath}: {exc}")
    random.shuffle(questions)
    return questions

def load_scores() -> pd.DataFrame:
    """Carga todas las puntuaciones ordenadas por menos intentos."""
    try:
        resp = supabase.table(TABLE_NAME).select("*").execute()
    except Exception as e:
        st.error(f"No se pudieron cargar las puntuaciones: {e}")
        return pd.DataFrame(columns=["Jugador", "Puntuacion", "Fecha"])

    # Si no hay datos todavía
    if not resp.data:
        return pd.DataFrame(columns=["Jugador", "Puntuacion", "Fecha"])

    df = pd.DataFrame(resp.data)
    df["Jugador"] = df["Jugador"].astype(str)
    return df.sort_values(by="Puntuacion", ascending=False)


def persist_score(player_name: str, score: int, questions_count: int):
    """Guarda la puntuación de un jugador si es su mejor marca."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    intentos = score / questions_count

    data = {
        "Jugador": player_name,
        "Puntuacion": intentos,
        "Fecha": now,
    }

    # Inserta el registro
    try:
        supabase.table(TABLE_NAME).insert(data).execute()
    except Exception as e:
        st.error(f"No se pudo guardar la puntuación: {e}")
    

# -----------------------------------------------------------------------------
# FUNCIÓN PRINCIPAL DE LA APP DE STREAMLIT
# -----------------------------------------------------------------------------

def run_quiz_app():
    """
    Ejecuta la aplicación de quiz de práctica de ML.
    Esta función se puede llamar desde otro script de Streamlit.
    """
    st.set_page_config(page_title="ML Practice Quiz", page_icon="📚")

    # --- INICIALIZACIÓN DEL ESTADO DE SESIÓN ---
    if "game_state" not in st.session_state:
        st.session_state.game_state = {
            "player_name": "",
            "questions": [],
            "q_idx": 0,
            "user_answers": {},
            "score": 0,
            "game_over": False,
            "selected_topics": []
        }

    # --- BARRA LATERAL (SIDEBAR) ---
    st.sidebar.header("👤 Jugador")
    player_name = st.sidebar.text_input(
        "Ingresa tu nombre para empezar",
        value=st.session_state.game_state.get("player_name", "")
    )

    st.sidebar.header("⚙️ Configuración del Quiz")
    root_dir = st.sidebar.text_input("Directorio raíz de preguntas", value=".")
    
    try:
        all_topics = get_all_topics(root_dir)
    except Exception as e:
        st.sidebar.error(f"Error al escanear temas: {e}")
        all_topics = []

    selected_topics = st.sidebar.multiselect(
        "Selecciona los temas a estudiar:",
        options=all_topics,
        default=st.session_state.game_state.get("selected_topics", []),
    )

    if st.sidebar.button("🚀 Empezar Nuevo Quiz", disabled=not player_name or not selected_topics):
        st.session_state.game_state = {
            "player_name": player_name,
            "questions": load_questions(root_dir, set(selected_topics)),
            "q_idx": 0,
            "user_answers": {},
            "score": 0,
            "game_over": False,
            "selected_topics": selected_topics
        }
        st.rerun()

    
    # --- TABLA DE PUNTUACIONES ---
    st.markdown("---")
    st.subheader("🏆 Tabla de puntuaciones")
    st.table(load_scores())

    # --- PANEL PRINCIPAL ---
    st.title("📚 ML Practice Quiz")

    # Acceso a las variables de estado
    gs = st.session_state.game_state

    if not gs["questions"]:
        st.info("👋 ¡Bienvenido! Ingresa tu nombre, selecciona temas y haz clic en 'Empezar Nuevo Quiz' en la barra lateral.")
        st.stop()
        
    if gs["game_over"]:
        st.balloons()
        st.success(f"🎉 ¡Quiz completado, {gs['player_name']}!")
        st.write(f"### Puntuación Final: {gs['score']} / {len(gs['questions'])}")
        st.info("Puedes empezar un nuevo quiz desde la barra lateral.")
        st.stop()

    # --- PANTALLA DE PREGUNTAS ---
    total_qs = len(gs["questions"])
    cur_idx = gs["q_idx"]
    cur_q = gs["questions"][cur_idx]

    # Barra de progreso y puntuación
    progress = len(gs["user_answers"])
    st.progress(progress / total_qs)
    st.write(f"**Jugador:** {gs['player_name']} | **Puntuación:** {gs['score']} | **Pregunta:** {cur_idx + 1}/{total_qs}")
    st.caption(f"**Tema:** *{cur_q.get('topic', 'N/A')}*")
    st.divider()

    st.markdown(cur_q["question"].replace("\n", "  \n"))

    multiple = len(cur_q.get("correct_answers", [])) > 1
    
    # Widget de respuesta (radio o multiselect)
    if multiple:
        user_selection = st.multiselect("Selecciona todas las que apliquen:", cur_q["options"], key=f"sel_{cur_idx}")
    else:
        user_selection = st.radio("Selecciona una:", cur_q["options"], key=f"sel_{cur_idx}", index=None)

    # --- LÓGICA DE SUBMIT Y FEEDBACK ---
    if st.button("Submit", key=f"submit_{cur_idx}"):
        gs["user_answers"][cur_idx] = user_selection
        
        # Calcular si la respuesta es correcta
        correct_set = set(cur_q["correct_answers"])
        user_set = set(user_selection) if isinstance(user_selection, list) else {user_selection}

        if user_set == correct_set:
            gs["score"] += 1 # Solo se suma al enviar, no se puede cambiar
            st.success("¡Correcto! 🥳")
        else:
            st.error("Incorrecto.")
        
        # Marcar la pregunta como respondida para deshabilitar el botón
        st.session_state[f'answered_{cur_idx}'] = True
        #st.rerun()
    
    # Mostrar feedback si ya se respondió
    if cur_idx in gs["user_answers"]:
        st.write("**Respuesta correcta:**")
        for ans in cur_q["correct_answers"]:
            st.markdown(f"- {ans}")
        refs = cur_q.get("references")
        if refs:
            with st.expander("Referencias"):
                for url in refs:
                    st.markdown(f"- {url}")

    st.divider()

    # --- NAVEGACIÓN ---
    col1, col2, col3 = st.columns([1, 6, 1])
    with col1:
        if cur_idx > 0:
            if st.button("⬅️ Back"):
                gs["q_idx"] -= 1
                st.rerun()
    with col3:
        if cur_idx < total_qs - 1:
            if st.button("Next ➡️"):
                gs["q_idx"] += 1
                st.rerun()

    # --- LÓGICA DE FIN DE JUEGO ---
    if len(gs["user_answers"]) == total_qs and not gs["game_over"]:
        persist_score(gs["player_name"], gs["score"],len(gs['questions']))
        gs["game_over"] = True
        st.rerun()

# -----------------------------------------------------------------------------
# EJECUCIÓN (para probar el script de forma independiente)
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    run_quiz_app()