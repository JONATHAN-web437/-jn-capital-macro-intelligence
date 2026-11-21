import streamlit as st

def apply_theme():
    st.markdown("""
    <style>
    .stApp {background: #0b0e13; color: #e7eaf0;}
    [data-testid="stSidebar"] {background: #111722;}
    h1,h2,h3 {color: #dce3ed;}
    .jn-card {border:1px solid #273243; border-radius:12px; padding:16px 18px;
       background:linear-gradient(135deg,#141b26,#0e131b); min-height:115px;}
    .jn-label {color:#9aa8ba; font-size:13px; letter-spacing:1px;}
    .jn-value {color:#e9eef5; font-size:28px; font-weight:650; padding-top:8px;}
    .jn-sub {color:#75869a; font-size:12px; padding-top:4px;}
    </style>
    """,unsafe_allow_html=True)

def metric_card(col,label,value,sub):
    with col:
        st.markdown(f'<div class="jn-card"><div class="jn-label">{label}</div><div class="jn-value">{value}</div><div class="jn-sub">{sub}</div></div>',unsafe_allow_html=True)
