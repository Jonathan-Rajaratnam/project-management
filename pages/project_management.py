import streamlit as st
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import io
from db import Database
import smtplib
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart


def send_email(recipient_email, subject, body, quote, pdf_bytes=None):
    # Set up the email message
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = st.secrets["gmail_user"]
    msg['To'] = recipient_email

    # Simple email body
    email_body = f"""
Dear {quote['client_name']},

Thank you for your interest in our services. Please find attached our detailed proposal for your project.

Best regards,
Your Company Name
    """

    msg.attach(MIMEText(email_body, 'plain'))

    # Add the PDF attachment
    if pdf_bytes:
        part = MIMEApplication(pdf_bytes, Name=f"quote_{quote['client_name']}_{quote['created_at'].strftime('%Y-%m-%d')}.pdf")
        part['Content-Disposition'] = f'attachment; filename="quote_{quote["client_name"]}_{quote["created_at"].strftime("%Y-%m-%d")}.pdf"'
        msg.attach(part)

    # Send the email
    with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
        smtp.starttls()
        smtp.login(st.secrets["gmail_user"], st.secrets["gmail_password"])
        smtp.send_message(msg)
        st.success(f"Email sent to {recipient_email}")

def generate_pdf(quote_details):
    pdf = FPDF()
    pdf.add_page()
    
    # Set up fonts
    pdf.set_font('Arial', 'B', 16)
    
    # Header
    pdf.cell(0, 10, 'Project Proposal', 0, 1, 'C')
    pdf.line(10, 30, 200, 30)
    
    # Client Information
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, f'\nClient Information', 0, 1)
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 10, f'Client Name: {quote_details["client_name"]}', 0, 1)
    pdf.cell(0, 10, f'Client Email: {quote_details["client_email"]}', 0, 1)
    pdf.cell(0, 10, f'Date: {quote_details["created_at"].strftime("%Y-%m-%d")}', 0, 1)
    
    # Proposal
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, f'\nProposal', 0, 1)
    pdf.set_font('Arial', '', 12)
    # Check if 'proposal' key exists in quote_details
    if 'proposal_text' in quote_details:
        pdf.multi_cell(0, 10, quote_details['proposal_text'], 0, 1)
    else:
        pdf.multi_cell(0, 10, 'No proposal available.', 0, 1)

    #pdf_bytes = pdf.output(dest='S').encode('latin-1')
    return pdf

def view_project_details():
    st.title("Project Management")
    
    # Initialize database connection
    db = Database()
    
    # Get all quotes from database
    quotes = db.get_all_quotes()
    
    if not quotes:
        st.warning("No quotes available.")
        return
    
    # Display all quotes in a table format
    quotes_data = []
    for quote in quotes:
        quotes_data.append({
            "Date": quote["created_at"].strftime("%Y-%m-%d"),
            "Client": quote["client_name"],
            "Total Cost": f"${float(quote['total_cost']):,.2f}",
            "Timeline": f"{quote['timeline']} weeks",
            "Status": quote.get("status", "Pending")
        })
    
    if quotes_data:
        df = pd.DataFrame(quotes_data)
        st.dataframe(df, use_container_width=True)
        
        # Quote details section
        st.subheader("Quote Details")
        quote_indices = [f"Quote #{q['id']}: {q['client_name']}" for q in quotes]
        selected_quote = st.selectbox("Select Quote to View", quote_indices)
        
        if selected_quote:
            quote_id = int(selected_quote.split("#")[1].split(":")[0])
            quote = db.get_quote(quote_id)
            
            # Display quote details in expandable sections
            with st.expander("Client Information", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    st.write("Client Name:", quote["client_name"])
                    st.write("Client Email:", quote["client_email"])
                with col2:
                    st.write("Date:", quote["created_at"].strftime("%Y-%m-%d"))
                    st.write("Status:", quote.get("status", "Pending"))
            
            with st.expander("Project Details", expanded=True):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write("Pages:", quote["pages"])
                    st.write("Complexity:", quote["complexity"])
                with col2:
                    st.write("Timeline:", f"{quote['timeline']} weeks")
                    st.write("Margin:", f"{float(quote['margin_percentage'])}%")
                with col3:
                    st.write("Technology Stack:", ", ".join(quote["tech_stack"]))
                    st.write("Marketing Strategy:", quote["marketing_strategy"])
            
            with st.expander("Team Allocation", expanded=True):
                team_data = []
                for member in quote["team_selections"]:
                    if member["name"]:
                        team_data.append({
                            "Name": member["name"],
                            "Role": member["role"],
                            "Weekly Rate": f"${float(member['rate'])}/week",
                            "Total": f"${float(member['rate']) * quote['timeline']:,.2f}"
                        })
                if team_data:
                    st.table(pd.DataFrame(team_data))
            
            with st.expander("Cost Breakdown", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    st.write("Base Cost:", f"${float(quote['base_cost']):,.2f}")
                    st.write("Margin:", f"{float(quote['margin_percentage'])}%")
                    st.write("Profit:", f"${float(quote['profit']):,.2f}")
                with col2:
                    st.write("Total Cost:", f"${float(quote['total_cost']):,.2f}")
                    st.write("Project Duration:", f"{quote['timeline']} weeks")
                    st.write("Weekly Revenue:", f"${float(quote['total_cost'])/quote['timeline']:,.2f}")
            
            # Actions
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("Download PDF", key=f"pdf_{quote_id}"):
                    pdf = generate_pdf(quote)
                    pdf_bytes = pdf.output(dest='S').encode('latin-1')
                    st.download_button(
                        label="Click to Download",
                        data=pdf_bytes,
                        file_name=f"quote_{quote['client_name']}_{quote['created_at'].strftime('%Y-%m-%d')}.pdf",
                        mime="application/pdf"
                    )

                if st.button("Send to Client", key=f"send_{quote_id}"):
                    pdf = generate_pdf(quote)
                    pdf_bytes = pdf.output(dest='S').encode('latin-1')
                    send_email(
                        quote["client_email"],
                        f"Project Proposal for {quote['client_name']}",
                        quote["proposal_text"],
                        quote,
                        pdf_bytes
                    )

            with col2:
                status = st.selectbox(
                    "Update Status",
                    ["Pending", "Approved", "Rejected", "In Progress", "Completed"],
                    index=["Pending", "Approved", "Rejected", "In Progress", "Completed"].index(quote.get("status", "Pending"))
                )
                if status != quote.get("status", "Pending"):
                    db.update_quote_status(quote_id, status)
                    st.success(f"Status updated to {status}")
            with col3:
                if st.button("Delete Quote", key=f"delete_{quote_id}"):
                    if db.delete_quote(quote_id):
                        st.success("Quote deleted successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to delete quote!")
    else:
        st.info("No quotes available. Generate some quotes to see them here.")

if __name__ == "__main__":
    view_project_details()