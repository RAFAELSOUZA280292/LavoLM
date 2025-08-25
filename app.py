import os
import re
import time
import streamlit as st
from dotenv import load_dotenv

# --- (Opcional) Gemini: só se quiser chat local sem NotebookLM ---
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except Exception:
    GEMINI_AVAILABLE = False

load_dotenv()

st.set_page_config(page_title="LAVO • NotebookLM Embed", page_icon="📒", layout="wide")

st.markdown("## LAVO • NotebookLM")
st.caption("App Streamlit (GitHub/Cloud) focado em **embed** do NotebookLM. Sem ChatGPT. 😉")

with st.sidebar:
    st.header("Configurações")
    nb_link = st.text_input(
        "Link público do NotebookLM",
        placeholder="https://notebooklm.google.com/notebook/865b4bd0-...",
        help="No NotebookLM: Share → Anyone with the link. (Consumo com conta Google; embed pode ser bloqueado pelo próprio Google.)"
    )
    st.markdown("---")
    use_gemini = st.toggle("Habilitar aba de Chat com Gemini (opcional)", value=False,
                           help="Não é o NotebookLM, mas permite ter um chat no mesmo app sem usar ChatGPT.")

# ------------ Validação simples do link ------------
def looks_like_notebooklm_url(url: str) -> bool:
    if not url:
        return False
    return bool(re.match(r"^https://notebooklm\.google\.com/notebook/[A-Za-z0-9\-]+$", url.strip()))

# ------------ Abas: Embed + (opcional) Gemini Chat ------------
tabs = ["NotebookLM"]
if use_gemini:
    tabs.append("Chat (Gemini)")
tab = st.tabs(tabs)

# ------------------ TAB: NOTEBOOKLM ------------------
with tab[0]:
    st.subheader("NotebookLM (tentativa de incorporação)")
    if not nb_link:
        st.info("Cole o link público do seu notebook na barra lateral para tentar o embed.")
    else:
        good = looks_like_notebooklm_url(nb_link)
        if not good:
            st.warning("O link não parece ser um URL direto do NotebookLM. Verifique se está no formato correto.")
        # Explicação rápida sobre políticas de frame
        with st.expander("⚠️ Por que o embed pode falhar?"):
            st.write(
                "Muitos serviços (incluindo Google) usam cabeçalhos de segurança como "
                "`X-Frame-Options`/`frame-ancestors` para **impedir** que a página seja exibida "
                "em iframes de outros domínios (anti-clickjacking). Se isso estiver ativo, o seu "
                "navegador bloqueará o carregamento, e veremos uma tela em branco ou erro."
            )

        # Tenta o iframe; se houver bloqueio, o navegador impedirá (não há como detectar 100%)
        st.components.v1.iframe(nb_link, height=760, scrolling=True)

        st.divider()
        st.subheader("Acesso direto (fallback)")
        st.write(
            "Se o embed estiver bloqueado, use o link abaixo para abrir o NotebookLM em uma nova aba."
        )
        st.link_button("🔗 Abrir NotebookLM em nova aba", nb_link, use_container_width=True)

        st.caption(
            "Dica: confirme no NotebookLM → **Share** se está como **Anyone with the link**. "
            "O compartilhamento público existe, mas o Google pode manter o bloqueio de iframe."
        )

# ------------------ TAB: GEMINI (opcional) ------------------
if use_gemini:
    with tab[1]:
        st.subheader("Chat local com Gemini (Google) — opcional")
        st.caption("Não é o NotebookLM, mas permite conversar no app sem usar ChatGPT.")

        GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
        if not GEMINI_AVAILABLE:
            st.error("Pacote google-generativeai não disponível. Verifique o requirements.txt.")
        elif not GEMINI_API_KEY:
            st.warning("Defina a variável de ambiente GEMINI_API_KEY para habilitar o chat com Gemini.")
        else:
            genai.configure(api_key=GEMINI_API_KEY)
            model_name = st.selectbox("Modelo", ["gemini-1.5-flash", "gemini-1.5-pro"], index=0)
            system_prompt = st.text_area(
                "Instruções do assistente",
                value="Você é a LAVO, especialista em Reforma Tributária (IBS/CBS) e auditorias fiscais.",
                height=120
            )

            if "gemini_history" not in st.session_state:
                st.session_state.gemini_history = []

            # Render histórico
            for role, content in st.session_state.gemini_history:
                with st.chat_message(role):
                    st.markdown(content)

            user_text = st.chat_input("Digite sua mensagem para o Gemini…")
            if user_text:
                st.session_state.gemini_history.append(("user", user_text))
                with st.chat_message("user"):
                    st.markdown(user_text)

                try:
                    model = genai.GenerativeModel(model_name, system_instruction=system_prompt)
                    # Gera resposta
                    with st.chat_message("assistant"):
                        placeholder = st.empty()
                        # Streaming “manual”: chama e imprime com pequeno delay (SDK não tem stream nativo estável)
                        resp = model.generate_content(user_text)
                        text = resp.text or ""
                        buf = ""
                        for ch in text:
                            buf += ch
                            placeholder.markdown(buf)
                            time.sleep(0.001)
                    st.session_state.gemini_history.append(("assistant", text))
                except Exception as e:
                    st.error(f"Erro ao chamar Gemini: {e}")
