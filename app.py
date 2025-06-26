import streamlit as st
import pandas as pd
import bcrypt
import io
from fpdf import FPDF
import datetime
import plotly.express as px
import plotly.graph_objects as go
from num2words import num2words
import sqlite3
import uuid

# --- Configuration for Company Authentication and Details ---

# INITIAL_USER_DB_STRUCTURE: Used for initial user setup and authentication.
# This structure defines companies and their associated users and roles.
INITIAL_USER_DB_STRUCTURE = {
    "east_concord_wll": {
        "company_name": "EAST CONCORD W.L.L",
        "company_pin": "EAST", # Simplified PIN for login
        "users": {
            "john_east": {"password_hash": bcrypt.hashpw("east123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'), "role": "user"},
            "jane_east": {"password_hash": bcrypt.hashpw("east123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'), "role": "user"},
        }
    },
    "sa_concord_international": {
        "company_name": "S.A. CONCORD INTERNATIONAL CARGO HANDLING CO W.L.L",
        "company_pin": "SA",
        "users": {
            "peter_sa": {"password_hash": bcrypt.hashpw("sa123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'), "role": "user"},
        }
    },
    "north_concord_cargo": {
        "company_name": "NORTH CONCORD CARGO HANDLING CO W.L.L",
        "company_pin": "NORTH",
        "users": {
            "alice_north": {"password_hash": bcrypt.hashpw("north123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'), "role": "user"},
        }
    },
    "management_company": {
        "company_name": "Global Management",
        "company_pin": "ADMIN", # Special PIN for admin access
        "users": {
            "admin": {"password_hash": bcrypt.hashpw("adminpass".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'), "role": "admin"},
        }
    }
}

# COMPANY_PROFILES: Used for populating detailed company information in PDFs,
# especially for the Tax Invoice, mirroring actual letterhead details.
COMPANY_PROFILES = {
    "EAST CONCORD W.L.L": {
        "name": "EAST CONCORD W.L.L",
        "trn": "2200221799400002", # Example TRN from bill background.PNG
        "address_line1": "Flat/Shop No. 11, Building 471",
        "address_line2": "Road/Shop 3513, MANAMA",
        "city_country": "UMM AL-HASSAM, Kingdom of Bahrain",
        "email": "concord@email.com", # Example email
        "phone": "Tel: 17228646 | Mob: 39884260, 339660641" # Example numbers
    },
    "S.A. CONCORD INTERNATIONAL CARGO HANDLING CO W.L.L": {
        "name": "S.A. CONCORD INTERNATIONAL CARGO HANDLING CO W.L.L",
        "trn": "TRN_SA_CONCORD_123", # Placeholder TRN
        "address_line1": "S.A. Concord International Office 1",
        "address_line2": "Building XYZ, Road ABC",
        "city_country": "Bahrain City, Kingdom of Bahrain",
        "email": "sa.concord@email.com",
        "phone": "Tel: 11223344 | Mob: 55667788"
    },
    "NORTH CONCORD CARGO HANDLING CO W.L.L": {
        "name": "NORTH CONCORD CARGO HANDLING CO W.L.L",
        "trn": "TRN_NORTH_CONCORD_456", # Placeholder TRN
        "address_line1": "North Concord Cargo Building 10",
        "address_line2": "Street 101, Block 202",
        "city_country": "Manama, Kingdom of Bahrain",
        "email": "north.concord@email.com",
        "phone": "Tel: 99887766 | Mob: 44332211"
    }
}


# --- Specific Module Field Configurations ---
TRIP_MANAGEMENT_FIELDS = {
    'Trip Type': {'type': 'select', 'options': ['Per Trip', 'Daily', 'Monthly']},
    'Vehicle Type': {'type': 'select', 'options': ['Open', 'Box', 'Chiller', 'Frozen', 'Chiller Van', 'Passenger Van', 'Others']},
    'Pickup Address': {'type': 'text'},
    'Delivery Address': {'type': 'text'},
    'Client': {'type': 'text'},
    'Vehicle': {'type': 'text'},
    'Assigned Driver': {'type': 'text'},
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
    'Particulars': {'type': 'text'},
    'Quantity': {'type': 'number'},
    'Rate': {'type': 'number'},
    'Amount': {'type': 'number'},
    'VAT (10%)': {'type': 'number'},
    'Total Amount': {'type': 'number'},
    'VAT Option': {'type': 'select', 'options': ['Include', 'Exclude']},
    'Linked ID': {'type': 'text'},
    'Remarks': {'type': 'text'},
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

# Populate the MODULE_FIELDS_MAP right after defining all individual field configs
MODULE_FIELDS_MAP = {
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

# --- Initialize Session State ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['company_id'] = None
    st.session_state['user_id'] = None
    st.session_state['company_name'] = None
    st.session_state['role'] = None
    st.session_state['admin_selected_company_for_modules_name'] = None

# Initialize USER_DB in session state (this will be populated from SQLite)
if 'USER_DB' not in st.session_state:
    st.session_state['USER_DB'] = {}


# --- SQLite Database Initialization and Operations ---
DB_NAME = 'logistic_erp.db'

def get_db_connection():
    """Establishes and returns a new connection to the SQLite database."""
    # Important: Create a new connection each time to avoid thread issues with Streamlit
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row # Allows accessing columns by name
    return conn

def init_db():
    """Initializes the database schema and populates initial user data."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                company_id TEXT NOT NULL,
                company_name TEXT NOT NULL,
                username TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL
            )
        """)

        # Populate initial users if table is empty
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            for company_id, company_data in INITIAL_USER_DB_STRUCTURE.items():
                for username, user_data in company_data['users'].items():
                    cursor.execute(
                        "INSERT INTO users (id, company_id, company_name, username, password_hash, role) VALUES (?, ?, ?, ?, ?, ?)",
                        (str(uuid.uuid4()), company_id, company_data['company_name'], username, user_data['password_hash'], user_data['role'])
                    )
            conn.commit()
            st.success("Initial users populated in database!")

        # Create tables for each module dynamically based on MODULE_FIELDS_MAP
        for table_name, fields_config in MODULE_FIELDS_MAP.items():
            columns = []
            columns.append("doc_id TEXT PRIMARY KEY") # Unique ID for each record
            columns.append("company_id TEXT NOT NULL") # Link to company_id from users
            columns.append("Company TEXT NOT NULL") # Store company name directly for display

            for field_name, config in fields_config.items():
                sql_type = "TEXT"
                if config['type'] == 'number':
                    sql_type = "REAL"
                elif config['type'] == 'date':
                    sql_type = "TEXT" # (%Y-%m-%d)
                elif config['type'] == 'datetime':
                    sql_type = "TEXT" # (%Y-%m-%d HH:MM:SS.ffffff)
                elif config['type'] == 'checkbox':
                    sql_type = "INTEGER" # 0 or 1
                
                # Quoting column names to handle spaces and special characters.
                columns.append(f"\"{field_name}\" {sql_type}") 

            # Add explicit columns for the auto-generated IDs and Net Salary if they are not naturally in fields_config keys
            if table_name == 'trips' and 'Trip ID' not in fields_config:
                columns.append("\"Trip ID\" TEXT")
            if table_name == 'rentals' and 'Rental ID' not in fields_config:
                columns.append("\"Rental ID\" TEXT")
            if table_name == 'invoices' and 'Inv Number' not in fields_config:
                columns.append("\"Inv Number\" TEXT")
            if table_name == 'invoices' and 'SI No' not in fields_config:
                columns.append("\"SI No\" TEXT")
            if table_name == 'payslips' and 'Payslip ID' not in fields_config:
                columns.append("\"Payslip ID\" TEXT")
            if table_name == 'payslips' and 'Net Salary' not in fields_config:
                columns.append("\"Net Salary\" REAL")

            create_table_sql = f"CREATE TABLE IF NOT EXISTS \"{table_name}\" ({', '.join(columns)})"
            cursor.execute(create_table_sql)
            conn.commit()
        # st.success("Database tables initialized successfully.") # Commented to reduce clutter on every rerun
    except Exception as e:
        st.error(f"Error initializing database: {e}")
    finally:
        conn.close()

# Run database initialization on every script rerun.
# 'CREATE TABLE IF NOT EXISTS' ensures idempotency.
init_db()


def get_db_collection(company_id, collection_name):
    """
    Fetches all documents from a SQLite table for a given company.
    Converts date/datetime strings to appropriate Python objects for Streamlit display.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(f"SELECT * FROM \"{collection_name}\" WHERE company_id = ?", (company_id,)) # Quote table name
        rows = cursor.fetchall()
        
        if not rows:
            # Return an empty DataFrame with appropriate columns if no data
            columns_for_empty_df = list(MODULE_FIELDS_MAP.get(collection_name, {}).keys())
            if collection_name == 'trips': columns_for_empty_df.insert(0, 'Trip ID')
            if collection_name == 'rentals': columns_for_empty_df.insert(0, 'Rental ID')
            if collection_name == 'invoices': 
                columns_for_empty_df.insert(0, 'Inv Number') 
                columns_for_empty_df.insert(1, 'SI No') # SI No is also an auto-generated ID for invoices
            if collection_name == 'payslips': columns_for_empty_df.insert(0, 'Payslip ID')
            if collection_name == 'payslips' and 'Net Salary' not in columns_for_empty_df: columns_for_empty_df.append('Net Salary') # Ensure Net Salary is there
            columns_for_empty_df.append('Company') # Company name will be stored in the table
            columns_for_empty_df.append('doc_id') # Add doc_id as it's the primary key
            columns_for_empty_df.append('company_id') # Internal link
            return pd.DataFrame(columns=columns_for_empty_df)

        # Convert list of sqlite3.Row objects to list of dicts
        data_list = [dict(row) for row in rows]
        df = pd.DataFrame(data_list)
        
        module_fields_config = MODULE_FIELDS_MAP.get(collection_name, {})

        # Post-processing for date and datetime fields
        for field, config in module_fields_config.items():
            if field in df.columns and df[field].dtype == 'object': # Only try to convert object types (strings)
                if config['type'] == 'date':
                    df[field] = pd.to_datetime(df[field], errors='coerce').dt.date
                elif config['type'] == 'datetime':
                    df[field] = pd.to_datetime(df[field], errors='coerce')
            elif field in df.columns and config['type'] == 'checkbox':
                df[field] = df[field].astype(bool) # Convert 0/1 to boolean

        # Ensure all expected columns are present, even if empty
        expected_cols = list(module_fields_config.keys())
        if collection_name == 'trips': expected_cols.insert(0, 'Trip ID')
        if collection_name == 'rentals': expected_cols.insert(0, 'Rental ID')
        if collection_name == 'invoices': 
            expected_cols.insert(0, 'Inv Number')
            expected_cols.insert(1, 'SI No')
        if collection_name == 'payslips': expected_cols.insert(0, 'Payslip ID')
        if collection_name == 'payslips' and 'Net Salary' not in expected_cols: expected_cols.append('Net Salary') # Ensure Net Salary is there

        expected_cols.insert(0, 'doc_id') # Primary key
        expected_cols.insert(1, 'company_id') # Internal link
        expected_cols.insert(2, 'Company') # User-friendly company name

        for col in expected_cols:
            if col not in df.columns:
                df[col] = None # Add missing columns with None

        # Reorder columns to match fields_config + Company + doc_id
        ordered_cols = [c for c in expected_cols if c in df.columns]
        df = df[ordered_cols]
        
        return df
    except sqlite3.OperationalError as e:
        # st.warning(f"Table '{collection_name}' might not exist yet. Please add data to create it. Error: {e}") # Commented to reduce clutter
        # Return an empty DataFrame with expected columns if table does not exist
        columns_for_empty_df = list(MODULE_FIELDS_MAP.get(collection_name, {}).keys())
        if collection_name == 'trips': columns_for_empty_df.insert(0, 'Trip ID')
        if collection_name == 'rentals': columns_for_empty_df.insert(0, 'Rental ID')
        if collection_name == 'invoices': 
            columns_for_empty_df.insert(0, 'Inv Number')
            columns_for_empty_df.insert(1, 'SI No')
        if collection_name == 'payslips': columns_for_empty_df.insert(0, 'Payslip ID')
        if collection_name == 'payslips' and 'Net Salary' not in columns_for_empty_df: columns_for_empty_df.append('Net Salary')
        columns_for_empty_df.insert(0, 'doc_id')
        columns_for_empty_df.insert(1, 'company_id')
        columns_for_empty_df.insert(2, 'Company')
        return pd.DataFrame(columns=columns_for_empty_df)
    except Exception as e:
        st.error(f"Error fetching data from SQLite for {collection_name}: {e}")
        return pd.DataFrame()
    finally:
        conn.close()


def add_db_document(company_id, collection_name, data):
    """Adds a document to a SQLite table for a given company."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    new_doc_id = str(uuid.uuid4())
    data['doc_id'] = new_doc_id # Assign unique ID

    # Ensure company_id and Company are in data for insertion
    data['company_id'] = company_id
    # Get company name from USER_DB_STRUCTURE if not already in data
    if 'Company' not in data:
        for comp_id, comp_details in INITIAL_USER_DB_STRUCTURE.items(): # Use INITIAL_USER_DB_STRUCTURE to get name for ID
            if comp_id == company_id:
                data['Company'] = comp_details['company_name']
                break
    
    # Convert Python types to SQLite-compatible strings/integers
    processed_data = {}
    for k, v in data.items():
        if isinstance(v, datetime.date):
            processed_data[k] = v.isoformat() # (%Y-%m-%d)
        elif isinstance(v, datetime.datetime):
            processed_data[k] = v.isoformat(sep=' ') # (%Y-%m-%d HH:MM:SS.ffffff)
        elif isinstance(v, bool):
            processed_data[k] = 1 if v else 0
        elif pd.isna(v): # Handle pandas NaNs
            processed_data[k] = None
        else:
            processed_data[k] = v

    columns = ', '.join([f'"{k}"' for k in processed_data.keys()])
    placeholders = ', '.join(['?' for _ in processed_data.keys()])
    values = tuple(processed_data.values())

    try:
        cursor.execute(f"INSERT INTO \"{collection_name}\" ({columns}) VALUES ({placeholders})", values) # Quote table name
        conn.commit()
        return new_doc_id
    except Exception as e:
        st.error(f"Error adding document to SQLite table '{collection_name}': {e}")
        return None
    finally:
        conn.close()


def update_db_document(company_id, collection_name, doc_id, data):
    """Updates a document in a SQLite table for a given company."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Exclude doc_id, company_id, Company from the update statement itself as they are primary/fixed keys
    update_data = {k: v for k, v in data.items() if k not in ['doc_id', 'company_id', 'Company']}

    # Convert Python types to SQLite-compatible strings/integers
    processed_update_data = {}
    for k, v in update_data.items():
        if isinstance(v, datetime.date):
            processed_update_data[k] = v.isoformat()
        elif isinstance(v, datetime.datetime):
            processed_update_data[k] = v.isoformat(sep=' ')
        elif isinstance(v, bool):
            processed_update_data[k] = 1 if v else 0
        elif pd.isna(v):
            processed_update_data[k] = None
        else:
            processed_update_data[k] = v

    set_clauses = [f'"{k}" = ?' for k in processed_update_data.keys()]
    values = tuple(processed_update_data.values()) + (doc_id, company_id)

    try:
        cursor.execute(f"UPDATE \"{collection_name}\" SET {', '.join(set_clauses)} WHERE doc_id = ? AND company_id = ?", values) # Quote table name
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error updating document {doc_id} in SQLite table '{collection_name}': {e}")
        return False
    finally:
        conn.close()


def delete_db_document(company_id, collection_name, doc_id):
    """Deletes a document from a SQLite table for a given company."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(f"DELETE FROM \"{collection_name}\" WHERE doc_id = ? AND company_id = ?", (doc_id, company_id)) # Quote table name
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error deleting document {doc_id} from SQLite table '{collection_name}': {e}")
        return False
    finally:
        conn.close()

# --- Helper Functions for Reports ---
def generate_excel_report(df, filename):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Report')
    processed_data = output.getvalue()
    return processed_data

def generate_pdf_report(df, title):
    """
    Generates a multi-page PDF report from a DataFrame, automatically breaking tables
    across pages to fit standard A4 size. Tables are designed to be responsive
    by adjusting column widths to available space and wrapping text.
    """
    pdf = FPDF()
    pdf.add_page()

    # --- Header ---
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, title, 0, 1, "C")
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 5, f"Report Date: {datetime.date.today().strftime('%Y-%m-%d')}", 0, 1, "C")
    pdf.ln(10) # Add some space after header

    # Ensure all DataFrame columns are strings for consistent width calculation
    df_str = df.astype(str).replace('None', '').replace('nan', '')

    available_width = pdf.w - pdf.l_margin - pdf.r_margin
    MIN_COL_WIDTH = 15 # mm

    desired_widths = {}
    # Temporarily set font for width calculation
    pdf.set_font("Arial", "B", 10) 
    for col in df_str.columns:
        header_width = pdf.get_string_width(str(col))
        # Ensure max_content_width is calculated with normal font size
        pdf.set_font("Arial", size=10)
        max_content_width = 0
        if not df_str[col].empty:
            max_content_width = df_str[col].apply(pdf.get_string_width).max()
        
        desired_widths[col] = max(header_width, max_content_width) + 6 # Add padding
        desired_widths[col] = max(desired_widths[col], MIN_COL_WIDTH)

    total_desired_width = sum(desired_widths.values())

    col_widths = {}
    if total_desired_width > available_width:
        scale_factor = available_width / total_desired_width
        for col in df_str.columns:
            col_widths[col] = max(desired_widths[col] * scale_factor, MIN_COL_WIDTH)
    else:
        # Distribute remaining space if total_desired_width is less than available_width
        remaining_width = available_width
        for col in df_str.columns:
            col_widths[col] = desired_widths[col]
            remaining_width -= col_widths[col]
        
        if remaining_width > 0:
            distributable_cols = [col for col, width in desired_widths.items()]
            if distributable_cols:
                extra_per_col = remaining_width / len(distributable_cols)
                for col in distributable_cols:
                    col_widths[col] += extra_per_col

    # Final adjustment to ensure all columns fit, and headers are readable
    final_total_width = sum(col_widths.values())
    if final_total_width > available_width:
        correction_factor = available_width / final_total_width
        for col in col_widths:
            col_widths[col] *= correction_factor

    # Render headers
    pdf.set_font("Arial", "B", 10)
    for col in df_str.columns:
        header_text = str(col)
        # Calculate how much space the text needs
        text_width = pdf.get_string_width(header_text)
        
        # If the text is too wide for the cell, truncate it with ellipsis
        # Adjust 2 to a slightly larger value (e.g., 4) for more visual padding
        if text_width > col_widths[col] - 4: 
            while pdf.get_string_width(header_text + '...') > col_widths[col] - 4 and len(header_text) > 3:
                header_text = header_text[:-1]
            header_text += '...'
        
        pdf.cell(col_widths[col], 10, header_text, 1, 0, "C") # Use the adjusted header_text
    pdf.ln()

    # Add data
    pdf.set_font("Arial", size=10)
    for index, row in df_str.iterrows():
        # Check if new page is needed before printing the row
        # This prediction is simplified; more complex might involve estimating row height
        if pdf.get_y() + 10 > pdf.h - pdf.b_margin: # 10 is a rough cell height
            pdf.add_page()
            # Re-render headers on new page
            pdf.set_font("Arial", "B", 10)
            for col in df_str.columns:
                header_text = str(col)
                text_width = pdf.get_string_width(header_text)
                if text_width > col_widths[col] - 4:
                    while pdf.get_string_width(header_text + '...') > col_widths[col] - 4 and len(header_text) > 3:
                        header_text = header_text[:-1]
                    header_text += '...'
                pdf.cell(col_widths[col], 10, header_text, 1, 0, "C")
            pdf.ln()
            pdf.set_font("Arial", size=10)

        max_row_height = 0 
        initial_x_for_row = pdf.get_x()
        initial_y_for_row = pdf.get_y()

        # First pass to determine max_row_height for multi_cell rows
        for col_idx, col in enumerate(df_str.columns):
            cell_text = str(row[col])
            # For multiline content, estimate num_lines based on actual content and column width
            estimated_num_lines = pdf.get_string_width(cell_text) / (col_widths[col] - pdf.c_margin * 2)
            num_lines = max(1, int(estimated_num_lines) + (1 if estimated_num_lines % 1 else 0))
            current_cell_height = num_lines * pdf.font_size * 1.2 # Adjust multiplier for line spacing
            max_row_height = max(max_row_height, current_cell_height)

        # Second pass to actually render the row with uniform height
        for col_idx, col in enumerate(df_str.columns):
            cell_text = str(row[col])
            
            # Save current position before multi_cell
            current_x = pdf.get_x()
            current_y = pdf.get_y()
            
            # Use multi_cell for all cells to handle potential wrapping, set ln=0
            pdf.multi_cell(col_widths[col], max_row_height / max(1, num_lines), txt=cell_text, border=1, align="L") # Calculate effective line height
            
            # Restore X position to just after the previous cell, and Y to the start of the current row segment
            # Then advance X for the next cell
            pdf.set_xy(current_x + col_widths[col], initial_y_for_row)
        
        # After all cells in a row are processed, move to the next line based on max_row_height
        pdf.set_y(initial_y_for_row + max_row_height + 1) # Add some padding
        pdf.set_x(pdf.l_margin) # Reset X to left margin

    # --- Footer ---
    pdf.set_y(pdf.h - 15)
    pdf.set_font("Arial", "I", 8)
    pdf.cell(0, 10, f"Page {pdf.page_no()}/{{nb}}", 0, 0, "C")

    return bytes(pdf.output(dest='S'))


def generate_management_pdf_report(all_companies_data, user_db_current):
    """
    Generates a multi-page management dashboard report PDF with aggregated KPIs and company-specific details.
    """
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # --- Background Image / Color for Management Report ---
    MANAGEMENT_REPORT_BACKGROUND_URL = "https://placehold.co/595x842/F0F8FF/313131?text=Management+Report+Background"
    try:
        # Check if the URL is valid and reachable. Otherwise, it might cause issues.
        # For a now, just attempt to load.
        pdf.image(MANAGEMENT_REPORT_BACKGROUND_URL, x=0, y=0, w=pdf.w, h=pdf.h)
    except Exception as e:
        pdf.set_fill_color(240, 248, 255) # Light blue background
        pdf.rect(0, 0, pdf.w, pdf.h, 'F')
        st.warning(f"Could not load management report background image from {MANAGEMENT_REPORT_BACKGROUND_URL}: {e}. Generating with fallback color.")

    # --- Header for Management Report ---
    pdf.set_y(10)
    pdf.set_font("Arial", "B", 20)
    pdf.cell(0, 10, "Global Logistic Management Dashboard Report", 0, 1, "C")
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 8, f"Report Date: {datetime.date.today().strftime('%Y-%m-%d')}", 0, 1, "C")
    pdf.ln(10)

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
            
            pdf.ln(5)

    # --- Footer for Management Report ---
    pdf.set_y(pdf.h - 15)
    pdf.set_font("Arial", "I", 8)
    pdf.cell(0, 10, f"Page {pdf.page_no()}/{{nb}} - Global Management Report", 0, 0, "C")

    return bytes(pdf.output(dest='S'))


def generate_single_tax_invoice_pdf(invoice_data, company_details, logo_url, logo_x, logo_y, logo_width, logo_height):
    """
    Generates a single tax invoice PDF based on the provided invoice data and company details.
    Incorporates a background image (simulating bill background.PNG) and a customizable logo.
    The output is constrained to a single A4 page for a standard invoice format,
    with text wrapping handled for 'Particulars' and 'Remarks'.
    
    Args:
        invoice_data (dict): Dictionary containing invoice details like 'Inv Number', 'Date',
                             'Amount', 'VAT (10%)', 'Total Amount', 'Client', 'Particulars', 'Remarks'.
        company_details (dict): Dictionary containing company-specific details:
                                'name', 'trn', 'address_line1', 'address_line2', 'city_country', 'email', 'phone'.
        logo_url (str): URL of the company logo.
        logo_x (int/float): X coordinate for logo placement.
        logo_y (int/float): Y coordinate for logo placement.
        logo_width (int/float): Width of the logo.
        logo_height (int/float): Height of the logo.
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=False, margin=10) # Set auto page break to False for single page control

    # --- Background Image (simulating bill background.PNG letterhead) ---
    BACKGROUND_IMAGE_URL = "https://i.ibb.co/RGTCjMb4/EAST-CONCORD-W-L-L-page-0001-1.jpg" 
    try:
        pdf.image(BACKGROUND_IMAGE_URL, x=0, y=0, w=pdf.w, h=pdf.h)
    except Exception as e:
        st.warning(f"Could not load background image from {BACKGROUND_IMAGE_URL}: {e}. Generating without background image.")
        pdf.set_fill_color(240, 248, 255)
        pdf.rect(0, 0, pdf.w, pdf.h, 'F')

    # --- Customizable Logo (separate from background, top left) ---
    try:
        if logo_url:
            pdf.image(logo_url, x=logo_x, y=logo_y, w=logo_width, h=logo_height)
    except Exception as e:
        st.warning(f"Could not load logo image from {logo_url}: {e}. Continuing without logo.")

    # --- Header Section (Company Info - dynamically populated based on company_details) ---
    pdf.set_y(25)
    pdf.set_font("Arial", "", 9)
    pdf.set_text_color(50, 50, 50)
    
    pdf.set_x(10)
    pdf.cell(0, 5, company_details.get("name", "YOUR COMPANY NAME W.L.L"), 0, 1, "L")
    pdf.set_x(10)
    pdf.cell(0, 5, company_details.get("address_line1", "Flat/Shop No. X, Building Y"), 0, 1, "L")
    pdf.set_x(10)
    pdf.cell(0, 5, company_details.get("address_line2", "Road/Shop XXXX, City"), 0, 1, "L")
    pdf.set_x(10)
    pdf.cell(0, 5, company_details.get("city_country", "District, Kingdom of Bahrain"), 0, 1, "L")
    pdf.set_x(10)
    pdf.cell(0, 5, f"TRN: {company_details.get('trn', 'N/A')}", 0, 1, "L")
    pdf.set_x(10)
    pdf.cell(0, 5, f"Email: {company_details.get('email', 'info@example.com')}", 0, 1, "L")
    pdf.set_x(10)
    pdf.cell(0, 5, f"Phone: {company_details.get('phone', 'N/A')}", 0, 1, "L")
    pdf.ln(5)
    pdf.set_text_color(0, 0, 0)


    pdf.set_y(pdf.get_y() + 5)
    pdf.set_font("Arial", "B", 24)
    pdf.cell(0, 20, "Tax Invoice", 0, 1, "C")
    pdf.ln(5)

    # --- Invoice Details & Bill To Section ---
    pdf.set_font("Arial", "B", 10)
    line_height = 6

    x_left_col = 10
    current_y_after_title = pdf.get_y() 
    pdf.set_xy(x_left_col, current_y_after_title)

    pdf.cell(30, line_height, "Invoice No.", 1, 0, "L")
    pdf.set_font("Arial", "", 10)
    pdf.cell(60, line_height, str(invoice_data.get('Inv Number', 'N/A')), 1, 1, "L")
    pdf.set_x(x_left_col)

    pdf.set_font("Arial", "B", 10)
    pdf.cell(30, line_height, "Date", 1, 0, "L")
    pdf.set_font("Arial", "", 10)
    pdf.cell(60, line_height, str(invoice_data.get('Date', 'N/A')), 1, 1, "L")
    pdf.set_x(x_left_col)

    pdf.set_font("Arial", "B", 10)
    pdf.cell(30, line_height, "Delivery Note", 1, 0, "L")
    pdf.set_font("Arial", "", 10)
    pdf.cell(60, line_height, "N/A", 1, 1, "L")
    pdf.set_x(x_left_col)

    pdf.set_font("Arial", "B", 10)
    pdf.cell(30, line_height, "Buyer's Order No.", 1, 0, "L")
    pdf.set_font("Arial", "", 10)
    pdf.cell(60, line_height, "N/A", 1, 1, "L")
    
    x_right_col = 105
    pdf.set_xy(x_right_col, current_y_after_title) 

    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, line_height, "Bill To:", 0, 1, "L")
    pdf.set_x(x_right_col)
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, line_height, str(invoice_data.get('Client', 'N/A')), 0, 1, "L")
    
    pdf.set_x(x_right_col)
    pdf.cell(0, line_height, "Client Address Line 1 (Mock)", 0, 1, "L")
    pdf.set_x(x_right_col)
    pdf.cell(0, line_height, "Client Address Line 2 (Mock)", 0, 1, "L")
    pdf.set_x(x_right_col)
    pdf.cell(0, line_height, f"Client TRN: ClientTaxID (Mock)", 0, 1, "L")
    
    pdf.set_y(max(pdf.get_y(), current_y_after_title + (4 * line_height) + 5))
    pdf.ln(5)

    # --- Particulars Table ---
    pdf.set_font("Arial", "B", 10)
    
    col_headers = ["SR.NO", "Particulars", "Quantity", "Rate", "Amount", "VAT(BHD)", "Total"]
    col_widths = [15, 65, 20, 25, 25, 25, 30]

    for i, header in enumerate(col_headers):
        pdf.cell(col_widths[i], 10, header, 1, 0, "C")
    pdf.ln()

    pdf.set_font("Arial", "", 10)
    sl_no = 1
    particulars = str(invoice_data.get('Particulars', 'Logistic Services'))
    qty = invoice_data.get('Quantity', 1) 
    rate = invoice_data.get('Rate', 0.0)
    amount = invoice_data.get('Amount', 0.0)
    vat_amount = invoice_data.get('VAT (10%)', 0.0)
    total_amount = invoice_data.get('Total Amount', 0.0)

    try:
        qty = float(qty)
    except (ValueError, TypeError):
        qty = 0.0
    try:
        rate = float(rate)
    except (ValueError, TypeError):
        rate = 0.0
    try:
        amount = float(amount)
    except (ValueError, TypeError):
        amount = 0.0
    try:
        vat_amount = float(vat_amount)
    except (ValueError, TypeError):
        vat_amount = 0.0
    try:
        total_amount = float(total_amount)
    except (ValueError, TypeError):
        total_amount = 0.0

    current_x = pdf.get_x()
    current_y = pdf.get_y()
    
    # Calculate particulars height for multi_cell
    temp_pdf = FPDF()
    temp_pdf.set_font("Arial", "", 10)
    # The trick is to temporarily add a page and use multi_cell to get the height
    # without actually drawing it.
    temp_pdf.add_page()
    # Reset x,y to 0,0 to ensure consistent calculation regardless of current PDF state
    temp_pdf.set_xy(0,0)
    # Call multi_cell with a dummy line height to get the number of lines
    # The actual second argument (h) for multi_cell doesn't matter for this calculation
    # as long as it's large enough to not force a page break within multi_cell itself.
    temp_pdf.multi_cell(col_widths[1] - (temp_pdf.c_margin * 2), 1, particulars, border=0, align="L", ln=0)
    
    # After multi_cell, the Y position will indicate the total height consumed.
    # We need the relative height from where multi_cell started.
    particulars_height_raw = temp_pdf.get_y() # This is cumulative height after the dummy multi_cell

    # The effective height for each line inside multi_cell is pdf.font_size * line_spacing_factor
    # A standard line in FPDF with a font size of 10 is about 4-5mm high.
    # The text_color_cell method also adds some internal padding.
    # Let's assume a line height of 5mm for single-line text and adjust for multiline.
    single_line_height = 5
    num_lines = max(1, round(particulars_height_raw / single_line_height)) # Estimate number of lines
    calculated_cell_height = max(10, num_lines * single_line_height) # Ensure minimum 10mm for table cell height

    pdf.cell(col_widths[0], calculated_cell_height, str(sl_no), 1, 0, "C")
    
    x_after_sr = pdf.get_x()
    pdf.multi_cell(col_widths[1], calculated_cell_height / num_lines, particulars, border=1, align="L", ln=0)
    pdf.set_xy(x_after_sr + col_widths[1], current_y) # Reset X to continue row after multi_cell

    pdf.cell(col_widths[2], calculated_cell_height, f"{qty:,.0f}", 1, 0, "R")
    pdf.cell(col_widths[3], calculated_cell_height, f"{rate:,.2f}", 1, 0, "R")
    pdf.cell(col_widths[4], calculated_cell_height, f"{amount:,.2f}", 1, 0, "R")
    pdf.cell(col_widths[5], calculated_cell_height, f"{vat_amount:,.2f}", 1, 0, "R")
    pdf.cell(col_widths[6], calculated_cell_height, f"{total_amount:,.2f}", 1, 1, "R")

    # Totals
    pdf.set_font("Arial", "B", 10)
    total_label_width = sum(col_widths[0:4])
    pdf.cell(total_label_width, 7, "Total", 1, 0, "L")
    pdf.set_font("Arial", "", 10)

    pdf.cell(col_widths[4], 7, f"{amount:,.2f}", 1, 0, "R")
    pdf.cell(col_widths[5], 7, f"{vat_amount:,.2f}", 1, 0, "R")
    pdf.cell(col_widths[6], 7, f"{total_amount:,.2f}", 1, 1, "R")

    # --- Amount in words ---
    pdf.set_y(pdf.get_y() + 10)
    pdf.set_font("Arial", "B", 10)
    amount_in_words_val = total_amount if isinstance(total_amount, (int, float)) else 0.0
    pdf.cell(0, 7, f"Amount chargeable (in words): {num2words(amount_in_words_val, lang='en_IN').replace(' and zero cents', '').title()} Only", 0, 1, "L")
    pdf.ln(5)

    # --- Remarks ---
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 7, "Remarks:", 0, 1, "L")
    pdf.set_font("Arial", "", 10)
    remarks_text = str(invoice_data.get('Remarks', 'No specific remarks.'))
    # Adjust multi_cell for remarks for single page fit
    pdf.multi_cell(pdf.w - pdf.l_margin - pdf.r_margin, 5, remarks_text, 0, "L")
    pdf.ln(10)

    # --- Signature block (positioned relative to bottom) ---
    # Calculate available vertical space for signature and footer
    remaining_vertical_space = pdf.h - pdf.get_y() - pdf.b_margin 
    
    # Signature block height estimate (2 lines of text + 1 line space + 2 underscores)
    signature_block_height_estimate = 5 + 5 + 15 + 5 # Approx. 30mm

    # Only print if there's enough space
    if remaining_vertical_space > signature_block_height_estimate:
        pdf.set_y(pdf.h - 65) # Adjust this value as needed to fit above the footer
        pdf.set_font("Arial", "B", 10)
        
        pdf.cell(pdf.w/2 - 20, 5, f"For {company_details['name']}", 0, 0, "L") 
        pdf.cell(0, 5, "Authorized Signatory", 0, 1, "R")
        pdf.ln(15)
        
        pdf.cell(pdf.w/2 - 20, 0, "____________________", 0, 0, "L")
        pdf.cell(0, 0, "____________________", 0, 1, "R")
    else:
        st.warning("Not enough space for signature block on invoice.")
    
    # --- Custom Footer Section (positioned at the very bottom) ---
    pdf.set_y(pdf.h - 15)
    pdf.set_font("Arial", "I", 8)
    pdf.set_text_color(50, 50, 50)
    pdf.cell(0, 10, f"CR No. 166155-1 | Tel: 17228646 | Mob: 39884260, 339660641 | Bldg: 471, Flat 11 | Road: 3513, Block: 335 | Manama / Umm Alhassam, Kingdom of Bahrain", 0, 0, "C")
    
    return bytes(pdf.output(dest='S'))


def add_serial_numbers(df):
    """Adds a 'SL No' column starting from 1 to a DataFrame."""
    df_copy = df.copy()
    if 'SL No' in df_copy.columns:
        df_copy = df_copy.drop(columns=['SL No'])
    
    if not df_copy.empty:
        df_copy.insert(0, 'SL No', range(1, len(df_copy) + 1))
    return df_copy


def display_module(module_name, fields_config, collection_name_in_db, crud_enabled=True, company_filter_id=None):
    """
    Displays a module with CRUD operations, search, and report generation.
    Handles data persistence to SQLite and UI updates.
    """
    actual_company_id_for_filter = company_filter_id if company_filter_id else st.session_state['company_id']
    actual_company_name_for_filter = None
    for comp_id, comp_details in st.session_state['USER_DB'].items():
        if comp_id == actual_company_id_for_filter:
            actual_company_name_for_filter = comp_details['company_name']
            break
    if not actual_company_name_for_filter:
        st.error("Error: Could not determine company name for the selected company ID.")
        return

    # Fetch data from SQLite
    current_company_data = get_db_collection(actual_company_id_for_filter, collection_name_in_db)

    with st.expander(f"**{module_name} Management**"):
        if crud_enabled:
            st.subheader("Add New Entry")
            # Initialize or retrieve widget values from session state for persistence across reruns
            session_state_key_for_add_form = f'add_new_entry_values_{collection_name_in_db}_{actual_company_id_for_filter}'
            if session_state_key_for_add_form not in st.session_state:
                st.session_state[session_state_key_for_add_form] = {}
                for field, config in fields_config.items():
                    if config['type'] == 'text':
                        st.session_state[session_state_key_for_add_form][field] = ""
                    elif config['type'] == 'number':
                        st.session_state[session_state_key_for_add_form][field] = 0.0
                    elif config['type'] == 'date':
                        st.session_state[session_state_key_for_add_form][field] = datetime.date.today()
                    elif config['type'] == 'datetime':
                        st.session_state[session_state_key_for_add_form][field] = datetime.datetime.combine(datetime.date.today(), datetime.time(8,0))
                    elif config['type'] == 'select':
                        st.session_state[session_state_key_for_add_form][field] = '--- Select ---'
                    elif config['type'] == 'checkbox':
                        st.session_state[session_state_key_for_add_form][field] = False
                    elif config['type'] == 'file':
                        st.session_state[session_state_key_for_add_form][field] = None

            new_entry_data_input = {}
            for field, config in fields_config.items():
                widget_key = f"{actual_company_id_for_filter}_{module_name}_add_{field}"

                # Special handling for auto-generated IDs - skip input
                if module_name == "Trip" and field == "Trip ID": continue
                if module_name == "Rental" and field == "Rental ID": continue
                if module_name == "Invoicing & Quoting" and (field == "Inv Number" or field == "SI No"): continue
                if module_name == "Payroll" and field == "Payslip ID": continue
                # Also skip Net Salary, it's calculated
                if module_name == "Payroll" and field == "Net Salary": continue

                current_value = st.session_state[session_state_key_for_add_form].get(field)

                if config['type'] == 'text':
                    new_entry_data_input[field] = st.text_input(field, value=current_value, placeholder=f"Enter {field}", key=widget_key)
                elif config['type'] == 'number':
                    # Ensure value is float, default to 0.0 if None
                    new_entry_data_input[field] = st.number_input(field, value=float(current_value if current_value is not None else 0.0), key=widget_key)
                elif config['type'] == 'date':
                    # Ensure value is datetime.date, default to today if None
                    new_entry_data_input[field] = st.date_input(field, value=current_value if current_value is not None else datetime.date.today(), key=widget_key)
                elif config['type'] == 'datetime':
                    # Split datetime into date and time inputs for granular control
                    date_val_add = st.date_input(
                        f"{field} Date", 
                        value=current_value.date() if isinstance(current_value, datetime.datetime) else datetime.date.today(), 
                        key=f"{widget_key}_date"
                    )
                    time_val_add = st.time_input(
                        f"{field} Time", 
                        value=current_value.time() if isinstance(current_value, datetime.datetime) else datetime.time(8,0), 
                        key=f"{widget_key}_time"
                    )
                    
                    if date_val_add and time_val_add:
                        new_entry_data_input[field] = datetime.datetime.combine(date_val_add, time_val_add)
                    else:
                        new_entry_data_input[field] = None
                elif config['type'] == 'select':
                    options_with_placeholder = ['--- Select ---'] + config['options']
                    default_index = options_with_placeholder.index(current_value) if current_value in options_with_placeholder else 0
                    new_entry_data_input[field] = st.selectbox(field, options=options_with_placeholder, index=default_index, key=widget_key)
                elif config['type'] == 'checkbox':
                    new_entry_data_input[field] = st.checkbox(field, value=current_value, key=widget_key)
                elif config['type'] == 'file':
                    new_entry_data_input[field] = st.file_uploader(field, key=widget_key)


            if st.button(f"Add {module_name} Entry", key=f"{actual_company_id_for_filter}_{module_name}_add_button"):
                entry_to_add = {}

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

                # Calculate Net Salary for Payroll module
                if module_name == "Payroll":
                    base_salary = new_entry_data_input.get('Base Salary', 0.0)
                    trip_bonus = new_entry_data_input.get('Trip Bonus', 0.0)
                    rental_commission = new_entry_data_input.get('Rental Commission', 0.0)
                    deductions = new_entry_data_input.get('Deductions', 0.0)
                    overtime = new_entry_data_input.get('Overtime', 0.0)
                    entry_to_add['Net Salary'] = base_salary + trip_bonus + rental_commission + overtime - deductions
                
                for field, value in new_entry_data_input.items():
                    if field.endswith(" Date") or field.endswith(" Time"): # Skip partial datetime fields
                        continue
                    # Only add if it's not the calculated Net Salary (which is handled above)
                    if not (module_name == "Payroll" and field == "Net Salary"):
                        entry_to_add[field] = value

                # Handle file uploads (store just the name/path)
                for field, config in fields_config.items():
                    if config['type'] == 'file' and new_entry_data_input.get(field):
                        entry_to_add[field] = new_entry_data_input[field].name
                
                add_db_document(actual_company_id_for_filter, collection_name_in_db, entry_to_add)
                st.success(f"{module_name} entry added successfully for {actual_company_name_for_filter}!")
                # Reset input fields in session state after successful add
                st.session_state[session_state_key_for_add_form] = {} # Clear all for the next rerun
                st.rerun() # Force rerun to clear form fields


        st.subheader(f"Existing {module_name} Entries")

        # Search and Filter
        search_term = st.text_input(f"Search {module_name} for {actual_company_name_for_filter}", key=f"{actual_company_id_for_filter}_{module_name}_search", placeholder="Type to search...")
        
        # Keep a reference to the original filtered_df *with* doc_id for mapping
        filtered_df_for_crud = current_company_data
        if search_term:
            filtered_df_for_crud = filtered_df_for_crud[
                filtered_df_for_crud.astype(str).apply(lambda row: row.str.contains(search_term, case=False, na=False).any(), axis=1)
            ]

        # Display data with SL No and allow editing. Crucially, pass the doc_id to the data editor.
        display_df_for_editor = add_serial_numbers(filtered_df_for_crud) # Now includes doc_id
        
        column_config = {
            "doc_id": st.column_config.Column(
                "Document ID",
                help="Unique ID for the entry (internal)",
                disabled=True, # Make it non-editable
                width="small"
            ),
            "company_id": st.column_config.Column(
                "Company ID",
                help="Internal Company ID",
                disabled=True,
                width="small"
            ),
            "Company": st.column_config.Column(
                "Company",
                help="Company Name",
                disabled=True,
                width="small"
            ),
             "SL No": st.column_config.Column(
                "SL No",
                help="Serial Number",
                disabled=True,
                width="extra_small"
            )
        }
        
        # Merge the auto-generated IDs into fields_config for column_config setup
        temp_fields_config = fields_config.copy()
        if module_name == "Trip": temp_fields_config['Trip ID'] = {'type': 'text'}
        if module_name == "Rental": temp_fields_config['Rental ID'] = {'type': 'text'}
        if module_name == "Invoicing & Quoting": 
            temp_fields_config['Inv Number'] = {'type': 'text'}
            temp_fields_config['SI No'] = {'type': 'text'}
        if module_name == "Payroll": temp_fields_config['Payslip ID'] = {'type': 'text'}
        if module_name == "Payroll": temp_fields_config['Net Salary'] = {'type': 'number'}

        for field, config in temp_fields_config.items():
            if config['type'] == 'number':
                column_config[field] = st.column_config.NumberColumn(
                    field,
                    format="%0.2f", # Display as float with 2 decimal places
                    help=f"Enter {field}",
                )
            elif config['type'] == 'date':
                 column_config[field] = st.column_config.DateColumn(
                    field,
                    format="YYYY-MM-DD",
                    help=f"Enter {field} (YYYY-MM-DD)",
                )
            elif config['type'] == 'datetime':
                 column_config[field] = st.column_config.DatetimeColumn(
                    field,
                    format="YYYY-MM-DD HH:mm",
                    help=f"Enter {field} (YYYY-MM-DD HH:MM)",
                )
            elif config['type'] == 'select':
                column_config[field] = st.column_config.SelectboxColumn(
                    field,
                    options=config['options'],
                    help=f"Select {field}",
                )
            elif config['type'] == 'checkbox':
                column_config[field] = st.column_config.CheckboxColumn(
                    field,
                    help=f"Check if {field}",
                )
            elif field in ['Trip ID', 'Rental ID', 'Inv Number', 'SI No', 'Payslip ID']:
                column_config[field] = st.column_config.TextColumn(
                    field,
                    disabled=True, # Make auto-generated IDs non-editable
                    help=f"Auto-generated {field}",
                )
            elif field == 'Net Salary' and module_name == 'Payroll':
                 column_config[field] = st.column_config.NumberColumn(
                    "Net Salary (Calculated)",
                    format="%0.2f",
                    disabled=True, # Make calculated field non-editable
                    help="Automatically calculated net salary",
                )


        if crud_enabled:
            # Pass display_df_for_editor directly to data_editor
            st.data_editor( # No need to capture the return value if using session state directly for changes
                display_df_for_editor,
                key=f"{actual_company_id_for_filter}_{module_name}_data_editor",
                hide_index=True,
                num_rows="dynamic",
                use_container_width=True,
                column_config=column_config # Apply column configurations
            )

            # Access changes directly from session state (Streamlit's internal mechanism)
            # This is available after the data_editor widget renders.
            data_editor_state_key = f"{actual_company_id_for_filter}_{module_name}_data_editor"
            
            changes_made = False
            
            if data_editor_state_key in st.session_state and st.session_state[data_editor_state_key]:
                edited_rows_dict = st.session_state[data_editor_state_key].get('edited_rows', {})
                added_rows_list = st.session_state[data_editor_state_key].get('added_rows', [])
                deleted_rows_indices = st.session_state[data_editor_state_key].get('deleted_rows', [])

                # Process Deletions
                deleted_count = 0
                for idx_to_delete in deleted_rows_indices:
                    # Get the original doc_id from the filtered_df_for_crud using the index
                    # .iloc is safer for integer-location based indexing after filtering
                    if idx_to_delete < len(filtered_df_for_crud):
                        doc_id_to_delete = filtered_df_for_crud.iloc[idx_to_delete]['doc_id']
                        if delete_db_document(actual_company_id_for_filter, collection_name_in_db, doc_id_to_delete):
                            deleted_count += 1
                            changes_made = True
                if deleted_count > 0:
                    st.success(f"{deleted_count} {module_name} entries deleted!")


                # Process Additions
                added_count = 0
                for new_row_data_from_editor in added_rows_list:
                    new_entry_data = {}
                    for field, value in new_row_data_from_editor.items():
                         # Convert types for database insertion
                        if fields_config.get(field, {}).get('type') == 'date' and isinstance(value, datetime.date):
                            new_entry_data[field] = value.isoformat()
                        elif fields_config.get(field, {}).get('type') == 'datetime' and isinstance(value, datetime.datetime):
                            new_entry_data[field] = value.isoformat(sep=' ')
                        elif fields_config.get(field, {}).get('type') == 'checkbox':
                            new_entry_data[field] = 1 if value else 0
                        elif pd.isna(value):
                            new_entry_data[field] = None
                        else:
                            new_entry_data[field] = value

                    # Handle auto-generated IDs for new rows
                    if module_name == "Trip":
                        new_entry_data['Trip ID'] = f"TRP-{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')}"
                    elif module_name == "Rental":
                        new_entry_data['Rental ID'] = f"RNT-{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')}"
                    elif module_name == "Invoicing & Quoting":
                        new_entry_data['Inv Number'] = f"INV-{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')}"
                        new_entry_data['SI No'] = f"SI-{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')}"
                    elif module_name == "Payroll":
                        new_entry_data['Payslip ID'] = f"PS-{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')}"

                    # Calculate Net Salary for Payroll module
                    if module_name == "Payroll":
                        base_salary = new_entry_data.get('Base Salary', 0.0)
                        trip_bonus = new_entry_data.get('Trip Bonus', 0.0)
                        rental_commission = new_entry_data.get('Rental Commission', 0.0)
                        deductions = new_entry_data.get('Deductions', 0.0)
                        overtime = new_entry_data.get('Overtime', 0.0)
                        new_entry_data['Net Salary'] = base_salary + trip_bonus + rental_commission + overtime - deductions

                    if 'Company' not in new_entry_data:
                        new_entry_data['Company'] = actual_company_name_for_filter # Ensure company is set for new rows

                    if add_db_document(actual_company_id_for_filter, collection_name_in_db, new_entry_data):
                        added_count += 1
                        changes_made = True
                if added_count > 0:
                    st.success(f"{added_count} new {module_name} entries added!")

                # Process Edits
                updated_count = 0
                for idx_to_edit, changes_dict in edited_rows_dict.items():
                    if idx_to_edit < len(filtered_df_for_crud): # Ensure index is valid
                        doc_id_to_update = filtered_df_for_crud.iloc[idx_to_edit]['doc_id']
                        
                        # Prepare data for update: convert types for database insertion
                        data_to_update = {}
                        for field, value in changes_dict.items():
                            if fields_config.get(field, {}).get('type') == 'date' and isinstance(value, datetime.date):
                                data_to_update[field] = value.isoformat()
                            elif fields_config.get(field, {}).get('type') == 'datetime' and isinstance(value, datetime.datetime):
                                data_to_update[field] = value.isoformat(sep=' ')
                            elif fields_config.get(field, {}).get('type') == 'checkbox':
                                data_to_update[field] = 1 if value else 0
                            elif pd.isna(value):
                                data_to_update[field] = None
                            else:
                                data_to_update[field] = value
                        
                        # Recalculate Net Salary for Payroll module if relevant fields are edited
                        if module_name == "Payroll":
                            # Get current row's data to ensure all needed fields are present for calculation
                            current_row_data_for_calc = filtered_df_for_crud.iloc[idx_to_edit].to_dict()
                            
                            # Update with edited values
                            current_row_data_for_calc.update(data_to_update)

                            base_salary = current_row_data_for_calc.get('Base Salary', 0.0)
                            trip_bonus = current_row_data_for_calc.get('Trip Bonus', 0.0)
                            rental_commission = current_row_data_for_calc.get('Rental Commission', 0.0)
                            deductions = current_row_data_for_calc.get('Deductions', 0.0)
                            overtime = current_row_data_for_calc.get('Overtime', 0.0)
                            data_to_update['Net Salary'] = base_salary + trip_bonus + rental_commission + overtime - deductions

                        if update_db_document(actual_company_id_for_filter, collection_name_in_db, doc_id_to_update, data_to_update):
                            updated_count += 1
                            changes_made = True
                if updated_count > 0:
                    st.success(f"{updated_count} {module_name} entries updated!")

                # If any changes were made, clear the data_editor's internal state and rerun
                if changes_made:
                    st.session_state[data_editor_state_key]['edited_rows'] = {}
                    st.session_state[data_editor_state_key]['added_rows'] = []
                    st.session_state[data_editor_state_key]['deleted_rows'] = []
                    st.rerun()

        else: # If CRUD is not enabled, just display the dataframe (after adding SL No)
            st.dataframe(add_serial_numbers(filtered_df_for_crud.drop(columns=['doc_id', 'company_id'], errors='ignore')), use_container_width=True, hide_index=True)


        # --- Invoice PDF Generation for Invoicing & Quoting module ---
        if module_name == "Invoicing & Quoting":
            st.subheader(f"Generate Specific Tax Invoice for {actual_company_name_for_filter}")
            
            logo_x_pos = 10
            logo_y_pos = 10
            logo_width_fixed = 50
            logo_height_fixed = 30
            
            logo_url_input = "https://i.ibb.co/RGTCjMb4/EAST-CONCORD-W-L-L-page-0001-1.jpg"

            invoice_options = filtered_df_for_crud['Inv Number'].dropna().tolist() # Ensure no NaNs in options
            if invoice_options:
                st.info("Invoice PDF generation is removed as requested.")
                # selected_invoice_number = st.selectbox(
                #     "Select an Invoice to Generate PDF:",
                #     ['--- Select Invoice ---'] + invoice_options,
                #     key=f"{actual_company_id_for_filter}_select_invoice_for_pdf"
                # )

                # if selected_invoice_number and selected_invoice_number != '--- Select Invoice ---':
                #     selected_invoice_data = filtered_df_for_crud[filtered_df_for_crud['Inv Number'] == selected_invoice_number].iloc[0].to_dict()
                #     company_profile_for_invoice = COMPANY_PROFILES.get(actual_company_name_for_filter)

                #     if company_profile_for_invoice:
                #         if st.button(f"Download Tax Invoice PDF for {selected_invoice_number}", key=f"{actual_company_id_for_filter}_{selected_invoice_number}_invoice_pdf_download"):
                #             tax_invoice_pdf_data = generate_single_tax_invoice_pdf(
                #                 selected_invoice_data,
                #                 company_profile_for_invoice,
                #                 logo_url=logo_url_input,
                #                 logo_x=logo_x_pos,
                #                 logo_y=logo_y_pos,
                #                 logo_width=logo_width_fixed,
                #                 logo_height=logo_height_fixed
                #             )
                #             st.download_button(
                #                 label=f"Download Invoice {selected_invoice_number} PDF",
                #                 data=tax_invoice_pdf_data,
                #                 file_name=f"Tax_Invoice_{selected_invoice_number}.pdf",
                #                 mime="application/pdf",
                #                 key=f"{actual_company_id_for_filter}_{selected_invoice_number}_pdf_download_final"
                #             )
                #             st.success(f"Tax Invoice PDF for {selected_invoice_number} generated successfully!")
                #     else:
                #         st.error(f"Company profile for '{actual_company_name_for_filter}' not found for invoice generation. Please ensure company profile is defined in COMPANY_PROFILES.")
                # else:
                #     st.info("Please select an invoice to generate its PDF.")
            else:
                st.info("No invoices available for PDF generation. Please add invoice entries first.")
        # --- End of New Invoice PDF Generation ---

        st.subheader(f"Download {module_name} Reports for {actual_company_name_for_filter}")
        # col1, col2 = st.columns(2) # Removed col2 as PDF is removed
        
        # with col1:
        excel_data = generate_excel_report(current_company_data.drop(columns=['doc_id', 'company_id'], errors='ignore'), f"{module_name}_Report_{actual_company_name_for_filter}")
        st.download_button(
            label=f"Download {module_name} Excel ({actual_company_name_for_filter})",
            data=excel_data,
            file_name=f"{module_name}_Report_{actual_company_name_for_filter}_{datetime.date.today()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key=f"{actual_company_id_for_filter}_{module_name}_excel_download"
        )
        # with col2: # Removed PDF download button
        #     pdf_data = generate_pdf_report(current_company_data.drop(columns=['doc_id', 'company_id'], errors='ignore'), f"{module_name} Report for {actual_company_name_for_filter}")
        #     st.download_button(
        #         label=f"Download {module_name} PDF ({actual_company_name_for_filter})",
        #         data=pdf_data,
        #         file_name=f"Report_{module_name}_Report_{actual_company_name_for_filter}_{datetime.date.today()}.pdf",
        #         mime="application/pdf",
        #         key=f"{actual_company_id_for_filter}_{module_name}_pdf_download"
        #     )

        st.markdown("---")
        st.info(f"Note: Data for {module_name} is persisted in SQLite database. Data might be lost on ephemeral deployments.")


# --- Authentication and Main App Flow ---

def login_page():
    st.title("Logistic Management System")
    st.image("https://placehold.co/600x150/EEEEEE/313131?text=Your+Company+Logo", use_column_width=True) # Corrected keyword argument here
    st.markdown("---")
    st.subheader("Login to Your Company Account")

    # Fetch users from SQLite
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT company_id, company_name, username, password_hash, role FROM users")
        db_users_raw = cursor.fetchall()
    except Exception as e:
        st.error(f"Error fetching users from database: {e}. Please try refreshing the app. This might indicate database initialization issues.")
        db_users_raw = []
    finally:
        conn.close()

    # Reconstruct a USER_DB-like structure from SQLite for login purposes
    current_user_db_from_sql = {}
    for row in db_users_raw:
        company_id = row['company_id']
        company_name = row['company_name']
        username = row['username']
        password_hash = row['password_hash']
        role = row['role']

        if company_id not in current_user_db_from_sql:
            current_user_db_from_sql[company_id] = {
                "company_name": company_name,
                # Get PIN from initial structure (or retrieve from DB if stored there)
                "company_pin": next((INITIAL_USER_DB_STRUCTURE.get(cid, {}).get('company_pin') for cid, cdata in INITIAL_USER_DB_STRUCTURE.items() if cdata['company_name'] == company_name), ''),
                "users": {}
            }
        current_user_db_from_sql[company_id]['users'][username] = {
            "password_hash": password_hash,
            "role": role
        }
    
    st.session_state['USER_DB'] = current_user_db_from_sql # Update session state with current DB users

    with st.form(key="main_login_form"):
        # Ensure company_names are from the dynamically loaded users, not just initial structure
        company_names = sorted(list(set([details['company_name'] for details in st.session_state['USER_DB'].values()])))
        
        # Add a default empty option for the selectbox
        selected_company_name = st.selectbox("Select Your Company", options=['--- Select Company ---'] + company_names, key="login_company_select")

        selected_company_id = None
        if selected_company_name != '--- Select Company ---':
            for comp_id, comp_details in st.session_state['USER_DB'].items():
                if comp_details['company_name'] == selected_company_name:
                    selected_company_id = comp_id
                    break

        username = st.text_input("Username", key="login_username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", key="login_password", placeholder="Enter your password")
        
        login_button = st.form_submit_button("Login")

        if login_button:
            if selected_company_id and username and password:
                if selected_company_id in st.session_state['USER_DB']:
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
                    st.error("Company not found in database. This should not happen if initialization was successful.")
            else:
                st.error("Please select a company and enter username/password.")


def main_app():
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

        all_companies_operational_data = {}
        # Filter out the 'management_company' (admin) from operational data
        operational_company_ids = [comp_id for comp_id, details in USER_DB_CURRENT.items() if details['company_pin'] != 'ADMIN']

        for module_name_key in MODULE_FIELDS_MAP.keys():
            combined_module_df = pd.DataFrame()
            for comp_id in operational_company_ids:
                df_for_comp = get_db_collection(comp_id, module_name_key)
                if not df_for_comp.empty:
                    combined_module_df = pd.concat([combined_module_df, df_for_comp], ignore_index=True)
            all_companies_operational_data[module_name_key] = combined_module_df


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
                    total_rentals_all += len(all_companies_operational_data['rentals'][all_companies_operational_data['rentals']['Company'] == comp_name])

                if 'payslips' in all_companies_operational_data and 'Company' in all_companies_operational_data['payslips'].columns:
                    total_payslips_net_salary_all += all_companies_operational_data['payslips'][all_companies_operational_data['payslips']['Company'] == comp_name]['Net Salary'].sum() if 'Net Salary' in all_companies_operational_data['payslips'].columns else 0.0
                
                if 'leaves' in all_companies_operational_data and 'Company' in all_companies_operational_data['leaves'].columns:
                    total_leaves_all += len(all_companies_operational_data['leaves'][all_companies_operational_data['leaves']['Company'] == comp_name])

                if 'vat_transactions' in all_companies_operational_data and 'Company' in all_companies_operational_data['vat_transactions'].columns:
                    total_vat_amount_all += all_companies_operational_data['vat_transactions'][all_companies_operational_data['vat_transactions']['Company'] == comp_name]['VAT Amount'].sum() if 'VAT Amount' in all_companies_operational_data['vat_transactions'].columns else 0.0

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
            st.warning("Note: All data is persisted in a SQLite database file.")

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
            for module_name_key in MODULE_FIELDS_MAP.keys():
                df = all_companies_operational_data.get(module_name_key, pd.DataFrame())
                if not df.empty:
                    # Filter out admin company entries if 'Company' column exists and is not empty
                    operational_df = df[df['Company'] != 'Global Management'].copy()
                    if not operational_df.empty: # Only count if there's actual data after filtering
                        module_counts[module_name_key.replace('_', ' ').title()] = len(operational_df)
                else:
                    module_counts[module_name_key.replace('_', ' ').title()] = 0 # Ensure module is listed even if empty


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
            st.warning("Note: All data is persisted in a SQLite database file.")


        elif menu_selection == "Cross-Company Reports":
            st.subheader("Generate Cross-Company Reports and Consolidated Data")
            st.info("This section provides reports that combine data from ALL operational companies in the system.")
            
            st.markdown("#### Consolidated Operational Data Overview (All Companies)")
            all_operational_data_concat = pd.DataFrame()
            for module_name_key in MODULE_FIELDS_MAP.keys():
                df = all_companies_operational_data.get(module_name_key, pd.DataFrame())
                if not df.empty and 'Company' in df.columns:
                    filtered_df_for_concat = df[df['Company'] != 'Global Management'].copy()
                    if not filtered_df_for_concat.empty:
                        filtered_df_for_concat['Module'] = module_name_key.replace('_', ' ').title()
                        all_operational_data_concat = pd.concat([all_operational_data_concat, filtered_df_for_concat], ignore_index=True)

            if not all_operational_data_concat.empty:
                st.dataframe(add_serial_numbers(all_operational_data_concat.drop(columns=['doc_id', 'company_id'], errors='ignore')), use_container_width=True, hide_index=True)
                # col_ex_overall, col_pdf_overall = st.columns(2) # Removed col2 for PDF
                # with col_ex_overall:
                st.download_button(
                    label="Download All Companies Consolidated Excel",
                    data=generate_excel_report(all_operational_data_concat.drop(columns=['doc_id', 'company_id'], errors='ignore'), "All_Companies_Consolidated_Report"),
                    file_name=f"All_Companies_Consolidated_Report_{datetime.date.today()}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="all_companies_consolidated_excel_download"
                )
                # with col_pdf_overall: # Removed PDF download button
                #     st.download_button(
                #         label="Download All Companies Consolidated PDF",
                #         data=generate_pdf_report(all_operational_data_concat.drop(columns=['doc_id', 'company_id'], errors='ignore'), "All Companies Consolidated Report"),
                #         file_name=f"All_Companies_Consolidated_Report_{datetime.date.today()}.pdf",
                #         mime="application/pdf",
                #         key="all_companies_consolidated_pdf_download"
                #     )
            else:
                st.info("No operational data available across all companies yet. Please add data using individual company logins.")

            st.markdown("---")
            st.subheader("Specific Cross-Company Reports")
            all_trips_df = all_companies_operational_data.get('trips', pd.DataFrame())
            if not all_trips_df.empty:
                st.markdown("#### All Trips Overview (All Companies)")
                st.dataframe(add_serial_numbers(all_trips_df.drop(columns=['doc_id', 'company_id'], errors='ignore')), use_container_width=True, hide_index=True)
                # col_ex, col_pdf = st.columns(2) # Removed col2 for PDF
                # with col_ex:
                st.download_button(
                    label="Download All Trips Excel",
                    data=generate_excel_report(all_trips_df.drop(columns=['doc_id', 'company_id'], errors='ignore'), "All_Trips_Report"),
                    file_name=f"All_Trips_Report_{datetime.date.today()}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="all_trips_excel_download"
                )
                # with col_pdf: # Removed PDF download button
                #     st.download_button(
                #         label="Download All Trips PDF",
                #         data=generate_pdf_report(all_trips_df.drop(columns=['doc_id', 'company_id'], errors='ignore'), "All Trips Report"),
                #         file_name=f"All_Trips_Report_{datetime.date.today()}.pdf",
                #         mime="application/pdf",
                #         key="all_trips_pdf_download"
                #     )
            else:
                st.info("No trip data available for cross-company reports yet.")
            
            st.markdown("---")
            st.markdown("#### Custom Management Report (PDF with Company Details)")
            st.info("Management Report PDF generation is removed as requested.")
            # st.write("This PDF report provides an overview of all companies, including their individual vehicle counts, employees, and financial summaries.")
            # if st.button("Download Management Report (PDF)", key="download_management_pdf_final"):
            #     management_pdf_data = generate_management_pdf_report(all_companies_operational_data, USER_DB_CURRENT)
            #     st.download_button(
            #         label="Download Management Report PDF",
            #         data=management_pdf_data,
            #         file_name=f"Management_Report_{datetime.date.today()}.pdf",
            #         mime="application/pdf",
            #         key="management_pdf_download_final"
            #     )


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

                display_module("Trip", TRIP_MANAGEMENT_FIELDS, 'trips', crud_enabled=True, company_filter_id=selected_company_id_for_modules)

                display_module("Rental", RENTAL_MANAGEMENT_FIELDS, 'rentals', crud_enabled=True, company_filter_id=selected_company_id_for_modules)
                
                display_module("Fleet", FLEET_MANAGEMENT_FIELDS, 'vehicles', crud_enabled=True, company_filter_id=selected_company_id_for_modules)

                display_module("Invoicing & Quoting", INVOICING_QUOTING_FIELDS, 'invoices', crud_enabled=True, company_filter_id=selected_company_id_for_modules)

                display_module("CRM / Customer Management", CRM_MANAGEMENT_FIELDS, 'clients', crud_enabled=True, company_filter_id=selected_company_id_for_modules)

                display_module("Employee", EMPLOYEE_MANAGEMENT_FIELDS, 'employees', crud_enabled=True, company_filter_id=selected_company_id_for_modules)

                with st.expander(f"**Payroll Management**"):
                    st.header("Payroll Management")
                    current_company_payslips_df = get_db_collection(selected_company_id_for_modules, 'payslips')

                    st.subheader(f"Generate Payslip for {selected_company_name_for_modules}")

                    # Initialize or retrieve widget values for payroll
                    session_state_key_for_payslip_add = f'add_new_payslip_values_{selected_company_id_for_modules}'
                    if session_state_key_for_payslip_add not in st.session_state:
                        st.session_state[session_state_key_for_payslip_add] = {
                            'Employee Name': '',
                            'Month': str(datetime.date.today().month),
                            'Year': str(datetime.date.today().year),
                            'Base Salary': 0.0,
                            'Trip Bonus': 0.0,
                            'Rental Commission': 0.0,
                            'Deductions': 0.0,
                            'Overtime': 0.0,
                            'Net Salary': 0.0,
                            'Payment Status': 'Unpaid'
                        }
                    
                    current_payslip_values = st.session_state[session_state_key_for_payslip_add]

                    payslip_emp_name = st.text_input("Employee Name (for Payslip)", value=current_payslip_values['Employee Name'], placeholder="Enter employee name", key=f"admin_{selected_company_id_for_modules}_payroll_emp_name")
                    payslip_month = st.selectbox("Month", options=[str(i) for i in range(1, 13)], index=[str(i) for i in range(1, 13)].index(current_payslip_values['Month']), key=f"admin_{selected_company_id_for_modules}_payroll_month")
                    payslip_year = st.selectbox("Year", options=[str(i) for i in range(2020, datetime.datetime.now().year + 2)], index=[str(i) for i in range(2020, datetime.datetime.now().year + 2)].index(current_payslip_values['Year']), key=f"admin_{selected_company_id_for_modules}_payroll_year")
                    base_salary = st.number_input("Base Salary", value=float(current_payslip_values['Base Salary']), key=f"admin_{selected_company_id_for_modules}_payroll_base_salary")
                    trip_bonus = st.number_input("Trip Bonus", value=float(current_payslip_values['Trip Bonus']), key=f"admin_{selected_company_id_for_modules}_payroll_trip_bonus")
                    rental_commission = st.number_input("Rental Commission", value=float(current_payslip_values['Rental Commission']), key=f"admin_{selected_company_id_for_modules}_payroll_rental_commission")
                    deductions = st.number_input("Deductions", value=float(current_payslip_values['Deductions']), key=f"admin_{selected_company_id_for_modules}_payroll_deductions")
                    overtime = st.number_input("Overtime", value=float(current_payslip_values['Overtime']), key=f"admin_{selected_company_id_for_modules}_payroll_overtime")

                    net_salary = base_salary + trip_bonus + rental_commission + overtime - deductions
                    st.write(f"Calculated Net Salary: **INR {net_salary:.2f}**")

                    if st.button(f"Generate Payslip for {selected_company_name_for_modules}", key=f"admin_{selected_company_id_for_modules}_generate_payslip_btn"):
                        existing_payslip_check = current_company_payslips_df[
                            (current_company_payslips_df['Employee Name'] == payslip_emp_name) &
                            (current_company_payslips_df['Month'] == payslip_month) &
                            (current_company_payslips_df['Year'] == payslip_year)
                        ]
                        
                        payslip_data = {
                            'Company': selected_company_name_for_modules,
                            'Payslip ID': f"PS_{payslip_emp_name[:3].upper()}_{payslip_month}{payslip_year}_{datetime.datetime.now().strftime('%H%M%S%f')}",
                            'Employee Name': payslip_emp_name, 'Month': payslip_month, 'Year': payslip_year,
                            'Base Salary': base_salary, 'Trip Bonus': trip_bonus,
                            'Rental Commission': rental_commission, 'Deductions': deductions,
                            'Overtime': overtime, 'Net Salary': net_salary, 'Payment Status': 'Unpaid'
                        }

                        if not existing_payslip_check.empty:
                            st.warning(f"A payslip for {payslip_emp_name} for {payslip_month}/{payslip_year} already exists in {selected_company_name_for_modules}. Do you want to overwrite it?")
                            col_confirm_yes, col_confirm_no = st.columns(2)
                            with col_confirm_yes:
                                if st.button("Confirm Overwrite", key=f"admin_{selected_company_id_for_modules}_confirm_overwrite"):
                                    doc_id_to_overwrite = existing_payslip_check['doc_id'].iloc[0]
                                    if update_db_document(selected_company_id_for_modules, 'payslips', doc_id_to_overwrite, payslip_data):
                                        st.success("Payslip overwritten and regenerated successfully!")
                                        st.session_state[session_state_key_for_payslip_add] = {} # Clear for rerun
                                        st.rerun()
                            with col_confirm_no:
                                if st.button("Cancel", key=f"admin_{selected_company_id_for_modules}_cancel_overwrite"):
                                    st.info("Payslip generation cancelled.")
                        else:
                            if add_db_document(selected_company_id_for_modules, 'payslips', payslip_data):
                                st.success("Payslip generated successfully!")
                                st.session_state[session_state_key_for_payslip_add] = {} # Clear for rerun
                                st.rerun()

                    st.subheader(f"Payroll History for {selected_company_name_for_modules}")
                    
                    # Prepare display_df for data_editor, ensuring doc_id is present
                    payslip_display_df_for_editor = add_serial_numbers(current_company_payslips_df)

                    payslip_column_config = {
                        "doc_id": st.column_config.Column("Document ID", disabled=True, width="small"),
                        "company_id": st.column_config.Column("Company ID", disabled=True, width="small"),
                        "Company": st.column_config.Column("Company Name", disabled=True, width="small"),
                        "SL No": st.column_config.Column("SL No", disabled=True, width="extra_small"),
                        "Payslip ID": st.column_config.TextColumn("Payslip ID", disabled=True),
                        "Net Salary": st.column_config.NumberColumn("Net Salary", format="%0.2f", disabled=True),
                    }
                    for field, config in PAYROLL_FIELDS.items():
                        if config['type'] == 'number':
                            if field not in payslip_column_config: # Don't overwrite Net Salary
                                payslip_column_config[field] = st.column_config.NumberColumn(field, format="%0.2f")
                        elif config['type'] == 'select':
                            payslip_column_config[field] = st.column_config.SelectboxColumn(field, options=config['options'])
                        elif config['type'] == 'text':
                            payslip_column_config[field] = st.column_config.TextColumn(field)


                    st.data_editor(
                        payslip_display_df_for_editor,
                        key=f"admin_{selected_company_id_for_modules}_payslip_history_editor",
                        hide_index=True,
                        num_rows="dynamic",
                        use_container_width=True,
                        column_config=payslip_column_config
                    )
                    
                    payslip_editor_state_key = f"admin_{selected_company_id_for_modules}_payslip_history_editor"
                    payslip_changes_made = False

                    if payslip_editor_state_key in st.session_state and st.session_state[payslip_editor_state_key]:
                        edited_payslip_rows_dict = st.session_state[payslip_editor_state_key].get('edited_rows', {})
                        added_payslip_rows_list = st.session_state[payslip_editor_state_key].get('added_rows', [])
                        deleted_payslip_rows_indices = st.session_state[payslip_editor_state_key].get('deleted_rows', [])

                        deleted_payslip_count = 0
                        for idx_to_delete in deleted_payslip_rows_indices:
                            if idx_to_delete < len(current_company_payslips_df):
                                doc_id_to_delete = current_company_payslips_df.iloc[idx_to_delete]['doc_id']
                                if delete_db_document(selected_company_id_for_modules, 'payslips', doc_id_to_delete):
                                    deleted_payslip_count += 1
                                    payslip_changes_made = True
                        if deleted_payslip_count > 0:
                            st.success(f"{deleted_payslip_count} Payslip entries deleted!")

                        added_payslip_count = 0
                        for new_row_data in added_payslip_rows_list:
                            new_entry_data = {}
                            for field, value in new_row_data.items():
                                if PAYROLL_FIELDS.get(field, {}).get('type') == 'select' and value == '--- Select ---':
                                    new_entry_data[field] = None
                                elif PAYROLL_FIELDS.get(field, {}).get('type') == 'checkbox':
                                    new_entry_data[field] = 1 if value else 0
                                elif pd.isna(value):
                                    new_entry_data[field] = None
                                else:
                                    new_entry_data[field] = value

                            # Auto-generate Payslip ID for new rows
                            emp_name_short = new_entry_data.get('Employee Name', 'UNK')[:3].upper()
                            month_val = new_entry_data.get('Month', '00')
                            year_val = new_entry_data.get('Year', '0000')
                            new_entry_data['Payslip ID'] = f"PS_{emp_name_short}_{month_val}{year_val}_{datetime.datetime.now().strftime('%H%M%S%f')}"
                            new_entry_data['Company'] = selected_company_name_for_modules # Ensure company is set

                            # Calculate Net Salary for new rows
                            base_salary = new_entry_data.get('Base Salary', 0.0)
                            trip_bonus = new_entry_data.get('Trip Bonus', 0.0)
                            rental_commission = new_entry_data.get('Rental Commission', 0.0)
                            deductions = new_entry_data.get('Deductions', 0.0)
                            overtime = new_entry_data.get('Overtime', 0.0)
                            new_entry_data['Net Salary'] = base_salary + trip_bonus + rental_commission + overtime - deductions

                            if add_db_document(selected_company_id_for_modules, 'payslips', new_entry_data):
                                added_payslip_count += 1
                                payslip_changes_made = True
                        if added_payslip_count > 0:
                            st.success(f"{added_payslip_count} new Payslip entries added successfully!")
                        
                        updated_payslip_count = 0
                        for idx_to_edit, changes_dict in edited_payslip_rows_dict.items():
                            if idx_to_edit < len(current_company_payslips_df):
                                doc_id_to_update = current_company_payslips_df.iloc[idx_to_edit]['doc_id']
                                
                                data_to_update = {}
                                for field, value in changes_dict.items():
                                    if PAYROLL_FIELDS.get(field, {}).get('type') == 'select' and value == '--- Select ---':
                                        data_to_update[field] = None
                                    elif PAYROLL_FIELDS.get(field, {}).get('type') == 'checkbox':
                                        data_to_update[field] = 1 if value else 0
                                    elif pd.isna(value):
                                        data_to_update[field] = None
                                    else:
                                        data_to_update[field] = value

                                # Recalculate Net Salary
                                current_row_data_for_calc = current_company_payslips_df.iloc[idx_to_edit].to_dict()
                                current_row_data_for_calc.update(data_to_update) # Apply current changes
                                
                                base_salary = current_row_data_for_calc.get('Base Salary', 0.0)
                                trip_bonus = current_row_data_for_calc.get('Trip Bonus', 0.0)
                                rental_commission = current_row_data_for_calc.get('Rental Commission', 0.0)
                                deductions = current_row_data_for_calc.get('Deductions', 0.0)
                                overtime = current_row_data_for_calc.get('Overtime', 0.0)
                                data_to_update['Net Salary'] = base_salary + trip_bonus + rental_commission + overtime - deductions


                                if update_db_document(selected_company_id_for_modules, 'payslips', doc_id_to_update, data_to_update):
                                    updated_payslip_count += 1
                                    payslip_changes_made = True
                        if updated_payslip_count > 0:
                            st.success(f"{updated_payslip_count} Payslip entries updated successfully!")

                        # If any changes were made, clear the data_editor's internal state and rerun
                        if payslip_changes_made:
                            st.session_state[payslip_editor_state_key]['edited_rows'] = {}
                            st.session_state[payslip_editor_state_key]['added_rows'] = []
                            st.session_state[payslip_editor_state_key]['deleted_rows'] = []
                            st.rerun()

                    st.subheader(f"Download Payslip Reports for {selected_company_name_for_modules}")
                    # col1, col2 = st.columns(2) # Removed col2 for PDF
                    # with col1:
                    excel_data = generate_excel_report(current_company_payslips_df.drop(columns=['doc_id', 'company_id'], errors='ignore'), f"Payroll_Report_{selected_company_name_for_modules}")
                    st.download_button(
                        label=f"Download Payroll Excel ({selected_company_name_for_modules})",
                        data=excel_data,
                        file_name=f"Payroll_Report_{selected_company_name_for_modules}_{datetime.date.today()}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key=f"admin_{selected_company_id_for_modules}_payroll_excel_download"
                    )
                    # with col2: # Removed PDF download button
                    #     pdf_data = generate_pdf_report(current_company_payslips_df.drop(columns=['doc_id', 'company_id'], errors='ignore'), f"Payroll Report ({selected_company_name_for_modules})")
                    #     st.download_button(
                    #         label=f"Download Payroll PDF ({selected_company_name_for_modules})",
                    #         data=pdf_data,
                    #         file_name=f"Payroll_Report_{selected_company_name_for_modules}_{datetime.date.today()}.pdf",
                    #         mime="application/pdf",
                    #         key=f"admin_{selected_company_id_for_modules}_payroll_pdf_download"
                    #     )

                    st.markdown("---")

                display_module("Planning & Time Off", PLANNING_TIMEOFF_FIELDS, 'leaves', crud_enabled=True, company_filter_id=selected_company_id_for_modules)

                display_module("VAT Input/Output", VAT_INPUT_OUTPUT_FIELDS, 'vat_transactions', crud_enabled=True, company_filter_id=selected_company_id_for_modules)
                
                with st.expander(f"**VAT Return Report for {selected_company_name_for_modules}**"):
                    st.subheader(f"VAT Return Report ({selected_company_name_for_modules}) (Placeholder)")
                    st.info("Automate VAT calculation and generate VAT return reports here.")
                    st.write("Output VAT from Sales Invoices.")
                    st.write("Input VAT from Purchases.")
                    # st.write("Auto-generate VAT Return Report for export.") # Removed PDF line
                    st.info("VAT Return Report PDF generation is removed as requested.")
                    # if st.button(f"Generate VAT Return Report ({selected_company_name_for_modules})", key=f"admin_{selected_company_id_for_modules}_generate_vat_report"):
                    #     vat_data_for_report = get_db_collection(selected_company_id_for_modules, 'vat_transactions')
                    #     vat_report_pdf = generate_pdf_report(vat_data_for_report.drop(columns=['doc_id', 'company_id'], errors='ignore'), f"VAT Return Report for {selected_company_name_for_modules}")
                    #     st.download_button(
                    #         label=f"Download VAT Return Report PDF ({selected_company_name_for_modules})",
                    #         data=vat_report_pdf,
                    #         file_name=f"VAT_Return_Report_{selected_company_name_for_modules}_{datetime.date.today()}.pdf",
                    #         mime="application/pdf",
                    #         key=f"admin_{selected_company_id_for_modules}_vat_pdf_download"
                    #     )
                    #     st.success(f"VAT Return Report generated (placeholder) for {selected_company_name_for_modules}.")


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
            st.warning("Note: All data is persisted in a SQLite database file.")


        elif selected_module == "Trip Management":
            display_module("Trip", TRIP_MANAGEMENT_FIELDS, 'trips', crud_enabled=True, company_filter_id=st.session_state['company_id'])

        elif selected_module == "Rental Management":
            display_module("Rental", RENTAL_MANAGEMENT_FIELDS, 'rentals', crud_enabled=True, company_filter_id=st.session_state['company_id'])

        elif selected_module == "Fleet Management":
            display_module("Fleet", FLEET_MANAGEMENT_FIELDS, 'vehicles', crud_enabled=True, company_filter_id=st.session_state['company_id'])

        elif selected_module == "Invoicing & Quoting":
            display_module("Invoicing & Quoting", INVOICING_QUOTING_FIELDS, 'invoices', crud_enabled=True, company_filter_id=st.session_state['company_id'])

        elif selected_module == "CRM / Customer Management":
            display_module("CRM / Customer Management", CRM_MANAGEMENT_FIELDS, 'clients', crud_enabled=True, company_filter_id=st.session_state['company_id'])

        elif selected_module == "Employee Management":
            display_module("Employee", EMPLOYEE_MANAGEMENT_FIELDS, 'employees', crud_enabled=True, company_filter_id=st.session_state['company_id'])

        elif selected_module == "Payroll":
            st.header("Payroll Management")
            current_company_payslips_df = get_db_collection(st.session_state['company_id'], 'payslips')

            st.subheader("Generate Payslip")
            # Initialize or retrieve widget values for payroll
            session_state_key_for_payslip_add_user = f'add_new_payslip_values_{st.session_state["company_id"]}'
            if session_state_key_for_payslip_add_user not in st.session_state:
                st.session_state[session_state_key_for_payslip_add_user] = {
                    'Employee Name': '',
                    'Month': str(datetime.date.today().month),
                    'Year': str(datetime.date.today().year),
                    'Base Salary': 0.0,
                    'Trip Bonus': 0.0,
                    'Rental Commission': 0.0,
                    'Deductions': 0.0,
                    'Overtime': 0.0,
                    'Net Salary': 0.0,
                    'Payment Status': 'Unpaid'
                }
            
            current_payslip_values_user = st.session_state[session_state_key_for_payslip_add_user]

            payslip_emp_name = st.text_input("Employee Name (for Payslip)", value=current_payslip_values_user['Employee Name'], placeholder="Enter employee name", key=f"{st.session_state['company_id']}_payroll_emp_name")
            payslip_month = st.selectbox("Month", options=[str(i) for i in range(1, 13)], index=[str(i) for i in range(1, 13)].index(current_payslip_values_user['Month']), key=f"{st.session_state['company_id']}_payroll_month")
            payslip_year = st.selectbox("Year", options=[str(i) for i in range(2020, datetime.datetime.now().year + 2)], index=[str(i) for i in range(2020, datetime.datetime.now().year + 2)].index(current_payslip_values_user['Year']), key=f"{st.session_state['company_id']}_payroll_year")
            base_salary = st.number_input("Base Salary", value=float(current_payslip_values_user['Base Salary']), key=f"{st.session_state['company_id']}_payroll_base_salary")
            trip_bonus = st.number_input("Trip Bonus", value=float(current_payslip_values_user['Trip Bonus']), key=f"{st.session_state['company_id']}_payroll_trip_bonus")
            rental_commission = st.number_input("Rental Commission", value=float(current_payslip_values_user['Rental Commission']), key=f"{st.session_state['company_id']}_payroll_rental_commission")
            deductions = st.number_input("Deductions", value=float(current_payslip_values_user['Deductions']), key=f"{st.session_state['company_id']}_payroll_deductions")
            overtime = st.number_input("Overtime", value=float(current_payslip_values_user['Overtime']), key=f"{st.session_state['company_id']}_payroll_overtime")

            net_salary = base_salary + trip_bonus + rental_commission + overtime - deductions
            st.write(f"Calculated Net Salary: **INR {net_salary:.2f}**")

            if st.button("Generate Payslip", key=f"{st.session_state['company_id']}_generate_payslip_btn"):
                existing_payslip_check = current_company_payslips_df[
                    (current_company_payslips_df['Employee Name'] == payslip_emp_name) &
                    (current_company_payslips_df['Month'] == payslip_month) &
                    (current_company_payslips_df['Year'] == payslip_year)
                ]
                
                payslip_data = {
                    'Company': st.session_state['company_name'],
                    'Payslip ID': f"PS_{payslip_emp_name[:3].upper()}_{payslip_month}{payslip_year}_{datetime.datetime.now().strftime('%H%M%S%f')}",
                    'Employee Name': payslip_emp_name, 'Month': payslip_month, 'Year': payslip_year,
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
                            if update_db_document(st.session_state['company_id'], 'payslips', doc_id_to_overwrite, payslip_data):
                                st.success("Payslip overwritten and regenerated successfully!")
                                st.session_state[session_state_key_for_payslip_add_user] = {} # Clear for rerun
                                st.rerun()
                    with col_confirm_no:
                        if st.button("Cancel", key=f"{st.session_state['company_id']}_cancel_overwrite"):
                            st.info("Payslip generation cancelled.")
                else:
                    if add_db_document(st.session_state['company_id'], 'payslips', payslip_data):
                        st.success("Payslip generated successfully!")
                        st.session_state[session_state_key_for_payslip_add_user] = {} # Clear for rerun
                        st.rerun()


            st.subheader("Payroll History")
            
            # Prepare display_df for data_editor, ensuring doc_id is present
            payslip_display_df_for_editor = add_serial_numbers(current_company_payslips_df)

            payslip_column_config = {
                "doc_id": st.column_config.Column("Document ID", disabled=True, width="small"),
                "company_id": st.column_config.Column("Company ID", disabled=True, width="small"),
                "Company": st.column_config.Column("Company Name", disabled=True, width="small"),
                "SL No": st.column_config.Column("SL No", disabled=True, width="extra_small"),
                "Payslip ID": st.column_config.TextColumn("Payslip ID", disabled=True),
                "Net Salary": st.column_config.NumberColumn("Net Salary", format="%0.2f", disabled=True),
            }
            for field, config in PAYROLL_FIELDS.items():
                if config['type'] == 'number':
                    if field not in payslip_column_config:
                        payslip_column_config[field] = st.column_config.NumberColumn(field, format="%0.2f")
                elif config['type'] == 'select':
                    payslip_column_config[field] = st.column_config.SelectboxColumn(field, options=config['options'])
                elif config['type'] == 'text':
                    payslip_column_config[field] = st.column_config.TextColumn(field)

            st.data_editor(
                payslip_display_df_for_editor,
                key=f"{st.session_state['company_id']}_payslip_history_editor",
                hide_index=True,
                num_rows="dynamic",
                use_container_width=True,
                column_config=payslip_column_config
            )
            
            payslip_editor_state_key = f"{st.session_state['company_id']}_payslip_history_editor"
            payslip_changes_made = False

            if payslip_editor_state_key in st.session_state and st.session_state[payslip_editor_state_key]:
                edited_payslip_rows_dict = st.session_state[payslip_editor_state_key].get('edited_rows', {})
                added_payslip_rows_list = st.session_state[payslip_editor_state_key].get('added_rows', [])
                deleted_payslip_rows_indices = st.session_state[payslip_editor_state_key].get('deleted_rows', [])

                deleted_payslip_count = 0
                for idx_to_delete in deleted_payslip_rows_indices:
                    if idx_to_delete < len(current_company_payslips_df):
                        doc_id_to_delete = current_company_payslips_df.iloc[idx_to_delete]['doc_id']
                        if delete_db_document(st.session_state['company_id'], 'payslips', doc_id_to_delete):
                            deleted_payslip_count += 1
                            payslip_changes_made = True
                if deleted_payslip_count > 0:
                    st.success(f"{deleted_payslip_count} Payslip entries deleted!")

                added_payslip_count = 0
                for new_row_data in added_payslip_rows_list:
                    new_entry_data = {}
                    for field, value in new_row_data.items():
                        if PAYROLL_FIELDS.get(field, {}).get('type') == 'select' and value == '--- Select ---':
                            new_entry_data[field] = None
                        elif PAYROLL_FIELDS.get(field, {}).get('type') == 'checkbox':
                            new_entry_data[field] = 1 if value else 0
                        elif pd.isna(value):
                            new_entry_data[field] = None
                        else:
                            new_entry_data[field] = value

                    # Auto-generate Payslip ID for new rows
                    emp_name_short = new_entry_data.get('Employee Name', 'UNK')[:3].upper()
                    month_val = new_entry_data.get('Month', '00')
                    year_val = new_entry_data.get('Year', '0000')
                    new_entry_data['Payslip ID'] = f"PS_{emp_name_short}_{month_val}{year_val}_{datetime.datetime.now().strftime('%H%M%S%f')}"
                    new_entry_data['Company'] = st.session_state['company_name'] # Ensure company is set

                    # Calculate Net Salary for new rows
                    base_salary = new_entry_data.get('Base Salary', 0.0)
                    trip_bonus = new_entry_data.get('Trip Bonus', 0.0)
                    rental_commission = new_entry_data.get('Rental Commission', 0.0)
                    deductions = new_entry_data.get('Deductions', 0.0)
                    overtime = new_entry_data.get('Overtime', 0.0)
                    new_entry_data['Net Salary'] = base_salary + trip_bonus + rental_commission + overtime - deductions

                    if add_db_document(st.session_state['company_id'], 'payslips', new_entry_data):
                        added_payslip_count += 1
                        payslip_changes_made = True
                if added_payslip_count > 0:
                    st.success(f"{added_payslip_count} new Payslip entries added successfully!")
                
                updated_payslip_count = 0
                for idx_to_edit, changes_dict in edited_payslip_rows_dict.items():
                    if idx_to_edit < len(current_company_payslips_df):
                        doc_id_to_update = current_company_payslips_df.iloc[idx_to_edit]['doc_id']
                        
                        data_to_update = {}
                        for field, value in changes_dict.items():
                            if PAYROLL_FIELDS.get(field, {}).get('type') == 'select' and value == '--- Select ---':
                                data_to_update[field] = None
                            elif PAYROLL_FIELDS.get(field, {}).get('type') == 'checkbox':
                                data_to_update[field] = 1 if value else 0
                            elif pd.isna(value):
                                data_to_update[field] = None
                            else:
                                data_to_update[field] = value

                        # Recalculate Net Salary
                        current_row_data_for_calc = current_company_payslips_df.iloc[idx_to_edit].to_dict()
                        current_row_data_for_calc.update(data_to_update) # Apply current changes
                        
                        base_salary = current_row_data_for_calc.get('Base Salary', 0.0)
                        trip_bonus = current_row_data_for_calc.get('Trip Bonus', 0.0)
                        rental_commission = current_row_data_for_calc.get('Rental Commission', 0.0)
                        deductions = current_row_data_for_calc.get('Deductions', 0.0)
                        overtime = current_row_data_for_calc.get('Overtime', 0.0)
                        data_to_update['Net Salary'] = base_salary + trip_bonus + rental_commission + overtime - deductions


                        if update_db_document(st.session_state['company_id'], 'payslips', doc_id_to_update, data_to_update):
                            updated_payslip_count += 1
                            payslip_changes_made = True
                if updated_payslip_count > 0:
                    st.success(f"{updated_payslip_count} Payslip entries updated successfully!")

                # If any changes were made, clear the data_editor's internal state and rerun
                if payslip_changes_made:
                    st.session_state[payslip_editor_state_key]['edited_rows'] = {}
                    st.session_state[payslip_editor_state_key]['added_rows'] = []
                    st.session_state[payslip_editor_state_key]['deleted_rows'] = []
                    st.rerun()

            st.subheader("Download Payslip Reports")
            # col1, col2 = st.columns(2) # Removed col2 for PDF
            # with col1:
            excel_data = generate_excel_report(current_company_payslips_df.drop(columns=['doc_id', 'company_id'], errors='ignore'), "Payroll_Report")
            st.download_button(
                label="Download Payroll Excel",
                data=excel_data,
                file_name=f"Payroll_Report_{st.session_state['company_name']}_{datetime.date.today()}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"{st.session_state['company_id']}_payroll_excel_download"
            )
            # with col2: # Removed PDF download button
            #     pdf_data = generate_pdf_report(current_company_payslips_df.drop(columns=['doc_id', 'company_id'], errors='ignore'), "Payroll Report")
            #     st.download_button(
            #         label="Download Payroll PDF",
            #         data=pdf_data,
            #         file_name=f"Payroll_Report_{st.session_state['company_name']}_{datetime.date.today()}.pdf",
            #         mime="application/pdf",
            #         key=f"{st.session_state['company_id']}_payroll_pdf_download"
            #     )


        elif selected_module == "Planning & Time Off":
            display_module("Planning & Time Off", PLANNING_TIMEOFF_FIELDS, 'leaves', crud_enabled=True, company_filter_id=st.session_state['company_id'])
            st.subheader("Calendar View (Placeholder)")
            st.info("Implement a calendar view here to show driver schedules and leave requests. Libraries like `streamlit_calendar` can be used.")
            st.warning("Logic for overlap warnings would go here, checking employee availability against schedules and leave.")

        elif selected_module == "Reports Dashboard":
            st.subheader(f"Comprehensive Reports for {st.session_state['company_name']}")
            st.info("This dashboard provides insights into your company's operations across various modules.")

            st.markdown("#### Consolidated Data Overview")
            all_company_data_for_user_concat = pd.DataFrame()
            for module_name_key in MODULE_FIELDS_MAP.keys():
                df = get_db_collection(st.session_state['company_id'], module_name_key)
                if not df.empty and 'Company' in df.columns:
                    company_filtered_df = df[df['Company'] == st.session_state['company_name']].copy()
                    if not company_filtered_df.empty:
                        company_filtered_df['Module'] = module_name_key.replace('_', ' ').title()
                        all_company_data_for_user_concat = pd.concat([all_company_data_for_user_concat, company_filtered_df], ignore_index=True)

            if not all_company_data_for_user_concat.empty:
                st.dataframe(add_serial_numbers(all_company_data_for_user_concat.drop(columns=['doc_id', 'company_id'], errors='ignore')), use_container_width=True, hide_index=True)
                # col_ex_all, col_pdf_all = st.columns(2) # Removed col2 for PDF
                # with col_ex_all:
                st.download_button(
                    label=f"Download Consolidated {st.session_state['company_name']} Excel",
                    data=generate_excel_report(all_company_data_for_user_concat.drop(columns=['doc_id', 'company_id'], errors='ignore'), f"{st.session_state['company_id']}_Consolidated_Report"),
                    file_name=f"{st.session_state['company_name']}_Consolidated_Report_{datetime.date.today()}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"{st.session_state['company_id']}_consolidated_excel"
                )
                # with col_pdf_all: # Removed PDF download button
                #     st.download_button(
                #         label=f"Download Consolidated {st.session_state['company_name']} PDF",
                #         data=generate_pdf_report(all_company_data_for_user_concat.drop(columns=['doc_id', 'company_id'], errors='ignore'), f"{st.session_state['company_name']} Consolidated Report"),
                #         file_name=f"{st.session_state['company_name']}_Consolidated_Report_{datetime.date.today()}.pdf",
                #         mime="application/pdf",
                #         key=f"{st.session_state['company_id']}_consolidated_pdf"
                #     )
            else:
                st.info(f"No data available to generate a consolidated report for {st.session_state['company_name']} yet. Please add data in other modules.")

            st.markdown("---")
            st.markdown("#### Module Entry Counts (Your Company)")
            user_module_counts = {}
            for module_name_key in MODULE_FIELDS_MAP.keys():
                df = get_db_collection(st.session_state['company_id'], module_name_key)
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
            display_module("VAT Input/Output", VAT_INPUT_OUTPUT_FIELDS, 'vat_transactions', crud_enabled=True, company_filter_id=st.session_state['company_id'])
            st.subheader("VAT Return Report (Placeholder)")
            st.info("Automate VAT calculation and generate VAT return reports here.")
            st.write("Output VAT from Sales Invoices.")
            st.write("Input VAT from Purchases.")
            # st.write("Auto-generate VAT Return Report for export.") # Removed PDF line
            st.info("VAT Return Report PDF generation is removed as requested.")
            # if st.button("Generate VAT Return Report", key=f"{st.session_state['company_id']}_generate_vat_report"):
            #     vat_data_for_report = get_db_collection(st.session_state['company_id'], 'vat_transactions')
            #     vat_report_pdf = generate_pdf_report(vat_data_for_report.drop(columns=['doc_id', 'company_id'], errors='ignore'), f"VAT Return Report for {st.session_state['company_name']}")
            #     st.download_button(
            #         label=f"Download VAT Return Report PDF ({st.session_state['company_name']})",
            #         data=vat_report_pdf,
            #         file_name=f"VAT_Return_Report_{st.session_state['company_name']}_{datetime.date.today()}.pdf",
            #         mime="application/pdf",
            #         key=f"{st.session_state['company_id']}_vat_pdf_download"
            #     )
            #     st.success("VAT Return Report generated (placeholder).")


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
