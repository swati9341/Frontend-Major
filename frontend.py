import streamlit as st
import streamlit_shadcn_ui as st_shadcn_ui
import requests
import os
import json # Added for JSON serialization
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="Invoice System", layout="wide")


# -----------------------------
# Session State
# -----------------------------
if "token" not in st.session_state:
    st.session_state.token = None

if "user_name" not in st.session_state:
    st.session_state.user_name = "User"   # later you can fetch from backend (/me)

if "user_id" not in st.session_state: # Add user_id to session state
    st.session_state.user_id = None


# -----------------------------
# Helpers
# -----------------------------
def auth_headers():
    if not st.session_state.token:
        return {}
    return {"Authorization": f"Bearer {st.session_state.token}"}


def fetch_templates():
    try:
        res = requests.get(f"{BACKEND_URL}/templates/", headers=auth_headers())
        if res.status_code == 200:
            return res.json()
        else:
            st.error(f"Error fetching templates: {res.text}")
        return []
    except Exception as e:
        st.error(f"Error fetching templates: {e}")
        return []

def fetch_invoice_items():
    """Fetch invoice items for the logged-in user."""
    try:
        if not st.session_state.user_id:
            return []

        res = requests.get(
            f"{BACKEND_URL}/invoice_items/",
            params={"user_id": st.session_state.user_id},
            headers=auth_headers()
        )


        if res.status_code == 200:
            return res.json()
        else:
            st.error(f"Error fetching invoice items: {res.text}")
        return []

    except Exception as e:
        st.error(f"Error fetching invoice items: {e}")
        return []

def fetch_demo_invoices():
    """Fetches demo invoices from the backend."""
    try:
        if not st.session_state.user_id:
            return []
        res = requests.get(f"{BACKEND_URL}/demo/invoice/{st.session_state.user_id}", headers=auth_headers())
        if res.status_code == 200:
            return res.json()
        else:
            st.warning(f"No demo invoices found for this user")
        return []
    except Exception as e:
        st.warning(f"Demo invoices not available: {e}")
        return []

# -----------------------------
# LOGIN/SIGNUP UI
# -----------------------------
def auth_ui():
    st.title("Invoice System - Login/Signup")

    tab1, tab2 = st.tabs(["Login", "Signup"])

    with tab1:
        st.header("Login")
        email = st_shadcn_ui.input("Email", key="login_email")
        password = st_shadcn_ui.input("Password", type="password", key="login_password")

        if st_shadcn_ui.button("Login", key="login_button"):
            try:
                response = requests.post(
                    f"{BACKEND_URL}/auth/login",
                    json={"email": email, "password": password}
                )
                if response.status_code == 200:
                    data = response.json()
                    st.session_state.token = data["access_token"]
                    # Assuming the backend returns user_id upon successful login
                    # You might need to adjust this based on your actual backend response
                    st.session_state.user_id = data.get("user_id") # Store user_id
                    st.session_state.user_name = email.split("@")[0].title()

                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid credentials")
            except Exception as e:
                st.error(f"Error: {e}")

    with tab2:
        st.header("Signup")
        name = st_shadcn_ui.input("Name", key="signup_name")
        email = st_shadcn_ui.input("Email", key="signup_email")
        phone = st_shadcn_ui.input("Phone", key="signup_phone")
        password = st_shadcn_ui.input("Password", type="password", key="signup_password")
        confirm_password = st_shadcn_ui.input("Confirm Password", type="password", key="signup_confirm")

        if st_shadcn_ui.button("Signup", key="signup_button"):
            if password != confirm_password:
                st.error("Passwords do not match!")
            else:
                try:
                    response = requests.post(
                        f"{BACKEND_URL}/auth/register",
                        json={
                            "name": name,
                            "email": email,
                            "phone": phone,
                            "password": password
                        }
                    )
                    if response.status_code == 200:
                        st.success("Signup successful! Now login.")
                    else:
                        st.error(f"Signup failed: {response.text}")
                except Exception as e:
                    st.error(f"Error: {e}")


