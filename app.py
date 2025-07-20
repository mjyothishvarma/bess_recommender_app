import streamlit as st
import pandas as pd
import re
from model import load_dataset, prepare_user_vector
from db import save_feedback

# -------------------------------
# 🔐 Basic Validation Functions
# -------------------------------

def is_valid_name(name):
    return bool(re.match(r"^[A-Za-z ]{2,}$", name.strip()))

def is_valid_email(email):
    return bool(re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email.strip()))

# -------------------------------
# 🧠 Load Data
# -------------------------------

st.set_page_config(page_title="BESS Recommender", layout="wide")
st.title("🔋 BESS Recommendation System")

df = load_dataset("Bess_data_final.csv")

# -------------------------------
# 👤 User Info Section
# -------------------------------

st.sidebar.header("👤 User Information")
user_name = st.sidebar.text_input("Full Name")
user_email = st.sidebar.text_input("Email Address")

if not is_valid_name(user_name):
    st.sidebar.error("Please enter a valid name (letters only).")
if not is_valid_email(user_email):
    st.sidebar.error("Please enter a valid email address.")

if not (is_valid_name(user_name) and is_valid_email(user_email)):
    st.warning("Enter valid name and email to proceed.")
    st.stop()

# -------------------------------
# 🔧 Basic Inputs
# -------------------------------

st.sidebar.header("🔧 Basic Inputs")
basic_inputs = {
    'Capacity': st.sidebar.number_input("Capacity", value=1000.0),
    'C-Rate': st.sidebar.number_input("C-Rate", value=0.5),
    'Cycle Life': st.sidebar.number_input("Cycle Life", value=3000),
    'Calender Life': st.sidebar.number_input("Calender Life", value=15)
}

# -------------------------------
# 🧠 Expert Inputs
# -------------------------------

st.sidebar.header("🧠 Expert Inputs")
expert_inputs = {
    'Energy Density': st.sidebar.number_input("Energy Density", value=150.0),
    'DOD': st.sidebar.number_input("Depth of Discharge", value=80.0),
    'Impedance': st.sidebar.number_input("Impedance", value=0.02),
    'Nominal Voltage': st.sidebar.text_input("Nominal Voltage", value=''),
    'Nominal Current': st.sidebar.text_input("Nominal Current", value=''),
    'Weight': st.sidebar.text_input("Weight", value=''),
    'Length': st.sidebar.text_input("Length", value=''),
    'Width': st.sidebar.text_input("Width", value=''),
    'Height': st.sidebar.number_input("Height", value=1500.0),
    'Min SOC': st.sidebar.number_input("Min SOC", value=20.0),
    'Max SOC': st.sidebar.number_input("Max SOC", value=80.0),
    'Min Operating Temperature': st.sidebar.number_input("Min Temp", value=-20.0),
    'Max Operating Temperature': st.sidebar.number_input("Max Temp", value=60.0),
}

# -------------------------------
# 🔍 Recommendation Details View
# -------------------------------

if "selected_rec_id" in st.session_state:
    rec_id = st.session_state.selected_rec_id
    if "recs" in st.session_state and rec_id < len(st.session_state.recs):
        rec_row = st.session_state.recs.iloc[rec_id]
        st.title(f"🔍 Details of Recommendation #{rec_id + 1}")
        st.markdown("### Full Battery Specification:")

        for col in rec_row.index:
            st.markdown(f"- **{col}**: {rec_row[col]}")

        if st.button("⬅️ Back to Recommendations"):
            del st.session_state.selected_rec_id
            st.session_state.show_recs = True
            st.rerun()
        st.stop()
    else:
        st.error("❌ Invalid recommendation selected.")
        del st.session_state.selected_rec_id
        st.stop()

# -------------------------------
# 🔎 Generate Recommendations
# -------------------------------

if st.button("🔍 Get Recommendations"):
    with st.spinner("Calculating recommendations..."):
        recs, cleaned_input = prepare_user_vector(df, basic_inputs, expert_inputs)
        st.session_state.recs = recs
        st.session_state.cleaned_input = cleaned_input
        st.session_state.show_recs = True

# -------------------------------
# 📋 Show Recommendations
# -------------------------------

if st.session_state.get("show_recs", False):
    st.subheader("📋 Top 10 Recommendations")
    recs = st.session_state.recs
    cleaned_input = st.session_state.cleaned_input
    user_feedback = []

    for i, row in recs.iterrows():
        st.markdown(f"""#### 🔋 Recommendation #{i+1} (Similarity: {round(row['similarity'], 2)})""")
        important_fields = ['Manufacturer', 'Capacity', 'C-Rate', 'Cycle Life', 'Energy Density', 'DOD']
        st.markdown(" | ".join([f"**{col}**: {row.get(col, 'N/A')}" for col in important_fields if col in row]))

        with st.expander("🔎 View Full Battery Specifications"):
            for col in row.index:
                st.markdown(f"- **{col}**: {row[col]}")

        rating = st.slider(f"Your Rating", 1, 5, 3, key=f"rate_{i}")
        comment = st.text_area("Comments", key=f"comment_{i}")
        user_feedback.append({
            "index": i,
            "similarity": round(row['similarity'], 2),
            "rating": rating,
            "comment": comment
        })

    global_comment = st.text_area("📝 Additional Comments (overall)", key="global_comment")

    if st.button("📩 Submit Feedback"):
        save_feedback(
            cleaned_input=cleaned_input,
            recommendations=recs,
            user_feedback=user_feedback,
            global_comment=global_comment,
            user_name=user_name,
            user_email=user_email
        )
        st.success("✅ Feedback submitted successfully!")
