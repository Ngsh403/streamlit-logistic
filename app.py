import streamlit as st
import pandas as pd
import bcrypt
import io
from fpdf import FPDF
import datetime
import plotly.express as px
import plotly.graph_objects as go
import json
from num2words import num2words

# --- Firebase Admin SDK Imports ---
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

# Set Streamlit page config as the first Streamlit command
st.set_page_config(layout="wide", page_title="Logistic Management System")

# --- Configuration ---
INITIAL_USER_DB_STRUCTURE = {
    "S.A. CONCORD INTERNATIONAL CARGO HANDLING CO W.L.L": {
        "company_name": "S.A. CONCORD INTERNATIONAL CARGO HANDLING CO W.L.L",
        "company_pin": "S.A. CONCORD INTERNATIONAL CARGO HANDLING CO W.L.L",
        "users": {
            "sa": {"password_hash": bcrypt.hashpw("pass123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'), "role": "user"},
        }
    },
    "NORTH CONCORD CARGO HANDLING CO W.L.L": {
        "company_name": "NORTH CONCORD CARGO HANDLING CO W.L.L",
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
FIREBASE_SERVICE_ACCOUNT_KEY_JSON = {
    "type": "service_account",
    "project_id": "logisticapp-63967",
    "private_key_id": "e1d431273631bae553df5e70ee6b471b9aa3a692",
    "private_key": """-----BEGIN PRIVATE KEY-----
MIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQC6lbnF91wNS+rT
0Itd+tqu8IIc6XOTMJFglW6FzEM1rf/z9rtqGqx8zOpmAGDeEE7uCeGcA6LOAQsG
L9i19cctBYpU2XrxgHrE+TkAyLhpN7exCihpO1FNCWr3yB3tvmlRFYfuoP051KKD
svSMgfdhiA3Qenq472Z2Jguk6eEaF+GVW9/HbCjDwDVPkrl5f39MtOeGxNr9rYBB
CRYvKS+fMdXetv17KGA2tMXq0UZBt9LCZufLcCb4oUYfgrn7e/iauDnjGPBy9vtW
pYC+xGb/iz+ARtbj/R7wpzhoPwv4D3BuLOTSJrXThb2ZKZvATunrh4bCQJeAyYp2
C5hoOrNpAgMBAAECggEAFT6qWQ1H1s89uRmyHrSrDPd/VyepNFmXuf+1xogKIIzz
+20s7IFGQc0KxOu2294PQKkRHlSnJ03k2ZLd2eUW5UxP0oazShd7Ex299PYF0lwo
3yCFFqtNf+gqPPWVG85+GyCIml4MCzdH/FcmY2/CcUFesk3Z1qASonIFSiUjr3bW
FSon03VAZYtWA8WB3qn/XrI45EspuzU1NI3+pW96rQRe8mT26ryx6+EcV8huS3nN
cp6XvPo24a0Wl1bfS8XzTElyq3CyJRjQvaI5RacRx7Y9PS5fJCfYFgwEgkHn7ZuB
mJXrm/4oTR5ISUurYceEcrLvkPPvi3fGi/RqB/CakQKBgQDj5txlt/yl8A0hRyg1
ddg9ALL65IEqGpKS5I/K868EftshAeKuUF2KdvB4dMAqGmUCUN2/hnlUzepZcSEz
alXzQLQk2xHTsMaw22OnWjo5LAVY/eexidp6lkfeyVvkF0SyahQMFQoPTl8KM1If
entsN6gX6utnqVM1Czj0AgKxeQKBgQDRls0UH3rWUsR08OTUuSPE7gI0USCiERut
JKZvN9G7cP3rAr/t1Ryxj8m3JFkFwS5OWwmwAD/rlmZP4qtzoiJ7CD8Qsx+kld2r
SsdpiCNmF572i8j3Y4/CN2KABY+vj2bfg2MD20M1pXPGFoN5s5bWd8AM7gAyWocy
+nqLGmsFcQKBgD439MvAYzVaR/th1dRii9p7qmFcqPa5snJv++HIjWuIxoJIZX55
alA3EIeSODRGaHUtZpy3NcC1RtmMTSggS77RV10IgeFtTZFTE+3IcETTg9I731lU
7VSyWoS0LGYlBBhBZZ+2zrxHBSNfx3fYlIGC4F1HQWVXkOPWYIIdWmbhAoGATUo3
Rnx1aCQNnrJXMLs1naHH3lMsnZeBhVBGsCz9gwogGVJiROqaMkC8OnWE/sJGuU6J
PAZbjB1ijYMhhvr7jDN2TkpAGQnLPSfOcfRqWXPMg075RYHJue2CvYNPgYZ4gWSK
Vxm8p0PkdeBHi9HWhjCS+jGqkOchhIMqPbH4VYECgYBJMgUi1NR2aIGxmnh/ZgD1
kAUuX6vMAp/cM2MWxf+voc8VHHLs68Y8J0KYziR2iJaWm6HwvRBnDw0aYtriJGeE
NfdlmyviDlSYRMv9wUvtlFhlcxkGGYw8s3c9z3u7AD43CnPs661hlCCAzpu9y71M
y80q6KbGDtuYTW/0j3fq0g==
-----END PRIVATE KEY-----""",
    "client_email": "firebase-adminsdk-fbsvc@logisticapp-63967.iam.gserviceaccount.com",
    "client_id": "116053489571436273496",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40logisticapp-63967.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com"
}

# Correct the private key string
FIREBASE_SERVICE_ACCOUNT_KEY_JSON['private_key'] = FIREBASE_SERVICE_ACCOUNT_KEY_JSON['private_key'].replace('\\n', '\n')

FIREBASE_PROJECT_ID = FIREBASE_SERVICE_ACCOUNT_KEY_JSON['project_id']
FIRESTORE_ROOT_COLLECTION = "logistic_app_data"

# Initialize Firebase only once at module level
firebase_initialized = False

if not firebase_initialized:
    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate(FIREBASE_SERVICE_ACCOUNT_KEY_JSON)
            firebase_admin.initialize_app(cred)
            firebase_initialized = True
        else:
            firebase_initialized = True
    except Exception as e:
        pass

# Get Firestore client
db = firestore.client() if firebase_initialized else None

# --- Firestore Interactions ---
def firestore_get_collection(company_id, collection_name):
    """Fetches all documents from a Firestore subcollection for a given company."""
    if db is None:
        st.error("Firestore database client not initialized.")
        return pd.DataFrame()

    collection_ref = db.collection(FIRESTORE_ROOT_COLLECTION).document(company_id).collection(collection_name)
    
    try:
        docs = collection_ref.stream()
        data_list = []
        for doc in docs:
            doc_data = doc.to_dict()
            doc_data['doc_id'] = doc.id
            data_list.append(doc_data)
        
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

            auto_generated_ids_map = {
                'trips': 'Trip ID',
                'rentals': 'Rental ID',
                'invoices': 'Inv Number',
                'payslips': 'Payslip ID'
            }

            fields = list(mapping.get(mod_name, {}).keys())
            cleaned_fields = []
            for field in fields:
                if field.endswith(" Date") or field.endswith(" Time"):
                    if mapping.get(mod_name, {}).get(field, {}).get('type') == 'datetime':
                        cleaned_fields.append(field)
                else:
                    cleaned_fields.append(field)

            if mod_name in auto_generated_ids_map and auto_generated_ids_map[mod_name] not in cleaned_fields:
                cleaned_fields.insert(0, auto_generated_ids_map[mod_name])

            return cleaned_fields + ['Company']

        if data_list:
            df = pd.DataFrame(data_list)
            expected_cols_base = get_expected_columns_for_module(collection_name)
            
            for col in expected_cols_base:
                if col not in df.columns:
                    df[col] = None
            
            if 'doc_id' not in df.columns:
                df['doc_id'] = None

            cols_to_keep = [col for col in expected_cols_base if col in df.columns]
            df = df[cols_to_keep + ['doc_id']]
            
            return df
        else:
            columns_for_empty_df = get_expected_columns_for_module(collection_name)
            empty_df = pd.DataFrame(columns=columns_for_empty_df)
            empty_df['doc_id'] = None
            return empty_df
    except Exception as e:
        st.error(f"Error fetching data from Firestore for {collection_name}: {e}")
        return pd.DataFrame()

def firestore_add_document(company_id, collection_name, data):
    """Adds a document to a Firestore subcollection for a given company."""
    if db is None:
        st.error("Firestore database client not initialized. Cannot add document.")
        return None

    collection_ref = db.collection(FIRESTORE_ROOT_COLLECTION).document(company_id).collection(collection_name)
    
    try:
        update_time, doc_ref = collection_ref.add(data)
        return doc_ref.id
    except Exception as e:
        st.error(f"Error adding document to Firestore: {e}")
        return None

def firestore_update_document(company_id, collection_name, doc_id, data):
    """Updates a document in a Firestore subcollection for a given company."""
    if db is None:
        st.error("Firestore database client not initialized. Cannot update document.")
        return False

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

    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, title, 0, 1, "C")
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 5, f"Report Date: {datetime.date.today().strftime('%Y-%m-%d')}", 0, 1, "C")
    pdf.ln(10)

    df_str = df.astype(str)
    available_width = pdf.w - pdf.l_margin - pdf.r_margin
    MIN_COL_WIDTH = 15

    desired_widths = {}
    pdf.set_font("Arial", "B", 10)
    for col in df_str.columns:
        header_width = pdf.get_string_width(col)
        pdf.set_font("Arial", size=10)
        max_content_width = 0
        if not df_str[col].empty:
            max_content_width = df_str[col].apply(pdf.get_string_width).max()
        
        desired_widths[col] = max(header_width, max_content_width) + 6

    total_desired_width = sum(desired_widths.values())

    col_widths = {}
    if total_desired_width > available_width:
        scale_factor = available_width / total_desired_width
        for col in df_str.columns:
            col_widths[col] = max(desired_widths[col] * scale_factor, MIN_COL_WIDTH)
    else:
        remaining_width = available_width
        for col in df_str.columns:
            col_widths[col] = max(desired_widths[col], MIN_COL_WIDTH)
            remaining_width -= col_widths[col]
        
        if remaining_width > 0:
            large_columns = [col for col, width in col_widths.items() if width > MIN_COL_WIDTH]
            if large_columns:
                extra_per_col = remaining_width / len(large_columns)
                for col in large_columns:
                    col_widths[col] += extra_per_col
            else:
                if col_widths:
                    col_widths[list(col_widths.keys())[0]] += remaining_width
    
    pdf.set_font("Arial", "B", 10)
    for col in df_str.columns:
        pdf.cell(col_widths[col], 10, txt=col, border=1, align="C")
    pdf.ln()

    pdf.set_font("Arial", size=10)
    for index, row in df_str.iterrows():
        for col in df_str.columns:
            cell_text = str(row[col])
            pdf.multi_cell(col_widths[col], 7, txt=cell_text, border=1, align="L", ln=0)
        pdf.ln()

    pdf.set_y(pdf.h - 15)
    pdf.set_font("Arial", "I", 8)
    pdf.cell(0, 10, f"Page {pdf.page_no()}/{{nb}}", 0, 0, "C")

    return bytes(pdf.output(dest='S'))

def generate_management_pdf_report(all_companies_data, user_db_current):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    MANAGEMENT_REPORT_BACKGROUND_URL = "https://placehold.co/595x842/F0F8FF/313131.png?text=Management+Report+Background"
    try:
        pdf.image(MANAGEMENT_REPORT_BACKGROUND_URL, x=0, y=0, w=pdf.w, h=pdf.h)
    except Exception as e:
        pdf.set_fill_color(240, 248, 255)
        pdf.rect(0, 0, pdf.w, pdf.h, 'F')
        st.warning(f"Could not load management report background image from {MANAGEMENT_REPORT_BACKGROUND_URL}: {e}. Generating with fallback color.")

    pdf.set_y(10)
    pdf.set_font("Arial", "B", 20)
    pdf.cell(0, 10, "Global Logistic Management Dashboard Report", 0, 1, "C")
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 8, f"Report Date: {datetime.date.today().strftime('%Y-%m-%d')}", 0, 1, "C")
    pdf.ln(10)

    total_vehicles_all = 0
    total_employees_all = 0
    total_revenue_all = 0.0
    total_trips_all = 0
    total_rentals_all = 0
    total_payslips_net_salary_all = 0.0
    total_leaves_all = 0
    total_vat_amount_all = 0.0

    vehicles_by_type_data = {}
    revenue_by_company_data = {}
    employees_by_company_data = {}
    trips_by_company_data = {}

    for company_id_key, company_details in user_db_current.items():
        if company_details['company_pin'] != 'ADMIN':
            comp_name = company_details['company_name']
            
            comp_vehicles_df = all_companies_data.get('vehicles', pd.DataFrame())
            if not comp_vehicles_df.empty and 'Company' in comp_vehicles_df.columns:
                company_specific_vehicles_df = comp_vehicles_df[comp_vehicles_df['Company'] == comp_name]
                total_vehicles_all += len(company_specific_vehicles_df)
                for v_type in company_specific_vehicles_df['Vehicle Type'].unique():
                    vehicles_by_type_data[v_type] = vehicles_by_type_data.get(v_type, 0) + len(company_specific_vehicles_df[company_specific_vehicles_df['Vehicle Type'] == v_type])

            comp_employees_df = all_companies_data.get('employees', pd.DataFrame())
            if not comp_employees_df.empty and 'Company' in comp_employees_df.columns:
                company_specific_employees_df = comp_employees_df[comp_employees_df['Company'] == comp_name]
                total_employees_all += len(company_specific_employees_df)
                employees_by_company_data[comp_name] = len(company_specific_employees_df)

            comp_invoices_df = all_companies_data.get('invoices', pd.DataFrame())
            if not comp_invoices_df.empty and 'Company' in comp_invoices_df.columns and 'Total Amount' in comp_invoices_df.columns:
                company_specific_invoices_df = comp_invoices_df[comp_invoices_df['Company'] == comp_name]
                company_revenue = company_specific_invoices_df['Total Amount'].sum()
                total_revenue_all += company_revenue
                revenue_by_company_data[comp_name] = company_revenue

            comp_trips_df = all_companies_data.get('trips', pd.DataFrame())
            if not comp_trips_df.empty and 'Company' in comp_trips_df.columns:
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

    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Vehicle Distribution by Type (All Companies)", 0, 1, "L")
    pdf.set_font("Arial", "", 10)
    if vehicles_by_type_data:
        for v_type, count in vehicles_by_type_data.items():
            pdf.cell(0, 7, f"- {v_type}: {count}", 0, 1, "L")
    else:
        pdf.cell(0, 7, "No vehicle data available.", 0, 1, "L")
    pdf.ln(5)

    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Revenue by Company", 0, 1, "L")
    pdf.set_font("Arial", "", 10)
    if revenue_by_company_data:
        for company, revenue in revenue_by_company_data.items():
            pdf.cell(0, 7, f"- {company}: INR {revenue:,.2f}", 0, 1, "L")
    else:
        pdf.cell(0, 7, "No revenue data available.", 0, 1, "L")
    pdf.ln(5)

    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Employees by Company", 0, 1, "L")
    pdf.set_font("Arial", "", 10)
    if employees_by_company_data:
        for company, employees in employees_by_company_data.items():
            pdf.cell(0, 7, f"- {company}: {employees}", 0, 1, "L")
    else:
        pdf.cell(0, 7, "No employee data available.", 0, 1, "L")
    pdf.ln(5)

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
        if company_details['company_pin'] != 'ADMIN':
            comp_name = company_details['company_name']
            
            pdf.set_font("Arial", "BU", 12)
            pdf.cell(0, 10, f"Company: {comp_name}", 0, 1, "L")
            pdf.set_font("Arial", "", 10)

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
            
            pdf.ln(5)

    pdf.set_y(pdf.h - 15)
    pdf.set_font("Arial", "I", 8)
    pdf.cell(0, 10, f"Page {pdf.page_no()}/{{nb}} - Global Management Report", 0, 0, "C")

    return bytes(pdf.output(dest='S'))

def generate_single_tax_invoice_pdf(invoice_data, company_name_actual, company_pin_actual, logo_url, logo_x, logo_y, logo_width, logo_height):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    BACKGROUND_IMAGE_URL = "https://i.ibb.co/RGTCjMb/EAST-CONCORD-W-L-L-page-0001-1.jpg"
    try:
        pdf.image(BACKGROUND_IMAGE_URL, x=0, y=0, w=pdf.w, h=pdf.h)
    except Exception as e:
        st.warning(f"Could not load background image from {BACKGROUND_IMAGE_URL}: {e}. Generating without background image.")
        pdf.set_fill_color(240, 248, 255)
        pdf.rect(0, 0, pdf.w, pdf.h, 'F')

    pdf.set_font("Arial", "B", 80)
    pdf.set_text_color(200, 200, 200)
    pdf.text(pdf.w / 2 - pdf.get_string_width("INVOICE") / 2, pdf.h / 2 + 10, "INVOICE")
    pdf.set_text_color(0, 0, 0)

    try:
        pdf.image(logo_url, x=logo_x, y=logo_y, w=logo_width, h=logo_height)
    except Exception as e:
        st.warning(f"Could not load logo image from {logo_url}: {e}. Continuing without logo.")

    pdf.set_y(25)
    pdf.set_font("Arial", "", 9)
    pdf.set_text_color(50, 50, 50)
    
    pdf.set_x(10)
    pdf.cell(0, 5, "EAST CONCORD W.L.L", 0, 1, "L")
    pdf.set_x(10)
    pdf.cell(0, 5, "Flat/Shop No. 11, Building 471", 0, 1, "L")
    pdf.set_x(10)
    pdf.cell(0, 5, "Road/Shop 3513, MANAMA", 0, 1, "L")
    pdf.set_x(10)
    pdf.cell(0, 5, "UMM AL-HASSAM, Kingdom of Bahrain", 0, 1, "L")
    pdf.set_x(10)
    pdf.cell(0, 5, f"TRN: {company_pin_actual}", 0, 1, "L")
    pdf.set_x(10)
    pdf.cell(0, 5, "Email: concord@email.com (Mock)", 0, 1, "L")
    pdf.ln(5)

    pdf.set_y(50)
    pdf.set_font("Arial", "B", 24)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, "TAX INVOICE", 0, 1, "C")
    pdf.ln(5)

    pdf.set_font("Arial", "", 10)
    current_y = pdf.get_y()
    right_col_x = pdf.w - pdf.r_margin - 60
    pdf.set_xy(right_col_x, current_y)
    pdf.cell(60, 7, f"Invoice Number: {invoice_data.get('Inv Number', 'N/A')}", 0, 1, "R")
    pdf.set_x(right_col_x)
    pdf.cell(60, 7, f"Invoice Date: {invoice_data.get('Inv Date', 'N/A')}", 0, 1, "R")
    pdf.set_x(right_col_x)
    pdf.cell(60, 7, f"Due Date: {invoice_data.get('Due Date', 'N/A')}", 0, 1, "R")
    pdf.set_x(right_col_x)
    pdf.cell(60, 7, f"Payment Status: {invoice_data.get('Payment Status', 'N/A')}", 0, 1, "R")
    pdf.ln(5)

    pdf.set_y(current_y)
    pdf.set_x(pdf.l_margin)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 7, "BILL TO:", 0, 1, "L")
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 5, f"{invoice_data.get('Client Name', 'N/A')}", 0, 1, "L")
    pdf.cell(0, 5, f"{invoice_data.get('Client Address', 'N/A')}", 0, 1, "L")
    pdf.cell(0, 5, f"Client Contact: {invoice_data.get('Client Contact', 'N/A')}", 0, 1, "L")
    pdf.cell(0, 5, f"Client TRN: {invoice_data.get('Client TRN', 'N/A')}", 0, 1, "L")
    pdf.ln(10)

    pdf.set_font("Arial", "B", 10)
    col_widths = [10, 80, 20, 25, 25]
    
    pdf.cell(col_widths[0], 10, "SN", 1, 0, "C")
    pdf.cell(col_widths[1], 10, "Item Description", 1, 0, "C")
    pdf.cell(col_widths[2], 10, "Quantity", 1, 0, "C")
    pdf.cell(col_widths[3], 10, "Unit Price", 1, 0, "C")
    pdf.cell(col_widths[4], 10, "Amount", 1, 1, "C")

    pdf.set_font("Arial", "", 9)
    items_json_str = invoice_data.get('Items', '[]')
    try:
        items = json.loads(items_json_str)
    except json.JSONDecodeError:
        items = []

    sn = 1
    for item in items:
        pdf.cell(col_widths[0], 7, str(sn), 1, 0, "C")
        pdf.cell(col_widths[1], 7, item.get('Description', ''), 1, 0, "L")
        pdf.cell(col_widths[2], 7, str(item.get('Quantity', '')), 1, 0, "C")
        pdf.cell(col_widths[3], 7, f"{float(item.get('Unit Price', 0)):,.2f}", 1, 0, "R")
        pdf.cell(col_widths[4], 7, f"{float(item.get('Amount', 0)):,.2f}", 1, 1, "R")
        sn += 1
    pdf.ln(5)

    pdf.set_x(pdf.w - pdf.r_margin - 80)
    pdf.set_font("Arial", "B", 10)
    
    subtotal = float(invoice_data.get('Subtotal', 0))
    pdf.cell(50, 7, "Subtotal:", 0, 0, "R")
    pdf.cell(30, 7, f"INR {subtotal:,.2f}", 0, 1, "R")

    discount = float(invoice_data.get('Discount', 0))
    pdf.set_x(pdf.w - pdf.r_margin - 80)
    pdf.cell(50, 7, "Discount:", 0, 0, "R")
    pdf.cell(30, 7, f"INR {discount:,.2f}", 0, 1, "R")

    vat_amount = float(invoice_data.get('VAT Amount', 0))
    pdf.set_x(pdf.w - pdf.r_margin - 80)
    pdf.cell(50, 7, f"VAT ({invoice_data.get('VAT Rate', 'N/A')}%):", 0, 0, "R")
    pdf.cell(30, 7, f"INR {vat_amount:,.2f}", 0, 1, "R")

    total_amount = float(invoice_data.get('Total Amount', 0))
    pdf.set_x(pdf.w - pdf.r_margin - 80)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(50, 8, "TOTAL AMOUNT:", 1, 0, "R", fill=True)
    pdf.cell(30, 8, f"INR {total_amount:,.2f}", 1, 1, "R", fill=True)
    pdf.ln(5)

    amount_in_words = ""
    try:
        amount_in_words = num2words(total_amount, lang='en_IN').title() + " Indian Rupees Only"
    except Exception as e:
        amount_in_words = "Amount in words conversion error."
        st.warning(f"Error converting amount to words: {e}")

    pdf.set_font("Arial", "I", 10)
    pdf.cell(0, 7, f"Amount In Words: {amount_in_words}", 0, 1, "L")
    pdf.ln(10)

    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 7, "Notes:", 0, 1, "L")
    pdf.multi_cell(0, 5, invoice_data.get('Notes', 'Thank you for your business!'), 0, "L")
    pdf.ln(10)

    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 7, "Bank Details:", 0, 1, "L")
    pdf.set_font("Arial", "", 9)
    pdf.cell(0, 5, "Bank Name: XYZ Bank", 0, 1, "L")
    pdf.cell(0, 5, "Account Name: EAST CONCORD W.L.L", 0, 1, "L")
    pdf.cell(0, 5, "Account Number: 1234567890", 0, 1, "L")
    pdf.cell(0, 5, "IBAN: BHXX XXXX XXXX XXXX XXXX XXXX", 0, 1, "L")
    pdf.cell(0, 5, "SWIFT/BIC: ABCDEFGH", 0, 1, "L")
    pdf.ln(15)

    pdf.set_x(pdf.w - pdf.r_margin - 60)
    pdf.cell(60, 5, "_________________________", 0, 1, "C")
    pdf.set_x(pdf.w - pdf.r_margin - 60)
    pdf.cell(60, 5, "Authorized Signature", 0, 1, "C")
    pdf.ln(10)

    pdf.set_y(pdf.h - 15)
    pdf.set_font("Arial", "I", 8)
    pdf.cell(0, 10, f"Page {pdf.page_no()}/{{nb}}", 0, 0, "C")

    return bytes(pdf.output(dest='S'))

