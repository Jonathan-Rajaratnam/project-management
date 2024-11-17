import streamlit as st
import pandas as pd
from datetime import datetime
from datetime import timedelta
import openai
from db import Database
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from fpdf import FPDF
from pages.project_management import generate_pdf
import json
from decimal import Decimal
import io


# Initialize session state
# if "quotes" not in st.session_state:
#     st.session_state.quotes = []
if "team_selections" not in st.session_state:
    st.session_state.team_selections = []
if "previous_selections" not in st.session_state:
    st.session_state.previous_selections = {}


def update_rate(dev_selection, developers):
    """Helper function to get developer's default rate"""
    if dev_selection != "Select a developer":
        dev_name = dev_selection.split(" | ")[0]
        dev = next((m for m in developers if m["name"] == dev_name), None)
        if dev:
            return float(dev["default_rate"])
    return 0.0

def calculate_quote(team_selections, timeline_weeks, strategy_cost, tech_stack, complexity, db):
    base_cost = 0.0
    for member in team_selections:
        if member.get("rate", 0) > 0:
            base_cost += float(member["rate"]) * float(timeline_weeks)

    # Add pricing for tech stack components
    for tech in tech_stack:
        tech_price = db.get_component_price(tech, "Technology Stack")
        base_cost += float(tech_price["base_price"]) * float(tech_price["multiplier"])

    # Add pricing for complexity
    complexity_price = db.get_component_price(complexity, "Complexity")
    base_cost += float(complexity_price["base_price"]) * float(complexity_price["multiplier"])

    # Get the profit margin from the previous month
    last_month = (datetime.now() - timedelta(days=30)).strftime("%B %Y")
    profit_margin = float(db.get_previous_month_revenue(last_month))
    if profit_margin is None:
        profit_margin = 50.0

    total_cost_with_margin = base_cost * (1 + profit_margin / 100)
    profit = total_cost_with_margin - base_cost - strategy_cost

    return base_cost, total_cost_with_margin, profit, profit_margin


def generate_proposal(project_details):
    #"""Generate project proposal using OpenAI"""
    openai.api_key = st.secrets["openai_api_key"]

    team_details = "\n".join(
        [
            f"- {member['name']} ({member['role']})"
            for member in project_details["team_selections"]
        ]
    )

    prompt = f"""Generate a professional website development proposal for {project_details['client_name']}.
    Project Details:
    - Pages: {project_details['pages']}
    - Complexity: {project_details['complexity']}
    - Technology Stack: {', '.join(project_details['tech_stack'])}
    - Timeline: {project_details['timeline']} weeks
    - Budget: ${project_details['total_cost']:,.2f}

    Team Allocation:
    {team_details}

    Include:
    1. Project Overview
    2. Scope of Work
    3. Technical Approach
    4. Timeline
    5. Team Composition
    6. Cost Breakdown"""

    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "You are a professional proposal writer for a web development agency.",
            },
            {"role": "user", "content": prompt},
        ],
    )

    return response.choices[0].message.content

