import streamlit as st
import requests

API_URL = "http://localhost:8000/api/v1"

st.set_page_config(page_title="CaseForge UI", page_icon="⚡", layout="wide")
st.title("⚡ CaseForge — AI Case Study Generator")

# ===== FIX: Move User ID to a global sidebar =====
st.sidebar.header("Global Settings")
user_id = st.sidebar.number_input("User ID", value=1, step=1, min_value=1)
st.sidebar.caption(f"Currently acting as User {user_id}")
# =================================================

tab1, tab2, tab3 = st.tabs(["Forge Case", "Evaluate Solution", "History"])

# Tab 1: Generate Case Study
with tab1:
    st.header("Generate a New Business Case")
    col1, col2 = st.columns(2)
    
    with col1:
        industry = st.selectbox("Industry", ["FinTech", "Healthcare", "E-commerce", "SaaS"])
        complexity = st.selectbox("Complexity", ["beginner", "intermediate", "advanced"])
    
    with col2:
        focus_area = st.text_input("Focus Area", "Product Strategy")
        time_limit = st.number_input("Time Limit (mins)", value=60, step=15)
        # user_id removed from here, now globally handled by the sidebar

    if st.button("Forge Case Study", type="primary"):
        with st.spinner("LangGraph is generating your case study..."):
            payload = {
                "user_id": int(user_id),
                "industry": industry,
                "complexity": complexity,
                "focus_area": focus_area,
                "time_limit": int(time_limit)
            }
            res = requests.post(f"{API_URL}/cases/generate", json=payload)
            if res.status_code == 200:
                data = res.json()
                st.success(f"Case Generated: {data.get('title')}")
                st.json(data)
            else:
                st.error(f"Failed to generate case study. Status code: {res.status_code}")

# Tab 2: Evaluate Solution
with tab2:
    st.header("Submit Solution for Evaluation")
    case_id = st.number_input("Case ID", value=1, step=1, min_value=1)
    solution_text = st.text_area("Your Solution", height=200)

    if st.button("Evaluate"):
        with st.spinner("Evaluating with AI..."):
            payload = {
                "user_id": int(user_id),
                "case_id": int(case_id),
                "solution": solution_text
            }
            res = requests.post(f"{API_URL}/solutions/evaluate", json=payload)
            if res.status_code == 200:
                st.success("Evaluation complete!")
                st.json(res.json())
            else:
                st.error(f"Failed to evaluate solution. Status code: {res.status_code}")

# Tab 3: History
with tab3:
    st.header(f"User {user_id} Case History")
    if st.button("Fetch History"):
        # ===== FIX: Use dynamic user_id instead of hardcoded '1' =====
        res = requests.get(f"{API_URL}/users/{int(user_id)}/cases")
        if res.status_code == 200:
            st.json(res.json())
        else:
            st.error(f"Failed to fetch history. Status code: {res.status_code}")