# --- Data Management ---
TRIP_MANAGEMENT_FIELDS = {
    "Trip ID": {"type": "text", "editable": False},
    "Customer Name": {"type": "text", "editable": True},
    "Origin": {"type": "text", "editable": True},
    "Destination": {"type": "text", "editable": True},
    "Start Date & Time": {"type": "datetime", "editable": True},
    "End Date & Time": {"type": "datetime", "editable": True},
    "Vehicle Used": {"type": "text", "editable": True},
    "Driver": {"type": "text", "editable": True},
    "Status": {"type": "select", "options": ["Scheduled", "In Progress", "Completed", "Cancelled"], "editable": True},
    "Cargo Type": {"type": "text", "editable": True},
    "Weight (kg)": {"type": "number", "editable": True},
    "Revenue (INR)": {"type": "number", "editable": True},
    "Expenses (INR)": {"type": "number", "editable": True},
    "Notes": {"type": "textarea", "editable": True},
}

RENTAL_MANAGEMENT_FIELDS = {
    "Rental ID": {"type": "text", "editable": False},
    "Client Name": {"type": "text", "editable": True},
    "Vehicle Rented": {"type": "text", "editable": True},
    "Start Date & Time": {"type": "datetime", "editable": True},
    "End Date & Time": {"type": "datetime", "editable": True},
    "Rental Rate per Day (INR)": {"type": "number", "editable": True},
    "Total Rental Cost (INR)": {"type": "number", "editable": False},
    "Status": {"type": "select", "options": ["Booked", "Active", "Completed", "Cancelled"], "editable": True},
    "Notes": {"type": "textarea", "editable": True},
}

