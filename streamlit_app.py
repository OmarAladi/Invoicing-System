# pip install streamlit streamlit-lottie

import streamlit as st
import requests
import base64
import pandas as pd
from streamlit_lottie import st_lottie

# Page configuration
st.set_page_config(page_title="Invoice Processor", layout="wide", page_icon="🧾")

# Load Lottie animation for header
@st.cache_data(show_spinner=False)
def load_lottie_url(url: str):
    try:
        r = requests.get(url)
        if r.status_code == 200:
            return r.json()
    except Exception:
        return None
    return None

lottie_header = load_lottie_url("https://assets10.lottiefiles.com/packages/lf20_jmehmyzz.json")
if lottie_header:
    st_lottie(lottie_header, height=200, key="header_anim")

# CSS for fade-in animation and colored sections
st.markdown(
    """
    <style>
    @keyframes fadeIn { from {opacity: 0;} to {opacity: 1;} }
    .title {
        text-align: center;
        background: linear-gradient(to right, #4facfe, #00f2fe);
        color: white;
        padding: 20px;
        border-radius: 10px;
        animation: fadeIn 2s;
    }
    .section {
        background-color: #f0f8ff;
        padding: 15px;
        border-radius: 10px;
        animation: fadeIn 1.5s;
    }
    </style>
    """, unsafe_allow_html=True
)

# Attractive title
st.markdown('<h1 class="title">🧾 Invoice Processor</h1>', unsafe_allow_html=True)

# Warning for single invoice upload
st.warning("⚠️ This system accepts only one invoice image at a time.", icon="⚠️")

# File uploader (single file)
uploaded_file = st.file_uploader(
    label="Upload Invoice Image",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=False
)

if uploaded_file:
    # Show processing animation
    with st.spinner("Processing your invoice, please wait..."):
        # Convert image to base64
        img_bytes = uploaded_file.read()
        img_b64 = base64.b64encode(img_bytes).decode()
        payload = {"image": f"data:image/jpeg;base64,{img_b64}"}
        try:
            # Call backend API
            response = requests.post(
                "http://localhost:8000/api/multiple-invoice",
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            data = response.json().get("data", {})
        except Exception as e:
            st.error(f"Error during processing: {e}")
            st.stop()

    # Layout: 2/3 for table, 1/3 for image
    col1, col2 = st.columns([2, 1])

    # Invoice details table
    with col1:
        st.markdown('<div class="section">', unsafe_allow_html=True)
        st.subheader("Invoice Details")
        invoice_date = data.get("date", "-")
        st.markdown(f"**Date:** {invoice_date}")
        products = data.get("products", [])
        if products:
            df = pd.DataFrame(products)
            df = df.rename(columns={
                "Item_ID": "Item ID",
                "Item_Description": "Description",
                "Unit_Price": "Unit Price",
                "Quantity": "Quantity",
                "Tax": "Tax",
                "Total_Amount": "Total Amount"
            })
            st.dataframe(df, use_container_width=True)
        else:
            st.write("No products found.")
        st.markdown('</div>', unsafe_allow_html=True)

    # Invoice image display
    with col2:
        st.markdown('<div class="section">', unsafe_allow_html=True)
        st.subheader("Invoice Image")
        st.image(uploaded_file, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

# streamlit run streamlit_app.py
