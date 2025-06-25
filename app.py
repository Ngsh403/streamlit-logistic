import streamlit as st
import pandas as pd
import bcrypt
import io
from fpdf import FPDF
import datetime
import plotly.express as px
import plotly.graph_objects as go
import json # Import json for parsing the firebase config string
from num2words import num2words # Import for converting numbers to words for invoice amounts

# --- Firebase Admin SDK Imports ---
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

# --- Configuration (unchanged, will be used for in-memory user management) ---
INITIAL_USER_DB_STRUCTURE = {
    "S.A. CONCORD INTERNATIONAL CARGO HANDLING CO W.L.L": {
        "company_name": "S.A. CONCORD INTERNATIONAL CARGO HANDLING CO W.L.L",
        "company_pin": "S.A. CONCORD INTERNATIONAL CARGO HANDLING CO W.L.L",
        "users": {
            "sa": {"password_hash": bcrypt.hashpw("pass123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'), "role": "user"},
            "sa": {"password_hash": bcrypt.hashpw("pass123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'), "role": "user"},
        }
    },
    "NORTH CONCORD CARGO HANDLING CO W.L.L": {
        "company_name":  "NORTH CONCORD CARGO HANDLING CO W.L.L",
        "company_pin": "NORTH CONCORD CARGO HANDLING CO W.L.L",
        "users": {
            "north": {"password_hash": bcrypt.hashpw("pass123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'), "role": "user"},
        }
    },
    "EAST CONCORD W.L.L": {
        "company_name": "EAST CONCORD W.L.L",
        "company_pin": "EAST CONCORD W.L.L",
        "users": {
            "east": {"password_hash": bcrypt.hashpw("pass123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'), "role": "user"},
        }
    },
    "COMPANY MANAGEMENT": {
        "company_name": "Company Management",
        "company_pin": "ADMIN",
        "users": {
            "admin": {"password_hash": bcrypt.hashpw("adminpass".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'), "role": "admin"},
        }
    }
}

# --- Initialize Session State ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['company_id'] = None
    st.session_state['user_id'] = None
    st.session_state['company_name'] = None
    st.session_state['role'] = None
    st.session_state['admin_selected_company_for_modules_name'] = None

if 'USER_DB' not in st.session_state:
    st.session_state['USER_DB'] = INITIAL_USER_DB_STRUCTURE.copy()

# --- Firebase Initialization ---
# Use the provided JSON key directly
FIREBASE_SERVICE_ACCOUNT_KEY_JSON = {
  "type": "service_account",
  "project_id": "logisticapp-63967",
  "private_key_id": "a61f0c389a0ce983d8510c1849c91d490b63bf54",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDZiV79HNnbbcUo\nnwqJgi5n8p8PjR+iWxHdkKMST8Du3qTLpbVuyqcbVndtKH0vXOKTE4ztwdlxPsfK\n8/fA6iWSgBQObR7PiEkTmywMZFEuW+6eNtE3KKiH5wc/axzV9hI/wJnRm/PKpIk5\n6wydKGP2aTREVLYJ1jBFLH+HfgQTlj9Bug+oeUAGbmCWe1IlGYxx5BH12PYMUCXo\nn8XqGGkcQgSwZxsI5tavYtcnWFpYLM23aTKKBRuSZ5k2+BEaGftuAnyCkXRhSESU\nqWwI0ZsFx1+HGQjlFpwFvsr6T/ZxPNCO/peeFkSUhw+ozHD5LGPAkOae77s3YljM\nlZGumQT3AgMBAAECggEAA4DeU7SHOeXPIwnNtbuOwFNVZ4hJNrZ6WgNXxiuXy1nu\nU+mDKLiRgBAxMGBcBM2a/HcP3KicLK4KEK/R30rGEndlsv8vrGrQYbuefUQVJYIL\nCaBDhzyutUPToY4T2zLNrmYD6q7bA+vjAAgkhC2T9YVSMEzKzrKGqKwq6y24nQx7\naGa1Lf+qwYDvTjStKE7hn5ibPOqZAk1Uckt7Rz+UWU0ieo8VMCW6LDB3B8LGqZ2X\nJjRfJxvvDbhjyIEwGHIBCiqomWFyms72Tr/FKvMl6EFv0uk9+pPC/jJfYxMODgAl\nvPjr9WqZfABZzalYgMCDxq516vKDUe+eehi3n5nehQKBgQD2rznJp/Jona7CPVKX\nRB9oU/0EPxkFOrSpvq/NbpLXFUHYxuRzTckdJ4hcMK/uFfmqnox79Al8JOBo5V0O\nNhglNTXXYfKhDLbOZp1DDCUtqyNAli/qB+MlW4KYa+ApIY0OGPcKl5+otOqyfwF+\nHH5/VkdKaH5IlxTeaiGZR8YwOwKBgQDhwF0rddzUh3Fjq+vwCCzRlY/gIJpvj4w4\neMYZlqCT0kukyeR0Snt2sEoiOeUh29QGkQ/XDAdXpVLB12wk1T3Ung0EcrYfY0MW\nDGCdIJ6nk0u6monoKyKdzTQeg58bnkSTlsCq2A4jzSnLSAe3ZEbsibB/iJWzwOwO\n1G4i4MlOdQKBgQCR8JCLkOSEp+Tf3U+jVhYOrsGdZYbz5QtE8R8otiYBQP43tVMq\nM/arXNv7ToKGpFGUc0BBhNqnq1loNWmcIryeJqC3z6avSMpNyb94DxNftUOhzjiC\niDAFxeG5Mvjm3IaKtJJSnelC8eV3vFOxvEHKK8z5ZGBxqZAbFUbTW/cQSQKBgDUS\nUxT3hW3VVZvX/ASW92piHcvT/lqBxbY09mVnmuKFitD3waRxKitR8GuxbqOSGXtd\nuPqWUleRfy4g5cSW+Q02Bttn2Fbyr//L8x6dX48HusLot8kD8wRkDH+r88i7YWXN\nCAhh+JkED3JBwcakZWQQTpT82CzFCvnFiQrcC5dNAoGBAMLBSbFD5qhavoKFr9id\nO+k8u+uLtPdIFzt/qjFZ7SIuJ/JK2uoCn3CDhd7jst7qL9p1zXVm/AntJnHSmmgh\n8LnC9QxGe5QeLdHNEwMbBMsC3ArRY2UOTIN00D6MKvNpW9n7eL3/Q+PHtM3CYdpR\nuN+mkMtSGwPi63/Z0GewkJDi\n-----END PRIVATE KEY-----\n",
  "client_email": "firebase-adminsdk-fbsvc@logisticapp-63967.iam.gserviceaccount.com",
  "client_id": "116053489571436273496",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40logisticapp-63967.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}

# Correct the private key string by replacing escaped newlines with actual newlines
FIREBASE_SERVICE_ACCOUNT_KEY_JSON['private_key'] = FIREBASE_SERVICE_ACCOUNT_KEY_JSON['private_key'].replace('\\n', '\n')


FIREBASE_PROJECT_ID = FIREBASE_SERVICE_ACCOUNT_KEY_JSON['project_id']
FIRESTORE_ROOT_COLLECTION = "logistic_app_data" # User specified this

if 'firebase_app_initialized' not in st.session_state:
    st.session_state['firebase_app_initialized'] = False

if not st.session_state['firebase_app_initialized']:
    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate(FIREBASE_SERVICE_ACCOUNT_KEY_JSON)
            firebase_admin.initialize_app(cred)
            st.session_state['firebase_app_initialized'] = True
            st.success("Firebase app initialized successfully!")
        else:
            st.session_state['firebase_app_initialized'] = True
            st.info("Firebase app already initialized.")
    except Exception as e:
        st.error(f"Error initializing Firebase: {e}")

# Get Firestore client
if st.session_state['firebase_app_initialized']:
    db = firestore.client()
else:
    db = None


# --- Firestore Interactions ---
def firestore_get_collection(company_id, collection_name):
    """Fetches all documents from a Firestore subcollection for a given company."""
    if db is None:
        st.error("Firestore database client not initialized.")
        return pd.DataFrame()

    # Path: logistic_app_data/{company_id}/{collection_name}
    collection_ref = db.collection(FIRESTORE_ROOT_COLLECTION).document(company_id).collection(collection_name)
    
    try:
        docs = collection_ref.stream()
        data_list = []
        for doc in docs:
            doc_data = doc.to_dict()
            doc_data['doc_id'] = doc.id # Store the actual Firestore document ID
            data_list.append(doc_data)
        
        # Helper to get expected columns from module configs
        def get_expected_columns_for_module(mod_name):
            mapping = {
                'trips': TRIP_MANAGEMENT_FIELDS,
                'rentals': RENTAL_MANAGEMENT_FIELDS,
                'vehicles': FLEET_MANAGEMENT_FIELDS,
                'invoices': INVOICING_QUOTING_FIELDS,
                'clients': CRM_MANAGEMENT_FIELDS,
                'employees': EMPLOYEE_MANAGEMENT_FIELDS,
                'payslips': PAYROLL_FIELDS,
                'leaves': PLANNING_TIMEOFF_FIELDS,
                'vat_transactions': VAT_INPUT_OUTPUT_FIELDS
            }

            # Map of auto-generated ID fields to ensure they are always included
            auto_generated_ids_map = {
                'trips': 'Trip ID',
                'rentals': 'Rental ID',
                'invoices': 'Inv Number', # Assuming Inv Number is the primary ID for invoices
                'payslips': 'Payslip ID'
            }

            fields = list(mapping.get(mod_name, {}).keys())
            cleaned_fields = []
            for field in fields:
                if field.endswith(" Date") or field.endswith(" Time"):
                    # These are input fields, the combined datetime string is the actual field
                    # The original fields_config defines "Start Date & Time" but not "Start Date" or "Start Time"
                    # So, we directly add the combined field name.
                    if mapping.get(mod_name, {}).get(field, {}).get('type') == 'datetime':
                        cleaned_fields.append(field)
                else:
                    cleaned_fields.append(field)

            # Ensure auto-generated ID field is always present
            if mod_name in auto_generated_ids_map and auto_generated_ids_map[mod_name] not in cleaned_fields:
                cleaned_fields.insert(0, auto_generated_ids_map[mod_name]) # Add at the beginning for consistency

            return cleaned_fields + ['Company'] # Always expect 'Company' column

        if data_list:
            df = pd.DataFrame(data_list)
            expected_cols_base = get_expected_columns_for_module(collection_name)
            
            # Add missing columns with None, then reorder
            for col in expected_cols_base:
                if col not in df.columns:
                    df[col] = None
            
            # Ensure 'doc_id' is always the last column for consistency
            if 'doc_id' not in df.columns:
                df['doc_id'] = None

            # Filter for expected columns and then reorder
            cols_to_keep = [col for col in expected_cols_base if col in df.columns]
            df = df[cols_to_keep + ['doc_id']]
            
            return df
        else:
            # Return an empty DataFrame with appropriate columns if no data
            # Use get_expected_columns_for_module here to ensure correct schema for empty DFs
            columns_for_empty_df = get_expected_columns_for_module(collection_name)
            empty_df = pd.DataFrame(columns=columns_for_empty_df)
            empty_df['doc_id'] = None # Always add doc_id for internal use
            return empty_df
    except Exception as e:
        st.error(f"Error fetching data from Firestore for {collection_name}: {e}")
        return pd.DataFrame()


def firestore_add_document(company_id, collection_name, data):
    """Adds a document to a Firestore subcollection for a given company."""
    if db is None:
        st.error("Firestore database client not initialized. Cannot add document.")
        return None

    # Path: logistic_app_data/{company_id}/{collection_name}
    collection_ref = db.collection(FIRESTORE_ROOT_COLLECTION).document(company_id).collection(collection_name)
    
    try:
        # Firestore automatically generates a document ID if you use add()
        update_time, doc_ref = collection_ref.add(data) # add() returns (update_time, DocumentReference)
        return doc_ref.id # Returns the new document ID
    except Exception as e:
        st.error(f"Error adding document to Firestore: {e}")
        return None


def firestore_update_document(company_id, collection_name, doc_id, data):
    """Updates a document in a Firestore subcollection for a given company."""
    if db is None:
        st.error("Firestore database client not initialized. Cannot update document.")
        return False

    # Path: logistic_app_data/{company_id}/{collection_name}/{doc_id}
    doc_ref = db.collection(FIRESTORE_ROOT_COLLECTION).document(company_id).collection(collection_name).document(doc_id)
    
    try:
        doc_ref.update(data)
        return True
    except Exception as e:
        st.error(f"Error updating document {doc_id} in Firestore: {e}")
        return False


def firestore_delete_document(company_id, collection_name, doc_id):
    """Deletes a document from a Firestore subcollection for a given company."""
    if db is None:
        st.error("Firestore database client not initialized. Cannot delete document.")
        return False

    # Path: logistic_app_data/{company_id}/{collection_name}/{doc_id}
    doc_ref = db.collection(FIRESTORE_ROOT_COLLECTION).document(company_id).collection(collection_name).document(doc_id)
    
    try:
        doc_ref.delete()
        return True
    except Exception as e:
        st.error(f"Error deleting document {doc_id} from Firestore: {e}")
        return False

# --- Helper Functions for Reports ---
def generate_excel_report(df, filename):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Report')
    processed_data = output.getvalue()
    return processed_data

def generate_pdf_report(df, title):
    pdf = FPDF()
    pdf.add_page()

    # --- Header ---
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, title, 0, 1, "C")
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 5, f"Report Date: {datetime.date.today().strftime('%Y-%m-%d')}", 0, 1, "C")
    pdf.ln(10) # Add some space after header

    # Ensure all DataFrame columns are strings for consistent width calculation
    df_str = df.astype(str)

    available_width = pdf.w - pdf.l_margin - pdf.r_margin
    # Define a reasonable minimum width to ensure character rendering
    MIN_COL_WIDTH = 15 # mm

    desired_widths = {}
    # Calculate desired width for each column based on header and max content
    pdf.set_font("Arial", "B", 10) # Use header font for header width calculation
    for col in df_str.columns:
        # Width needed for header
        header_width = pdf.get_string_width(col)
        # Width needed for maximum content in the column (using normal font)
        pdf.set_font("Arial", size=10) # Switch to data font for content width calculation
        max_content_width = 0
        if not df_str[col].empty:
            max_content_width = df_str[col].apply(pdf.get_string_width).max()
        
        # Take the maximum of header width and content width, plus padding
        desired_widths[col] = max(header_width, max_content_width) + 6 # Add padding

    total_desired_width = sum(desired_widths.values())

    # If total desired width exceeds available page width, scale down
    col_widths = {}
    if total_desired_width > available_width:
        # Scale all column widths proportionally
        scale_factor = available_width / total_desired_width
        for col in df_str.columns:
            col_widths[col] = max(desired_widths[col] * scale_factor, MIN_COL_WIDTH)
    else:
        # If total desired width is less than or equal to available width, use desired widths
        # and ensure minimum, then distribute remaining space if any.
        remaining_width = available_width
        for col in df_str.columns:
            col_widths[col] = max(desired_widths[col], MIN_COL_WIDTH)
            remaining_width -= col_widths[col]
        
        # Distribute any remaining space to larger columns
        if remaining_width > 0:
            large_columns = [col for col, width in col_widths.items() if width > MIN_COL_WIDTH]
            if large_columns:
                extra_per_col = remaining_width / len(large_columns)
                for col in large_columns:
                    col_widths[col] += extra_per_col
            else: # If all columns are at min width, just add to the first column
                if col_widths:
                    col_widths[list(col_widths.keys())[0]] += remaining_width
    
    # Render headers
    pdf.set_font("Arial", "B", 10) # Set font for headers
    for col in df_str.columns:
        pdf.cell(col_widths[col], 10, txt=col, border=1, align="C")
    pdf.ln()

    # Add data
    pdf.set_font("Arial", size=10) # Smaller font for data
    for index, row in df_str.iterrows(): # Iterate through the string-converted DataFrame
        for col in df_str.columns:
            cell_text = str(row[col]) # Ensure it's a string
            # Using multi_cell with the calculated column width
            pdf.multi_cell(col_widths[col], 7, txt=cell_text, border=1, align="L", ln=0)
        pdf.ln() # Move to next line after all columns for the row

    # --- Footer ---
    pdf.set_y(pdf.h - 15) # Position 15 units from bottom
    pdf.set_font("Arial", "I", 8)
    pdf.cell(0, 10, f"Page {pdf.page_no()}/{{nb}}", 0, 0, "C") # Use {nb} for total pages

    return bytes(pdf.output(dest='S')) # Explicitly cast to bytes

# Function for generating the customized management PDF
def generate_management_pdf_report(all_companies_data, user_db_current):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # --- Background Image / Color for Management Report ---
    # Placeholder for the background image URL. In a real application, you would host
    # your 'bill background.PNG' and use its URL here.
    MANAGEMENT_REPORT_BACKGROUND_URL = "https://placehold.co/595x842/F0F8FF/313131.png?text=Management+Report+Background"
    try:
        pdf.image(MANAGEMENT_REPORT_BACKGROUND_URL, x=0, y=0, w=pdf.w, h=pdf.h)
    except Exception as e:
        # Fallback to a solid light blue background if image fails to load
        pdf.set_fill_color(240, 248, 255) # Light blue background
        pdf.rect(0, 0, pdf.w, pdf.h, 'F')
        st.warning(f"Could not load management report background image from {MANAGEMENT_REPORT_BACKGROUND_URL}: {e}. Generating with fallback color.")

    # --- Header for Management Report ---
    pdf.set_y(10) # Start header from top
    pdf.set_font("Arial", "B", 20)
    pdf.cell(0, 10, "Global Logistic Management Dashboard Report", 0, 1, "C")
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 8, f"Report Date: {datetime.date.today().strftime('%Y-%m-%d')}", 0, 1, "C")
    pdf.ln(10) # Space after header

    # Calculate overall KPIs
    total_vehicles_all = 0
    total_employees_all = 0
    total_revenue_all = 0.0
    total_trips_all = 0
    total_rentals_all = 0
    total_payslips_net_salary_all = 0.0
    total_leaves_all = 0
    total_vat_amount_all = 0.0

    # Data for charts (summaries for PDF)
    vehicles_by_type_data = {}
    revenue_by_company_data = {}
    employees_by_company_data = {}
    trips_by_company_data = {}


    for company_id_key, company_details in user_db_current.items(): # Iterating through USER_DB_CURRENT for companies
        if company_details['company_pin'] != 'ADMIN': # Exclude the admin company for operational data
            comp_name = company_details['company_name']
            
            # Safely get dataframes from the 'all_companies_data' (which is sourced from Firestore)
            comp_vehicles_df = all_companies_data.get('vehicles', pd.DataFrame())
            if not comp_vehicles_df.empty and 'Company' in comp_vehicles_df.columns:
                # FIX: Corrected indexing to use comp_vehicles_df for filtering
                company_specific_vehicles_df = comp_vehicles_df[comp_vehicles_df['Company'] == comp_name]
                total_vehicles_all += len(company_specific_vehicles_df)
                # Aggregate for Vehicles by Type
                for v_type in company_specific_vehicles_df['Vehicle Type'].unique():
                    vehicles_by_type_data[v_type] = vehicles_by_type_data.get(v_type, 0) + len(company_specific_vehicles_df[company_specific_vehicles_df['Vehicle Type'] == v_type])


            comp_employees_df = all_companies_data.get('employees', pd.DataFrame())
            if not comp_employees_df.empty and 'Company' in comp_employees_df.columns:
                # FIX: Corrected indexing to use comp_employees_df for filtering
                company_specific_employees_df = comp_employees_df[comp_employees_df['Company'] == comp_name]
                total_employees_all += len(company_specific_employees_df)
                employees_by_company_data[comp_name] = len(company_specific_employees_df)

            comp_invoices_df = all_companies_data.get('invoices', pd.DataFrame())
            if not comp_invoices_df.empty and 'Company' in comp_invoices_df.columns and 'Total Amount' in comp_invoices_df.columns:
                # FIX: Corrected indexing to use comp_invoices_df for filtering
                company_specific_invoices_df = comp_invoices_df[comp_invoices_df['Company'] == comp_name]
                company_revenue = company_specific_invoices_df['Total Amount'].sum()
                total_revenue_all += company_revenue
                revenue_by_company_data[comp_name] = company_revenue

            comp_trips_df = all_companies_data.get('trips', pd.DataFrame())
            if not comp_trips_df.empty and 'Company' in comp_trips_df.columns:
                # FIX: Corrected indexing to use comp_trips_df for filtering
                company_specific_trips_df = comp_trips_df[comp_trips_df['Company'] == comp_name]
                total_trips_all += len(company_specific_trips_df)
                trips_by_company_data[comp_name] = len(company_specific_trips_df)


            comp_rentals_df = all_companies_data.get('rentals', pd.DataFrame())
            if not comp_rentals_df.empty and 'Company' in comp_rentals_df.columns:
                total_rentals_all += len(comp_rentals_df[comp_rentals_df['Company'] == comp_name])

            comp_payslips_df = all_companies_data.get('payslips', pd.DataFrame())
            if not comp_payslips_df.empty and 'Company' in comp_payslips_df.columns and 'Net Salary' in comp_payslips_df.columns:
                total_payslips_net_salary_all += comp_payslips_df[comp_payslips_df['Company'] == comp_name]['Net Salary'].sum()
            
            comp_leaves_df = all_companies_data.get('leaves', pd.DataFrame())
            if not comp_leaves_df.empty and 'Company' in comp_leaves_df.columns:
                total_leaves_all += len(comp_leaves_df[comp_leaves_df['Company'] == comp_name])

            comp_vat_df = all_companies_data.get('vat_transactions', pd.DataFrame())
            if not comp_vat_df.empty and 'Company' in comp_vat_df.columns and 'VAT Amount' in comp_vat_df.columns:
                total_vat_amount_all += comp_vat_df[comp_vat_df['Company'] == comp_name]['VAT Amount'].sum()


    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Overall Company KPIs", 0, 1, "L")
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 8, f"Total Vehicles Across All Companies: {total_vehicles_all}", 0, 1, "L")
    pdf.cell(0, 8, f"Total Employees Across All Companies: {total_employees_all}", 0, 1, "L")
    pdf.cell(0, 8, f"Total Revenue Across All Companies: INR {total_revenue_all:,.2f}", 0, 1, "L")
    pdf.ln(5)
    pdf.cell(0, 8, f"Total Trips Across All Companies: {total_trips_all}", 0, 1, "L")
    pdf.cell(0, 8, f"Total Rentals Across All Companies: {total_rentals_all}", 0, 1, "L")
    pdf.cell(0, 8, f"Total Net Salary Paid Across All Companies: INR {total_payslips_net_salary_all:,.2f}", 0, 1, "L")
    pdf.cell(0, 8, f"Total Leave Requests Across All Companies: {total_leaves_all}", 0, 1, "L")
    pdf.cell(0, 8, f"Total VAT Amount Processed Across All Companies: INR {total_vat_amount_all:,.2f}", 0, 1, "L")
    pdf.ln(10)

    # Add summary of vehicle types for PDF
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Vehicle Distribution by Type (All Companies)", 0, 1, "L")
    pdf.set_font("Arial", "", 10)
    if vehicles_by_type_data:
        for v_type, count in vehicles_by_type_data.items():
            pdf.cell(0, 7, f"- {v_type}: {count}", 0, 1, "L")
    else:
        pdf.cell(0, 7, "No vehicle data available.", 0, 1, "L")
    pdf.ln(5)

    # Add summary of Revenue by Company for PDF
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Revenue by Company", 0, 1, "L")
    pdf.set_font("Arial", "", 10)
    if revenue_by_company_data:
        for company, revenue in revenue_by_company_data.items():
            pdf.cell(0, 7, f"- {company}: INR {revenue:,.2f}", 0, 1, "L")
    else:
        pdf.cell(0, 7, "No revenue data available.", 0, 1, "L")
    pdf.ln(5)

    # Add summary of Employees by Company for PDF
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Employees by Company", 0, 1, "L")
    pdf.set_font("Arial", "", 10)
    if employees_by_company_data:
        for company, employees in employees_by_company_data.items():
            pdf.cell(0, 7, f"- {company}: {employees}", 0, 1, "L")
    else:
        pdf.cell(0, 7, "No employee data available.", 0, 1, "L")
    pdf.ln(5)

    # Add summary of Trips by Company for PDF
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Trips by Company", 0, 1, "L")
    pdf.set_font("Arial", "", 10)
    if trips_by_company_data:
        for company, trips_count in trips_by_company_data.items():
            pdf.cell(0, 7, f"- {company}: {trips_count}", 0, 1, "L")
    else:
        pdf.cell(0, 7, "No trip data available.", 0, 1, "L")
    pdf.ln(10)


    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Details Per Company", 0, 1, "L")
    pdf.ln(5)

    for company_id_key, company_details in user_db_current.items():
        if company_details['company_pin'] != 'ADMIN': # Exclude the admin company
            comp_name = company_details['company_name']
            
            pdf.set_font("Arial", "BU", 12)
            pdf.cell(0, 10, f"Company: {comp_name}", 0, 1, "L")
            pdf.set_font("Arial", "", 10)

            # Get company specific data from the 'all_companies_data' (Firestore sourced)
            comp_vehicles_df = all_companies_data.get('vehicles', pd.DataFrame())
            comp_vehicles_df_filtered = comp_vehicles_df[comp_vehicles_df['Company'] == comp_name] if not comp_vehicles_df.empty and 'Company' in comp_vehicles_df.columns else pd.DataFrame()

            comp_employees_df = all_companies_data.get('employees', pd.DataFrame())
            comp_employees_df_filtered = comp_employees_df[comp_employees_df['Company'] == comp_name] if not comp_employees_df.empty and 'Company' in comp_employees_df.columns else pd.DataFrame()

            comp_invoices_df = all_companies_data.get('invoices', pd.DataFrame())
            comp_invoices_df_filtered = comp_invoices_df[comp_invoices_df['Company'] == comp_name] if not comp_invoices_df.empty and 'Company' in comp_invoices_df.columns else pd.DataFrame()

            comp_trips_df = all_companies_data.get('trips', pd.DataFrame())
            comp_trips_df_filtered = comp_trips_df[comp_trips_df['Company'] == comp_name] if not comp_trips_df.empty and 'Company' in comp_trips_df.columns else pd.DataFrame()

            comp_rentals_df = all_companies_data.get('rentals', pd.DataFrame())
            comp_rentals_df_filtered = comp_rentals_df[comp_rentals_df['Company'] == comp_name] if not comp_rentals_df.empty and 'Company' in comp_rentals_df.columns else pd.DataFrame()

            comp_payslips_df = all_companies_data.get('payslips', pd.DataFrame())
            comp_payslips_df_filtered = comp_payslips_df[comp_payslips_df['Company'] == comp_name] if not comp_payslips_df.empty and 'Company' in comp_payslips_df.columns else pd.DataFrame()

            comp_leaves_df = all_companies_data.get('leaves', pd.DataFrame())
            comp_leaves_df_filtered = comp_leaves_df[comp_leaves_df['Company'] == comp_name] if not comp_leaves_df.empty and 'Company' in comp_leaves_df.columns else pd.DataFrame()

            comp_vat_df = all_companies_data.get('vat_transactions', pd.DataFrame())
            comp_vat_df_filtered = comp_vat_df[comp_vat_df['Company'] == comp_name] if not comp_vat_df.empty and 'Company' in comp_vat_df.columns else pd.DataFrame()


            # Company-specific summary
            pdf.cell(0, 7, f"- Vehicles: {len(comp_vehicles_df_filtered)}", 0, 1, "L")
            pdf.cell(0, 7, f"- Employees: {len(comp_employees_df_filtered)}", 0, 1, "L")
            company_revenue = comp_invoices_df_filtered['Total Amount'].sum() if 'Total Amount' in comp_invoices_df_filtered.columns else 0.0
            pdf.cell(0, 7, f"- Revenue: INR {company_revenue:,.2f}", 0, 1, "L")
            pdf.cell(0, 7, f"- Total Trips: {len(comp_trips_df_filtered)}", 0, 1, "L")
            pdf.cell(0, 7, f"- Total Rentals: {len(comp_rentals_df_filtered)}", 0, 1, "L")
            company_net_salary = comp_payslips_df_filtered['Net Salary'].sum() if 'Net Salary' in comp_payslips_df_filtered.columns else 0.0
            pdf.cell(0, 7, f"- Total Net Salary Paid: INR {company_net_salary:,.2f}", 0, 1, "L")
            pdf.cell(0, 7, f"- Total Leave Requests: {len(comp_leaves_df_filtered)}", 0, 1, "L")
            company_vat_amount = comp_vat_df_filtered['VAT Amount'].sum() if 'VAT Amount' in comp_vat_df_filtered.columns else 0.0
            pdf.cell(0, 7, f"- Total VAT Amount: INR {company_vat_amount:,.2f}", 0, 1, "L")
            
            pdf.ln(5) # Space between companies

    # --- Footer for Management Report ---
    pdf.set_y(pdf.h - 15) # Position 15 units from bottom
    pdf.set_font("Arial", "I", 8)
    pdf.cell(0, 10, f"Page {pdf.page_no()}/{{nb}} - Global Management Report", 0, 0, "C")

    return bytes(pdf.output(dest='S'))


def generate_single_tax_invoice_pdf(invoice_data, company_name_actual, company_pin_actual, logo_url, logo_x, logo_y, logo_width, logo_height):
    """
    Generates a single tax invoice PDF based on the provided invoice data and company details.
    Incorporates a background image (simulating bill background.PNG) and a customizable logo.
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # --- Background Image (simulating bill background.PNG letterhead) ---
    # IMPORTANT: Replace this URL with the actual hosted URL of your 'bill background.PNG' image.
    # For testing, you can use a placeholder like the one below, but it won't show your specific image.
    BACKGROUND_IMAGE_URL = "https://i.ibb.co/RGTCjMb4/EAST-CONCORD-W-L-L-page-0001-1.jpg" 
    try:
        pdf.image(BACKGROUND_IMAGE_URL, x=0, y=0, w=pdf.w, h=pdf.h)
    except Exception as e:
        st.warning(f"Could not load background image from {BACKGROUND_IMAGE_URL}: {e}. Generating without background image.")
        # Fallback to a solid light blue background if image fails to load
        pdf.set_fill_color(240, 248, 255) # Light blue background
        pdf.rect(100, 20, pdf.w, pdf.h, 'F')

    # Add background watermark (if not part of the background image, or to overlay)
    pdf.set_font("Arial", "B", 80)
    pdf.set_text_color(200, 200, 200) # Light gray
    pdf.text(pdf.w / 2 - pdf.get_string_width("INVOICE") / 2, pdf.h / 2 + 10, "INVOICE")
    pdf.set_text_color(0, 0, 0) # Reset text color

    # --- Customizable Logo (separate from background, top left) ---
    # This logo will overlay on the background image. Replace with actual hosted logo URL.
    # try:
    #     pdf.image(logo_url, x=logo_x, y=logo_y, w=logo_width, h=logo_height)
    # except Exception as e:
    #     st.warning(f"Could not load logo image from {logo_url}: {e}. Continuing without logo.")

    # --- Custom Header Section for Invoice ---
    # Position adjusted to not overlap with typical letterhead top area
    pdf.set_y(25) # Adjust starting Y position for header content
    pdf.set_font("Arial", "", 9)
    pdf.set_text_color(50, 50, 50) # Darker gray for header text
    
    # # Example header content (replace with actual data for your company if not in background image)
     pdf.set_x(1) # Align with left margin
     pdf.cell(0, 5, "EAST CONCORD W.L.L", 0, 1, "L")
     pdf.set_x(50)
     pdf.cell(0, 5, "Flat/Shop No. 11, Building 471", 0, 1, "L")
     pdf.set_x(10)
     pdf.cell(0, 5, "Road/Shop 3513, MANAMA", 0, 1, "L")
     pdf.set_x(10)
     pdf.cell(0, 5, "UMM AL-HASSAM, Kingdom of Bahrain", 0, 1, "L")
     pdf.set_x(10)
     pdf.cell(0, 5, f"TRN: {company_pin_actual}", 0, 1, "L") # Using company_pin as TRN example
     pdf.set_x(10)
     pdf.cell(0, 5, "Email: concord@email.com (Mock)", 0, 1, "L")
     pdf.ln(5) # Space after header details
     pdf.set_text_color(0, 0, 0) # Reset text color


    pdf.set_y(pdf.get_y() + 5) # Ensure content starts below the custom header
    pdf.set_font("Arial", "B", 24)
    pdf.cell(0, 20, "Tax Invoice", 0, 1, "C")
    pdf.ln(5)

    # --- Invoice Details & Bill To ---
    # Left column for invoice details
    start_y_details = pdf.get_y() # Capture current Y
    
    pdf.set_xy(10, start_y_details) 
    pdf.set_font("Arial", "B", 10)
    pdf.cell(30, 6, "Invoice No.", 1, 0, "L")
    pdf.set_font("Arial", "", 10)
    pdf.cell(60, 6, str(invoice_data.get('Inv Number', 'N/A')), 1, 1, "L")

    pdf.set_x(10)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(30, 6, "Date", 1, 0, "L")
    pdf.set_font("Arial", "", 10)
    pdf.cell(60, 6, str(invoice_data.get('Date', 'N/A')), 1, 1, "L")

    pdf.set_x(10)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(30, 6, "Delivery Note", 1, 0, "L")
    pdf.set_font("Arial", "", 10)
    pdf.cell(60, 6, "N/A", 1, 1, "L") # Not directly available in current data fields

    pdf.set_x(10)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(30, 6, "Buyer's Order No.", 1, 0, "L")
    pdf.set_font("Arial", "", 10)
    pdf.cell(60, 6, "N/A", 1, 1, "L") # Not directly available in current data fields


    # Right column (for Bill To)
    pdf.set_xy(105, start_y_details) # Adjust X for right column, reuse start_y
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 6, "Bill To:", 0, 1, "L")
    pdf.set_x(105)
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 6, str(invoice_data.get('Client', 'N/A')), 0, 1, "L") # Assuming 'Client' field
    # Mock some address details for the client
    pdf.set_x(105)
    pdf.cell(0, 6, "Client Address Line 1 (Mock)", 0, 1, "L")
    pdf.set_x(105)
    pdf.cell(0, 6, "Client Address Line 2 (Mock)", 0, 1, "L")
    pdf.set_x(105)
    pdf.cell(0, 6, f"Client TRN: ClientTaxID (Mock)", 0, 1, "L")
    
    pdf.set_y(max(pdf.get_y(), start_y_details + 4 * 6) + 5) # Ensure Y position is below the longest column, plus some margin


    # --- Particulars Table ---
    pdf.set_y(pdf.get_y() + 5) # Move down after details section
    pdf.set_font("Arial", "B", 10)
    # Headers - Adjusted to match the image precisely
    col_headers = ["SR.NO", "Particulars", "Quantity", "Rate", "Amount", "VAT(BHD)", "Total"]
    col_widths = [15, 60, 15, 20, 25, 25, 30] # Adjusted widths for columns
    for i, header in enumerate(col_headers):
        pdf.cell(col_widths[i], 10, header, 1, 0, "C")
    pdf.ln()

    pdf.set_font("Arial", "", 10)
    # Data Row (Using single invoice fields)
    sl_no = 1
    particulars = str(invoice_data.get('Particulars', 'Logistic Services')) # Added 'Particulars' field in config
    qty = 1 # Assuming quantity of 1 for service/lump sum
    rate = invoice_data.get('Amount', 0.0) # Assuming 'Amount' is the rate for a single item
    amount = invoice_data.get('Amount', 0.0)
    vat_amount = invoice_data.get('VAT (10%)', 0.0) # Use 'VAT (10%)' from data
    total_amount = invoice_data.get('Total Amount', 0.0)

    pdf.cell(col_widths[0], 10, str(sl_no), 1, 0, "C")
    pdf.cell(col_widths[1], 10, particulars, 1, 0, "L")
    pdf.cell(col_widths[2], 10, str(qty), 1, 0, "R")
    pdf.cell(col_widths[3], 10, f"{rate:,.2f}", 1, 0, "R")
    pdf.cell(col_widths[4], 10, f"{amount:,.2f}", 1, 0, "R")
    pdf.cell(col_widths[5], 10, f"{vat_amount:,.2f}", 1, 0, "R")
    pdf.cell(col_widths[6], 10, f"{total_amount:,.2f}", 1, 1, "R") # Last cell moves to next line

    # Totals (Grand Total, VAT, etc.) - adjusted to match image layout
    current_y = pdf.get_y()
    # "Total" label spans from SR.NO to Rate columns
    pdf.set_font("Arial", "B", 10)
    pdf.cell(sum(col_widths[0:4]), 7, "Total", 1, 0, "L") # "Total" label spans multiple cells
    pdf.set_font("Arial", "", 10)
    # The actual numerical values under Amount, VAT(BHD), and Total
    pdf.cell(col_widths[4], 7, f"{amount:,.2f}", 1, 0, "R") # Amount column total
    pdf.cell(col_widths[5], 7, f"{vat_amount:,.2f}", 1, 0, "R") # VAT total
    pdf.cell(col_widths[6], 7, f"{total_amount:,.2f}", 1, 1, "R") # Grand Total

    # --- Amount in words ---
    pdf.set_y(pdf.get_y() + 10)
    pdf.set_font("Arial", "B", 10)
    # Ensure numerical value before converting to words
    amount_in_words_val = total_amount if isinstance(total_amount, (int, float)) else 0.0
    pdf.cell(0, 7, f"Amount chargeable (in words): {num2words(amount_in_words_val).title()} Rupees Only", 0, 1, "L")
    pdf.ln(5)

    # --- Remarks ---
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 7, "Remarks:", 0, 1, "L")
    pdf.set_font("Arial", "", 10)
    pdf.multi_cell(0, 5, str(invoice_data.get('Remarks', 'No specific remarks.')), 0, "L")
    pdf.ln(10)

    # --- Signature block ---
    # Position near bottom, adjusted for the new footer (implied by background image)
    # This assumes the background image leaves space at the bottom for signature.
    pdf.set_y(pdf.h - 65) 
    pdf.set_font("Arial", "B", 10)
    pdf.cell(pdf.w/2 - 20, 5, f"For {company_name_actual}", 0, 0, "L")
    pdf.cell(0, 5, "Authorized Signatory", 0, 1, "R")
    pdf.ln(15)
    pdf.cell(pdf.w/2 - 20, 0, "____________________", 0, 0, "L")
    pdf.cell(0, 0, "____________________", 0, 1, "R")
    
    # --- Custom Footer Section for Invoice ---
    pdf.set_y(pdf.h - 15) # Position 15 units from bottom
    pdf.set_font("Arial", "I", 8)
    pdf.cell(0, 10, f"CR No. 166155-1 | Tel: 17228646 | Mob: 39884260, 339660641 | Bldg: 471, Flat 11 | Road: 3513, Block: 335 | Manama / Umm Alhassam, Kingdom of Bahrain", 0, 0, "C")


    return bytes(pdf.output(dest='S')) # Explicitly cast to bytes


def add_serial_numbers(df):
    """Adds a 'SL No' column starting from 1 to a DataFrame, if it doesn't exist.
       If it exists, it's removed and re-inserted to ensure correct sequential numbering.
    """
    df_copy = df.copy() # Work on a copy to avoid modifying original df in session state indirectly
    if 'SL No' in df_copy.columns:
        # If 'SL No' already exists, remove it before re-inserting to get correct numbering
        df_copy = df_copy.drop(columns=['SL No'])
    
    if not df_copy.empty:
        df_copy.insert(0, 'SL No', range(1, len(df_copy) + 1))
    return df_copy

# --- Module Functions (Placeholders) ---

def display_module(module_name, fields_config, sample_data_key=None, crud_enabled=True, company_filter_id=None):
    # Use company_filter_id if provided, otherwise use the current session's company ID
    actual_company_id_for_filter = company_filter_id if company_filter_id else st.session_state['company_id']
    actual_company_name_for_filter = None # Need to get company name from ID
    for comp_id, comp_details in st.session_state['USER_DB'].items():
        if comp_id == actual_company_id_for_filter:
            actual_company_name_for_filter = comp_details['company_name']
            break
    if not actual_company_name_for_filter:
        st.error("Error: Could not determine company name for the selected company ID.")
        return # Exit if company name cannot be found

    collection_name_in_firestore = sample_data_key if sample_data_key else module_name.lower().replace(" ", "_")
    
    # Fetch data from Firestore
    current_company_data = firestore_get_collection(actual_company_id_for_filter, collection_name_in_firestore)

    with st.expander(f"**{module_name} Management**"):
        if crud_enabled:
            st.subheader("Add New Entry")
            new_entry_data = {}
            for field, config in fields_config.items():
                widget_key = f"{actual_company_id_for_filter}_{module_name}_add_{field}"

                # Special handling for auto-generated IDs - skip input
                if module_name == "Trip" and field == "Trip ID":
                    continue
                if module_name == "Rental" and field == "Rental ID":
                    continue
                if module_name == "Invoicing & Quoting" and (field == "Inv Number" or field == "SI No"):
                    continue
                if module_name == "Payroll" and field == "Payslip ID":
                    continue

                if config['type'] == 'text':
                    new_entry_data[field] = st.text_input(field, key=widget_key)
                elif config['type'] == 'number':
                    new_entry_data[field] = st.number_input(field, value=0.0 if field in ['Distance', 'Price', 'Fuel Charge / Surcharges', 'Daily/Monthly Rate', 'Amount', 'VAT (10%)', 'Total Amount', 'Credit Limit', 'Base Salary', 'Trip Bonus', 'Rental Commission', 'Deductions', 'Overtime', 'Net Salary', 'VAT Amount'] else 0, key=widget_key)
                elif config['type'] == 'date':
                    # Convert datetime.date to ISO format string for Firestore compatibility
                    date_val = st.date_input(field, datetime.date.today(), key=widget_key)
                    new_entry_data[field] = date_val.isoformat() if date_val else None
                elif config['type'] == 'datetime':
                    date_val = st.date_input(f"{field} Date", datetime.date.today(), key=f"{widget_key}_date")
                    time_val = st.time_input(f"{field} Time", datetime.time(8,0), key=f"{widget_key}_time")
                    new_entry_data[field] = f"{date_val.isoformat()} {time_val.isoformat()}" if date_val and time_val else None
                elif config['type'] == 'select':
                    new_entry_data[field] = st.selectbox(field, options=config['options'], key=widget_key)
                elif config['type'] == 'checkbox':
                    new_entry_data[field] = st.checkbox(field, key=widget_key)
                elif config['type'] == 'file':
                    new_entry_data[field] = st.file_uploader(field, key=widget_key)

            if st.button(f"Add {module_name} Entry", key=f"{actual_company_id_for_filter}_{module_name}_add_button"):
                entry_to_add = {'Company': actual_company_name_for_filter} # Always associate with the current company

                # Handle auto-generation for specific IDs
                if module_name == "Trip":
                    entry_to_add['Trip ID'] = f"TRP-{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')}"
                elif module_name == "Rental":
                    entry_to_add['Rental ID'] = f"RNT-{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')}"
                elif module_name == "Invoicing & Quoting":
                    entry_to_add['Inv Number'] = f"INV-{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')}"
                    entry_to_add['SI No'] = f"SI-{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')}"
                elif module_name == "Payroll":
                    entry_to_add['Payslip ID'] = f"PS-{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')}"

                for field, value in new_entry_data.items():
                    if field.endswith(" Date") or field.endswith(" Time"):
                        continue
                    entry_to_add[field] = value

                # Handle file uploads (store just the name/path)
                for field, config in fields_config.items():
                    if config['type'] == 'file' and new_entry_data.get(field):
                        entry_to_add[field] = new_entry_data[field].name
                
                try:
                    firestore_add_document(actual_company_id_for_filter, collection_name_in_firestore, entry_to_add)
                    st.success(f"{module_name} entry added successfully for {actual_company_name_for_filter}!")
                    st.rerun() # Refresh data after adding
                except Exception as e:
                    st.error(f"Error adding {module_name} entry: {e}")


        st.subheader(f"Existing {module_name} Entries")

        # Search and Filter
        search_term = st.text_input(f"Search {module_name} for {actual_company_name_for_filter}", key=f"{actual_company_id_for_filter}_{module_name}_search", placeholder="Type to search...")
        
        filtered_df = current_company_data

        if search_term:
            filtered_df = filtered_df[
                filtered_df.astype(str).apply(lambda row: row.str.contains(search_term, case=False, na=False).any(), axis=1)
            ]

        # Display data with SL No and allow editing
        display_df_with_slno = add_serial_numbers(filtered_df.drop(columns=['doc_id'], errors='ignore')) # Drop doc_id for display

        if crud_enabled:
            edited_df = st.data_editor(
                display_df_with_slno,
                key=f"{actual_company_id_for_filter}_{module_name}_data_editor",
                hide_index=True,
                num_rows="dynamic",
                use_container_width=True
            )

            # Check for changes and update/delete in Firestore
            # Re-fetch the original data including 'doc_id' for comparison
            original_data_for_comparison = firestore_get_collection(actual_company_id_for_filter, collection_name_in_firestore)
            original_data_dict_by_pk = {} # Using a primary key from your data for easier comparison
            
            # Decide on a primary key for each module for efficient comparison
            # Example: 'Trip ID' for trips, 'Rental ID' for rentals, 'Plate No' for vehicles, 'Inv Number' for invoices, etc.
            # If no natural primary key, you might need to iterate or use doc_id (but doc_id is internal to Firestore)
            primary_key_map = {
                'trips': 'Trip ID',
                'rentals': 'Rental ID',
                'vehicles': 'Plate No',
                'invoices': 'Inv Number',
                'clients': 'Client Name',
                'employees': 'CPR No', # Assuming CPR No is unique for employees
                'payslips': 'Payslip ID',
                'leaves': ('Employee Name', 'Start Date', 'Leave Type'), # Composite key
                'vat_transactions': 'Related ID' # Or a composite key
            }
            pk_field = primary_key_map.get(collection_name_in_firestore)

            if pk_field:
                if isinstance(pk_field, tuple): # Composite key
                    for _, row in original_data_for_comparison.iterrows():
                        key_values = tuple(row[k] for k in pk_field if k in row)
                        original_data_dict_by_pk[key_values] = row.to_dict()
                    
                    # Create a temporary edited_df with doc_id from original for comparison
                    edited_df_temp_for_comparison = edited_df.copy()
                    edited_df_temp_for_comparison['doc_id'] = None # Initialize doc_id column
                    for index, row in edited_df_temp_for_comparison.iterrows():
                        key_values = tuple(row[k] for k in pk_field if k in row)
                        if key_values in original_data_dict_by_pk:
                            edited_df_temp_for_comparison.loc[index, 'doc_id'] = original_data_dict_by_pk[key_values].get('doc_id')
                    edited_data_dict_by_pk = {}
                    for _, row in edited_df_temp_for_comparison.iterrows():
                        key_values = tuple(row[k] for k in pk_field if k in row)
                        edited_data_dict_by_pk[key_values] = row.to_dict()

                else: # Single primary key
                    original_data_dict_by_pk = original_data_for_comparison.set_index(pk_field).to_dict(orient='index')
                    # To align with how edited_df might look, especially for 'doc_id'
                    edited_df_temp = edited_df.copy()
                    # Add doc_id back to edited_df_temp for comparison with original data's doc_id
                    for index, row in edited_df_temp.iterrows():
                        if row[pk_field] in original_data_dict_by_pk:
                            edited_df_temp.loc[index, 'doc_id'] = original_data_dict_by_pk[row[pk_field]].get('doc_id')
                    edited_data_dict_by_pk = edited_df_temp.set_index(pk_field).to_dict(orient='index')
            else:
                st.warning(f"No primary key defined for module '{module_name}'. Data edits might not be accurately reflected in Firestore.")
                # Fallback to direct comparison if no PK, but it's less robust for deletions
                original_data_dict_by_pk = {row.get('doc_id'): row for _, row in original_data_for_comparison.iterrows()}
                edited_data_dict_by_pk = {row.get('doc_id'): row for _, row in edited_df.iterrows() if 'doc_id' in row}


            updated_count = 0
            deleted_count = 0
            added_count = 0 # For newly added rows via data_editor

            # Identify deleted rows (rows in original that are NOT in edited_data_dict_by_pk)
            if pk_field:
                original_pks = set(original_data_dict_by_pk.keys())
                edited_pks = set(edited_data_dict_by_pk.keys())

                deleted_pks = original_pks - edited_pks
                for pk in deleted_pks:
                    doc_id_to_delete = original_data_dict_by_pk[pk].get('doc_id')
                    if doc_id_to_delete: # Only delete if a real Firestore doc_id exists
                        try:
                            if firestore_delete_document(actual_company_id_for_filter, collection_name_in_firestore, doc_id_to_delete):
                                deleted_count += 1
                        except Exception as e:
                            st.error(f"Error deleting document (PK: {pk}): {e}")

                # Identify updated and newly added rows
                for pk, edited_row_data in edited_data_dict_by_pk.items():
                    edited_doc_id = edited_row_data.get('doc_id')
                    
                    # Remove 'SL No' and 'doc_id' for comparison/storage
                    cleaned_edited_data = {k: v for k, v in edited_row_data.items() if k not in ['SL No', 'doc_id']}

                    if edited_doc_id and pk in original_data_dict_by_pk: # Existing row, potentially updated
                        original_row_data = original_data_dict_by_pk[pk]
                        cleaned_original_data = {k: v for k, v in original_row_data.items() if k not in ['SL No', 'doc_id']}
                        
                        if cleaned_edited_data != cleaned_original_data:
                            try:
                                if firestore_update_document(actual_company_id_for_filter, collection_name_in_firestore, edited_doc_id, cleaned_edited_data):
                                    updated_count += 1
                            except Exception as e:
                                st.error(f"Error updating document (PK: {pk}): {e}")
                    elif not edited_doc_id and pk not in original_pks: # New row added via data_editor
                        try:
                            firestore_add_document(actual_company_id_for_filter, collection_name_in_firestore, cleaned_edited_data)
                            added_count += 1
                        except Exception as e:
                            st.error(f"Error adding new document (PK: {pk}): {e}")
            else: # Fallback if no primary key strategy (less robust)
                if not edited_df.equals(display_df_with_slno):
                    st.warning("Data edits detected, but cannot granularly update/delete without a primary key. Refreshing to reflect changes from last save.")
                # Force a full refresh which re-fetches from Firestore
                st.rerun()


            if updated_count > 0 or deleted_count > 0 or added_count > 0:
                if updated_count > 0:
                    st.success(f"{updated_count} {module_name} entries updated in Firestore!")
                if deleted_count > 0:
                    st.success(f"{deleted_count} {module_name} entries deleted from Firestore!")
                if added_count > 0:
                    st.success(f"{added_count} new {module_name} entries added to Firestore!")
                st.rerun() # Rerun to display updated data from Firestore

        else: # If CRUD is not enabled, just display the dataframe
            st.dataframe(display_df_with_slno, use_container_width=True, hide_index=True)

        # --- New Invoice PDF Generation for Invoicing & Quoting module ---
        if module_name == "Invoicing & Quoting":
            st.subheader(f"Generate Specific Tax Invoice for {actual_company_name_for_filter}")
            
            # Removed Logo Width (mm) and Logo Height (mm) inputs as requested
            # Default logo position (can be made configurable later if needed)
            logo_x_pos = 10
            logo_y_pos = 10
            # Hardcoded logo dimensions as requested
            logo_width_fixed = 50
            logo_height_fixed = 30
            
            # Placeholder for the company's specific logo. Replace with actual hosted URL if available.
            logo_url_input = "https://placehold.co/50x30/FFFFFF/000000.png?text=Your+Company+Logo" 

            # Use current_company_data (pre-filtered by search term if any) for selection
            invoice_options = filtered_df['Inv Number'].tolist()
            if invoice_options:
                selected_invoice_number = st.selectbox(
                    "Select an Invoice to Generate PDF:",
                    ['--- Select Invoice ---'] + invoice_options,
                    key=f"{actual_company_id_for_filter}_select_invoice_for_pdf"
                )

                if selected_invoice_number and selected_invoice_number != '--- Select Invoice ---':
                    # Find the selected invoice data
                    selected_invoice_data = filtered_df[filtered_df['Inv Number'] == selected_invoice_number].iloc[0].to_dict()
                    
                     if st.button(f"Download Tax Invoice PDF for {selected_invoice_number}", key=f"{actual_company_id_for_filter}_{selected_invoice_number}_invoice_pdf_download"):
                         # Pass actual company name and pin for the invoice header
                         tax_invoice_pdf_data = generate_single_tax_invoice_pdf(
                             selected_invoice_data,
                             actual_company_name_for_filter,
                             st.session_state['USER_DB'][actual_company_id_for_filter]['company_pin'],
                             logo_url=logo_url_input,
                             logo_x=logo_x_pos,
                             logo_y=logo_y_pos,
                             logo_width=logo_width_fixed, # Using fixed width
                             logo_height=logo_height_fixed # Using fixed height
                         )
                         st.download_button(
                             label=f"Download Invoice {selected_invoice_number} PDF",
                             data=tax_invoice_pdf_data, # Data is already bytes
                             file_name=f"Tax_Invoice_{selected_invoice_number}.pdf",
                             mime="application/pdf",
                             key=f"{actual_company_id_for_filter}_{selected_invoice_number}_pdf_download_final"
                         )
                         st.success(f"Tax Invoice PDF for {selected_invoice_number} generated successfully!")
                 else:
                     st.info("No invoices available for PDF generation in the current view.")
             else:
                 st.info("No invoices available for PDF generation. Please add invoice entries first.")
        # --- End of New Invoice PDF Generation ---

        st.subheader(f"Download {module_name} Reports for {actual_company_name_for_filter}")
        col1, col2 = st.columns(2)
        with col1:
            excel_data = generate_excel_report(current_company_data.drop(columns=['doc_id'], errors='ignore'), f"{module_name}_Report_{actual_company_name_for_filter}")
            st.download_button(
                label=f"Download {module_name} Excel ({actual_company_name_for_filter})",
                data=excel_data,
                file_name=f"{module_name}_Report_{actual_company_name_for_filter}_{datetime.date.today()}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"{actual_company_id_for_filter}_{module_name}_excel_download"
            )
        with col2:
             pdf_data = generate_pdf_report(current_company_data.drop(columns=['doc_id'], errors='ignore'), f"{module_name} Report for {actual_company_name_for_filter}")
             st.download_button(
                 label=f"Download {module_name} PDF ({actual_company_name_for_filter})",
                 data=pdf_data, # Data is already bytes
                 file_name=f"Report_{module_name}_Report_{actual_company_name_for_filter}_{datetime.date.today()}.pdf",
                 mime="application/pdf",
                 key=f"{actual_company_id_for_filter}_{module_name}_pdf_download"
             )

        st.markdown("---")
        st.info("Note: Data is persisted in Firebase Firestore. Reloading the app will NOT reset data.")

# --- Specific Module Field Configurations (Updated for Invoicing & Quoting) ---
TRIP_MANAGEMENT_FIELDS = {
    'Trip Type': {'type': 'select', 'options': ['Per Trip', 'Daily', 'Monthly']},
    'Vehicle Type': {'type': 'select', 'options': ['Open', 'Box', 'Chiller', 'Frozen', 'Chiller Van', 'Passenger Van', 'Others']},
    'Pickup Address': {'type': 'text'},
    'Delivery Address': {'type': 'text'},
    'Client': {'type': 'text'}, # In real app, link to CRM clients
    'Vehicle': {'type': 'text'}, # In real app, link to Fleet vehicles
    'Assigned Driver': {'type': 'text'}, # In real app, link to Employees
    'Trip Category': {'type': 'select', 'options': ['Frozen', 'Dry', 'Hourly']},
    'Start Date & Time': {'type': 'datetime'},
    'End Date & Time': {'type': 'datetime'},
    'Status': {'type': 'select', 'options': ['Scheduled', 'Ongoing', 'Completed']},
    'Distance': {'type': 'number'},
    'Price': {'type': 'number'},
    'Fuel Charge / Surcharges': {'type': 'number'},
}

RENTAL_MANAGEMENT_FIELDS = {
    'Start Date': {'type': 'date'},
    'End Date': {'type': 'date'},
    'Client': {'type': 'text'},
    'Vehicle': {'type': 'text'},
    'Assigned Driver': {'type': 'text'},
    'Daily/Monthly Rate': {'type': 'number'},
    'VAT Exclusion': {'type': 'checkbox'},
    'Fuel Included': {'type': 'checkbox'},
    'Maintenance Notes': {'type': 'text'},
    'Status': {'type': 'select', 'options': ['Active', 'Returned']},
}

FLEET_MANAGEMENT_FIELDS = {
    'Vehicle Type': {'type': 'select', 'options': ['Open', 'Box', 'Chiller', 'Frozen', 'Chiller Van', 'Passenger Van', 'Others']},
    'Plate No': {'type': 'text'},
    'Type': {'type': 'text'},
    'Capacity': {'type': 'text'},
    'Registration Details': {'type': 'text'},
    'Insurance Details': {'type': 'text'},
    'Maintenance History': {'type': 'text'},
    'Service Alerts': {'type': 'text'},
    'Odometer Log': {'type': 'number'},
    'Fuel Tracking': {'type': 'text'},
    'Availability Status': {'type': 'select', 'options': ['In Use', 'Rented', 'Out of Service']},
}

INVOICING_QUOTING_FIELDS = {
    'Date': {'type': 'date'},
    'Particulars': {'type': 'text'}, # New field for invoice line item description
    'Amount': {'type': 'number'},
    'VAT (10%)': {'type': 'number'},
    'Total Amount': {'type': 'number'},
    'VAT Option': {'type': 'select', 'options': ['Include', 'Exclude']},
    'Linked ID': {'type': 'text'}, # Trip or Rental ID
    'Remarks': {'type': 'text'}, # New field for remarks
}

CRM_MANAGEMENT_FIELDS = {
    'Client Name': {'type': 'text'},
    'Client Type': {'type': 'select', 'options': ['Rental', 'Logistics', 'Both']},
    'Contact Person': {'type': 'text'},
    'Contract Details': {'type': 'text'},
    'Communication Log': {'type': 'text'},
    'Payment Terms': {'type': 'text'},
    'VAT Profile': {'type': 'text'},
    'Credit Limit': {'type': 'number'},
}

EMPLOYEE_MANAGEMENT_FIELDS = {
    'Name': {'type': 'text'},
    'Designation': {'type': 'text'},
    'Employee Type': {'type': 'select', 'options': ['Driver', 'Admin', 'Mechanic']},
    'CPR No': {'type': 'text'},
    'License No': {'type': 'text'},
    'License Exp': {'type': 'date'},
    'Passport Num': {'type': 'text'},
    'Visa Exp': {'type': 'date'},
    'Nationality': {'type': 'text'},
    'Assigned Vehicle History': {'type': 'text'},
    'Availability Status': {'type': 'select', 'options': ['On leave', 'Active']},
    'ID/Passport/DL Uploads': {'type': 'file'},
}

PAYROLL_FIELDS = {
    'Employee Name': {'type': 'text'},
    'Month': {'type': 'select', 'options': [str(i) for i in range(1, 13)]},
    'Year': {'type': 'select', 'options': [str(i) for i in range(2020, datetime.datetime.now().year + 2)]},
    'Base Salary': {'type': 'number'},
    'Trip Bonus': {'type': 'number'},
    'Rental Commission': {'type': 'number'},
    'Deductions': {'type': 'number'},
    'Overtime': {'type': 'number'},
    'Net Salary': {'type': 'number'}, # This would be calculated
    'Payment Status': {'type': 'select', 'options': ['Paid', 'Unpaid']},
}

PLANNING_TIMEOFF_FIELDS = {
    'Employee Name': {'type': 'text'},
    'Leave Type': {'type': 'text'},
    'Start Date': {'type': 'date'},
    'End Date': {'type': 'date'},
    'Status': {'type': 'select', 'options': ['Pending', 'Approved', 'Rejected']},
}

VAT_INPUT_OUTPUT_FIELDS = {
    'Transaction Type': {'type': 'select', 'options': ['Input VAT', 'Output VAT']},
    'Date': {'type': 'date'},
    'Amount': {'type': 'number'},
    'VAT Amount': {'type': 'number'},
    'Description': {'type': 'text'},
    'Related ID': {'type': 'text'},
}


# --- Authentication and Main App Flow ---

def login_page():
    st.title("Logistic Management System")
    st.image("https://placehold.co/600x150/EEEEEE/313131?text=Your+Company+Logo", use_column_width=True) # Placeholder for a logo
    st.markdown("---")
    st.subheader("Login to Your Company Account")

    with st.form(key="main_login_form"):
        # Get list of company names for the selectbox
        company_names = sorted([details['company_name'] for details in st.session_state['USER_DB'].values()])
        selected_company_name = st.selectbox("Select Your Company", options=company_names, key="login_company_select")

        # Get the company_id based on the selected company name
        selected_company_id = None
        for comp_id, comp_details in st.session_state['USER_DB'].items():
            if comp_details['company_name'] == selected_company_name:
                selected_company_id = comp_id
                break

        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        
        login_button = st.form_submit_button("Login")

        if login_button:
            if selected_company_id and username and password:
                users_in_company = st.session_state['USER_DB'][selected_company_id]['users']
                if username in users_in_company:
                    stored_password_hash = users_in_company[username]['password_hash']
                    if bcrypt.checkpw(password.encode('utf-8'), stored_password_hash.encode('utf-8')):
                        st.session_state['logged_in'] = True
                        st.session_state['company_id'] = selected_company_id
                        st.session_state['user_id'] = username
                        st.session_state['company_name'] = selected_company_name
                        st.session_state['role'] = users_in_company[username]['role']
                        st.success(f"Logged in as {username} for {st.session_state['company_name']}!")
                        st.rerun()
                    else:
                        st.error("Invalid Username or Password.")
                else:
                    st.error("Invalid Username or Password.")
            else:
                st.error("Please select a company and enter username/password.")


def main_app():
    # Access USER_DB from session_state for dynamic display
    USER_DB_CURRENT = st.session_state['USER_DB']

    if st.session_state['role'] == 'admin':
        st.sidebar.title("Management Dashboard")
        st.sidebar.write(f"Logged in as: {st.session_state['user_id']}")
        st.sidebar.write("Role: **Admin**")

        menu_options = ["Overall Dashboard", "Analysis Dashboard", "Cross-Company Reports", "User & Company Management", "View Company Modules"]
        
        if st.session_state.get('set_admin_nav_to_view_modules'):
            st.session_state['admin_nav'] = "View Company Modules"
            del st.session_state['set_admin_nav_to_view_modules']

        if 'admin_nav' not in st.session_state:
            st.session_state['admin_nav'] = "Overall Dashboard"

        menu_selection = st.sidebar.radio(
            "Navigation",
            options=menu_options,
            key="admin_nav"
        )

        total_companies_count = 0
        total_vehicles_all = 0
        total_employees_all = 0
        total_revenue_all = 0.0
        total_trips_all = 0
        total_rentals_all = 0
        total_payslips_net_salary_all = 0.0
        total_leaves_all = 0
        total_vat_amount_all = 0.0

        # Fetch all operational data from Firestore for admin dashboard calculations
        all_companies_operational_data = {}
        # Iterate through all company IDs from the in-memory USER_DB (excluding admin company)
        # to ensure we fetch data for all known operational companies.
        operational_company_ids = [comp_id for comp_id, details in USER_DB_CURRENT.items() if details['company_pin'] != 'ADMIN']

        for module_name_key in ['trips', 'rentals', 'vehicles', 'invoices', 'clients', 'employees', 'payslips', 'leaves', 'vat_transactions']:
            # For admin, get data across ALL operational companies by iterating
            combined_module_df = pd.DataFrame()
            for comp_id in operational_company_ids:
                df_for_comp = firestore_get_collection(comp_id, module_name_key)
                if not df_for_comp.empty:
                    combined_module_df = pd.concat([combined_module_df, df_for_comp], ignore_index=True)
            all_companies_operational_data[module_name_key] = combined_module_df


        # This loop calculates the totals for all admin dashboard sections
        for company_id_key, company_details in USER_DB_CURRENT.items():
            if company_details['company_pin'] != 'ADMIN':
                total_companies_count += 1
                comp_name = company_details['company_name']
                
                if 'vehicles' in all_companies_operational_data and 'Company' in all_companies_operational_data['vehicles'].columns:
                    comp_vehicles_df = all_companies_operational_data['vehicles'][all_companies_operational_data['vehicles']['Company'] == comp_name]
                    total_vehicles_all += len(comp_vehicles_df)

                if 'employees' in all_companies_operational_data and 'Company' in all_companies_operational_data['employees'].columns:
                    comp_employees_df = all_companies_operational_data['employees'][all_companies_operational_data['employees']['Company'] == comp_name]
                    total_employees_all += len(comp_employees_df)

                if 'invoices' in all_companies_operational_data and 'Company' in all_companies_operational_data['invoices'].columns:
                    comp_invoices_df = all_companies_operational_data['invoices'][all_companies_operational_data['invoices']['Company'] == comp_name]
                    total_revenue_all += comp_invoices_df['Total Amount'].sum() if 'Total Amount' in comp_invoices_df.columns else 0.0

                if 'trips' in all_companies_operational_data and 'Company' in all_companies_operational_data['trips'].columns:
                    comp_trips_df = all_companies_operational_data['trips'][all_companies_operational_data['trips']['Company'] == comp_name]
                    total_trips_all += len(comp_trips_df)

                if 'rentals' in all_companies_operational_data and 'Company' in all_companies_operational_data['rentals'].columns:
                    comp_rentals_df = all_companies_operational_data['rentals'][all_companies_operational_data['rentals']['Company'] == comp_name]
                    total_rentals_all += len(comp_rentals_df)

                if 'payslips' in all_companies_operational_data and 'Company' in all_companies_operational_data['payslips'].columns:
                    comp_payslips_df = all_companies_operational_data['payslips'][all_companies_operational_data['payslips']['Company'] == comp_name]
                    total_payslips_net_salary_all += comp_payslips_df['Net Salary'].sum() if 'Net Salary' in comp_payslips_df.columns else 0.0
                
                if 'leaves' in all_companies_operational_data and 'Company' in all_companies_operational_data['leaves'].columns:
                    comp_leaves_df = all_companies_operational_data['leaves'][all_companies_operational_data['leaves']['Company'] == comp_name]
                    total_leaves_all += len(comp_leaves_df)

                if 'vat_transactions' in all_companies_operational_data and 'Company' in all_companies_operational_data['vat_transactions'].columns:
                    comp_vat_df = all_companies_operational_data['vat_transactions'][all_companies_operational_data['vat_transactions']['Company'] == comp_name]
                    total_vat_amount_all += comp_vat_df['VAT Amount'].sum() if 'VAT Amount' in comp_vat_df.columns else 0.0

        st.title("Admin / Management Dashboard")
        if menu_selection == "Overall Dashboard":
            st.subheader("Key Performance Indicators Across All Companies")
            
            col_comp, col_v, col_e, col_r = st.columns(4)
            with col_comp:
                st.metric("Total Companies", total_companies_count)
            with col_v:
                st.metric("Total Vehicles", total_vehicles_all)
            with col_e:
                st.metric("Total Employees", total_employees_all)
            with col_r:
                st.metric("Total Revenue", f"INR {total_revenue_all:,.2f}")

            st.markdown("---")
            st.subheader("Aggregated Module Statistics (All Companies)")

            col_t, col_rent, col_pay = st.columns(3)
            with col_t:
                st.metric("Total Trips", total_trips_all)
            with col_rent:
                st.metric("Total Rentals", total_rentals_all)
            with col_pay:
                st.metric("Total Net Salary Paid", f"INR {total_payslips_net_salary_all:,.2f}")
            
            col_l, col_vat = st.columns(2)
            with col_l:
                st.metric("Total Leave Requests", total_leaves_all)
            with col_vat:
                st.metric("Total VAT Processed", f"INR {total_vat_amount_all:,.2f}")


            st.markdown("---")
            st.info("This section displays aggregated data, charts, and summaries from all companies.")
            st.warning("Data is persisted in Firebase Firestore.")

        elif menu_selection == "Analysis Dashboard":
            st.subheader("Cross-Company Analytical Insights")

            st.markdown("#### Overall Revenue Performance")
            gauge_max_revenue = max(total_revenue_all * 1.5, 100000.0) if total_revenue_all > 0 else 100000.0

            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=total_revenue_all,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Total Revenue (INR)"},
                gauge={
                    'axis': {'range': [None, gauge_max_revenue], 'tickwidth': 1, 'tickcolor': "darkblue"},
                    'bar': {'color': "darkgreen"},
                    'bgcolor': "white",
                    'borderwidth': 2,
                    'bordercolor': "gray",
                    'steps': [
                        {'range': [0, gauge_max_revenue * 0.5], 'color': 'lightgray'},
                        {'range': [gauge_max_revenue * 0.5, gauge_max_revenue], 'color': 'gray'}],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': gauge_max_revenue * 0.8}
                }
            ))
            st.plotly_chart(fig_gauge, use_container_width=True)

            st.markdown("#### Vehicle Distribution by Type (All Companies)")
            all_vehicles_df = all_companies_operational_data.get('vehicles', pd.DataFrame())
            if not all_vehicles_df.empty:
                vehicle_type_counts = all_vehicles_df['Vehicle Type'].value_counts().reset_index()
                vehicle_type_counts.columns = ['Vehicle Type', 'Count']
                fig_donut = px.pie(
                    vehicle_type_counts,
                    values='Count',
                    names='Vehicle Type',
                    title='Total Vehicles by Type',
                    hole=0.4
                )
                st.plotly_chart(fig_donut, use_container_width=True)
            else:
                st.info("No vehicle data available for analysis yet.")

            st.markdown("#### Revenue Per Company")
            revenue_data_list = []
            for comp_id_key, comp_details in USER_DB_CURRENT.items():
                if comp_details['company_pin'] != 'ADMIN':
                    comp_name = comp_details['company_name']
                    comp_invoices_df = all_companies_operational_data.get('invoices', pd.DataFrame())
                    company_revenue = 0.0
                    if not comp_invoices_df.empty and 'Company' in comp_invoices_df.columns:
                        company_revenue = comp_invoices_df[comp_invoices_df['Company'] == comp_name]['Total Amount'].sum() if 'Total Amount' in comp_invoices_df.columns else 0.0
                    revenue_data_list.append({'Company': comp_name, 'Revenue': company_revenue})
            
            revenue_by_company_df = pd.DataFrame(revenue_data_list)

            if not revenue_by_company_df.empty and revenue_by_company_df['Revenue'].sum() > 0:
                fig_revenue_bar = px.bar(
                    revenue_by_company_df,
                    x='Company',
                    y='Revenue',
                    title='Total Revenue by Company',
                    labels={'Revenue': 'Total Revenue (INR)'},
                    color='Company'
                )
                st.plotly_chart(fig_revenue_bar, use_container_width=True)
            else:
                st.info("No revenue data available for analysis yet.")

            st.markdown("#### Employees Per Company")
            employee_data_list = []
            for comp_id_key, comp_details in USER_DB_CURRENT.items():
                if comp_details['company_pin'] != 'ADMIN':
                    comp_name = comp_details['company_name']
                    comp_employees_df = all_companies_operational_data.get('employees', pd.DataFrame())
                    num_employees = 0
                    if not comp_employees_df.empty and 'Company' in comp_employees_df.columns:
                        num_employees = len(comp_employees_df[comp_employees_df['Company'] == comp_name])
                    employee_data_list.append({'Company': comp_name, 'Employees': num_employees})
            
            employees_by_company_df = pd.DataFrame(employee_data_list)

            if not employees_by_company_df.empty and employees_by_company_df['Employees'].sum() > 0:
                fig_employee_bar = px.bar(
                    employees_by_company_df,
                    x='Company',
                    y='Employees',
                    title='Number of Employees by Company',
                    labels={'Employees': 'Number of Employees'},
                    color='Company'
                )
                st.plotly_chart(fig_employee_bar, use_container_width=True)
            else:
                st.info("No employee data available for analysis yet.")

            st.markdown("#### Total Trips Per Company")
            trips_data_list = []
            for comp_id_key, comp_details in USER_DB_CURRENT.items():
                if comp_details['company_pin'] != 'ADMIN':
                    comp_name = comp_details['company_name']
                    comp_trips_df = all_companies_operational_data.get('trips', pd.DataFrame())
                    num_trips = 0
                    if not comp_trips_df.empty and 'Company' in comp_trips_df.columns:
                        num_trips = len(comp_trips_df[comp_trips_df['Company'] == comp_name])
                    trips_data_list.append({'Company': comp_name, 'Total Trips': num_trips})
            
            trips_by_company_df = pd.DataFrame(trips_data_list)

            if not trips_by_company_df.empty and trips_by_company_df['Total Trips'].sum() > 0:
                fig_trips_bar = px.bar(
                    trips_by_company_df,
                    x='Company',
                    y='Total Trips',
                    title='Total Number of Trips by Company',
                    labels={'Total Trips': 'Number of Trips'},
                    color='Company'
                )
                st.plotly_chart(fig_trips_bar, use_container_width=True)
            else:
                st.info("No trip data available for this chart yet.")

            st.markdown("#### Total Entries Across All Modules (All Companies)")
            module_counts = {}
            for module_name, df in all_companies_operational_data.items():
                if module_name not in ['users', 'management_company'] :
                    operational_df = df[df['Company'] != 'Global Management'] if 'Company' in df.columns else df
                    module_counts[module_name.replace('_', ' ').title()] = len(operational_df)

            module_counts_df = pd.DataFrame(list(module_counts.items()), columns=['Module', 'Count'])

            if not module_counts_df.empty and module_counts_df['Count'].sum() > 0:
                fig_all_modules_bar = px.bar(
                    module_counts_df,
                    x='Module',
                    y='Count',
                    title='Total Entries by Module (All Companies)',
                    labels={'Count': 'Number of Entries'},
                    color='Module'
                )
                st.plotly_chart(fig_all_modules_bar, use_container_width=True)
            else:
                st.info("No data available across all modules for this chart yet.")


            st.markdown("---")
            st.info("These charts provide a visual summary of your companies' performance.")
            st.warning("Data is persisted in Firebase Firestore.")


        elif menu_selection == "Cross-Company Reports":
            st.subheader("Generate Cross-Company Reports and Consolidated Data")
            st.info("This section provides reports that combine data from ALL operational companies in the system.")
            
            st.markdown("#### Consolidated Operational Data Overview (All Companies)")
            all_operational_data_concat = pd.DataFrame()
            for module_name_key, df in all_companies_operational_data.items():
                if not df.empty and 'Company' in df.columns:
                    filtered_df_for_concat = df[df['Company'] != 'Global Management'].copy()
                    if not filtered_df_for_concat.empty:
                        filtered_df_for_concat['Module'] = module_name_key.replace('_', ' ').title()
                        all_operational_data_concat = pd.concat([all_operational_data_concat, filtered_df_for_concat], ignore_index=True)

            if not all_operational_data_concat.empty:
                st.dataframe(add_serial_numbers(all_operational_data_concat.drop(columns=['doc_id'], errors='ignore')), use_container_width=True, hide_index=True)
                col_ex_overall, col_pdf_overall = st.columns(2)
                with col_ex_overall:
                    st.download_button(
                        label="Download All Companies Consolidated Excel",
                        data=generate_excel_report(all_operational_data_concat.drop(columns=['doc_id'], errors='ignore'), "All_Companies_Consolidated_Report"),
                        file_name=f"All_Companies_Consolidated_Report_{datetime.date.today()}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="all_companies_consolidated_excel_download"
                    )
                 with col_pdf_overall:
                     st.download_button(
                         label="Download All Companies Consolidated PDF",
                         data=generate_pdf_report(all_operational_data_concat.drop(columns=['doc_id'], errors='ignore'), "All Companies Consolidated Report"),
                         file_name=f"All_Companies_Consolidated_Report_{datetime.date.today()}.pdf",
                         mime="application/pdf",
                         key="all_companies_consolidated_pdf_download"
                     )
            else:
                st.info("No operational data available across all companies yet. Please add data using individual company logins.")

            st.markdown("---")
            st.subheader("Specific Cross-Company Reports")
            all_trips_df = all_companies_operational_data.get('trips', pd.DataFrame())
            if not all_trips_df.empty:
                st.markdown("#### All Trips Overview (All Companies)")
                st.dataframe(add_serial_numbers(all_trips_df.drop(columns=['doc_id'], errors='ignore')), use_container_width=True, hide_index=True)
                col_ex, col_pdf = st.columns(2)
                with col_ex:
                    st.download_button(
                        label="Download All Trips Excel",
                        data=generate_excel_report(all_trips_df.drop(columns=['doc_id'], errors='ignore'), "All_Trips_Report"),
                        file_name=f"All_Trips_Report_{datetime.date.today()}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="all_trips_excel_download"
                    )
                 with col_pdf:
                     st.download_button(
                         label="Download All Trips PDF",
                         data=generate_pdf_report(all_trips_df.drop(columns=['doc_id'], errors='ignore'), "All Trips Report"),
                         file_name=f"All_Trips_Report_{datetime.date.today()}.pdf",
                         mime="application/pdf",
                         key="all_trips_pdf_download"
                     )
            else:
                st.info("No trip data available for cross-company reports yet.")
            
            st.markdown("---")
            st.markdown("#### Custom Management Report (PDF with Company Details)")
            st.write("This PDF report provides an overview of all companies, including their individual vehicle counts, employees, and financial summaries.")
             if st.button("Download Management Report (PDF)", key="download_management_pdf_final"):
                 management_pdf_data = generate_management_pdf_report(all_companies_operational_data, USER_DB_CURRENT)
                 st.download_button(
                     label="Download Management Report PDF",
                     data=management_pdf_data,
                     file_name=f"Management_Report_{datetime.date.today()}.pdf",
                     mime="application/pdf",
                     key="management_pdf_download_final"
                 )


        elif menu_selection == "User & Company Management":
            st.subheader("Manage System Users and Companies")
            st.info("Click 'View Details' on a company card to see its operational modules, or use 'View Company Modules' in the sidebar to directly select a company.")
            
            operational_companies = {cid: cdetails for cid, cdetails in USER_DB_CURRENT.items() if cdetails['company_pin'] != 'ADMIN'}
            
            num_columns = 3
            cols = st.columns(num_columns)

            company_list_for_display = sorted(list(operational_companies.items()), key=lambda item: item[1]['company_name'])

            for i, (comp_id, comp_details) in enumerate(company_list_for_display):
                with cols[i % num_columns]:
                    st.markdown(f"**{comp_details['company_name']}**")
                    st.markdown(f"PIN: `{comp_details['company_pin']}`")
                    st.markdown(f"Users: {len(comp_details['users'])}")
                    
                    if st.button(f"View Details for {comp_details['company_name']}", key=f"view_company_details_{comp_id}"):
                        st.session_state['admin_selected_company_for_modules_name'] = comp_details['company_name']
                        st.session_state['set_admin_nav_to_view_modules'] = True
                        st.rerun()
                if (i + 1) % num_columns == 0 and (i + 1) < len(company_list_for_display):
                    st.markdown("---")

            st.markdown("---")


        elif menu_selection == "View Company Modules":
            st.subheader("View Individual Company Operational Data")
            operational_companies = {cid: cdetails for cid, cdetails in USER_DB_CURRENT.items() if cdetails['company_pin'] != 'ADMIN'}
            
            company_names = sorted([details['company_name'] for details in operational_companies.values()])
            
            default_index = 0
            if st.session_state['admin_selected_company_for_modules_name'] and st.session_state['admin_selected_company_for_modules_name'] in company_names:
                default_index = company_names.index(st.session_state['admin_selected_company_for_modules_name']) + 1

            selected_company_name_for_modules = st.selectbox(
                "Select a Company to View its Modules:", 
                ['--- Select a Company ---'] + company_names,
                index=default_index,
                key="admin_select_company_for_modules"
            )
            st.session_state['admin_selected_company_for_modules_name'] = None 


            if selected_company_name_for_modules and selected_company_name_for_modules != '--- Select a Company ---':
                selected_company_id_for_modules = None
                for comp_id, comp_details in USER_DB_CURRENT.items():
                    if comp_details['company_name'] == selected_company_name_for_modules:
                        selected_company_id_for_modules = comp_id
                        break
                
                if not selected_company_id_for_modules:
                    st.error("Error: Could not retrieve company ID for the selected company name.")
                    return

                st.markdown(f"### Showing Modules for: {selected_company_name_for_modules}")
                st.markdown("---")

                if selected_company_id_for_modules:
                    st.subheader(f"Company Details: {selected_company_name_for_modules}")
                    col_name, col_pin, col_users = st.columns(3)
                    with col_name:
                        st.info(f"**Company Name:**\n\n {selected_company_name_for_modules}")
                    with col_pin:
                        st.info(f"**Company PIN:**\n\n {USER_DB_CURRENT[selected_company_id_for_modules]['company_pin']}")
                    with col_users:
                        st.info(f"**Number of Users:**\n\n {len(USER_DB_CURRENT[selected_company_id_for_modules]['users'])}")
                    st.markdown("---")

                display_module("Trip", TRIP_MANAGEMENT_FIELDS, sample_data_key='trips', crud_enabled=True, company_filter_id=selected_company_id_for_modules)

                display_module("Rental", RENTAL_MANAGEMENT_FIELDS, sample_data_key='rentals', crud_enabled=True, company_filter_id=selected_company_id_for_modules)
                
                display_module("Fleet", FLEET_MANAGEMENT_FIELDS, sample_data_key='vehicles', crud_enabled=True, company_filter_id=selected_company_id_for_modules)

                display_module("Invoicing & Quoting", INVOICING_QUOTING_FIELDS, sample_data_key='invoices', crud_enabled=True, company_filter_id=selected_company_id_for_modules)

                display_module("CRM / Customer Management", CRM_MANAGEMENT_FIELDS, sample_data_key='clients', crud_enabled=True, company_filter_id=selected_company_id_for_modules)

                display_module("Employee", EMPLOYEE_MANAGEMENT_FIELDS, sample_data_key='employees', crud_enabled=True, company_filter_id=selected_company_id_for_modules)

                with st.expander(f"**Payroll Management**"):
                    st.header("Payroll Management")
                    current_company_payslips = firestore_get_collection(selected_company_id_for_modules, 'payslips')

                    st.subheader(f"Generate Payslip for {selected_company_name_for_modules}")
                    employee_name = st.text_input(f"Employee Name (for Payslip) ({selected_company_name_for_modules})", key=f"admin_{selected_company_id_for_modules}_payroll_emp_name")
                    payslip_month = st.selectbox(f"Month ({selected_company_name_for_modules})", options=[str(i) for i in range(1, 13)], key=f"admin_{selected_company_id_for_modules}_payroll_month")
                    payslip_year = st.selectbox(f"Year ({selected_company_name_for_modules})", options=[str(i) for i in range(2020, datetime.datetime.now().year + 2)], key=f"admin_{selected_company_id_for_modules}_payroll_year")
                    base_salary = st.number_input(f"Base Salary ({selected_company_name_for_modules})", value=0.0, key=f"admin_{selected_company_id_for_modules}_payroll_base_salary")
                    trip_bonus = st.number_input(f"Trip Bonus ({selected_company_name_for_modules})", value=0.0, key=f"admin_{selected_company_id_for_modules}_payroll_trip_bonus")
                    rental_commission = st.number_input(f"Rental Commission ({selected_company_name_for_modules})", value=0.0, key=f"admin_{selected_company_id_for_modules}_payroll_rental_commission")
                    deductions = st.number_input(f"Deductions ({selected_company_name_for_modules})", value=0.0, key=f"admin_{selected_company_id_for_modules}_payroll_deductions")
                    overtime = st.number_input(f"Overtime ({selected_company_name_for_modules})", value=0.0, key=f"admin_{selected_company_id_for_modules}_payroll_overtime")

                    net_salary = base_salary + trip_bonus + rental_commission + overtime - deductions
                    st.write(f"Calculated Net Salary: **INR {net_salary:.2f}**")

                    if st.button(f"Generate Payslip for {selected_company_name_for_modules}", key=f"admin_{selected_company_id_for_modules}_generate_payslip_btn"):
                        existing_payslip_check = current_company_payslips[
                            (current_company_payslips['Employee Name'] == employee_name) &
                            (current_company_payslips['Month'] == payslip_month) &
                            (current_company_payslips['Year'] == payslip_year)
                        ]
                        
                        payslip_data = {
                            'Company': selected_company_name_for_modules,
                            'Payslip ID': f"PS_{employee_name[:3].upper()}_{payslip_month}{payslip_year}_{datetime.datetime.now().strftime('%H%M%S%f')}",
                            'Employee Name': employee_name, 'Month': payslip_month, 'Year': payslip_year,
                            'Base Salary': base_salary, 'Trip Bonus': trip_bonus,
                            'Rental Commission': rental_commission, 'Deductions': deductions,
                            'Overtime': overtime, 'Net Salary': net_salary, 'Payment Status': 'Unpaid'
                        }

                        if not existing_payslip_check.empty:
                            st.warning(f"A payslip for {employee_name} for {payslip_month}/{payslip_year} already exists in {selected_company_name_for_modules}. Do you want to overwrite it?")
                            col_confirm_yes, col_confirm_no = st.columns(2)
                            with col_confirm_yes:
                                if st.button("Confirm Overwrite", key=f"admin_{selected_company_id_for_modules}_confirm_overwrite"):
                                    doc_id_to_overwrite = existing_payslip_check['doc_id'].iloc[0]
                                    try:
                                        firestore_update_document(selected_company_id_for_modules, 'payslips', doc_id_to_overwrite, payslip_data)
                                        st.success("Payslip overwritten and regenerated successfully!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error overwriting payslip: {e}")
                            with col_confirm_no:
                                if st.button("Cancel", key=f"admin_{selected_company_id_for_modules}_cancel_overwrite"):
                                    st.info("Payslip generation cancelled.")
                        else:
                            try:
                                firestore_add_document(selected_company_id_for_modules, 'payslips', payslip_data)
                                st.success("Payslip generated successfully!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error generating payslip: {e}")

                    st.subheader(f"Payroll History for {selected_company_name_for_modules}")
                    display_df = add_serial_numbers(current_company_payslips.drop(columns=['doc_id'], errors='ignore'))

                    edited_payslip_df = st.data_editor(
                        display_df,
                        key=f"admin_{selected_company_id_for_modules}_payslip_history_editor",
                        hide_index=True,
                        num_rows="dynamic",
                        use_container_width=True
                    )
                    
                    original_payslip_data_for_comparison = firestore_get_collection(selected_company_id_for_modules, 'payslips')
                    original_payslip_data_dict = original_payslip_data_for_comparison.set_index('Payslip ID').to_dict(orient='index')
                    edited_payslip_data_dict_temp = edited_payslip_df.copy()
                    for index, row in edited_payslip_data_dict_temp.iterrows():
                        if row['Payslip ID'] in original_payslip_data_dict:
                            edited_payslip_data_dict_temp.loc[index, 'doc_id'] = original_payslip_data_dict[row['Payslip ID']].get('doc_id')
                    edited_payslip_data_dict = edited_payslip_data_dict_temp.set_index('Payslip ID').to_dict(orient='index')

                    updated_payslip_count = 0
                    deleted_payslip_count = 0
                    added_payslip_count = 0

                    deleted_payslip_ids = set(original_payslip_data_dict.keys()) - set(edited_payslip_data_dict.keys())
                    for payslip_id in deleted_payslip_ids:
                        doc_id_to_delete = original_payslip_data_dict[payslip_id]['doc_id']
                        if doc_id_to_delete:
                            try:
                                if firestore_delete_document(selected_company_id_for_modules, 'payslips', doc_id_to_delete):
                                    deleted_payslip_count += 1
                            except Exception as e:
                                st.error(f"Error deleting payslip {payslip_id}: {e}")

                    for payslip_id, edited_row_data in edited_payslip_data_dict.items():
                        edited_doc_id = edited_row_data.get('doc_id')
                        cleaned_edited_data = {k: v for k, v in edited_row_data.items() if k not in ['SL No', 'doc_id']}

                        if edited_doc_id and payslip_id in original_payslip_data_dict:
                            original_row_data = original_payslip_data_dict[payslip_id]
                            cleaned_original_data = {k: v for k, v in original_row_data.items() if k not in ['SL No', 'doc_id']}
                            
                            if cleaned_edited_data != cleaned_original_data:
                                try:
                                    if firestore_update_document(selected_company_id_for_modules, 'payslips', edited_doc_id, cleaned_edited_data):
                                        updated_payslip_count += 1
                                except Exception as e:
                                    st.error(f"Error updating payslip {payslip_id}: {e}")
                        elif not edited_doc_id and payslip_id not in original_payslip_data_dict:
                            try:
                                firestore_add_document(selected_company_id_for_modules, 'payslips', cleaned_edited_data)
                                added_payslip_count += 1
                            except Exception as e:
                                st.error(f"Error adding new payslip {payslip_id}: {e}")
                    
                    if updated_payslip_count > 0 or deleted_payslip_count > 0 or added_payslip_count > 0:
                        if updated_payslip_count > 0:
                            st.success(f"{updated_payslip_count} Payslip entries updated successfully!")
                        if deleted_payslip_count > 0:
                            st.success(f"{deleted_payslip_count} Payslip entries deleted successfully!")
                        if added_payslip_count > 0:
                            st.success(f"{added_payslip_count} new Payslip entries added successfully!")
                        st.rerun()

                    st.subheader(f"Download Payslip Reports for {selected_company_name_for_modules}")
                    col1, col2 = st.columns(2)
                    with col1:
                        excel_data = generate_excel_report(current_company_payslips.drop(columns=['doc_id'], errors='ignore'), f"Payroll_Report_{selected_company_name_for_modules}")
                        st.download_button(
                            label=f"Download Payroll Excel ({selected_company_name_for_modules})",
                            data=excel_data,
                            file_name=f"Payroll_Report_{selected_company_name_for_modules}_{datetime.date.today()}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key=f"admin_{selected_company_id_for_modules}_payroll_excel_download"
                        )
                     with col2:
                         pdf_data = generate_pdf_report(current_company_payslips.drop(columns=['doc_id'], errors='ignore'), f"Payroll Report ({selected_company_name_for_modules})")
                         st.download_button(
                             label=f"Download Payroll PDF ({selected_company_name_for_modules})",
                             data=pdf_data,
                             file_name=f"Payroll_Report_{selected_company_name_for_modules}_{datetime.date.today()}.pdf",
                             mime="application/pdf",
                             key=f"admin_{selected_company_id_for_modules}_payroll_pdf_download"
                         )

                    st.markdown("---")

                display_module("Planning & Time Off", PLANNING_TIMEOFF_FIELDS, sample_data_key='leaves', crud_enabled=True, company_filter_id=selected_company_id_for_modules)

                display_module("VAT Input/Output", VAT_INPUT_OUTPUT_FIELDS, sample_data_key='vat_transactions', crud_enabled=True, company_filter_id=selected_company_id_for_modules)
                
                 with st.expander(f"**VAT Return Report for {selected_company_name_for_modules}**"):
                     st.subheader(f"VAT Return Report ({selected_company_name_for_modules}) (Placeholder)")
                     st.info("Automate VAT calculation and generate VAT return reports here.")
                     if st.button(f"Generate VAT Return Report ({selected_company_name_for_modules})", key=f"admin_{selected_company_id_for_modules}_generate_vat_report"):
                         vat_data_for_report = firestore_get_collection(selected_company_id_for_modules, 'vat_transactions')
                         vat_report_pdf = generate_pdf_report(vat_data_for_report.drop(columns=['doc_id'], errors='ignore'), f"VAT Return Report for {selected_company_name_for_modules}")
                         st.download_button(
                             label=f"Download VAT Return Report PDF ({selected_company_name_for_modules})",
                             data=vat_report_pdf,
                             file_name=f"VAT_Return_Report_{selected_company_name_for_modules}_{datetime.date.today()}.pdf",
                             mime="application/pdf",
                             key=f"admin_{selected_company_id_for_modules}_vat_pdf_download"
                         )
                         st.success(f"VAT Return Report generated (placeholder) for {selected_company_name_for_modules}.")


            else:
                st.info("Please select a company from the dropdown to view its detailed module data.")


    else: # Regular user dashboard
        st.sidebar.title(f"{st.session_state['company_name']} Dashboard")
        st.sidebar.write(f"Logged in as: {st.session_state['user_id']}")
        st.sidebar.write(f"Company ID: `{st.session_state['company_id']}`")

        menu_options = [
            "Home Dashboard",
            "Trip Management",
            "Rental Management",
            "Fleet Management",
            "Invoicing & Quoting",
            "CRM / Customer Management",
            "Employee Management",
            "Payroll",
            "Planning & Time Off",
            "Reports Dashboard",
            "VAT Input/Output"
        ]
        selected_module = st.sidebar.radio("Modules", menu_options, key="user_nav")

        st.title(f"{st.session_state['company_name']} - {selected_module}")

        if selected_module == "Home Dashboard":
            st.subheader("Welcome to Your Company's Dashboard!")
            st.info("This section will provide key performance indicators and summaries specific to your company.")
            st.write("E.g., Number of Ongoing Trips, Recent Rentals, Fleet Availability, Revenue this month.")
            st.warning("Data is persisted in Firebase Firestore.")


        elif selected_module == "Trip Management":
            display_module("Trip", TRIP_MANAGEMENT_FIELDS, sample_data_key='trips', crud_enabled=True, company_filter_id=st.session_state['company_id'])

        elif selected_module == "Rental Management":
            display_module("Rental", RENTAL_MANAGEMENT_FIELDS, sample_data_key='rentals', crud_enabled=True, company_filter_id=st.session_state['company_id'])

        elif selected_module == "Fleet Management":
            display_module("Fleet", FLEET_MANAGEMENT_FIELDS, sample_data_key='vehicles', crud_enabled=True, company_filter_id=st.session_state['company_id'])

        elif selected_module == "Invoicing & Quoting":
            display_module("Invoicing & Quoting", INVOICING_QUOTING_FIELDS, sample_data_key='invoices', crud_enabled=True, company_filter_id=st.session_state['company_id'])

        elif selected_module == "CRM / Customer Management":
            display_module("CRM / Customer Management", CRM_MANAGEMENT_FIELDS, sample_data_key='clients', crud_enabled=True, company_filter_id=st.session_state['company_id'])

        elif selected_module == "Employee Management":
            display_module("Employee", EMPLOYEE_MANAGEMENT_FIELDS, sample_data_key='employees', crud_enabled=True, company_filter_id=st.session_state['company_id'])

        elif selected_module == "Payroll":
            st.header("Payroll Management")
            current_company_payslips = firestore_get_collection(st.session_state['company_id'], 'payslips')

            st.subheader("Generate Payslip")
            employee_name = st.text_input("Employee Name (for Payslip)", key=f"{st.session_state['company_id']}_payroll_emp_name")
            payslip_month = st.selectbox("Month", options=[str(i) for i in range(1, 13)], key=f"{st.session_state['company_id']}_payroll_month")
            payslip_year = st.selectbox("Year", options=[str(i) for i in range(2020, datetime.datetime.now().year + 2)], key=f"{st.session_state['company_id']}_payroll_year")
            base_salary = st.number_input("Base Salary", value=0.0, key=f"{st.session_state['company_id']}_payroll_base_salary")
            trip_bonus = st.number_input("Trip Bonus", value=0.0, key=f"{st.session_state['company_id']}_payroll_trip_bonus")
            rental_commission = st.number_input("Rental Commission", value=0.0, key=f"{st.session_state['company_id']}_payroll_rental_commission")
            deductions = st.number_input("Deductions", value=0.0, key=f"{st.session_state['company_id']}_payroll_deductions")
            overtime = st.number_input("Overtime", value=0.0, key=f"{st.session_state['company_id']}_payroll_overtime")

            net_salary = base_salary + trip_bonus + rental_commission + overtime - deductions
            st.write(f"Calculated Net Salary: **INR {net_salary:.2f}**")

            if st.button("Generate Payslip", key=f"{st.session_state['company_id']}_generate_payslip_btn"):
                existing_payslip_check = current_company_payslips[
                    (current_company_payslips['Employee Name'] == employee_name) &
                    (current_company_payslips['Month'] == payslip_month) &
                    (current_company_payslips['Year'] == payslip_year)
                ]
                
                payslip_data = {
                    'Company': st.session_state['company_name'],
                    'Payslip ID': f"PS_{employee_name[:3].upper()}_{payslip_month}{payslip_year}_{datetime.datetime.now().strftime('%H%M%S%f')}",
                    'Employee Name': employee_name, 'Month': payslip_month, 'Year': payslip_year,
                    'Base Salary': base_salary, 'Trip Bonus': trip_bonus,
                    'Rental Commission': rental_commission, 'Deductions': deductions,
                    'Overtime': overtime, 'Net Salary': net_salary, 'Payment Status': 'Unpaid'
                }

                if not existing_payslip_check.empty:
                    st.warning("A payslip for this employee and month/year already exists. Do you want to overwrite it?")
                    col_confirm_yes, col_confirm_no = st.columns(2)
                    with col_confirm_yes:
                        if st.button("Confirm Overwrite", key=f"{st.session_state['company_id']}_confirm_overwrite"):
                            doc_id_to_overwrite = existing_payslip_check['doc_id'].iloc[0]
                            try:
                                firestore_update_document(st.session_state['company_id'], 'payslips', doc_id_to_overwrite, payslip_data)
                                st.success("Payslip overwritten and regenerated successfully!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error overwriting payslip: {e}")
                    with col_confirm_no:
                        if st.button("Cancel", key=f"{st.session_state['company_id']}_cancel_overwrite"):
                            st.info("Payslip generation cancelled.")
                else:
                    try:
                        firestore_add_document(st.session_state['company_id'], 'payslips', payslip_data)
                        st.success("Payslip generated successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error generating payslip: {e}")


            st.subheader("Payroll History")
            display_df = add_serial_numbers(current_company_payslips.drop(columns=['doc_id'], errors='ignore'))
            edited_payslip_df = st.data_editor(
                display_df,
                key=f"{st.session_state['company_id']}_payslip_history_editor",
                hide_index=True,
                num_rows="dynamic",
                use_container_width=True
            )
            
            original_payslip_data_for_comparison = firestore_get_collection(st.session_state['company_id'], 'payslips')
            original_payslip_data_dict = original_payslip_data_for_comparison.set_index('Payslip ID').to_dict(orient='index')
            edited_payslip_data_dict_temp = edited_payslip_df.copy()
            for index, row in edited_payslip_data_dict_temp.iterrows():
                if row['Payslip ID'] in original_payslip_data_dict:
                    edited_payslip_data_dict_temp.loc[index, 'doc_id'] = original_payslip_data_dict[row['Payslip ID']].get('doc_id')
            edited_payslip_data_dict = edited_payslip_data_dict_temp.set_index('Payslip ID').to_dict(orient='index')

            updated_payslip_count = 0
            deleted_payslip_count = 0
            added_payslip_count = 0

            deleted_payslip_ids = set(original_payslip_data_dict.keys()) - set(edited_payslip_data_dict.keys())
            for payslip_id in deleted_payslip_ids:
                doc_id_to_delete = original_payslip_data_dict[payslip_id]['doc_id']
                if doc_id_to_delete:
                    try:
                        if firestore_delete_document(st.session_state['company_id'], 'payslips', doc_id_to_delete):
                            deleted_payslip_count += 1
                    except Exception as e:
                        st.error(f"Error deleting payslip {payslip_id}: {e}")

            for payslip_id, edited_row_data in edited_payslip_data_dict.items():
                edited_doc_id = edited_row_data.get('doc_id')
                cleaned_edited_data = {k: v for k, v in edited_row_data.items() if k not in ['SL No', 'doc_id']}

                if edited_doc_id and payslip_id in original_payslip_data_dict:
                    original_row_data = original_payslip_data_dict[payslip_id]
                    cleaned_original_data = {k: v for k, v in original_row_data.items() if k not in ['SL No', 'doc_id']}
                    
                    if cleaned_edited_data != cleaned_original_data:
                        try:
                            if firestore_update_document(st.session_state['company_id'], 'payslips', edited_doc_id, cleaned_edited_data):
                                updated_payslip_count += 1
                        except Exception as e:
                            st.error(f"Error updating payslip {payslip_id}: {e}")
                elif not edited_doc_id and payslip_id not in original_payslip_data_dict:
                    try:
                        firestore_add_document(st.session_state['company_id'], 'payslips', cleaned_edited_data)
                        added_payslip_count += 1
                    except Exception as e:
                        st.error(f"Error adding new payslip {payslip_id}: {e}")
            
            if updated_payslip_count > 0 or deleted_payslip_count > 0 or added_payslip_count > 0:
                if updated_payslip_count > 0:
                    st.success(f"{updated_payslip_count} Payslip entries updated successfully!")
                if deleted_payslip_count > 0:
                    st.success(f"{deleted_payslip_count} Payslip entries deleted successfully!")
                if added_payslip_count > 0:
                    st.success(f"{added_payslip_count} new Payslip entries added successfully!")
                st.rerun()

            st.subheader("Download Payslip Reports")
            col1, col2 = st.columns(2)
            with col1:
                excel_data = generate_excel_report(current_company_payslips.drop(columns=['doc_id'], errors='ignore'), "Payroll_Report")
                st.download_button(
                    label="Download Payroll Excel",
                    data=excel_data,
                    file_name=f"Payroll_Report_{st.session_state['company_name']}_{datetime.date.today()}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"{st.session_state['company_id']}_payroll_excel_download"
                )
             with col2:
                 pdf_data = generate_pdf_report(current_company_payslips.drop(columns=['doc_id'], errors='ignore'), "Payroll Report")
                 st.download_button(
                     label="Download Payroll PDF",
                     data=pdf_data,
                     file_name=f"Payroll_Report_{st.session_state['company_name']}_{datetime.date.today()}.pdf",
                     mime="application/pdf",
                     key=f"{st.session_state['company_id']}_payroll_pdf_download"
                 )


        elif selected_module == "Planning & Time Off":
            display_module("Planning & Time Off", PLANNING_TIMEOFF_FIELDS, sample_data_key='leaves', crud_enabled=True, company_filter_id=st.session_state['company_id'])
            st.subheader("Calendar View (Placeholder)")
            st.info("Implement a calendar view here to show driver schedules and leave requests. Libraries like `streamlit_calendar` can be used.")
            st.warning("Logic for overlap warnings would go here, checking employee availability against schedules and leave.")

        elif selected_module == "Reports Dashboard":
            st.subheader(f"Comprehensive Reports for {st.session_state['company_name']}")
            st.info("This dashboard provides insights into your company's operations across various modules.")

            st.markdown("#### Consolidated Data Overview")
            all_company_data_for_user_concat = pd.DataFrame()
            for module_name_key in ['trips', 'rentals', 'vehicles', 'invoices', 'clients', 'employees', 'payslips', 'leaves', 'vat_transactions']:
                df = firestore_get_collection(st.session_state['company_id'], module_name_key)
                if not df.empty and 'Company' in df.columns:
                    company_filtered_df = df[df['Company'] == st.session_state['company_name']].copy()
                    if not company_filtered_df.empty:
                        company_filtered_df['Module'] = module_name_key.replace('_', ' ').title()
                        all_company_data_for_user_concat = pd.concat([all_company_data_for_user_concat, company_filtered_df], ignore_index=True)

            if not all_company_data_for_user_concat.empty:
                st.dataframe(add_serial_numbers(all_company_data_for_user_concat.drop(columns=['doc_id'], errors='ignore')), use_container_width=True, hide_index=True)
                col_ex_all, col_pdf_all = st.columns(2)
                with col_ex_all:
                    st.download_button(
                        label=f"Download Consolidated {st.session_state['company_name']} Excel",
                        data=generate_excel_report(all_company_data_for_user_concat.drop(columns=['doc_id'], errors='ignore'), f"{st.session_state['company_name']}_Consolidated_Report"),
                        file_name=f"{st.session_state['company_name']}_Consolidated_Report_{datetime.date.today()}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key=f"{st.session_state['company_id']}_consolidated_excel"
                    )
                 with col_pdf_all:
                     st.download_button(
                         label=f"Download Consolidated {st.session_state['company_name']} PDF",
                         data=generate_pdf_report(all_company_data_for_user_concat.drop(columns=['doc_id'], errors='ignore'), f"{st.session_state['company_name']} Consolidated Report"),
                         file_name=f"{st.session_state['company_name']}_Consolidated_Report_{datetime.date.today()}.pdf",
                         mime="application/pdf",
                         key=f"{st.session_state['company_id']}_consolidated_pdf"
                     )
            else:
                st.info(f"No data available to generate a consolidated report for {st.session_state['company_name']} yet. Please add data in other modules.")

            st.markdown("---")
            st.markdown("#### Module Entry Counts (Your Company)")
            user_module_counts = {}
            for module_name_key in ['trips', 'rentals', 'vehicles', 'invoices', 'clients', 'employees', 'payslips', 'leaves', 'vat_transactions']:
                df = firestore_get_collection(st.session_state['company_id'], module_name_key)
                user_module_counts[module_name_key.replace('_', ' ').title()] = len(df)
            
            user_module_counts_df = pd.DataFrame(list(user_module_counts.items()), columns=['Module', 'Count'])

            if not user_module_counts_df.empty and user_module_counts_df['Count'].sum() > 0:
                fig_user_modules_bar = px.bar(
                    user_module_counts_df,
                    x='Module',
                    y='Count',
                    title='Number of Entries by Module (Your Company)',
                    labels={'Count': 'Number of Entries'},
                    color='Module'
                )
                st.plotly_chart(fig_user_modules_bar, use_container_width=True)
            else:
                st.info("No module data available for your company yet for this chart.")

            st.markdown("---")
            st.markdown("#### Trips by Client / Driver / Vehicle (Placeholder)")
            st.write("Generate charts and tables here based on Trip Management data specific to your company.")
            st.markdown("#### Income from Rentals vs Deliveries (Placeholder)")
            st.write("Visualize revenue breakdown for your company.")
            st.markdown("#### Overdue Payments (Placeholder)")
            st.write("List and track overdue invoices for your company.")
            st.markdown("#### Top Customers (Placeholder)")
            st.write("Identify high-value clients for your company.")
            st.markdown("#### Vehicle Utilization Rate (Placeholder)")
            st.write("Analyze fleet usage efficiency for your company.")
            st.markdown("#### Payroll Summary (Placeholder)")
            st.write("Summarize monthly payrolls for your company.")


        elif selected_module == "VAT Input/Output":
            display_module("VAT Input/Output", VAT_INPUT_OUTPUT_FIELDS, sample_data_key='vat_transactions', crud_enabled=True, company_filter_id=st.session_state['company_id'])
            st.subheader("VAT Return Report (Placeholder)")
            st.info("Automate VAT calculation and generate VAT return reports here.")
            st.write("Output VAT from Sales Invoices.")
            st.write("Input VAT from Purchases.")
            st.write("Auto-generate VAT Return Report for export.")
             if st.button("Generate VAT Return Report", key=f"{st.session_state['company_id']}_generate_vat_report"):
                 vat_data_for_report = firestore_get_collection(st.session_state['company_id'], 'vat_transactions')
                 vat_report_pdf = generate_pdf_report(vat_data_for_report.drop(columns=['doc_id'], errors='ignore'), f"VAT Return Report for {st.session_state['company_name']}")
                 st.download_button(
                     label=f"Download VAT Return Report PDF ({st.session_state['company_name']})",
                     data=vat_report_pdf,
                     file_name=f"VAT_Return_Report_{st.session_state['company_name']}_{datetime.date.today()}.pdf",
                     mime="application/pdf",
                     key=f"{st.session_state['company_id']}_vat_pdf_download"
                 )
                 st.success("VAT Return Report generated (placeholder).")


    st.sidebar.markdown("---")
    if st.sidebar.button("Logout", use_container_width=True):
        st.session_state['logged_in'] = False
        st.session_state['company_id'] = None
        st.session_state['user_id'] = None
        st.session_state['company_name'] = None
        st.session_state['role'] = None
        st.session_state['admin_selected_company_for_modules_name'] = None
        st.rerun()

# --- Main App Execution Flow ---
if st.session_state['logged_in']:
    main_app()
else:
    login_page()