FLEET_MANAGEMENT_FIELDS = {
    "Vehicle ID": {"type": "text", "editable": False},
    "Vehicle Type": {"type": "select", "options": ["Truck", "Trailer", "Van", "Car", "Motorbike", "Other"], "editable": True},
    "Make": {"type": "text", "editable": True},
    "Model": {"type": "text", "editable": True},
    "Year": {"type": "number", "editable": True},
    "License Plate": {"type": "text", "editable": True},
    "VIN": {"type": "text", "editable": True},
    "Acquisition Date": {"type": "date", "editable": True},
    "Current Mileage (km)": {"type": "number", "editable": True},
    "Maintenance Due Date": {"type": "date", "editable": True},
    "Insurance Expiry Date": {"type": "date", "editable": True},
    "Registration Expiry Date": {"type": "date", "editable": True},
    "Status": {"type": "select", "options": ["Active", "Under Maintenance", "Retired"], "editable": True},
    "Assigned Driver": {"type": "text", "editable": True},
    "Notes": {"type": "textarea", "editable": True},
}

INVOICING_QUOTING_FIELDS = {
    "Inv Number": {"type": "text", "editable": False},
    "Inv Date": {"type": "date", "editable": True},
    "Due Date": {"type": "date", "editable": True},
    "Client Name": {"type": "text", "editable": True},
    "Client Address": {"type": "text", "editable": True},
    "Client Contact": {"type": "text", "editable": True},
    "Client TRN": {"type": "text", "editable": True},
    "Items": {"type": "json_table", "editable": True},
    "Subtotal": {"type": "number", "editable": False},
    "Discount": {"type": "number", "editable": True},
    "VAT Rate": {"type": "select", "options": [0, 5, 10, 15], "editable": True},
    "VAT Amount": {"type": "number", "editable": False},
    "Total Amount": {"type": "number", "editable": False},
    "Payment Status": {"type": "select", "options": ["Pending", "Paid", "Overdue", "Partial"], "editable": True},
    "Notes": {"type": "textarea", "editable": True},
}

