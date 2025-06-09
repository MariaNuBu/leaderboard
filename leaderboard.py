import streamlit as st
import pandas as pd

# --- Configuración de la página ---
# Esto le da un título a la pestaña de tu navegador y un ícono.
st.set_page_config(
    page_title="Leaderboard Focus Group",
    page_icon="🏆",
    layout="centered"
)

# --- Título principal de la aplicación ---
st.title("🏆 Leaderboard del Focus Group AWS")

# --- Carga de datos ---
# Usamos un bloque try-except para manejar el error si el archivo no se encuentra.
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