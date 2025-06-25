import os
import random
import csv
from datetime import datetime

import streamlit as st
import pandas as pd


# -------------------------------------------------
# Datos de servicios y descripciones
# -------------------------------------------------
COLLECT_CARDS = {
    "Data lakes": "Centralized locations that store large amounts of structured, unstructured, and semi-structured",
    "Data warehouses": "Store structured data in relational databases. Optimized for analytical processes",
    "Database": "Store structured data in relational databases. Optimized for transactional processes",
    "Amazon S3": "Highly scalable, available, and redundant object-storage service accessed through an API.",
    "Amazon EBS": "Persistent, block-level storage volumes for Amazon Elastic Compute Cloud (Amazon EC2) instances so you can scale storage performance and cost as needed.",
    "Amazon EFS:": "Designed to grow and shrink automatically as files are added or removed",
    "Amazon FSx:": "Fully managed service that provides access to popular file systems like Lustre, NetApp ONTAP, OpenZFS, and Windows File Server",
}

INGEST_CARDS = {
    "Amazon Kinesis": "Real-time data streaming service that collects, processes, and analyzes real-time data streams",
    "Amazon Kinesis Data Firehose": "Fully managed service that automatically scales and does not require writing any custom application code",
    "Amazon Kinesis Data Streams": "build custom applications for processing real-time data at scale",
    "Amazon MSK": "Fully managed service that makes it convenient for developers to build and run highly available, secure, and scalable applications. "
}

EXTRACT_CARDS = {
    "AWS CLI": "Similar functionality to the graphical AWS Management Console while handling authentication, validation, and formatting.",
    "AWS SDKs": "software toolkits that provides ready-made code packages to extract data",
    "Amazon S3 Transfer Acceleration": "Uses Amazon CloudFront edge locations to accelerate large data transfers to and from Amazon S3",
    "AWS DMS": "AWS Data Migration Service facilitates database migration between databases or to Amazon S3 by extracting data in various formats, such as SQL, JSON, CSV, and XML",
    "AWS Lambda": "Serverless compute service that runs code without provisioning servers, you can run functions with events that extract data from AWS storage services",
    "AWS Glue": "ETL service that prepares and loads data. Can extract data from AWS services and integrate with ML workflows",
    "AWS DataSync": "Transfer data between on-premises systems or AWS services by extracting data from different sources and then upload it to AWS services.",
    "AWS Snowball": "Physical device service used to transfer data in and out of AWS when network transfers are infeasible",
    "AWS Glue": "ETL service that you can use to prepare data for analytics and ML flows",
    "Amazon EMR": "Service for processing and analyzing large datasets using open-source tools of big data analysis.Intefrates data from different sources into one refined platform",
    "Amazon SageMaker Data Wrangler": "Purpose-built data aggregation and preparation toolthat streamlines the process of data preparation and feature engineering"
}


topics = {  "Store" : COLLECT_CARDS,
            "Ingest": INGEST_CARDS,
            "Extract and Merge": EXTRACT_CARDS}

# Configuración
COLS = 3                             # columnas de la cuadrícula de definiciones
SCORE_FILE = "scores.csv"            # archivo local para guardar puntuaciones

# -------------------------------------------------
# Funciones auxiliares
# -------------------------------------------------

def init_game():
    """Prepara un nuevo juego almacenando todo en session_state"""
    SERVICES = st.session_state.selected_cards_set
    descriptions = []
    for svc, desc in SERVICES.items():
        descriptions.append(
            {
                "id": f"{svc}_desc",
                "text": desc,
                "pair": svc,
                "matched": False,
            }
        )
    random.shuffle(descriptions)
    st.session_state.descriptions = descriptions
    st.session_state.selected_desc_idx = None   # índice de descripción actualmente revelada
    st.session_state.matched_pairs = 0
    st.session_state.fails = 0                  # intentos fallidos
    st.session_state.game_over = False
    st.session_state.feedback = ""  # mensaje de acierto/error


