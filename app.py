import streamlit as st
import pandas as pd
import datetime
from datetime import date, timedelta
import uuid
import json
from io import BytesIO
import base64
from reportlab.lib.pagesizes import letter, A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
import plotly.express as px
import plotly.graph_objects as go

# Initialize session state for data storage
def init_session_state():
    if 'trips' not in st.session_state:
        st.session_state.trips = []
    if 'rentals' not in st.session_state:
        st.session_state.rentals = []
    if 'fleet' not in st.session_state:
        st.session_state.fleet = []
    if 'invoices' not in st.session_state:
        st.session_state.invoices = []
    if 'customers' not in st.session_state:
        st.session_state.customers = []
    if 'employees' not in st.session_state:
        st.session_state.employees = []
    if 'payroll' not in st.session_state:
        st.session_state.payroll = []
    if 'leave_requests' not in st.session_state:
        st.session_state.leave_requests = []
    if 'vat_records' not in st.session_state:
        st.session_state.vat_records = []

def generate_pdf_report(data, title, filename):
    """Generate PDF report for any data"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], 
                                fontSize=18, spaceAfter=30, textColor=colors.darkblue)
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 20))
    
    if isinstance(data, pd.DataFrame) and not data.empty:
        # Convert DataFrame to table
        table_data = [data.columns.tolist()] + data.values.tolist()
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(table)
    else:
        story.append(Paragraph("No data available", styles['Normal']))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

# 1. Trip Management
def trip_management():
    st.header("Trip Management")
    
    tab1, tab2 = st.tabs(["Add New Trip", "View Trips"])
    
    with tab1:
        with st.form("trip_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                company_name = st.text_input("Company Name")
                vehicle = st.selectbox("Vehicle", options=[v['plate_no'] for v in st.session_state.fleet] if st.session_state.fleet else ["No vehicles available"])
                pickup_address = st.text_area("Pickup Address")
                client = st.selectbox("Client", options=[c['name'] for c in st.session_state.customers] if st.session_state.customers else ["No clients available"])
                trip_type = st.selectbox("Trip Type", ["Frozen", "Dry", "Hourly", "Express"])
                start_date = st.date_input("Start Date")
                start_time = st.time_input("Start Time")
                
            with col2:
                delivery_address = st.text_area("Delivery Address")
                driver = st.selectbox("Assigned Driver", options=[e['name'] for e in st.session_state.employees if e['type'] == 'Driver'] if st.session_state.employees else ["No drivers available"])
                end_date = st.date_input("End Date")
                end_time = st.time_input("End Time")
                distance = st.number_input("Distance (km)", min_value=0.0, step=0.1)
                price = st.number_input("Price", min_value=0.0, step=0.01)
                fuel_charge = st.number_input("Fuel Charge", min_value=0.0, step=0.01)
                surcharges = st.number_input("Other Surcharges", min_value=0.0, step=0.01)
            
            status = st.selectbox("Status", ["Scheduled", "Ongoing", "Completed"])
            
            if st.form_submit_button("Add Trip"):
                trip_id = f"TRIP-{len(st.session_state.trips) + 1:04d}"
                trip = {
                    'trip_id': trip_id,
                    'company_name': company_name,
                    'vehicle': vehicle,
                    'pickup_address': pickup_address,
                    'delivery_address': delivery_address,
                    'client': client,
                    'driver': driver,
                    'trip_type': trip_type,
                    'start_date': start_date,
                    'start_time': start_time,
                    'end_date': end_date,
                    'end_time': end_time,
                    'status': status,
                    'distance': distance,
                    'price': price,
                    'fuel_charge': fuel_charge,
                    'surcharges': surcharges,
                    'total': price + fuel_charge + surcharges
                }
                st.session_state.trips.append(trip)
                st.success(f"Trip {trip_id} added successfully!")
    
    with tab2:
        if st.session_state.trips:
            df = pd.DataFrame(st.session_state.trips)
            st.dataframe(df, use_container_width=True)
            
            if st.button("Export Trips to PDF"):
                pdf_buffer = generate_pdf_report(df, "Trip Management Report", "trips_report.pdf")
                st.download_button(
                    label="Download PDF",
                    data=pdf_buffer,
                    file_name="trips_report.pdf",
                    mime="application/pdf"
                )
        else:
            st.info("No trips recorded yet.")

# 2. Rental Management
def rental_management():
    st.header("Rental Management")
    
    tab1, tab2 = st.tabs(["Add New Rental", "View Rentals"])
    
    with tab1:
        with st.form("rental_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                start_date = st.date_input("Start Date")
                client = st.selectbox("Client", options=[c['name'] for c in st.session_state.customers] if st.session_state.customers else ["No clients available"])
                vehicle = st.selectbox("Vehicle", options=[v['plate_no'] for v in st.session_state.fleet] if st.session_state.fleet else ["No vehicles available"])
                daily_rate = st.number_input("Daily Rate", min_value=0.0, step=0.01)
                monthly_rate = st.number_input("Monthly Rate", min_value=0.0, step=0.01)
                fuel_included = st.checkbox("Fuel Included")
                
            with col2:
                end_date = st.date_input("End Date")
                driver = st.selectbox("Assigned Driver (Optional)", options=["None"] + [e['name'] for e in st.session_state.employees if e['type'] == 'Driver'])
                vat_excluded = st.checkbox("VAT Excluded")
                maintenance_notes = st.text_area("Maintenance Notes")
                status = st.selectbox("Status", ["Active", "Returned", "Overdue"])
            
            if st.form_submit_button("Add Rental"):
                rental_id = f"RENT-{len(st.session_state.rentals) + 1:04d}"
                rental = {
                    'rental_id': rental_id,
                    'start_date': start_date,
                    'end_date': end_date,
                    'client': client,
                    'vehicle': vehicle,
                    'driver': driver if driver != "None" else None,
                    'daily_rate': daily_rate,
                    'monthly_rate': monthly_rate,
                    'vat_excluded': vat_excluded,
                    'fuel_included': fuel_included,
                    'maintenance_notes': maintenance_notes,
                    'status': status
                }
                st.session_state.rentals.append(rental)
                st.success(f"Rental {rental_id} added successfully!")
    
    with tab2:
        if st.session_state.rentals:
            df = pd.DataFrame(st.session_state.rentals)
            st.dataframe(df, use_container_width=True)
            
            if st.button("Export Rentals to PDF"):
                pdf_buffer = generate_pdf_report(df, "Rental Management Report", "rentals_report.pdf")
                st.download_button(
                    label="Download PDF",
                    data=pdf_buffer,
                    file_name="rentals_report.pdf",
                    mime="application/pdf"
                )
        else:
            st.info("No rentals recorded yet.")

# 3. Fleet Management
def fleet_management():
    st.header("Fleet Management")
    
    tab1, tab2 = st.tabs(["Add Vehicle", "Fleet Overview"])
    
    with tab1:
        with st.form("fleet_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                plate_no = st.text_input("Plate Number")
                vehicle_type = st.selectbox("Vehicle Type", ["Truck", "Van", "Pickup", "Trailer"])
                capacity = st.text_input("Capacity")
                registration_date = st.date_input("Registration Date")
                insurance_expiry = st.date_input("Insurance Expiry")
                
            with col2:
                last_service = st.date_input("Last Service Date")
                next_service = st.date_input("Next Service Date")
                odometer = st.number_input("Current Odometer (km)", min_value=0)
                fuel_consumption = st.number_input("Fuel Consumption (L/100km)", min_value=0.0, step=0.1)
                availability = st.selectbox("Availability", ["Available", "In Use", "Rented", "Under Maintenance", "Out of Service"])
            
            maintenance_notes = st.text_area("Maintenance Notes")
            
            if st.form_submit_button("Add Vehicle"):
                vehicle = {
                    'plate_no': plate_no,
                    'type': vehicle_type,
                    'capacity': capacity,
                    'registration_date': registration_date,
                    'insurance_expiry': insurance_expiry,
                    'last_service': last_service,
                    'next_service': next_service,
                    'odometer': odometer,
                    'fuel_consumption': fuel_consumption,
                    'availability': availability,
                    'maintenance_notes': maintenance_notes
                }
                st.session_state.fleet.append(vehicle)
                st.success(f"Vehicle {plate_no} added successfully!")
    
    with tab2:
        if st.session_state.fleet:
            df = pd.DataFrame(st.session_state.fleet)
            st.dataframe(df, use_container_width=True)
            
            # Fleet Statistics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Vehicles", len(st.session_state.fleet))
            with col2:
                available = len([v for v in st.session_state.fleet if v['availability'] == 'Available'])
                st.metric("Available", available)
            with col3:
                in_use = len([v for v in st.session_state.fleet if v['availability'] == 'In Use'])
                st.metric("In Use", in_use)
            with col4:
                rented = len([v for v in st.session_state.fleet if v['availability'] == 'Rented'])
                st.metric("Rented", rented)
            
            if st.button("Export Fleet to PDF"):
                pdf_buffer = generate_pdf_report(df, "Fleet Management Report", "fleet_report.pdf")
                st.download_button(
                    label="Download PDF",
                    data=pdf_buffer,
                    file_name="fleet_report.pdf",
                    mime="application/pdf"
                )
        else:
            st.info("No vehicles in fleet yet.")

# 4. Invoicing & Quoting
def invoicing_quoting():
    st.header("Invoicing & Quoting")
    
    tab1, tab2, tab3 = st.tabs(["Generate Invoice", "Generate Quote", "View Invoices"])
    
    with tab1:
        st.subheader("Generate Invoice")
        with st.form("invoice_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                invoice_type = st.selectbox("Invoice Type", ["Trip", "Rental"])
                if invoice_type == "Trip":
                    reference_id = st.selectbox("Trip ID", options=[t['trip_id'] for t in st.session_state.trips] if st.session_state.trips else ["No trips available"])
                else:
                    reference_id = st.selectbox("Rental ID", options=[r['rental_id'] for r in st.session_state.rentals] if st.session_state.rentals else ["No rentals available"])
                
                client = st.selectbox("Client", options=[c['name'] for c in st.session_state.customers] if st.session_state.customers else ["No clients available"])
                amount = st.number_input("Base Amount", min_value=0.0, step=0.01)
                fuel_surcharge = st.number_input("Fuel Surcharge", min_value=0.0, step=0.01)
                driver_charge = st.number_input("Driver Charge", min_value=0.0, step=0.01)
                
            with col2:
                discount = st.number_input("Discount %", min_value=0.0, max_value=100.0, step=0.1)
                include_vat = st.checkbox("Include VAT", value=True)
                vat_rate = st.number_input("VAT Rate %", value=15.0, min_value=0.0, step=0.1)
                due_date = st.date_input("Due Date", value=date.today() + timedelta(days=30))
                
            subtotal = amount + fuel_surcharge + driver_charge
            discount_amount = subtotal * (discount / 100)
            net_amount = subtotal - discount_amount
            vat_amount = net_amount * (vat_rate / 100) if include_vat else 0
            total_amount = net_amount + vat_amount
            
            st.write(f"**Subtotal:** Rs.{subtotal:.2f}")
            st.write(f"**Discount:** Rs.{discount_amount:.2f}")
            st.write(f"**Net Amount:** Rs.{net_amount:.2f}")
            st.write(f"**VAT:** Rs.{vat_amount:.2f}")
            st.write(f"**Total:** Rs.{total_amount:.2f}")
            
            if st.form_submit_button("Generate Invoice"):
                invoice_id = f"INV-{len(st.session_state.invoices) + 1:04d}"
                invoice = {
                    'invoice_id': invoice_id,
                    'type': invoice_type,
                    'reference_id': reference_id,
                    'client': client,
                    'date': date.today(),
                    'due_date': due_date,
                    'amount': amount,
                    'fuel_surcharge': fuel_surcharge,
                    'driver_charge': driver_charge,
                    'discount_percent': discount,
                    'discount_amount': discount_amount,
                    'net_amount': net_amount,
                    'vat_rate': vat_rate,
                    'vat_amount': vat_amount,
                    'total_amount': total_amount,
                    'status': 'Pending'
                }
                st.session_state.invoices.append(invoice)
                st.success(f"Invoice {invoice_id} generated successfully!")
    
    with tab2:
        st.subheader("Generate Quote")
        st.info("Quote functionality - similar to invoice but for estimates")
    
    with tab3:
        if st.session_state.invoices:
            df = pd.DataFrame(st.session_state.invoices)
            st.dataframe(df, use_container_width=True)
            
            if st.button("Export Invoices to PDF"):
                pdf_buffer = generate_pdf_report(df, "Invoices Report", "invoices_report.pdf")
                st.download_button(
                    label="Download PDF",
                    data=pdf_buffer,
                    file_name="invoices_report.pdf",
                    mime="application/pdf"
                )
        else:
            st.info("No invoices generated yet.")

# 5. CRM / Customer Management
def customer_management():
    st.header("CRM / Customer Management")
    
    tab1, tab2 = st.tabs(["Add Customer", "Customer List"])
    
    with tab1:
        with st.form("customer_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Company Name")
                client_type = st.multiselect("Client Type", ["Rental", "Logistics"])
                contact_person = st.text_input("Contact Person")
                email = st.text_input("Email")
                phone = st.text_input("Phone")
                
            with col2:
                address = st.text_area("Address")
                contract_start = st.date_input("Contract Start Date")
                contract_end = st.date_input("Contract End Date")
                payment_terms = st.selectbox("Payment Terms", ["Net 30", "Net 15", "COD", "Net 60"])
                credit_limit = st.number_input("Credit Limit", min_value=0.0, step=100.0)
            
            vat_number = st.text_input("VAT Number")
            notes = st.text_area("Notes")
            
            if st.form_submit_button("Add Customer"):
                customer = {
                    'name': name,
                    'client_type': client_type,
                    'contact_person': contact_person,
                    'email': email,
                    'phone': phone,
                    'address': address,
                    'contract_start': contract_start,
                    'contract_end': contract_end,
                    'payment_terms': payment_terms,
                    'credit_limit': credit_limit,
                    'vat_number': vat_number,
                    'notes': notes,
                    'created_date': date.today()
                }
                st.session_state.customers.append(customer)
                st.success(f"Customer {name} added successfully!")
    
    with tab2:
        if st.session_state.customers:
            df = pd.DataFrame(st.session_state.customers)
            st.dataframe(df, use_container_width=True)
            
            if st.button("Export Customers to PDF"):
                pdf_buffer = generate_pdf_report(df, "Customer Management Report", "customers_report.pdf")
                st.download_button(
                    label="Download PDF",
                    data=pdf_buffer,
                    file_name="customers_report.pdf",
                    mime="application/pdf"
                )
        else:
            st.info("No customers registered yet.")

# 6. Employee Management
def employee_management():
    st.header("Employee Management")
    
    tab1, tab2 = st.tabs(["Add Employee", "Employee List"])
    
    with tab1:
        with st.form("employee_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Full Name")
                employee_type = st.selectbox("Employee Type", ["Driver", "Admin", "Mechanic"])
                phone = st.text_input("Phone")
                email = st.text_input("Email")
                hire_date = st.date_input("Hire Date")
                base_salary = st.number_input("Base Salary", min_value=0.0, step=100.0)
                
            with col2:
                license_number = st.text_input("License Number")
                license_expiry = st.date_input("License Expiry")
                id_number = st.text_input("ID Number")
                address = st.text_area("Address")
                availability = st.selectbox("Availability", ["Active", "On Leave", "Terminated"])
            
            emergency_contact = st.text_input("Emergency Contact")
            notes = st.text_area("Notes")
            
            if st.form_submit_button("Add Employee"):
                employee = {
                    'name': name,
                    'type': employee_type,
                    'phone': phone,
                    'email': email,
                    'hire_date': hire_date,
                    'base_salary': base_salary,
                    'license_number': license_number,
                    'license_expiry': license_expiry,
                    'id_number': id_number,
                    'address': address,
                    'availability': availability,
                    'emergency_contact': emergency_contact,
                    'notes': notes
                }
                st.session_state.employees.append(employee)
                st.success(f"Employee {name} added successfully!")
    
    with tab2:
        if st.session_state.employees:
            df = pd.DataFrame(st.session_state.employees)
            st.dataframe(df, use_container_width=True)
            
            if st.button("Export Employees to PDF"):
                pdf_buffer = generate_pdf_report(df, "Employee Management Report", "employees_report.pdf")
                st.download_button(
                    label="Download PDF",
                    data=pdf_buffer,
                    file_name="employees_report.pdf",
                    mime="application/pdf"
                )
        else:
            st.info("No employees registered yet.")

# 7. Payroll Management
def payroll_management():
    st.header("Payroll Management")
    
    tab1, tab2 = st.tabs(["Generate Payroll", "Payroll History"])
    
    with tab1:
        st.subheader("Generate Monthly Payroll")
        
        if not st.session_state.employees:
            st.warning("No employees found. Please add employees first.")
            return
        
        selected_month = st.selectbox("Select Month", 
                                    [f"{i:02d}" for i in range(1, 13)])
        selected_year = st.selectbox("Select Year", 
                                   [str(year) for year in range(2020, 2030)])
        
        for employee in st.session_state.employees:
            st.subheader(f"Payroll for {employee['name']}")
            
            with st.form(f"payroll_{employee['name']}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    base_salary = st.number_input("Base Salary", 
                                                value=employee.get('base_salary', 0.0),
                                                key=f"base_{employee['name']}")
                    trip_bonus = st.number_input("Trip Bonus", 
                                               min_value=0.0, step=10.0,
                                               key=f"bonus_{employee['name']}")
                    overtime = st.number_input("Overtime Pay", 
                                             min_value=0.0, step=10.0,
                                             key=f"overtime_{employee['name']}")
                    
                with col2:
                    deductions = st.number_input("Deductions", 
                                               min_value=0.0, step=10.0,
                                               key=f"deductions_{employee['name']}")
                    rental_commission = st.number_input("Rental Commission", 
                                                      min_value=0.0, step=10.0,
                                                      key=f"commission_{employee['name']}")
                
                gross_salary = base_salary + trip_bonus + overtime + rental_commission
                net_salary = gross_salary - deductions
                
                st.write(f"**Gross Salary:** Rs.{gross_salary:.2f}")
                st.write(f"**Net Salary:** Rs.{net_salary:.2f}")
                
                if st.form_submit_button(f"Generate Payslip for {employee['name']}"):
                    payroll_record = {
                        'employee_name': employee['name'],
                        'month': selected_month,
                        'year': selected_year,
                        'base_salary': base_salary,
                        'trip_bonus': trip_bonus,
                        'overtime': overtime,
                        'rental_commission': rental_commission,
                        'deductions': deductions,
                        'gross_salary': gross_salary,
                        'net_salary': net_salary,
                        'status': 'Generated',
                        'generated_date': date.today()
                    }
                    st.session_state.payroll.append(payroll_record)
                    st.success(f"Payslip generated for {employee['name']}")
    
    with tab2:
        if st.session_state.payroll:
            df = pd.DataFrame(st.session_state.payroll)
            st.dataframe(df, use_container_width=True)
            
            if st.button("Export Payroll to PDF"):
                pdf_buffer = generate_pdf_report(df, "Payroll Report", "payroll_report.pdf")
                st.download_button(
                    label="Download PDF",
                    data=pdf_buffer,
                    file_name="payroll_report.pdf",
                    mime="application/pdf"
                )
        else:
            st.info("No payroll records yet.")

# 8. Planning & Time Off
def planning_timeoff():
    st.header("Planning & Time Off")
    
    tab1, tab2, tab3 = st.tabs(["Leave Requests", "Driver Schedule", "Calendar View"])
    
    with tab1:
        st.subheader("Submit Leave Request")
        
        with st.form("leave_request"):
            employee = st.selectbox("Employee", 
                                  options=[e['name'] for e in st.session_state.employees] if st.session_state.employees else ["No employees available"])
            leave_type = st.selectbox("Leave Type", ["Annual Leave", "Sick Leave", "Emergency Leave"])
            start_date = st.date_input("Start Date")
            end_date = st.date_input("End Date")
            reason = st.text_area("Reason")
            
            if st.form_submit_button("Submit Request"):
                leave_request = {
                    'employee': employee,
                    'leave_type': leave_type,
                    'start_date': start_date,
                    'end_date': end_date,
                    'reason': reason,
                    'status': 'Pending',
                    'submitted_date': date.today()
                }
                st.session_state.leave_requests.append(leave_request)
                st.success("Leave request submitted!")
        
        st.subheader("Pending Leave Requests")
        if st.session_state.leave_requests:
            for i, request in enumerate(st.session_state.leave_requests):
                if request['status'] == 'Pending':
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.write(f"**{request['employee']}** - {request['leave_type']}")
                        st.write(f"{request['start_date']} to {request['end_date']}")
                    with col2:
                        if st.button("Approve", key=f"approve_{i}"):
                            st.session_state.leave_requests[i]['status'] = 'Approved'
                            st.success("Request approved!")
                    with col3:
                        if st.button("Reject", key=f"reject_{i}"):
                            st.session_state.leave_requests[i]['status'] = 'Rejected'
                            st.success("Request rejected!")
    
    with tab2:
        st.subheader("Driver Schedules")
        drivers = [e for e in st.session_state.employees if e['type'] == 'Driver']
        
        for driver in drivers:
            st.write(f"**{driver['name']}**")
            # Show assigned trips and availability
            assigned_trips = [t for t in st.session_state.trips if t.get('driver') == driver['name']]
            if assigned_trips:
                st.write(f"Assigned trips: {len(assigned_trips)}")
            else:
                st.write("No trips assigned")
    
    with tab3:
        st.subheader("Calendar Overview")
        st.info("Calendar view would show trips, rentals, and leave requests in a visual calendar format")

# 9. Reports Dashboard
def reports_dashboard():
    st.header("Reports Dashboard")
    
    # Key Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_trips = len(st.session_state.trips)
        st.metric("Total Trips", total_trips)
    
    with col2:
        total_rentals = len(st.session_state.rentals)
        st.metric("Active Rentals", total_rentals)
    
    with col3:
        total_revenue = sum([t.get('total', 0) for t in st.session_state.trips])
        st.metric("Trip Revenue", f"Rs.{total_revenue:.2f}")
    
    with col4:
        fleet_utilization = len([v for v in st.session_state.fleet if v.get('availability') in ['In Use', 'Rented']])
        total_fleet = len(st.session_state.fleet)
        utilization_rate = (fleet_utilization / total_fleet * 100) if total_fleet > 0 else 0
        st.metric("Fleet Utilization", f"{utilization_rate:.1f}%")
    
    # Charts and Visualizations
    st.subheader("Business Analytics")
    
    if st.session_state.trips or st.session_state.rentals:
        tab1, tab2, tab3, tab4 = st.tabs(["Trip Analysis", "Revenue Analysis", "Fleet Analysis", "Customer Analysis"])
        
        with tab1:
            if st.session_state.trips:
                # Trip Status Distribution
                trip_df = pd.DataFrame(st.session_state.trips)
                status_counts = trip_df['status'].value_counts()
                
                fig_status = px.pie(values=status_counts.values, names=status_counts.index, 
                                  title="Trip Status Distribution")
                st.plotly_chart(fig_status, use_container_width=True)
                
                # Trips by Driver
                if 'driver' in trip_df.columns:
                    driver_counts = trip_df['driver'].value_counts()
                    fig_driver = px.bar(x=driver_counts.index, y=driver_counts.values,
                                      title="Trips by Driver")
                    fig_driver.update_xaxes(title="Driver")
                    fig_driver.update_yaxes(title="Number of Trips")
                    st.plotly_chart(fig_driver, use_container_width=True)
            else:
                st.info("No trip data available for analysis")
        
        with tab2:
            if st.session_state.trips or st.session_state.invoices:
                # Revenue from Trips
                if st.session_state.trips:
                    trip_df = pd.DataFrame(st.session_state.trips)
                    if 'total' in trip_df.columns:
                        monthly_revenue = trip_df.groupby(trip_df['start_date'].dt.to_period('M'))['total'].sum()
                        
                        fig_revenue = px.line(x=monthly_revenue.index.astype(str), y=monthly_revenue.values,
                                            title="Monthly Revenue from Trips")
                        fig_revenue.update_xaxes(title="Month")
                        fig_revenue.update_yaxes(title="Revenue (Rs.)")
                        st.plotly_chart(fig_revenue, use_container_width=True)
                
                # Invoice Status
                if st.session_state.invoices:
                    invoice_df = pd.DataFrame(st.session_state.invoices)
                    invoice_status = invoice_df['status'].value_counts()
                    
                    fig_invoice = px.pie(values=invoice_status.values, names=invoice_status.index,
                                       title="Invoice Status Distribution")
                    st.plotly_chart(fig_invoice, use_container_width=True)
            else:
                st.info("No revenue data available for analysis")
        
        with tab3:
            if st.session_state.fleet:
                fleet_df = pd.DataFrame(st.session_state.fleet)
                
                # Fleet Availability
                availability_counts = fleet_df['availability'].value_counts()
                fig_fleet = px.bar(x=availability_counts.index, y=availability_counts.values,
                                 title="Fleet Availability Status")
                fig_fleet.update_xaxes(title="Status")
                fig_fleet.update_yaxes(title="Number of Vehicles")
                st.plotly_chart(fig_fleet, use_container_width=True)
                
                # Vehicle Types
                type_counts = fleet_df['type'].value_counts()
                fig_types = px.pie(values=type_counts.values, names=type_counts.index,
                                 title="Vehicle Type Distribution")
                st.plotly_chart(fig_types, use_container_width=True)
            else:
                st.info("No fleet data available for analysis")
        
        with tab4:
            if st.session_state.customers:
                customer_df = pd.DataFrame(st.session_state.customers)
                
                # Customer Types
                if 'client_type' in customer_df.columns:
                    # Flatten the client_type lists
                    all_types = []
                    for types in customer_df['client_type']:
                        if isinstance(types, list):
                            all_types.extend(types)
                        else:
                            all_types.append(types)
                    
                    type_counts = pd.Series(all_types).value_counts()
                    fig_customer = px.bar(x=type_counts.index, y=type_counts.values,
                                        title="Customer Types")
                    fig_customer.update_xaxes(title="Customer Type")
                    fig_customer.update_yaxes(title="Count")
                    st.plotly_chart(fig_customer, use_container_width=True)
                
                # Top Customers by Credit Limit
                if 'credit_limit' in customer_df.columns:
                    top_customers = customer_df.nlargest(10, 'credit_limit')[['name', 'credit_limit']]
                    fig_credit = px.bar(top_customers, x='name', y='credit_limit',
                                      title="Top 10 Customers by Credit Limit")
                    fig_credit.update_xaxes(title="Customer")
                    fig_credit.update_yaxes(title="Credit Limit (Rs.)")
                    st.plotly_chart(fig_credit, use_container_width=True)
            else:
                st.info("No customer data available for analysis")
    else:
        st.info("No data available for analytics. Please add some trips or rentals first.")
    
    # Export All Reports
    st.subheader("Export Reports")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Export Complete Business Report"):
            # Combine all data for comprehensive report
            all_data = {
                'Trips': pd.DataFrame(st.session_state.trips) if st.session_state.trips else pd.DataFrame(),
                'Rentals': pd.DataFrame(st.session_state.rentals) if st.session_state.rentals else pd.DataFrame(),
                'Fleet': pd.DataFrame(st.session_state.fleet) if st.session_state.fleet else pd.DataFrame(),
                'Customers': pd.DataFrame(st.session_state.customers) if st.session_state.customers else pd.DataFrame(),
                'Employees': pd.DataFrame(st.session_state.employees) if st.session_state.employees else pd.DataFrame()
            }
            
            # Create comprehensive report
            buffer = generate_comprehensive_report(all_data)
            st.download_button(
                label="Download Complete Report",
                data=buffer,
                file_name="complete_business_report.pdf",
                mime="application/pdf"
            )
    
    with col2:
        if st.button("Export to Excel"):
            # Create Excel file with multiple sheets
            excel_buffer = create_excel_report()
            st.download_button(
                label="Download Excel Report",
                data=excel_buffer,
                file_name="logistics_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    with col3:
        if st.button("Export Summary CSV"):
            # Create summary CSV
            summary_data = create_summary_data()
            csv_buffer = summary_data.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download CSV Summary",
                data=csv_buffer,
                file_name="business_summary.csv",
                mime="text/csv"
            )

def generate_comprehensive_report(all_data):
    """Generate comprehensive business report"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], 
                                fontSize=20, spaceAfter=30, textColor=colors.darkblue)
    story.append(Paragraph("Complete Business Report", title_style))
    story.append(Spacer(1, 20))
    
    # Summary Statistics
    story.append(Paragraph("Business Summary", styles['Heading2']))
    summary_text = f"""
    • Total Trips: {len(st.session_state.trips)}
    • Active Rentals: {len(st.session_state.rentals)}
    • Fleet Size: {len(st.session_state.fleet)}
    • Total Customers: {len(st.session_state.customers)}
    • Total Employees: {len(st.session_state.employees)}
    """
    story.append(Paragraph(summary_text, styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Add each section
    for section_name, df in all_data.items():
        if not df.empty:
            story.append(Paragraph(f"{section_name} Details", styles['Heading2']))
            
            # Convert DataFrame to table
            table_data = [df.columns.tolist()] + df.head(10).values.tolist()  # Limit to first 10 rows
            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(table)
            story.append(Spacer(1, 20))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

def create_excel_report():
    """Create Excel report with multiple sheets"""
    from io import BytesIO
    import pandas as pd
    
    buffer = BytesIO()
    
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        if st.session_state.trips:
            pd.DataFrame(st.session_state.trips).to_excel(writer, sheet_name='Trips', index=False)
        if st.session_state.rentals:
            pd.DataFrame(st.session_state.rentals).to_excel(writer, sheet_name='Rentals', index=False)
        if st.session_state.fleet:
            pd.DataFrame(st.session_state.fleet).to_excel(writer, sheet_name='Fleet', index=False)
        if st.session_state.customers:
            pd.DataFrame(st.session_state.customers).to_excel(writer, sheet_name='Customers', index=False)
        if st.session_state.employees:
            pd.DataFrame(st.session_state.employees).to_excel(writer, sheet_name='Employees', index=False)
        if st.session_state.invoices:
            pd.DataFrame(st.session_state.invoices).to_excel(writer, sheet_name='Invoices', index=False)
        if st.session_state.payroll:
            pd.DataFrame(st.session_state.payroll).to_excel(writer, sheet_name='Payroll', index=False)
    
    buffer.seek(0)
    return buffer

def create_summary_data():
    """Create summary data for CSV export"""
    summary = {
        'Metric': ['Total Trips', 'Active Rentals', 'Fleet Size', 'Total Customers', 'Total Employees', 'Total Revenue'],
        'Value': [
            len(st.session_state.trips),
            len(st.session_state.rentals),
            len(st.session_state.fleet),
            len(st.session_state.customers),
            len(st.session_state.employees),
            sum([t.get('total', 0) for t in st.session_state.trips])
        ]
    }
    return pd.DataFrame(summary)

# 10. VAT Input/Output
def vat_management():
    st.header("VAT Input/Output Management")
    
    tab1, tab2, tab3 = st.tabs(["VAT Records", "VAT Return", "Export VAT Report"])
    
    with tab1:
        st.subheader("Add VAT Record")
        
        with st.form("vat_record"):
            col1, col2 = st.columns(2)
            
            with col1:
                record_type = st.selectbox("Record Type", ["Input VAT", "Output VAT"])
                date = st.date_input("Date")
                description = st.text_input("Description")
                net_amount = st.number_input("Net Amount", min_value=0.0, step=0.01)
                
            with col2:
                vat_rate = st.number_input("VAT Rate %", value=15.0, min_value=0.0, step=0.1)
                vat_amount = net_amount * (vat_rate / 100)
                st.write(f"VAT Amount: Rs.{vat_amount:.2f}")
                total_amount = net_amount + vat_amount
                st.write(f"Total Amount: Rs.{total_amount:.2f}")
                
                supplier_customer = st.text_input("Supplier/Customer")
                invoice_number = st.text_input("Invoice Number")
            
            if st.form_submit_button("Add VAT Record"):
                vat_record = {
                    'type': record_type,
                    'date': date,
                    'description': description,
                    'supplier_customer': supplier_customer,
                    'invoice_number': invoice_number,
                    'net_amount': net_amount,
                    'vat_rate': vat_rate,
                    'vat_amount': vat_amount,
                    'total_amount': total_amount
                }
                st.session_state.vat_records.append(vat_record)
                st.success("VAT record added successfully!")
        
        # Display VAT Records
        if st.session_state.vat_records:
            st.subheader("VAT Records")
            df = pd.DataFrame(st.session_state.vat_records)
            st.dataframe(df, use_container_width=True)
    
    with tab2:
        st.subheader("VAT Return Summary")
        
        if st.session_state.vat_records:
            df = pd.DataFrame(st.session_state.vat_records)
            
            # Calculate totals
            output_vat = df[df['type'] == 'Output VAT']['vat_amount'].sum()
            input_vat = df[df['type'] == 'Input VAT']['vat_amount'].sum()
            net_vat_due = output_vat - input_vat
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Output VAT", f"Rs.{output_vat:.2f}")
            with col2:
                st.metric("Input VAT", f"Rs.{input_vat:.2f}")
            with col3:
                st.metric("Net VAT Due", f"Rs.{net_vat_due:.2f}")
            
            # Monthly breakdown
            df['month'] = pd.to_datetime(df['date']).dt.to_period('M')
            monthly_summary = df.groupby(['month', 'type'])['vat_amount'].sum().unstack(fill_value=0)
            
            if not monthly_summary.empty:
                st.subheader("Monthly VAT Summary")
                st.dataframe(monthly_summary, use_container_width=True)
        else:
            st.info("No VAT records available")
    
    with tab3:
        if st.session_state.vat_records:
            df = pd.DataFrame(st.session_state.vat_records)
            
            if st.button("Export VAT Report to PDF"):
                pdf_buffer = generate_pdf_report(df, "VAT Management Report", "vat_report.pdf")
                st.download_button(
                    label="Download VAT PDF Report",
                    data=pdf_buffer,
                    file_name="vat_report.pdf",
                    mime="application/pdf"
                )
            
            if st.button("Export VAT to Excel"):
                excel_buffer = BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name='VAT Records', index=False)
                    
                    # Add summary sheet
                    output_vat = df[df['type'] == 'Output VAT']['vat_amount'].sum()
                    input_vat = df[df['type'] == 'Input VAT']['vat_amount'].sum()
                    summary_data = pd.DataFrame({
                        'Description': ['Output VAT', 'Input VAT', 'Net VAT Due'],
                        'Amount': [output_vat, input_vat, output_vat - input_vat]
                    })
                    summary_data.to_excel(writer, sheet_name='VAT Summary', index=False)
                
                excel_buffer.seek(0)
                st.download_button(
                    label="Download VAT Excel Report",
                    data=excel_buffer,
                    file_name="vat_report.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        else:
            st.info("No VAT records to export")

# Main Application
def main():
    st.set_page_config(
        page_title="Logistics App",
        page_icon="🚚",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state
    init_session_state()
    
    # Sidebar Navigation
    st.sidebar.title("Logistics App")
    st.sidebar.markdown("---")
    
    menu_options = {
        "Trip Management": trip_management,
        "Rental Management": rental_management,
        "Fleet Management": fleet_management,
        "Invoicing & Quoting": invoicing_quoting,
        "Customer Management": customer_management,
        "Employee Management": employee_management,
        "Payroll Management": payroll_management,
        "Planning & Time Off": planning_timeoff,
        "Reports Dashboard": reports_dashboard,
        "VAT Management": vat_management
    }
    
    selected_menu = st.sidebar.selectbox(
        "Select Module",
        options=list(menu_options.keys())
    )
    
    # Display selected module
    menu_options[selected_menu]()
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("**System Status**")
    st.sidebar.success("All modules operational")
    
    # Data Summary in Sidebar
    st.sidebar.markdown("**Quick Stats**")
    st.sidebar.metric("Active Trips", len(st.session_state.trips))
    st.sidebar.metric("Fleet Vehicles", len(st.session_state.fleet))
    st.sidebar.metric("Total Customers", len(st.session_state.customers))

if __name__ == "__main__":
    main()
    