def main():
    st.title("Website Quote Generator")

    # Initialize database
    db = Database()

    # # Navigation
    # st.sidebar.title("Navigation")
    # page = st.sidebar.radio("Go to", ["Quote Generator", "Project Management"])
    
    # if page == "Project Management":
    #     view_project_details()
    #     return

    # Add team member button (outside form)
    if st.button("Add Team Member"):
        st.session_state.team_selections.append({
            "name": None,
            "role": None,
            "hours": 0.0,
            "rate": 0.0
        })
        st.rerun()

    # Main form
    with st.form("quote_form"):
        st.header("Project Details")

        # Client Information
        col1, col2 = st.columns(2)
        with col1:
            client_name = st.text_input("Client Name")
        with col2:
            client_email = st.text_input("Client Email")

        # Project Specifications
        col1, col2, col3 = st.columns(3)
        with col1:
            pages = st.number_input("Number of Pages", min_value=1, value=1)
        with col2:
            complexity = st.selectbox("Project Complexity", [
                                    "Website", "Project", "Product"])
        with col3:
            timeline = st.number_input(
                "Project Timeline (weeks)", min_value=1, value=4)

        # Technology Stack
        tech_options = [
            "React", "Node.js", "Python", "Django",
            "WordPress", "Vue.js", "Angular",
        ]
        tech_stack = st.multiselect("Select Technology Stack", tech_options)

        # # Add project margins
        # margin_percentage = st.number_input(
        #     "Project Margin (%)", min_value=0.0, value=0.0, step=0.1
        # )

        #Marketing Strategy
        col1, col2 = st.columns(2)
        with col1:
            # Marketing strategy
            pricing_strategies = [
                "Psycological Pricing", "Market Skimming",
                "Overhead Pricing", "Value-Based Pricing",
            ]
            selected_strategy = st.selectbox(
                "Select Marketing Strategy", 
                pricing_strategies
            )
        with col2:
            strategy_cost = st.number_input(
                "Marketing Strategy Cost ($)",
                min_value=0.0,
                value=0.0,
                step=100.0
            )

        # Team Selection
        st.subheader("Team Allocation")
        
        # Get team members from database
        developers = [m for m in db.get_team_members() if m["role_type"] == "Developer"]
        designers = [m for m in db.get_team_members() if m["role_type"] == "Designer"]
        
        # Developer Selections
        st.subheader("Developers")
        for i in range(len(st.session_state.team_selections)):
            cols = st.columns([3, 2])
            
            with cols[0]:
                dev_options = ["Select a developer"] + [
                    f"{m['name']} | {m['role']}" for m in developers
                ]
                dev_key = f"dev_selection_{i}"
                dev_selection = st.selectbox(
                    "Select Developer",
                    dev_options,
                    key=dev_key
                )
                
                # Check if selection changed and update rate
                prev_selection = st.session_state.previous_selections.get(dev_key)
                if dev_selection != prev_selection:
                    st.session_state.previous_selections[dev_key] = dev_selection
                    if i < len(st.session_state.team_selections):
                        st.session_state.team_selections[i] = {
                            "name": dev_selection.split(" | ")[0] if dev_selection != "Select a developer" else None,
                            "role": dev_selection.split(" | ")[1] if dev_selection != "Select a developer" else None,
                            "rate": update_rate(dev_selection, developers)
                        }
        
            
            with cols[1]:
                # Changed from hourly to weekly rate
                current_rate = st.session_state.team_selections[i].get("rate", 0.0)
                rate = st.number_input(
                    "Weekly Rate ($)",  # Changed label
                    min_value=0.0,
                    value=current_rate,
                    key=f"dev_rate_{i}"
                )
            
            # Update session state
            if dev_selection != "Select a developer":
                st.session_state.team_selections[i] = {
                    "name": dev_selection.split(" | ")[0],
                    "role": dev_selection.split(" | ")[1],
                    "rate": float(rate)
                }


            # Calculate base cost and total cost with margin
            base_cost, total_cost_with_margin, profit, profit_margin_percentage = calculate_quote(st.session_state.team_selections, timeline, strategy_cost, tech_stack, complexity, db)

            st.write(f"Base Development Cost: ${base_cost:,.2f}")
            st.write(f"Marketing Strategy Cost: ${strategy_cost:,.2f}")
            st.write(f"Total Cost (with margin): ${total_cost_with_margin:,.2f}")

        # Form submit button
        submitted = st.form_submit_button("Generate Quote")
        if submitted:
            if not st.session_state.team_selections:
                st.error("Please add at least one team member.")
                return

            project_details = {
                "client_name": client_name,
                "client_email": client_email,
                "pages": pages,
                "complexity": complexity,
                "tech_stack": tech_stack,
                "timeline": timeline,
                "margin_percentage": profit_margin_percentage,
                "marketing_strategy": selected_strategy,
                "marketing_cost": strategy_cost,
                "team_selections": st.session_state.team_selections,
                "total_cost": total_cost_with_margin,
                "base_cost": base_cost,
                "profit": profit,
                "date": datetime.now().strftime("%Y-%m-%d"),
            }

            with st.spinner("Generating proposal..."):
                proposal = generate_proposal(project_details)
                project_details["proposal"] = proposal

            st.success(f"Quote Generated: ${total_cost_with_margin:,.2f}")
            st.subheader("Generated Proposal")
            st.text_area("Proposal", proposal, height=300)

            st.subheader("Cost Breakdown")
            breakdown_data = [
                {
                    "Team Member": member["name"],
                    "Weekly Rate ($)": member["rate"],
                    "Total Cost": member["rate"] * timeline,
                }
                for member in st.session_state.team_selections
                if member["name"] is not None
            ]
            if breakdown_data:
                st.table(pd.DataFrame(breakdown_data))

            quote_id = db.save_quote(project_details)
            if quote_id:
                st.success(f"Quote #{quote_id} saved successfully!")
            else:
                st.error("Failed to save quote to database.")

    # Remove team members (outside form)
    st.subheader("Remove Team Members")
    for i in range(len(st.session_state.team_selections)):
        if st.button(f"Remove Team Member {i + 1}"):
            st.session_state.team_selections.pop(i)
            st.rerun()

    # Additional actions such as Save PDF and Send to Client
    if st.button("Save as PDF"):
        if not st.session_state.quotes:
            st.error("No quote to save! Please generate a quote first.")
        else:
            latest_quote = db.get_all_quotes()[0]
            pdf = generate_pdf(latest_quote)
            pdf_output = pdf.output(dest='S').encode('latin-1')
            st.download_button(
                label="Download PDF",
                data=pdf_output,
                file_name=f"proposal_{latest_quote['client_name']}_{latest_quote['date']}.pdf",
                mime="application/pdf"
            )

    if st.button("Send to Client"):
        st.info(f"Proposal would be sent to {client_email}")

    # Sidebar with saved quotes
    with st.sidebar:
        st.header("Saved Quotes")
        saved_quotes = db.get_all_quotes()
        for quote in saved_quotes:
            with st.expander(f"Quote #{quote['id']}: {quote['client_name']}"):
                st.write(f"Date: {quote['created_at'].strftime('%Y-%m-%d')}")
                st.write(f"Amount: ${float(quote['total_cost']):,.2f}")
                st.write(f"Timeline: {quote['timeline']} weeks")
                if st.button("Delete Quote", key=f"delete_quote_{quote['id']}"):
                    if db.delete_quote(quote['id']):
                        st.success("Quote deleted!")
                        st.rerun()
                    else:
                        st.error("Failed to delete quote!")

if __name__ == "__main__":
    main()