def persist_score():
    """Registra la puntuación final en disco (CSV)."""
    SERVICES = st.session_state.selected_cards_set

    player = st.session_state.get("player_name", "").strip()
    if not player:
        return
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    intentos = st.session_state.fails + len(SERVICES)
    with open(SCORE_FILE, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([player,st.session_state.selected_topic_name, intentos, now])


def load_scores() -> pd.DataFrame:
    """Carga las puntuaciones en un DataFrame ordenado."""
    if not os.path.exists(SCORE_FILE):
        return pd.DataFrame(columns=["Jugador", "Tarjeta","Intentos","Fecha"])
    df = pd.read_csv(
        SCORE_FILE, names=["Jugador", "Tarjeta", "Intentos", "Fecha"], dtype={"Jugador": str}
    )
    return df.sort_values(by=["Intentos"], ascending=[True])


# -------------------------------------------------
# Lógica del juego
# -------------------------------------------------

def reveal_description(idx: int):
    """Destapa una carta de definición"""
    if st.session_state.descriptions[idx]["matched"]:
        return
    st.session_state.selected_desc_idx = idx
    st.session_state.feedback = ""  # borra feedback previo
    st.rerun()  # recarga para mostrar la carta revelada


def choose_service(service: str):
    """Comprueba si el servicio elegido coincide con la definición revelada"""
    SERVICES = st.session_state.selected_cards_set

    idx = st.session_state.selected_desc_idx
    if idx is None:
        return
    card = st.session_state.descriptions[idx]
    if card["pair"] == service:
        card["matched"] = True
        st.session_state.matched_pairs += 1
        st.session_state.feedback = "✅ ¡Correcto!"
    else:
        st.session_state.feedback = "❌ Incorrecto. Intenta de nuevo."
        st.session_state.fails += 1
    
    st.session_state.selected_desc_idx = None

    if st.session_state.matched_pairs == len(SERVICES):
        st.session_state.game_over = True
        persist_score()
    st.rerun()  # recarga para actualizar el estado del juego

def render_description_grid():
    """Muestra la cuadrícula de definiciones (ocultas o reveladas)"""
    descs = st.session_state.descriptions
    for i, card in enumerate(descs):
        if i % COLS == 0:
            cols = st.columns(COLS)
        col = cols[i % COLS]

        # decide qué mostrar
        if card["matched"]:
            label = "✔️"  # carta ya completada
            disabled = True
        elif i == st.session_state.selected_desc_idx:
            label = card["text"]  # revelada
            disabled = True  # no se puede volver a hacer clic hasta responder
        else:
            label = "❓"  # oculta
            disabled = False

        if col.button(label, key=f"desc_{i}", disabled=disabled):
            reveal_description(i)


def render_service_buttons():
    """Muestra los botones con nombres de servicios siempre visibles"""
    SERVICES = st.session_state.selected_cards_set

    matched_services = {c["pair"] for c in st.session_state.descriptions if c["matched"]}
    st.markdown("### Selecciona el servicio correspondiente:")
    cols = st.columns(2)
    for i, svc in enumerate(SERVICES.keys()):
        col = cols[i % 2]
        if svc in matched_services:
            label = f"✔️ {svc}"  # ya acertado
            disabled = True
        else:
            label = svc
            disabled = st.session_state.selected_desc_idx is None or st.session_state.game_over
        if col.button(label, key=f"svc_{i}", disabled=disabled):
            choose_service(svc)


# -------------------------------------------------
# Aplicación principal
# -------------------------------------------------

def mostrar_juego():
    st.set_page_config(
        page_title="Modulo 1 AWS – Definiciones",
        page_icon="🂠",
        initial_sidebar_state="expanded"
    )

    # ---- Sidebar (nombre) ----
    with st.sidebar:
        st.header("👤 Jugador")
        jugador = st.text_input("Ingresa tu nombre", key="player_name")
        selected_topic_name = st.selectbox(
        "Selecciona un tipo de tarjetas:",
        list(topics.keys()),
        key="topic_selector")
        st.session_state.selected_cards_set = topics[selected_topic_name]
        st.session_state.selected_topic_name = selected_topic_name
        SERVICES = st.session_state.selected_cards_set

        if st.button("🔄 Nuevo juego"):
            if not jugador:
                st.error("Por favor, ingresa tu nombre antes de comenzar.")
                return
            init_game()
            st.rerun()

        st.markdown("---")
        st.subheader("Instrucciones⌨️")
        st.markdown(
            "1. Haz clic en un **❓** para revelar una definición.\n"
            "2. Elige el servicio correcto de la lista.\n"
            "3. Repite hasta acertar todas las definiciones."
        )

    # ---- Estado inicial ----
    if "descriptions" not in st.session_state:
        st.info("Pulsa **Nuevo juego** para comenzar.")
        st.stop()

    # ---- Feedback de la jugada anterior ----
    if st.session_state.feedback:
        st.write(st.session_state.feedback)

    # ---- Cuadrícula de definiciones ----
    render_description_grid()

    st.markdown("---")

    # ---- Botones de servicios ----
    render_service_buttons()

    # ---- Progreso ----
    st.markdown(
        f"### Progreso: {st.session_state.matched_pairs} / {len(SERVICES)} definiciones acertadas"
    )

    # ---- Fin de juego ----
    if st.session_state.game_over:
        st.balloons()
        st.success("🎉 ¡Juego completado!")
        st.session_state.feedback = ""  # limpia feedback

    # ---- Tabla de puntuaciones ----
    st.markdown("---")
    st.subheader("🏆 Tabla de puntuaciones")
    st.table(load_scores())

