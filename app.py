import os
import re
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

st.set_page_config(page_title="LAVO Chat", page_icon="💬", layout="wide")

st.markdown("# LAVO • Chat")
st.caption("Chat Streamlit pronto para GitHub/Cloud. Modo OpenAI + tentativa de embed NotebookLM (se o Google permitir).")

# --- Sidebar
with st.sidebar:
    st.header("Configurações")
    mode = st.radio(
        "Modo de uso",
        ["Chat (OpenAI)", "Tentar embutir NotebookLM (iframe)"],
        help="NotebookLM pode bloquear iframe; se falhar, use o modo Chat."
    )
    nb_link = st.text_input(
        "Link do NotebookLM (opcional)",
        placeholder="https://notebooklm.google.com/notebook/......",
        help="Se o notebook estiver público ('Anyone with the link'), o iframe pode abrir (se não houver bloqueio)."
    )
    sys_prompt = st.text_area(
        "Instruções do assistente (System Prompt)",
        value=(
            "Você é a LAVO, especialista em Reforma Tributária brasileira (IBS/CBS), "
            "SAP B1 e auditoria SPED. Seja claro, técnico e objetivo; cite dispositivos legais quando útil."
        ),
        height=140
    )
    st.divider()
    st.markdown("**API Key**")
    if not OPENAI_API_KEY:
        st.warning("Defina a variável de ambiente OPENAI_API_KEY para habilitar o chat.", icon="⚠️")
    else:
        st.success("OPENAI_API_KEY detectada.", icon="✅")

# --- Estado de conversa
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": sys_prompt}
    ]

def reset_system_prompt():
    # Atualiza o system prompt da conversa atual
    msgs = [m for m in st.session_state.messages if m["role"] != "system"]
    st.session_state.messages = [{"role": "system", "content": sys_prompt}] + msgs

# Se o usuário alterou o prompt, permite reaplicar
apply_prompt = st.sidebar.button("Aplicar novo System Prompt", on_click=reset_system_prompt)

# --- Modo 2: tentativa de embed NotebookLM
if mode == "Tentar embutir NotebookLM (iframe)":
    st.subheader("NotebookLM (iframe)")
    if not nb_link:
        st.info("Cole o link público do seu NotebookLM na barra lateral e deixe este modo selecionado.")
    else:
        # Saneia e valida um formato de URL básico
        if not re.match(r"^https://notebooklm\.google\.com/notebook/[A-Za-z0-9\-]+$", nb_link):
            st.warning("Esse link não parece um link direto de notebook. Verifique se é o URL público do seu notebook.")
        st.markdown(
            "Se o Google bloquear o carregamento por **X-Frame-Options**, você verá uma tela em branco ou erro. "
            "Nesse caso, use o **modo Chat (OpenAI)** abaixo."
        )
        # Tenta incorporar o iframe; se for bloqueado, o navegador que vai impedir
        st.components.v1.iframe(nb_link, height=700, scrolling=True)

    st.divider()
    st.subheader("Chat (OpenAI) — em paralelo")
    st.caption("Mesmo com o iframe, seu chat próprio segue funcionando aqui embaixo.")

# --- Modo 1: Chat OpenAI
st.subheader("Chat com a LAVO (OpenAI)")
user_input = st.chat_input("Digite sua pergunta...")

# Exibe histórico (sem o system)
for m in st.session_state.messages:
    if m["role"] in ("user", "assistant"):
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

def call_openai(messages):
    if not OPENAI_API_KEY:
        st.error("OPENAI_API_KEY não configurada.")
        return None

    client = OpenAI(api_key=OPENAI_API_KEY)

    # Modelo leve e barato para chat contínuo; ajuste conforme seu plano
    model = "gpt-4o-mini"

    # Streaming simples
    stream = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.2,
        stream=True,
    )
    return stream

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_text = ""
        stream = call_openai(st.session_state.messages)
        if stream is None:
            pass
        else:
            try:
                for chunk in stream:
                    delta = chunk.choices[0].delta.content or ""
                    full_text += delta
                    placeholder.markdown(full_text)
            except Exception as e:
                st.error(f"Erro no streaming: {e}")
        st.session_state.messages.append({"role": "assistant", "content": full_text})