CRM_MANAGEMENT_FIELDS = {
    "Client ID": {"type": "text", "editable": False},
    "Client Name": {"type": "text", "editable": True},
    "Contact Person": {"type": "text", "editable": True},
    "Email": {"type": "text", "editable": True},
    "Phone": {"type": "text", "editable": True},
    "Address": {"type": "text", "editable": True},
    "TRN": {"type": "text", "editable": True},
    "Notes": {"type": "textarea", "editable": True},
    "Last Interaction Date": {"type": "date", "editable": True},
    "Preferred Service": {"type": "text", "editable": True},
}

EMPLOYEE_MANAGEMENT_FIELDS = {
    "Employee ID": {"type": "text", "editable": False},
    "Name": {"type": "text", "editable": True},
    "Position": {"type": "text", "editable": True},
    "Department": {"type": "text", "editable": True},
    "Date of Joining": {"type": "date", "editable": True},
    "Contact Number": {"type": "text", "editable": True},
    "Email": {"type": "text", "editable": True},
    "Address": {"type": "text", "editable": True},
    "Emergency Contact Name": {"type": "text", "editable": True},
    "Emergency Contact Number": {"type": "text", "editable": True},
    "Bank Account Number": {"type": "text", "editable": True},
    "IBAN": {"type": "text", "editable": True},
    "Civil ID/Passport No.": {"type": "text", "editable": True},
    "Nationality": {"type": "text", "editable": True},
    "Basic Salary (INR)": {"type": "number", "editable": True},
    "Allowance (INR)": {"type": "number", "editable": True},
    "Deductions (INR)": {"type": "number", "editable": True},
    "Status": {"type": "select", "options": ["Active", "On Leave", "Terminated"], "editable": True},
    "Notes": {"type": "textarea", "editable": True},
}

PAYROLL_FIELDS = {
    "Payslip ID": {"type": "text", "editable": False},
    "Employee ID": {"type": "text", "editable": True},
    "Employee Name": {"type": "text", "editable": True},
    "Pay Period Start Date": {"type": "date", "editable": True},
    "Pay Period End Date": {"type": "date", "editable": True},
    "Payment Date": {"type": "date", "editable": True},
    "Basic Salary (INR)": {"type": "number", "editable": True},
    "Allowance (INR)": {"type": "number", "editable": True},
    "Overtime Pay (INR)": {"type": "number", "editable": True},
    "Gross Salary (INR)": {"type": "number", "editable": False},
    "Deductions (INR)": {"type": "number", "editable": True},
    "Net Salary (INR)": {"type": "number", "editable": False},
    "Payment Method": {"type": "select", "options": ["Bank Transfer", "Cash", "Cheque"], "editable": True},
    "Status": {"type": "select", "options": ["Paid", "Pending"], "editable": True},
    "Notes": {"type": "textarea", "editable": True},
}

PLANNING_TIMEOFF_FIELDS = {
    "Leave ID": {"type": "text", "editable": False},
    "Employee ID": {"type": "text", "editable": True},
    "Employee Name": {"type": "text", "editable": True},
    "Leave Type": {"type": "select", "options": ["Annual Leave", "Sick Leave", "Maternity Leave", "Paternity Leave", "Unpaid Leave", "Other"], "editable": True},
    "Start Date": {"type": "date", "editable": True},
    "End Date": {"type": "date", "editable": True},
    "Number of Days": {"type": "number", "editable": False},
    "Status": {"type": "select", "options": ["Pending", "Approved", "Rejected", "Cancelled"], "editable": True},
    "Reason": {"type": "textarea", "editable": True},
    "Approved By": {"type": "text", "editable": True},
}

VAT_INPUT_OUTPUT_FIELDS = {
    "Transaction ID": {"type": "text", "editable": False},
    "Date": {"type": "date", "editable": True},
    "Type": {"type": "select", "options": ["Input VAT", "Output VAT"], "editable": True},
    "Description": {"type": "textarea", "editable": True},
    "Net Amount (INR)": {"type": "number", "editable": True},
    "VAT Rate (%)": {"type": "select", "options": [0, 5, 10, 15], "editable": True},
    "VAT Amount (INR)": {"type": "number", "editable": False},
    "Total Amount (INR)": {"type": "number", "editable": False},
    "Supplier/Client Name": {"type": "text", "editable": True},
    "Supplier/Client TRN": {"type": "text", "editable": True},
    "Invoice/Receipt Number": {"type": "text", "editable": True},
    "Notes": {"type": "textarea", "editable": True},
}

MODULE_CONFIGS = {
    "Trip Management": {"collection": "trips", "fields": TRIP_MANAGEMENT_FIELDS},
    "Rental Management": {"collection": "rentals", "fields": RENTAL_MANAGEMENT_FIELDS},
    "Fleet Management": {"collection": "vehicles", "fields": FLEET_MANAGEMENT_FIELDS},
    "Invoicing & Quoting": {"collection": "invoices", "fields": INVOICING_QUOTING_FIELDS},
    "CRM Management": {"collection": "clients", "fields": CRM_MANAGEMENT_FIELDS},
    "Employee Management": {"collection": "employees", "fields": EMPLOYEE_MANAGEMENT_FIELDS},
    "Payroll": {"collection": "payslips", "fields": PAYROLL_FIELDS},
    "Planning & Time Off": {"collection": "leaves", "fields": PLANNING_TIMEOFF_FIELDS},
    "VAT Input/Output": {"collection": "vat_transactions", "fields": VAT_INPUT_OUTPUT_FIELDS},
}

def load_data(company_id, module_name):
    collection_name = MODULE_CONFIGS[module_name]["collection"]
    df = firestore_get_collection(company_id, collection_name)
    return df

