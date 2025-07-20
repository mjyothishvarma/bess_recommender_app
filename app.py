import streamlit as st
import re
import pandas as pd
from model import load_dataset, prepare_user_vector
from db import save_feedback
from fpdf import FPDF
import io

# -------------------------------
# 🔐 Basic Validation Functions
# -------------------------------

def is_valid_name(name):
    return bool(re.match(r"^[A-Za-z ]{2,}$", name.strip()))

def is_valid_email(email):
    return bool(re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email.strip()))

# -------------------------------
# 📏 Unit Mapping
# -------------------------------

unit_map = {
    'Capacity': 'Wh',
    'C-Rate': '/hr',
    'Cycle Life': 'cycles',
    'Calender Life': 'years',
    'Battery Size' : 'KWh',
    'Energy Density': 'Wh/kg',
    'DOD': '%',
    'Impedance': 'MΩ',
    'Nominal Voltage': 'V',
    'Nominal Current': 'mA',
    'Weight': 'kg',
    'Length': 'mm',
    'Width': 'mm',
    'Height': 'mm',
    'Min SOC': '%',
    'Max SOC': '%',
    'Min Operating Temperature': '°C',
    'Max Operating Temperature': '°C',
    'Round Trip Efficiency': '%',
    'Stand by Losses': '%/hr',
    'Capital Expenses': 'Rs/kWh',
    'Operating Expenses Per Year': 'Rs/kWh',
}

# -------------------------------
# 🧠 Load Data
# -------------------------------

st.set_page_config(page_title="BESS Recommender", layout="wide")
st.title("Vayumithra's BESS Recommendation System")

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
    'Capacity': st.sidebar.number_input("Capacity (Wh)", value=1000.0),
    'C-Rate': st.sidebar.number_input("C-Rate (/hr)", value=0.5),
    'Cycle Life': st.sidebar.number_input("Cycle Life (cycles)", value=3000),
    'Calender Life': st.sidebar.number_input("Calender Life (years)", value=15)
}

# -------------------------------
# 🧠 Expert Inputs
# -------------------------------

st.sidebar.header("🧠 Expert Inputs")
expert_inputs = {
    'Energy Density': st.sidebar.number_input("Energy Density (Wh/kg)", value=150.0),
    'DOD': st.sidebar.number_input("Depth of Discharge (%)", value=80.0),
    'Impedance': st.sidebar.number_input("Impedance (MΩ)", value=0.02),
    'Nominal Voltage': st.sidebar.number_input("Nominal Voltage (V)", value=3.7),
    'Nominal Current': st.sidebar.number_input("Nominal Current (mA)", value=2000.0),
    'Weight': st.sidebar.number_input("Weight (kg)", value=2500.0),
    'Length': st.sidebar.number_input("Length (mm)", value=2000.0),
    'Width': st.sidebar.number_input("Width (mm)", value=1200.0),
    'Height': st.sidebar.number_input("Height (mm)", value=1500.0),
    'Min SOC': st.sidebar.number_input("Min SOC (%)", value=20.0),
    'Max SOC': st.sidebar.number_input("Max SOC (%)", value=80.0),
    'Min Operating Temperature': st.sidebar.number_input("Min Temp (°C)", value=-20.0),
    'Max Operating Temperature': st.sidebar.number_input("Max Temp (°C)", value=60.0),
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
            unit = unit_map.get(col, "")
            st.markdown(f"- **{col}**: {rec_row[col]} {unit}")

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
    rec_number = 0
    for i, row in recs.iterrows():
        rec_number += 1
        st.markdown(f"""#### 🔋 Recommendation {rec_number} (Similarity: {round(row['similarity'], 2)})""")

        important_fields = ['Manufacturer', 'Capacity', 'C-Rate', 'Cycle Life', 'Energy Density', 'DOD']
        display_fields = []
        for col in important_fields:
            val = row.get(col, 'N/A')
            unit = unit_map.get(col, "")
            display_fields.append(f"**{col}**: {val} {unit}")
        st.markdown(" | ".join(display_fields))

        with st.expander("🔎 View Full Battery Specifications"):
            for col in row.index:
                unit = unit_map.get(col, "")
                st.markdown(f"- **{col}**: {row[col]} {unit}")

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

   
    def generate_pdf(user_name, user_email, input_data, recs, feedback, comment):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        pdf.cell(200, 10, txt="Battery Energy Storage System (BESS) Report", ln=True, align="C")
        pdf.ln(10)

        pdf.cell(200, 10, txt=f"Name: {user_name}", ln=True)
        pdf.cell(200, 10, txt=f"Email: {user_email}", ln=True)
        pdf.ln(10)

        pdf.cell(200, 10, txt="Input Specifications:", ln=True)
        for key, value in input_data.items():
            pdf.cell(200, 10, txt=f"{key}: {value}", ln=True)
        pdf.ln(10)

        pdf.cell(200, 10, txt="Recommendations:", ln=True)
        for key, value in recs.items():  # 🔁 Use .items() instead of enumerate()
            pdf.cell(200, 10, txt=f"{key}: {value}", ln=True)
        pdf.ln(10)

        pdf.cell(200, 10, txt="User Feedback:", ln=True)
        for i, f in enumerate(feedback, 1):
            pdf.cell(200, 10, txt=f"{i}. {f}", ln=True)
        pdf.ln(10)

        pdf.cell(200, 10, txt="Overall Comment:", ln=True)
        pdf.multi_cell(0, 10, txt=comment)

        # Save to BytesIO
        pdf_buffer = io.BytesIO()
        pdf_bytes = pdf.output(dest='S').encode('latin1')
        pdf_buffer.write(pdf_bytes)
        pdf_buffer.seek(0)

        return pdf_buffer

    pdf_file = generate_pdf(user_name, user_email, cleaned_input, recs, user_feedback, global_comment)

    st.download_button(
        label="📄 Download Report as PDF",
        data=pdf_file,
        file_name="bess_report.pdf",
        mime="application/pdf"
    )
    


