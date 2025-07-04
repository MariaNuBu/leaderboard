import streamlit as st
import pandas as pd
import card_game
import crucigrama
import sopa_letras
from ExamenesAWS import questions_app

# --- Configuración de la página ---
# Esto le da un título a la pestaña de tu navegador y un ícono.
st.set_page_config(
    page_title="AWS Focus Group",
    page_icon="🏆",
    layout="centered"
)



def leaderboard_view():
    # --- Título principal de la aplicación ---
    st.title("🏆 Leaderboard del Focus Group AWS")
   
    # --- Carga de datos ---
    # Usamos un bloque try-except para manejar el error si el archivo no se encuentra.
    if st.session_state.vista == "leaderboard":
        try:
            # Lee el archivo de Excel. Asegúrate de que esté en la misma carpeta que tu script.
            df = pd.read_csv('puntuaciones.csv')

            # --- Lógica del Leaderboard ---
            # Ordena el DataFrame por 'Preguntas Acertadas' de mayor a menor.
            df_sorted = df.sort_values(by="TOTAL", ascending=False)

            # --- Muestra a los 3 primeros ---
            st.subheader("¡El podio de la semana! 🚀")

            # Encuentra los tres puntajes únicos más altos
            top_scores = df_sorted["TOTAL"].drop_duplicates().head(3).tolist()

            # Diccionario para los lugares y emojis
            podium = {
                0: ("🥇 1er Lugar", "###"),
                1: ("🥈 2do Lugar", "####"),
                2: ("🥉 3er Lugar", "####"),
            }

            for idx, score in enumerate(top_scores):
                personas = df_sorted[df_sorted["TOTAL"] == score]
                nombres = ", ".join(personas["NOMBRES"])
                if idx == 0 and not personas.empty:
                    st.markdown(f"{podium[idx][1]} {podium[idx][0]}: {nombres} con `{score}` aciertos!")
                    st.balloons()
                elif not personas.empty:
                    st.markdown(f"{podium[idx][1]} {podium[idx][0]}: {nombres} con `{score}` aciertos.")

            st.divider() # Una línea para separar secciones

            # --- Muestra la tabla completa ---
            st.header("Clasificación Completa")
            
            # Reiniciamos el índice para que empiece en 1 y lo nombramos 'Posición'
            df_sorted_display = df_sorted.reset_index(drop=True)
            df_sorted_display.index = df_sorted_display.index + 1
            df_sorted_display = df_sorted_display.rename_axis('Posición', axis='index')

            st.dataframe(df_sorted_display, use_container_width=True)

        except FileNotFoundError:
            st.error("⚠️ No se encontró el archivo `puntajes.xlsx`.")
            st.info("Asegúrate de que el archivo de Excel esté en la misma carpeta que el script y tenga las columnas 'Nombre' y 'Preguntas Acertadas'.")

        # Un pequeño pie de página
        st.caption("Hecho con ❤️ ")

def mostrar_juego():
    card_game.mostrar_juego()

def mostrar_juego2():
    crucigrama.mostrar_crucigrama()
def mostrar_juego3():
    sopa_letras.mostrar_sopa_letras()

def mostrar_quiz():
    questions_app.run_quiz_app()

if "vista" not in st.session_state:
    st.session_state.vista = "leaderboard"
# Botón para cargar otro archivo o visualización
# Botones para cambiar la vista (en una fila)
col1, col2 = st.columns(2)
with col1:
    if st.button("🏆 Ver Leaderboard"):
        st.session_state.vista = "leaderboard"
with col2:
    if st.button("📝 Ver Quiz"):
        st.session_state.vista = "quiz"
st.divider()  
row2_col1, row2_col2, row2_col3 = st.columns(3)
with row2_col1:
    if st.button("🃏 Modulo 1.1"):
        st.session_state.vista = "juego"
with row2_col2:
    if st.button("🧩 Modulo 1.2"):
        st.session_state.vista = "juego2"
with row2_col3:
    if st.button("🍲 Modulo 1.3"):
        st.session_state.vista = "juego3"

if st.session_state.vista == "leaderboard":
    leaderboard_view()
elif st.session_state.vista == "juego":
    mostrar_juego()
elif st.session_state.vista == "juego2":
    mostrar_juego2()
elif st.session_state.vista == "juego3":
    mostrar_juego3()
elif st.session_state.vista == "quiz":
    mostrar_quiz()