def save_data(company_id, module_name, df):
    collection_name = MODULE_CONFIGS[module_name]["collection"]
    
    current_firestore_df = firestore_get_collection(company_id, collection_name)
    current_firestore_ids = set(current_firestore_df['doc_id'].dropna().tolist()) if not current_firestore_df.empty else set()
    
    st_df_ids = set(df['doc_id'].dropna().tolist()) if not df.empty else set()

    to_delete_ids = current_firestore_ids - st_df_ids
    for doc_id in to_delete_ids:
        firestore_delete_document(company_id, collection_name, doc_id)

    for index, row in df.iterrows():
        record_data = row.drop(labels=['doc_id']).to_dict()
        
        for field_name, field_config in MODULE_CONFIGS[module_name]["fields"].items():
            if field_config['type'] == 'number' and field_name in record_data and record_data[field_name] is not None:
                try:
                    record_data[field_name] = float(record_data[field_name])
                except (ValueError, TypeError):
                    record_data[field_name] = 0.0

        if 'Company' not in record_data or record_data['Company'] is None:
            record_data['Company'] = st.session_state['company_name']

        if pd.isna(row['doc_id']):
            firestore_add_document(company_id, collection_name, record_data)
        else:
            firestore_update_document(company_id, collection_name, row['doc_id'], record_data)
    st.success(f"{module_name} data saved to Firestore!")
    st.session_state[f'df_{collection_name}'] = load_data(company_id, module_name)
    return True

def apply_calculations(df, module_name):
    if df.empty:
        return df

    if module_name == "Rental Management":
        if "Start Date & Time" in df.columns and "End Date & Time" in df.columns and "Rental Rate per Day (INR)" in df.columns:
            df["Start Date & Time"] = pd.to_datetime(df["Start Date & Time"], errors='coerce')
            df["End Date & Time"] = pd.to_datetime(df["End Date & Time"], errors='coerce')
            df["Rental Rate per Day (INR)"] = pd.to_numeric(df["Rental Rate per Day (INR)"], errors='coerce').fillna(0)

            valid_dates_mask = df["Start Date & Time"].notna() & df["End Date & Time"].notna()
            
            duration = (df["End Date & Time"] - df["Start Date & Time"]).dt.days + 1
            duration = duration.apply(lambda x: max(x, 1) if pd.notna(x) else 0)

            df.loc[valid_dates_mask, "Total Rental Cost (INR)"] = \
                duration[valid_dates_mask] * df.loc[valid_dates_mask, "Rental Rate per Day (INR)"]
            df["Total Rental Cost (INR)"] = df["Total Rental Cost (INR)"].fillna(0)

    elif module_name == "Invoicing & Quoting":
        if "Items" in df.columns and "Discount" in df.columns and "VAT Rate" in df.columns:
            df["Discount"] = pd.to_numeric(df["Discount"], errors='coerce').fillna(0)
            df["VAT Rate"] = pd.to_numeric(df["VAT Rate"], errors='coerce').fillna(0) / 100

            subtotals = []
            for _, row in df.iterrows():
                row_subtotal = 0
                items_json_str = row['Items']
                try:
                    items = json.loads(items_json_str) if isinstance(items_json_str, str) else items_json_str
                    if isinstance(items, list):
                        for item in items:
                            try:
                                qty = float(item.get('Quantity', 0))
                                price = float(item.get('Unit Price', 0))
                                row_subtotal += (qty * price)
                            except (ValueError, TypeError):
                                pass
                except (json.JSONDecodeError, TypeError):
                    pass
                subtotals.append(row_subtotal)
            df['Subtotal'] = subtotals

            df["VAT Amount"] = (df["Subtotal"] - df["Discount"]) * df["VAT Rate"]
            df["Total Amount"] = df["Subtotal"] - df["Discount"] + df["VAT Amount"]
            df["VAT Amount"] = df["VAT Amount"].fillna(0)
            df["Total Amount"] = df["Total Amount"].fillna(0)

    elif module_name == "Payroll":
        if "Basic Salary (INR)" in df.columns and "Allowance (INR)" in df.columns and "Overtime Pay (INR)" in df.columns and "Deductions (INR)" in df.columns:
            df["Basic Salary (INR)"] = pd.to_numeric(df["Basic Salary (INR)"], errors='coerce').fillna(0)
            df["Allowance (INR)"] = pd.to_numeric(df["Allowance (INR)"], errors='coerce').fillna(0)
            df["Overtime Pay (INR)"] = pd.to_numeric(df["Overtime Pay (INR)"], errors='coerce').fillna(0)
            df["Deductions (INR)"] = pd.to_numeric(df["Deductions (INR)"], errors='coerce').fillna(0)
            
            df["Gross Salary (INR)"] = df["Basic Salary (INR)"] + df["Allowance (INR)"] + df["Overtime Pay (INR)"]
            df["Net Salary (INR)"] = df["Gross Salary (INR)"] - df["Deductions (INR)"]
            df["Gross Salary (INR)"] = df["Gross Salary (INR)"].fillna(0)
            df["Net Salary (INR)"] = df["Net Salary (INR)"].fillna(0)

    elif module_name == "Planning & Time Off":
        if "Start Date" in df.columns and "End Date" in df.columns:
            df["Start Date"] = pd.to_datetime(df["Start Date"], errors='coerce')
            df["End Date"] = pd.to_datetime(df["End Date"], errors='coerce')

            valid_dates_mask = df["Start Date"].notna() & df["End Date"].notna()
            df.loc[valid_dates_mask, "Number of Days"] = (df["End Date"] - df["Start Date"]).dt.days + 1
            df["Number of Days"] = df["Number of Days"].fillna(0)

    elif module_name == "VAT Input/Output":
        if "Net Amount (INR)" in df.columns and "VAT Rate (%)" in df.columns:
            df["Net Amount (INR)"] = pd.to_numeric(df["Net Amount (INR)"], errors='coerce').fillna(0)
            df["VAT Rate (%)"] = pd.to_numeric(df["VAT Rate (%)"], errors='coerce').fillna(0) / 100

            df["VAT Amount (INR)"] = df["Net Amount (INR)"] * df["VAT Rate (%)"]
            df["Total Amount (INR)"] = df["Net Amount (INR)"] + df["VAT Amount (INR)"]
            df["VAT Amount (INR)"] = df["VAT Amount (INR)"].fillna(0)
            df["Total Amount (INR)"] = df["Total Amount (INR)"].fillna(0)

    return df

def get_next_id(df, id_prefix):
    if df.empty or not any(col.startswith(id_prefix) for col in df.columns):
        return f"{id_prefix}001"
    
    id_col = None
    for col in df.columns:
        if col.startswith(id_prefix):
            id_col = col
            break
            
    if id_col is None:
        return f"{id_prefix}001"

    existing_ids = df[id_col].dropna().astype(str)
    if existing_ids.empty:
        return f"{id_prefix}001"

    max_num = 0
    for an_id in existing_ids:
        try:
            num_part = ''.join(filter(str.isdigit, an_id))
            if num_part:
                max_num = max(max_num, int(num_part))
        except ValueError:
            continue

    return f"{id_prefix}{max_num + 1:03d}"

# --- User Authentication ---
def login():
    st.sidebar.title("Login")
    company_name_input = st.sidebar.selectbox("Select Company", options=list(st.session_state['USER_DB'].keys()))
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")

    if st.sidebar.button("Login"):
        company_data = st.session_state['USER_DB'].get(company_name_input)
        if company_data:
            user_data = company_data["users"].get(username)
            if user_data and bcrypt.checkpw(password.encode('utf-8'), user_data["password_hash"].encode('utf-8')):
                st.session_state['logged_in'] = True
                st.session_state['company_id'] = company_name_input
                st.session_state['user_id'] = username
                st.session_state['company_name'] = company_data['company_name']
                st.session_state['role'] = user_data['role']
                st.success(f"Logged in as {username} for {company_data['company_name']}")
                st.rerun()
            else:
                st.sidebar.error("Invalid Username or Password.")
        else:
            st.sidebar.error("Company not found.")

def logout():
    st.session_state['logged_in'] = False
    st.session_state['company_id'] = None
    st.session_state['user_id'] = None
    st.session_state['company_name'] = None
    st.session_state['role'] = None
    st.session_state['admin_selected_company_for_modules_name'] = None
    st.info("Logged out successfully.")
    st.rerun()