# -----------------------------
# DASHBOARD UI
# -----------------------------
def dashboard_ui():
    # Top header row
    col1, col2 = st.columns([8, 2])

    with col1:
        st.markdown(f"## Hi, **{st.session_state.user_name}** 👋")
        st.caption("Welcome back! Manage invoices and create new ones easily.")

    with col2:
        if st_shadcn_ui.button("Logout", key="logout_btn"):
            st.session_state.token = None
            st.session_state.user_name = "User"
            st.session_state.user_id = None # Clear user_id on logout
            st.rerun()

    st.divider()

    tab1, tab2 = st.tabs(["📄 Your Invoices", "➕ Create New Invoice"])

    # -----------------------------
    # TAB 1: Your Invoices
    # -----------------------------
    with tab1:
        st.subheader("Your Invoices")

        colA, colB = st.columns([3, 2])
        with colA:
            search = st.text_input("Search invoice (Invoice No / Customer)")
        with colB:
            filter_value = st.selectbox("Filter", ["All", "This Month", "Last 30 Days"])

        # Fetch invoice items
        invoice_items = fetch_invoice_items()
        
        if not invoice_items:
            st.info("No invoices found. Create one in the 'Create New Invoice' tab.")
        else:
            # Display invoice items with created_at column
            st.markdown("### Invoice Items")
            
            for item in invoice_items:
                col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
                
                with col1:
                    st.write(f"**ID:** {item['id']}")
                
                with col2:
                    st.write(f"**created_at:** {item.get('created_at', 'N/A')}")
                
                with col3:
                    st.write(f"**Template:** {item.get('template_name', 'N/A')}")
                
                with col4:
                    if st.button("📥 PDF", key=f"pdf_download_{item['id']}", help="Download invoice as PDF"):
                        try:
                            response = requests.get(
                                f"{BACKEND_URL}/invoice_items/{item['id']}/pdf",
                                headers=auth_headers(),
                                stream=True
                            )
                            if response.status_code == 200:
                                st.download_button(
                                    label="Download PDF",
                                    data=response.content,
                                    file_name=f"invoice_{item['id']}.pdf",
                                    mime="application/pdf",
                                    key=f"download_{item['id']}"
                                )
                            else:
                                st.error(f"Error generating PDF: {response.text}")
                        except Exception as e:
                            st.error(f"Error: {e}")
        
        st.caption("✅ Click PDF button to download invoice as PDF")

    # -----------------------------
    # TAB 2: Create New Invoice (From Template)
    # -----------------------------
    with tab2:
        st.subheader("Create New Invoice")

        templates = fetch_templates()

        if not templates:
            st.warning("No templates found. Create templates using /templates/create API.")
            st.stop()

        template_map = {t["template_name"]: t for t in templates}
        selected_template_name = st.selectbox("Select Template", list(template_map.keys()))
        selected_template = template_map[selected_template_name]

        st.markdown("### Template Info")
        st.write("**Template Type:**", selected_template["type"])
        st.write("**Mandatory Params:**", selected_template["mandatory_params"])

        st.divider()

        st.markdown("### Enter Invoice Details")

        input_data = {}
        for param in selected_template["mandatory_params"]:
            label = param.replace("_", " ").title()
            input_data[param] = st.text_input(f"{label}", key=f"param_{param}")

        colP1, colP2 = st.columns([2, 2])

        with colP1:
            if st.button("Preview Template HTML"):
                st.code(selected_template["html_content"], language="html")

        with colP2:
            if st.button("Generate Invoice ✅"):
                payload = {
                    "invoice_id": selected_template["id"],
                    "userId": st.session_state.user_id,
                    "description": f"Invoice item from template '{selected_template_name}' with details: {json.dumps(input_data)}",
                    "data": json.dumps(input_data)
                }

                if not st.session_state.user_id:
                    st.error("User ID not available. Please log in again.")
                    st.stop()

                try:
                    response = requests.post(
                        f"{BACKEND_URL}/invoice_items/",
                        json=payload,
                        headers=auth_headers()
                    )
                    if response.status_code == 201:
                        st.success("Invoice generated successfully!")
                        st.json(response.json())
                    else:
                        st.error(f"Error generating invoice: {response.text}")
                except Exception as e:
                    st.error(f"Error: {e}")


# -----------------------------
# Main Entry
# -----------------------------
if not st.session_state.token:
    auth_ui()
else:
    dashboard_ui()
