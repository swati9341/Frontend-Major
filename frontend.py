import streamlit as st
import streamlit_shadcn_ui as st_shadcn_ui
import requests
import os
import json # Added for JSON serialization
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@invoicesystem.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

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

if "current_page" not in st.session_state:
    st.session_state.current_page = 1

if "is_admin" not in st.session_state:
    st.session_state.is_admin = False


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

def create_template(template_data):
    """Create a new invoice template."""
    try:
        response = requests.post(
            f"{BACKEND_URL}/templates/create",
            json=template_data
        )
        return response
    except Exception as e:
        st.error(f"Error creating template: {e}")
        return None

# -----------------------------
# LOGIN/SIGNUP UI
# -----------------------------
def auth_ui():
    st.title("Invoice System - Login/Signup")

    # Login Type Selection (Admin vs User)
    login_type = st.radio("Select Login Type", ["User", "Admin"], horizontal=True)
    st.divider()

    if login_type == "User":
        tab1, tab2 = st.tabs(["Login", "Signup"])

        with tab1:
            st.header("User Login")
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
                        st.session_state.is_admin = False

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

    else:  # Admin Login
        st.header("Admin Login")
        st.info("🔐 Admin access requires special credentials.")
        
        admin_email = st_shadcn_ui.input("Admin Email", key="admin_email")
        admin_password = st_shadcn_ui.input("Admin Password", type="password", key="admin_password")

        if st_shadcn_ui.button("Admin Login", key="admin_login_button"):
            # Verify admin credentials against env variables
            if admin_email == ADMIN_EMAIL and admin_password == ADMIN_PASSWORD:
                st.session_state.token = "admin_token"  # Set a simple admin token
                st.session_state.user_name = "Admin"
                st.session_state.is_admin = True
                st.session_state.user_id = None  # Admin doesn't have user_id
                
                st.success("Admin login successful!")
                st.rerun()
            else:
                st.error("Invalid admin credentials")


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
            st.session_state.current_page = 1
            st.rerun()

    st.divider()

    tab1, tab2 = st.tabs(["📄 Your Invoices", "➕ Create New Invoice"])

    # -----------------------------
    # TAB 1: Your Invoices
    # -----------------------------
    with tab1:
        st.subheader("Your Invoices")

        colA, colB, colC = st.columns([3, 2, 1])
        with colA:
            search = st.text_input("Search invoice (Invoice No / Customer)")
        with colB:
            filter_value = st.selectbox("Filter", ["All", "This Month", "Last 30 Days"])
        with colC:
            if st_shadcn_ui.button("🔄 Refresh", key="refresh_invoices"):
                st.rerun()

        # Fetch invoice items
        invoice_items = fetch_invoice_items()
        
        if not invoice_items:
            st.info("No invoices found. Create one in the 'Create New Invoice' tab.")
        else:
            # Pagination logic
            ITEMS_PER_PAGE = 5
            total_items = len(invoice_items)
            total_pages = (total_items - 1) // ITEMS_PER_PAGE + 1
            
            if st.session_state.current_page > total_pages:
                st.session_state.current_page = total_pages
                
            start_idx = (st.session_state.current_page - 1) * ITEMS_PER_PAGE
            end_idx = start_idx + ITEMS_PER_PAGE
            paged_items = invoice_items[start_idx:end_idx]

            # Display invoice items with created_at column
            st.markdown("### Invoice Items")
            
            for item in paged_items:
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
        
        if invoice_items:
            # Pagination Controls
            st.divider()
            col_prev, col_info, col_next = st.columns([1, 8, 1])
            with col_prev:
                if st.button("⬅️ Prev", disabled=(st.session_state.current_page <= 1)):
                    st.session_state.current_page -= 1
                    st.rerun()
            with col_info:
                st.markdown(f"<div style='text-align: center;'>Page {st.session_state.current_page} of {total_pages}</div>", unsafe_allow_html=True)
            with col_next:
                if st.button("Next ➡️", disabled=(st.session_state.current_page >= total_pages)):
                    st.session_state.current_page += 1
                    st.rerun()

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
                    "data": input_data
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
# ADMIN DASHBOARD UI
# -----------------------------
def admin_dashboard_ui():
    # Top header row
    col1, col2 = st.columns([8, 2])

    with col1:
        st.markdown(f"## 👨‍💼 **Admin Dashboard**")
        st.caption("Manage invoice templates and system configuration.")

    with col2:
        if st_shadcn_ui.button("Logout", key="admin_logout_btn"):
            st.session_state.token = None
            st.session_state.user_name = "User"
            st.session_state.user_id = None
            st.session_state.is_admin = False
            st.session_state.current_page = 1
            st.rerun()

    st.divider()

    tab1, tab2 = st.tabs(["📋 View Templates", "➕ Create Template"])

    # -----------------------------
    # TAB 1: View Templates
    # -----------------------------
    with tab1:
        st.subheader("All Invoice Templates")

        if st_shadcn_ui.button("🔄 Refresh Templates", key="refresh_templates"):
            st.rerun()

        templates = fetch_templates()

        if not templates:
            st.info("No templates found. Create one in the 'Create Template' tab.")
        else:
            # Display templates in a table-like format
            for template in templates:
                with st.expander(f"📄 {template['template_name']}", expanded=False):
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.write(f"**ID:** {template['id']}")
                        st.write(f"**Type:** {template['type']}")
                        st.write(f"**Created At:** {template.get('created_at', 'N/A')}")
                        st.write(f"**Mandatory Params:** {', '.join(template.get('mandatory_params', []))}")
                    with col2:
                        st.write("**HTML Content:**")
                        st.code(template['html_content'], language="html")

    # -----------------------------
    # TAB 2: Create Template
    # -----------------------------
    with tab2:
        st.subheader("Create New Invoice Template")

        st.info("Fill in the details below to create a new invoice template.")

        template_name = st.text_input(
            "Template Name",
            placeholder="e.g., Professional Invoice",
            key="template_name_input"
        )

        template_type = st.selectbox(
            "Template Type",
            ["invoice", "estimate", "receipt", "quotation"],
            key="template_type_select"
        )

        st.write("**Mandatory Parameters** (comma-separated)")
        mandatory_params_input = st.text_area(
            "Enter parameter names",
            placeholder="e.g., customer_name, invoice_date, total_amount",
            key="mandatory_params_input",
            height=100
        )

        st.write("**HTML Content**")
        html_content = st.text_area(
            "Paste your HTML template",
            placeholder="<html><body>Your template here...</body></html>",
            key="html_content_input",
            height=250
        )

        # Parse mandatory params
        mandatory_params = [
            param.strip() for param in mandatory_params_input.split(",")
            if param.strip()
        ] if mandatory_params_input else []

        col1, col2 = st.columns([1, 1])

        with col1:
            if st_shadcn_ui.button("Preview HTML", key="preview_html_btn"):
                if html_content:
                    st.code(html_content, language="html")
                else:
                    st.warning("Please enter HTML content first.")

        with col2:
            if st_shadcn_ui.button("Create Template ✅", key="create_template_btn"):
                # Validation
                if not template_name:
                    st.error("Template name is required.")
                elif not html_content:
                    st.error("HTML content is required.")
                elif not mandatory_params and not st.checkbox("Allow template without mandatory parameters?", key="allow_no_params"):
                    st.error("Please add at least one mandatory parameter or allow none.")
                else:
                    # Prepare payload
                    template_payload = {
                        "template_name": template_name,
                        "html_content": html_content,
                        "type": template_type,
                        "mandatory_params": mandatory_params
                    }

                    # Call API
                    response = create_template(template_payload)

                    if response and response.status_code == 200:
                        st.success("✅ Template created successfully!")
                        st.json(response.json())
                        st.info("Form will reset. Refresh the page to create another template.")
                    else:
                        if response:
                            st.error(f"❌ Error creating template: {response.text}")
                        else:
                            st.error("Failed to create template.")


# -----------------------------
# Main Entry
# -----------------------------
if not st.session_state.token:
    auth_ui()
elif st.session_state.is_admin:
    admin_dashboard_ui()
else:
    dashboard_ui()