# --- Admin Functionality ---
def admin_user_management():
    st.header("Admin User Management")
    st.write("Manage users and their associated companies.")

    st.subheader("Add/Edit User")
    with st.form("add_edit_user_form"):
        company_options = list(st.session_state['USER_DB'].keys())
        selected_company_for_user_ops = st.selectbox("Select Company (for user operations)", options=company_options + ["Add New Company..."])

        new_company_name = ""
        new_company_pin = ""
        if selected_company_for_user_ops == "Add New Company...":
            new_company_name = st.text_input("New Company Name (e.g., 'NEW CARGO W.L.L')")
            new_company_pin = st.text_input("New Company PIN (e.g., 'NEW CARGO W.L.L')")

        user_to_edit = st.selectbox("Select User (to edit or type new)", options=["(New User)"] + list(st.session_state['USER_DB'].get(selected_company_for_user_ops, {}).get('users', {}).keys()))
        
        new_username = st.text_input("Username", value="" if user_to_edit == "(New User)" else user_to_edit)
        new_password = st.text_input("Password (leave blank if not changing)", type="password")
        new_role = st.selectbox("Role", options=["user", "admin"], index=0 if user_to_edit == "(New User)" else (0 if st.session_state['USER_DB'].get(selected_company_for_user_ops, {}).get('users', {}).get(user_to_edit, {}).get('role') == 'user' else 1))

        submitted = st.form_submit_button("Save User")
        if submitted:
            target_company_id = selected_company_for_user_ops
            if selected_company_for_user_ops == "Add New Company...":
                if new_company_name and new_company_pin:
                    if new_company_name not in st.session_state['USER_DB']:
                        st.session_state['USER_DB'][new_company_name] = {
                            "company_name": new_company_name,
                            "company_pin": new_company_pin,
                            "users": {}
                        }
                        target_company_id = new_company_name
                        st.success(f"New company '{new_company_name}' added.")
                    else:
                        st.warning(f"Company '{new_company_name}' already exists. Adding user to existing company.")
                        target_company_id = new_company_name
                else:
                    st.error("Please provide both New Company Name and New Company PIN.")
                    submitted = False
            
            if submitted and target_company_id:
                if new_username:
                    if new_password:
                        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                    else:
                        if user_to_edit != "(New User)" and new_username == user_to_edit:
                            hashed_password = st.session_state['USER_DB'][target_company_id]['users'][user_to_edit]['password_hash']
                        else:
                            st.error("New users require a password.")
                            return
                    
                    if target_company_id not in st.session_state['USER_DB']:
                        st.session_state['USER_DB'][target_company_id] = {"company_name": target_company_id, "company_pin": target_company_id, "users": {}}
                        
                    st.session_state['USER_DB'][target_company_id]['users'][new_username] = {
                        "password_hash": hashed_password,
                        "role": new_role
                    }
                    st.success(f"User '{new_username}' for '{target_company_id}' saved successfully.")
                    st.rerun()
                else:
                    st.error("Please provide a username.")

    st.subheader("Delete User")
    with st.form("delete_user_form"):
        company_to_delete_from = st.selectbox("Select Company (to delete user from)", options=list(st.session_state['USER_DB'].keys()))
        user_to_delete = st.selectbox("Select User to Delete", options=list(st.session_state['USER_DB'].get(company_to_delete_from, {}).get('users', {}).keys()))
        delete_submitted = st.form_submit_button("Delete User")
        if delete_submitted and user_to_delete:
            if st.session_state['USER_DB'][company_to_delete_from]['users'].pop(user_to_delete, None):
                st.success(f"User '{user_to_delete}' deleted from '{company_to_delete_from}'.")
                st.rerun()
            else:
                st.error("User not found.")

    st.subheader("Delete Company")
    with st.form("delete_company_form"):
        company_to_delete = st.selectbox("Select Company to Delete", options=list(st.session_state['USER_DB'].keys()))
        delete_company_submitted = st.form_submit_button("Delete Company and All Its Users")
        if delete_company_submitted and company_to_delete:
            if company_to_delete != "COMPANY MANAGEMENT":
                if st.session_state['USER_DB'].pop(company_to_delete, None):
                    st.success(f"Company '{company_to_delete}' and all its users deleted.")
                    if db:
                        try:
                            company_doc_ref = db.collection(FIRESTORE_ROOT_COLLECTION).document(company_to_delete)
                            for module_config in MODULE_CONFIGS.values():
                                collection_name = module_config['collection']
                                docs_to_delete = company_doc_ref.collection(collection_name).stream()
                                for doc in docs_to_delete:
                                    doc.reference.delete()
                            company_doc_ref.delete()
                            st.success(f"All data for '{company_to_delete}' deleted from Firestore.")
                        except Exception as e:
                            st.error(f"Error deleting Firestore data for company '{company_to_delete}': {e}")
                    st.rerun()
                else:
                    st.error("Company not found.")
            else:
                st.error("Cannot delete the 'COMPANY MANAGEMENT' company.")

    st.subheader("Current User Database Structure")
    st.json(st.session_state['USER_DB'])

def admin_data_management():
    st.header("Admin Data Management")
    st.write("View and manage data across all companies.")

    company_keys = [comp_id for comp_id in st.session_state['USER_DB'].keys() if st.session_state['USER_DB'][comp_id]['company_pin'] != 'ADMIN']
    selected_company_for_data = st.selectbox("Select Company to View Data", options=company_keys)
    st.session_state['admin_selected_company_for_modules_name'] = selected_company_for_data

    if selected_company_for_data:
        st.subheader(f"Data for {selected_company_for_data}")
        module_options = list(MODULE_CONFIGS.keys())
        selected_module_for_admin = st.selectbox("Select Module", options=module_options)

        if selected_module_for_admin:
            st.markdown("---")
            st.subheader(f"{selected_module_for_admin} Data")
            company_id_for_data = selected_company_for_data
            
            collection_name = MODULE_CONFIGS[selected_module_for_admin]["collection"]
            
            df_key = f'df_{company_id_for_data}_{collection_name}'

            if df_key not in st.session_state:
                st.session_state[df_key] = load_data(company_id_for_data, selected_module_for_admin)

            current_df = st.session_state[df_key].copy()

            if not current_df.empty:
                st.dataframe(current_df, use_container_width=True)
            else:
                st.info(f"No data available for {selected_module_for_admin} in {selected_company_for_data}.")

            if st.button(f"Refresh {selected_module_for_admin} Data"):
                st.session_state[df_key] = load_data(company_id_for_data, selected_module_for_admin)
                st.rerun()

def admin_reports_dashboard():
    st.header("Admin Global Reports & Dashboard")
    st.write("Generate comprehensive reports and view dashboards across all companies.")

    if st.button("Generate Overall Management PDF Report"):
        all_companies_data = {}
        for module_name, config in MODULE_CONFIGS.items():
            collection_name = config['collection']
            combined_df = pd.DataFrame()
            for company_id_key, company_details in st.session_state['USER_DB'].items():
                if company_details['company_pin'] != 'ADMIN':
                    company_df = firestore_get_collection(company_id_key, collection_name)
                    if not company_df.empty:
                        company_df['Company'] = company_details['company_name']
                        combined_df = pd.concat([combined_df, company_df], ignore_index=True)
            all_companies_data[collection_name] = combined_df

        pdf_output = generate_management_pdf_report(all_companies_data, st.session_state['USER_DB'])
        st.download_button(
            label="Download Overall Management Report (PDF)",
            data=pdf_output,
            file_name=f"Global_Management_Report_{datetime.date.today().strftime('%Y%m%d')}.pdf",
            mime="application/pdf"
        )
    st.markdown("---")

    st.subheader("Individual Company Data Overview (Interactive)")

    company_keys = [comp_id for comp_id in st.session_state['USER_DB'].keys() if st.session_state['USER_DB'][comp_id]['company_pin'] != 'ADMIN']
    selected_company_dashboard = st.selectbox("Select Company for Dashboard View", options=company_keys, key="dashboard_company_select")

    if selected_company_dashboard:
        st.write(f"### {selected_company_dashboard} Dashboard")
        
        company_trips_df = firestore_get_collection(selected_company_dashboard, "trips")
        company_invoices_df = firestore_get_collection(selected_company_dashboard, "invoices")
        company_vehicles_df = firestore_get_collection(selected_company_dashboard, "vehicles")
        company_employees_df = firestore_get_collection(selected_company_dashboard, "employees")
        
        col1, col2, col3 = st.columns(3)

        with col1:
            total_trips = len(company_trips_df) if not company_trips_df.empty else 0
            st.metric(label="Total Trips", value=total_trips)
            
            if not company_trips_df.empty and 'Status' in company_trips_df.columns:
                trip_status_counts = company_trips_df['Status'].value_counts().reset_index()
                trip_status_counts.columns = ['Status', 'Count']
                fig_trips_status = px.pie(trip_status_counts, values='Count', names='Status', 
                                           title='Trips by Status', 
                                           color_discrete_sequence=px.colors.qualitative.Pastel)
                st.plotly_chart(fig_trips_status, use_container_width=True)

        with col2:
            total_revenue = company_invoices_df['Total Amount'].sum() if not company_invoices_df.empty and 'Total Amount' in company_invoices_df.columns else 0
            st.metric(label="Total Revenue (INR)", value=f"{total_revenue:,.2f}")

            if not company_invoices_df.empty and 'Payment Status' in company_invoices_df.columns and 'Total Amount' in company_invoices_df.columns:
                revenue_by_status = company_invoices_df.groupby('Payment Status')['Total Amount'].sum().reset_index()
                fig_revenue_status = px.pie(revenue_by_status, values='Total Amount', names='Payment Status',
                                            title='Revenue by Payment Status',
                                            color_discrete_sequence=px.colors.qualitative.Set2)
                st.plotly_chart(fig_revenue_status, use_container_width=True)

        with col3:
            total_vehicles = len(company_vehicles_df) if not company_vehicles_df.empty else 0
            st.metric(label="Total Vehicles", value=total_vehicles)

            if not company_vehicles_df.empty and 'Vehicle Type' in company_vehicles_df.columns:
                vehicle_type_counts = company_vehicles_df['Vehicle Type'].value_counts().reset_index()
                vehicle_type_counts.columns = ['Vehicle Type', 'Count']
                fig_vehicle_type = px.bar(vehicle_type_counts, x='Vehicle Type', y='Count',
                                        title='Vehicles by Type',
                                        color='Vehicle Type',
                                        color_discrete_sequence=px.colors.qualitative.D3)
                st.plotly_chart(fig_vehicle_type, use_container_width=True)
        
        st.markdown("---")
        st.subheader("Employee Overview")
        total_employees = len(company_employees_df) if not company_employees_df.empty else 0
        st.metric(label="Total Employees", value=total_employees)

        if not company_employees_df.empty and 'Position' in company_employees_df.columns:
            employee_positions = company_employees_df['Position'].value_counts().reset_index()
            employee_positions.columns = ['Position', 'Count']
            fig_employee_pos = px.bar(employee_positions, x='Position', y='Count',
                                    title='Employees by Position',
                                    color='Position',
                                    color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_employee_pos, use_container_width=True)

