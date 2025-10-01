import streamlit as st
import pandas as pd
from pandasai.llm.base import LLM
from pandasai import SmartDataframe
from groq import Groq
import hashlib
import os
import json
import matplotlib.pyplot as plt
import os

GROQ_KEY = os.environ.get("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY")

# ----------------------------
# User Management Helpers
# ----------------------------
USERS_FILE = "users.json"
#groq_key = "xxxxx"

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# ----------------------------
# LLM Class (Groq + PandasAI)
# ----------------------------
class GroqLLM(LLM):
    def __init__(self, api_key: str, model: str = "openai/gpt-oss-20b", temperature: float = 0.7):
        super().__init__()
        self.client = Groq(api_key=api_key)
        self.model = model
        self.temperature = temperature

    def call(self, instruction, value: str = "", suffix: str = ""):
        prompt = f"""{instruction}
{value}
{suffix}

# If the task requires Python code, output ONLY valid Python code (no explanations).
# If the task requires a direct answer, output ONLY that value.
"""
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature,
        )
        response = completion.choices[0].message.content.strip()

        if response.startswith("```"):
            response = response.strip("`")
            response = response.replace("python", "", 1).strip()
            response = response.replace("return ", "")
            return response

        try:
            evaluated = eval(response, {"__builtins__": {}})
            return evaluated
        except Exception:
            return response

    @property
    def type(self) -> str:
        return "groq"

# ----------------------------
# Streamlit Web App
# ----------------------------
st.set_page_config(page_title="AI Data Insights", layout="wide")

# --- CSS ---
st.markdown("""
    <style>
        body { background-color: #f7f9fc; }
        .main-title { text-align: center; font-size: 2.2rem; font-weight: 700; color: #2c3e50; margin-bottom: 10px; }
        .subtitle { text-align: center; font-size: 1rem; color: #7f8c8d; margin-bottom: 30px; }
        .card { background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

# --- App Header ---
st.markdown("<h1 class='main-title'>📊 AI-Powered Data Insights</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Upload your data, ask questions, and uncover insights instantly.</p>", unsafe_allow_html=True)

# ----------------------------
# Auth System (Login + Signup)
# ----------------------------
users = load_users()

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = None

if not st.session_state.authenticated:
    tab1, tab2 = st.tabs(["🔑 Login", "📝 Signup"])

    with tab1:
        st.subheader("Login")
        username = st.text_input("Username (Login)")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if username in users and users[username] == hash_password(password):
                st.session_state.authenticated = True
                st.session_state.username = username
                st.success("✅ Login successful!")
            else:
                st.error("❌ Invalid credentials")

    with tab2:
        st.subheader("Signup")
        new_user = st.text_input("Choose Username")
        new_pass = st.text_input("Choose Password", type="password")
        if st.button("Signup"):
            if new_user in users:
                st.error("⚠️ Username already exists")
            else:
                users[new_user] = hash_password(new_pass)
                save_users(users)
                st.success("✅ Signup successful! Please login.")

    st.stop()

# ----------------------------
# File Upload
# ----------------------------
with st.container():
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader(f"📂 Upload Dataset (User: {st.session_state.username})")
    uploaded_file = st.file_uploader("Choose a CSV or Excel file", type=["csv", "xlsx"])
    st.markdown("</div>", unsafe_allow_html=True)

if uploaded_file:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    st.success("✅ File uploaded successfully!")
    st.dataframe(df.head(10))

    # Init LLM + SmartDataframe
    #llm = GroqLLM(api_key= "xxxxxx")
    #llm = GroqLLM(api_key=st.secrets["GROQ_API_KEY"])
    # prefer env var (set from Secret Manager), fallback to st.secrets (local dev)
    
    if not GROQ_KEY:
        st.error("GROQ_API_KEY not set. Set in Secret Manager or st.secrets for local dev.")
        st.stop()

    llm = GroqLLM(api_key=GROQ_KEY)
    sdf = SmartDataframe(df, config={"llm": llm})

    # ----------------------------
    # Chat Section
    # ----------------------------
    # if "chat_history" not in st.session_state:
    #     st.session_state.chat_history = []

    # with st.container():
    #     st.markdown("<div class='card'>", unsafe_allow_html=True)
    #     st.subheader("💬 Chat with Your Data")

    #     query = st.text_area("Ask a question:", height=80)

    #     if st.button("Send"):
    #         if query.strip() == "":
    #             st.warning("⚠️ Please type a question.")
    #         else:
    #             with st.spinner("🔎 Thinking..."):
    #                 try:
    #                     answer = sdf.chat(query)
    #                     st.session_state.chat_history.append({"q": query, "a": answer})
    #                 except Exception as e:
    #                     st.error(f"⚠️ Error: {e}")

    #     # Display Chat History
    #     for chat in st.session_state.chat_history:
    #         st.markdown(f"**🧑 You:** {chat['q']}")
    #         st.markdown(f"**🤖 AI:** {chat['a']}")

    #     st.markdown("</div>", unsafe_allow_html=True)
#=================================================================
# ----------------------------
# Chat Section
# ----------------------------
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("💬 Chat with Your Data")

        query = st.text_area("Ask a question:", height=80)

        if st.button("Send"):
            if query.strip() == "":
                st.warning("⚠️ Please type a question.")
            else:
                with st.spinner("🔎 Thinking..."):
                    try:
                        # Get AI answer
                        answer = sdf.chat(query)
                        # Save to history
                        st.session_state.chat_history.append({"q": query, "a": answer})
                    except Exception as e:
                        st.error(f"⚠️ Error: {e}")

        # Display Chat History with formatting
        for chat in st.session_state.chat_history:
            st.markdown(f"**🧑 You:** {chat['q']}")

            ans = chat["a"]

            # 1. If it's a DataFrame → show as table
            if isinstance(ans, pd.DataFrame):
                st.dataframe(ans)

            # 2. If it's a list of dicts → convert to DataFrame and show as table
            elif isinstance(ans, list) and all(isinstance(x, dict) for x in ans):
                st.dataframe(pd.DataFrame(ans))

            # 3. If it's a Pandas Series or numeric list → show chart
            elif isinstance(ans, pd.Series):
                st.line_chart(ans)
            elif isinstance(ans, list) and all(isinstance(x, (int, float)) for x in ans):
                st.line_chart(pd.Series(ans))

            # 4. Fallback → show plain text
            else:
                st.markdown(f"**🤖 AI:** {ans}")

        st.markdown("</div>", unsafe_allow_html=True)


     
        

    # ----------------------------
    # Optional: Auto-Render Tables & Charts
    # ----------------------------
    with st.expander("📊 Generate Visualizations"):
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Table View")
            st.dataframe(df.describe())

        with col2:
            st.subheader("Chart View")
            try:
                df.plot(kind="line", figsize=(6,4))
                st.pyplot(plt)
            except Exception as e:
                st.warning(f"Chart error: {e}")