# --- Main App Logic ---
def main():
    if not st.session_state['logged_in']:
        login()
    else:
        st.sidebar.title(f"Welcome, {st.session_state['user_id']}!")
        st.sidebar.markdown(f"**Company:** {st.session_state['company_name']}")
        st.sidebar.markdown(f"**Role:** {st.session_state['role'].capitalize()}")
        if st.sidebar.button("Logout"):
            logout()

        st.sidebar.markdown("---")
        
        if st.session_state['role'] == 'admin':
            st.sidebar.subheader("Admin Functions")
            admin_options = ["User Management", "Data Management", "Global Reports & Dashboard"]
            selected_admin_option = st.sidebar.radio("Admin Menu", admin_options)

            if selected_admin_option == "User Management":
                admin_user_management()
            elif selected_admin_option == "Data Management":
                admin_data_management()
            elif selected_admin_option == "Global Reports & Dashboard":
                admin_reports_dashboard()
        
        else:
            st.sidebar.subheader("Modules")
            module_options = list(MODULE_CONFIGS.keys())
            selected_module = st.sidebar.radio("Select a Module", module_options)

            st.title(selected_module)
            st.write(f"Managing {selected_module} for **{st.session_state['company_name']}**")
            st.markdown("---")

            company_id_for_data_ops = st.session_state['company_id']

            collection_name = MODULE_CONFIGS[selected_module]["collection"]
            fields_config = MODULE_CONFIGS[selected_module]["fields"]
            
            df_key = f'df_{company_id_for_data_ops}_{collection_name}'
            if df_key not in st.session_state:
                st.session_state[df_key] = load_data(company_id_for_data_ops, selected_module)
            
            current_df = st.session_state[df_key].copy()

            st.subheader("Current Records")
            if not current_df.empty:
                display_df = current_df.drop(columns=['doc_id'], errors='ignore')
                st.dataframe(display_df, use_container_width=True)
            else:
                st.info(f"No records found for {selected_module}. Add a new record below.")
            
            st.markdown("---")

            action = st.radio("Choose Action", ["Add New Record", "Edit Existing Record", "Delete Record", "Generate Report"])

            if action == "Add New Record":
                st.subheader("Add New Record")
                new_record_data = {}
                id_col_name = None

                for field_name, config in fields_config.items():
                    if config["editable"]:
                        if config["type"] == "text":
                            new_record_data[field_name] = st.text_input(f"{field_name}:")
                        elif config["type"] == "number":
                            new_record_data[field_name] = st.number_input(f"{field_name}:", value=0.0 if "INR" in field_name else 0, format="%.2f" if "INR" in field_name else "%d")
                        elif config["type"] == "date":
                            new_record_data[field_name] = st.date_input(f"{field_name}:", value=datetime.date.today())
                        elif config["type"] == "datetime":
                            date_val = st.date_input(f"{field_name} (Date):", value=datetime.date.today(), key=f"new_{field_name}_date")
                            time_val = st.time_input(f"{field_name} (Time):", value=datetime.time(0, 0), key=f"new_{field_name}_time")
                            new_record_data[field_name] = f"{date_val} {time_val}" if date_val and time_val else None
                        elif config["type"] == "select":
                            new_record_data[field_name] = st.selectbox(f"{field_name}:", options=config["options"])
                        elif config["type"] == "textarea":
                            new_record_data[field_name] = st.text_area(f"{field_name}:")
                        elif config["type"] == "json_table":
                            st.write(f"**{field_name}:** (Add/Edit Items below)")
                            num_items = st.number_input("Number of Items", min_value=1, value=1, key="num_items_new")
                            items_list = []
                            for i in range(int(num_items)):
                                st.markdown(f"***Item {i+1}***")
                                item_description = st.text_input(f"Description (Item {i+1})", key=f"new_item_desc_{i}")
                                item_quantity = st.number_input(f"Quantity (Item {i+1})", min_value=0.0, value=1.0, key=f"new_item_qty_{i}")
                                item_unit_price = st.number_input(f"Unit Price (Item {i+1})", min_value=0.0, value=0.0, format="%.2f", key=f"new_item_price_{i}")
                                item_amount = item_quantity * item_unit_price
                                st.write(f"Calculated Amount: {item_amount:,.2f} INR")
                                items_list.append({
                                    "Description": item_description,
                                    "Quantity": item_quantity,
                                    "Unit Price": item_unit_price,
                                    "Amount": item_amount
                                })
                            new_record_data[field_name] = json.dumps(items_list)

                    else:
                        if field_name == "Company":
                            new_record_data[field_name] = st.session_state['company_name']
                        elif "ID" in field_name or "Number" in field_name:
                            id_col_name = field_name
                            id_prefix_map = {
                                "Trip ID": "TRP-",
                                "Rental ID": "RNT-",
                                "Vehicle ID": "VHC-",
                                "Inv Number": "INV-",
                                "Client ID": "CLI-",
                                "Employee ID": "EMP-",
                                "Payslip ID": "PSL-",
                                "Leave ID": "LEV-",
                                "Transaction ID": "TRN-"
                            }
                            prefix = id_prefix_map.get(field_name, "REC-")
                            new_record_data[field_name] = get_next_id(current_df, prefix)
                
                if st.button("Add Record"):
                    record_to_add = {field: new_record_data.get(field, None) for field, _ in fields_config.items()}
                    record_to_add['Company'] = st.session_state['company_name']

                    temp_df = pd.DataFrame([record_to_add])
                    temp_df = apply_calculations(temp_df, selected_module)
                    record_to_add = temp_df.iloc[0].to_dict()

                    new_doc_id = firestore_add_document(company_id_for_data_ops, collection_name, record_to_add)
                    if new_doc_id:
                        st.success("Record added successfully!")
                        st.session_state[df_key] = load_data(company_id_for_data_ops, selected_module)
                        st.rerun()
                    else:
                        st.error("Failed to add record to Firestore.")

            elif action == "Edit Existing Record":
                st.subheader("Edit Existing Record")
                if not current_df.empty:
                    primary_id_col = next((col for col in fields_config if "ID" in col or "Number" in col), None)
                    if primary_id_col is None:
                        st.error("Cannot find a suitable ID column for editing.")
                        return

                    record_to_edit_id = st.selectbox(f"Select Record by {primary_id_col}", options=current_df[primary_id_col].tolist())
                    
                    if record_to_edit_id:
                        selected_record = current_df[current_df[primary_id_col] == record_to_edit_id].iloc[0].to_dict()
                        selected_doc_id = selected_record.get('doc_id')

                        edited_data = {}
                        for field_name, config in fields_config.items():
                            if field_name == primary_id_col or field_name == "Company":
                                st.text_input(f"{field_name}:", value=selected_record.get(field_name), disabled=True)
                                continue
                            
                            current_value = selected_record.get(field_name)

                            if config["editable"]:
                                if config["type"] == "text":
                                    edited_data[field_name] = st.text_input(f"{field_name}:", value=str(current_value) if current_value is not None else "")
                                elif config["type"] == "number":
                                    edited_data[field_name] = st.number_input(f"{field_name}:", value=float(current_value) if current_value is not None else 0.0, format="%.2f" if "INR" in field_name else "%d")
                                elif config["type"] == "date":
                                    if isinstance(current_value, datetime.date):
                                        value_date = current_value
                                    elif isinstance(current_value, str):
                                        try:
                                            value_date = datetime.datetime.strptime(current_value, "%Y-%m-%d").date()
                                        except ValueError:
                                            value_date = datetime.date.today()
                                    else:
                                        value_date = datetime.date.today()
                                    edited_data[field_name] = st.date_input(f"{field_name}:", value=value_date)
                                elif config["type"] == "datetime":
                                    dt_val = None
                                    if isinstance(current_value, str):
                                        try:
                                            dt_val = datetime.datetime.strptime(current_value, "%Y-%m-%d %H:%M:%S")
                                        except ValueError:
                                            pass
                                    
                                    date_val_init = dt_val.date() if dt_val else datetime.date.today()
                                    time_val_init = dt_val.time() if dt_val else datetime.time(0, 0)

                                    date_val = st.date_input(f"{field_name} (Date):", value=date_val_init, key=f"edit_{field_name}_date_{record_to_edit_id}")
                                    time_val = st.time_input(f"{field_name} (Time):", value=time_val_init, key=f"edit_{field_name}_time_{record_to_edit_id}")
                                    edited_data[field_name] = f"{date_val} {time_val}" if date_val and time_val else None
                                elif config["type"] == "select":
                                    index = config["options"].index(current_value) if current_value in config["options"] else 0
                                    edited_data[field_name] = st.selectbox(f"{field_name}:", options=config["options"], index=index)
                                elif config["type"] == "textarea":
                                    edited_data[field_name] = st.text_area(f"{field_name}:", value=str(current_value) if current_value is not None else "")
                                elif config["type"] == "json_table":
                                    st.write(f"**{field_name}:** (Edit Items below)")
                                    try:
                                        current_items = json.loads(current_value) if isinstance(current_value, str) else current_value
                                        if not isinstance(current_items, list):
                                            current_items = []
                                    except (json.JSONDecodeError, TypeError):
                                        current_items = []

                                    num_items = st.number_input("Number of Items", min_value=1, value=len(current_items) if current_items else 1, key=f"num_items_edit_{record_to_edit_id}")
                                    
                                    items_list = []
                                    for i in range(int(num_items)):
                                        st.markdown(f"***Item {i+1}***")
                                        item_desc_val = current_items[i].get('Description', '') if i < len(current_items) else ''
                                        item_qty_val = float(current_items[i].get('Quantity', 0)) if i < len(current_items) else 1.0
                                        item_price_val = float(current_items[i].get('Unit Price', 0)) if i < len(current_items) else 0.0
                                        
                                        item_description = st.text_input(f"Description (Item {i+1})", value=item_desc_val, key=f"edit_item_desc_{record_to_edit_id}_{i}")
                                        item_quantity = st.number_input(f"Quantity (Item {i+1})", min_value=0.0, value=item_qty_val, key=f"edit_item_qty_{record_to_edit_id}_{i}")
                                        item_unit_price = st.number_input(f"Unit Price (Item {i+1})", min_value=0.0, value=item_price_val, format="%.2f", key=f"edit_item_price_{record_to_edit_id}_{i}")
                                        item_amount = item_quantity * item_unit_price
                                        st.write(f"Calculated Amount: {item_amount:,.2f} INR")
                                        items_list.append({
                                            "Description": item_description,
                                            "Quantity": item_quantity,
                                            "Unit Price": item_unit_price,
                                            "Amount": item_amount
                                        })
                                    edited_data[field_name] = json.dumps(items_list)

                        else:
                            edited_data[field_name] = current_value

                        if 'Company' not in edited_data:
                            edited_data['Company'] = st.session_state['company_name']

                        temp_df = pd.DataFrame([edited_data])
                        temp_df = apply_calculations(temp_df, selected_module)
                        data_to_save = temp_df.iloc[0].to_dict()

                        data_to_save.pop('doc_id', None)

                        if st.button("Update Record"):
                            if firestore_update_document(company_id_for_data_ops, collection_name, selected_doc_id, data_to_save):
                                st.success("Record updated successfully!")
                                st.session_state[df_key] = load_data(company_id_for_data_ops, selected_module)
                                st.rerun()
                            else:
                                st.error("Failed to update record in Firestore.")
                else:
                    st.info("No records to edit.")

            elif action == "Delete Record":
                st.subheader("Delete Record")
                if not current_df.empty:
                    primary_id_col = next((col for col in fields_config if "ID" in col or "Number" in col), None)
                    if primary_id_col is None:
                        st.error("Cannot find a suitable ID column for deletion.")
                        return

                    record_to_delete_id = st.selectbox(f"Select Record by {primary_id_col} to Delete", options=current_df[primary_id_col].tolist())
                    
                    if record_to_delete_id:
                        selected_record = current_df[current_df[primary_id_col] == record_to_delete_id].iloc[0]
                        selected_doc_id = selected_record.get('doc_id')

                        st.warning(f"Are you sure you want to delete the record with {primary_id_col}: **{record_to_delete_id}**?")
                        if st.button("Confirm Delete"):
                            if firestore_delete_document(company_id_for_data_ops, collection_name, selected_doc_id):
                                st.success("Record deleted successfully!")
                                st.session_state[df_key] = load_data(company_id_for_data_ops, selected_module)
                                st.rerun()
                            else:
                                st.error("Failed to delete record from Firestore.")
                else:
                    st.info("No records to delete.")

            elif action == "Generate Report":
                st.subheader(f"Generate {selected_module} Report")
                if not current_df.empty:
                    report_df = current_df.drop(columns=['doc_id'], errors='ignore')

                    col_rpt1, col_rpt2 = st.columns(2)

                    with col_rpt1:
                        excel_report_data = generate_excel_report(report_df, f"{selected_module}_Report.xlsx")
                        st.download_button(
                            label="Download Excel Report",
                            data=excel_report_data,
                            file_name=f"{st.session_state['company_name'].replace(' ', '_')}_{selected_module}_Report_{datetime.date.today().strftime('%Y%m%d')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    
                    with col_rpt2:
                        if selected_module == "Invoicing & Quoting":
                            st.info("Select an invoice to generate a detailed PDF.")
                            invoice_numbers = report_df['Inv Number'].tolist()
                            selected_invoice_num = st.selectbox("Select Invoice Number", options=invoice_numbers)
                            if selected_invoice_num:
                                invoice_data = report_df[report_df['Inv Number'] == selected_invoice_num].iloc[0].to_dict()
                                mock_logo_url = "https://i.ibb.co/vYc4XjC/concord-logo.jpg"
                                logo_x = 10
                                logo_y = 10
                                logo_width = 30
                                logo_height = 15

                                invoice_pdf_output = generate_single_tax_invoice_pdf(
                                    invoice_data,
                                    st.session_state['company_name'],
                                    st.session_state['USER_DB'][st.session_state['company_id']]['company_pin'],
                                    mock_logo_url, logo_x, logo_y, logo_width, logo_height
                                )
                                st.download_button(
                                    label=f"Download Invoice {selected_invoice_num} (PDF)",
                                    data=invoice_pdf_output,
                                    file_name=f"Invoice_{selected_invoice_num}_{datetime.date.today().strftime('%Y%m%d')}.pdf",
                                    mime="application/pdf"
                                )
                            
                        else:
                            pdf_report_data = generate_pdf_report(report_df, f"{selected_module} Report for {st.session_state['company_name']}")
                            st.download_button(
                                label="Download PDF Report",
                                data=pdf_report_data,
                                file_name=f"{st.session_state['company_name'].replace(' ', '_')}_{selected_module}_Report_{datetime.date.today().strftime('%Y%m%d')}.pdf",
                                mime="application/pdf"
                            )
                else:
                    st.info("No data available to generate a report.")
                
            if firebase_initialized:
                st.info("Firebase app initialized successfully.")
            else:
                st.error("Firebase initialization failed. Database operations may not work.")

if __name__ == "__main__":
    main()
