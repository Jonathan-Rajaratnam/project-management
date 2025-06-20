import io
import json
from datetime import datetime, timedelta
from decimal import Decimal
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import openai
import pandas as pd
import streamlit as st

from auth import Auth, initialize_auth
from db import Database
from fpdf import FPDF
from pages.Project_Management import generate_pdf, send_email



# Initialize session state so it 
if "team_selections" not in st.session_state:
    st.session_state.team_selections = []
if "previous_selections" not in st.session_state:
    st.session_state.previous_selections = {}

def apply_psychological_pricing(price):
    #Apply psychological pricing strategy by converting to .99 format
    if price >= 100:
        # For prices >= 100, round to nearest whole number and subtract 0.01
        return round(price) - 0.01
    else:
        # For prices < 100, round to nearest 0.99
        return round(price - 0.01) + 0.99


# def calculate_quote(team_selections, timeline_weeks, tech_stack, complexity, marketing_strategy, db,):
#     base_cost = 0.0

#     # Calculate team cost using default rates
#     for member in team_selections:
#         if member.get("name"):
#             # Get default rate from database
#             team_member = db.get_team_member_by_name(member["name"])
#             if team_member:
#                 base_cost += float(team_member["default_rate"]) * float(timeline_weeks)

#     # Add pricing for tech stack components
#     for tech in tech_stack:
#         tech_price = db.get_component_price(tech, "Technology Stack")
#         base_cost += float(tech_price["base_price"]) * float(tech_price["multiplier"])

#     # Add pricing for complexity
#     complexity_price = db.get_component_price(complexity, "Complexity")
#     base_cost += float(complexity_price["base_price"]) * float(complexity_price["multiplier"])

#     # Get the profit margin from the previous month
#     last_month = (datetime.now() - timedelta(days=30)).strftime("%B %Y")
#     previous_revenue = db.get_previous_month_revenue(last_month)
#     profit_margin = float(previous_revenue) if previous_revenue else 50.0

#     total_cost_with_margin = base_cost * (1 + profit_margin / 100)

#     # Apply marketing strategy pricing
#     if marketing_strategy == "Psychological Pricing":
#         total_cost_with_margin = apply_psychological_pricing(total_cost_with_margin)
#     else:
#         # Get pricing adjustment from database for other strategies
#         strategy_price = db.get_component_price(marketing_strategy, "Pricing Strategy")
#         if strategy_price:
#             total_cost_with_margin *= float(strategy_price["multiplier"])

#     profit = total_cost_with_margin - base_cost

#     return base_cost, total_cost_with_margin, profit, profit_margin

def calculate_quote(team_selections, timeline_weeks, tech_stack, complexity, marketing_strategy, db):
    base_cost = 0.0
    
    print("\n=== DETAILED COST CALCULATION LOG ===")
    print(f"\nTimeline: {timeline_weeks} weeks")
    print(f"Complexity: {complexity}")
    print(f"Marketing Strategy: {marketing_strategy}")
    
    # Get current month for reference
    current_month = datetime.now().strftime("%B %Y")
    print(f"\nCalculation Month: {current_month}")
    
    # Calculate team cost
    print("\n1. TEAM COSTS:")
    team_total = 0
    for member in team_selections:
        if member.get("name"):
            team_member = db.get_team_member_by_name(member["name"])
            if team_member:
                member_cost = float(team_member["default_rate"]) * float(timeline_weeks)
                team_total += member_cost
                print(f"   - {member['name']} ({member['role']}):")
                print(f"     Rate: ${float(team_member['default_rate'])}/week")
                print(f"     Timeline: {timeline_weeks} weeks")
                print(f"     Total: ${member_cost:,.2f}")
    
    base_cost += team_total
    print(f"\nTotal Team Cost: ${team_total:,.2f}")
    
    # Technology stack costs
    print("\n2. TECHNOLOGY STACK COSTS:")
    tech_total = 0
    for tech in tech_stack:
        tech_price = db.get_component_price(tech, "Technology Stack")
        tech_cost = float(tech_price["base_price"]) * float(tech_price["multiplier"])
        tech_total += tech_cost
        print(f"   - {tech}:")
        print(f"     Base Price: ${float(tech_price['base_price']):,.2f}")
        print(f"     Multiplier: {float(tech_price['multiplier'])}")
        print(f"     Total: ${tech_cost:,.2f}")
    
    base_cost += tech_total
    print(f"\nTotal Tech Stack Cost: ${tech_total:,.2f}")
    
    # Complexity costs
    print("\n3. COMPLEXITY COSTS:")
    complexity_price = db.get_component_price(complexity, "Complexity")
    complexity_cost = float(complexity_price["base_price"]) * float(complexity_price["multiplier"])
    base_cost += complexity_cost
    print(f"   - {complexity}:")
    print(f"     Base Price: ${float(complexity_price['base_price']):,.2f}")
    print(f"     Multiplier: {float(complexity_price['multiplier'])}")
    print(f"     Total: ${complexity_cost:,.2f}")
    
    # Get the profit margin
    last_month = (datetime.now() - timedelta(days=30)).strftime("%B %Y")
    previous_revenue = db.get_previous_month_revenue(last_month)
    print("Previous Month Revenue:", previous_revenue);
    profit_margin = float(previous_revenue) if previous_revenue else 50.0  # Default margin
    
    print(f"\n4. PROFIT CALCULATION:")
    print(f"   Previous Month: {last_month}")
    print(f"   Previous Month Revenue: ${previous_revenue if previous_revenue else 'No data'}")
    print(f"   Applied Profit Margin: {profit_margin}%")
    
    # Calculate total with margin
    total_cost_with_margin = base_cost * (1 + profit_margin / 100)
    
    print("\n5. MARKETING STRATEGY ADJUSTMENT:")
    if marketing_strategy == "Psychological Pricing":
        original_price = total_cost_with_margin
        total_cost_with_margin = apply_psychological_pricing(total_cost_with_margin)
        print(f"   - Psychological Pricing Applied:")
        print(f"     Original: ${original_price:,.2f}")
        print(f"     Adjusted: ${total_cost_with_margin:,.2f}")
    else:
        strategy_price = db.get_component_price(marketing_strategy, "Pricing Strategy")
        print(f"   Retrieved strategy price data: {strategy_price}")  # Debug print
        
        if strategy_price and 'multiplier' in strategy_price:
            original_price = total_cost_with_margin
            multiplier = float(strategy_price['multiplier'])
            total_cost_with_margin *= multiplier
            print(f"   - {marketing_strategy}:")
            print(f"     Original: ${original_price:,.2f}")
            print(f"     Multiplier: {multiplier}")
            print(f"     Adjusted: ${total_cost_with_margin:,.2f}")
        else:
            print(f"   Warning: Could not find valid multiplier for {marketing_strategy}")
    
    # Calculate final profit
    profit = total_cost_with_margin - base_cost
    
    print("\n=== FINAL COST BREAKDOWN ===")
    print(f"Base Development Cost: ${base_cost:,.2f}")
    print(f"Profit Margin: {profit_margin}%")
    print(f"Profit Amount: ${profit:,.2f}")
    print(f"Total Cost (with margin): ${total_cost_with_margin:,.2f}")
    print(f"Weekly Revenue Rate: ${total_cost_with_margin/float(timeline_weeks):,.2f}/week")
    print("==============================\n")
    
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
    6. Cost Breakdown
    
    Don't include thing such as:
    Sincerely,
    [Your Name]
    [Web Development Agency]
    """

    

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

    st.set_page_config(
        page_title="Website Quote Generator",
        page_icon="💰",
        layout="wide",
    )

    if 'db' not in st.session_state:
        st.session_state.db = Database()

    # Check if user is logged in
    if not initialize_auth():
        return


    st.title("Website Quote Generator")

    # Initialize database
    db = Database()

    # Add team member button (outside form)
    if st.button("Add Team Member"):
        st.session_state.team_selections.append({
            "name": None,
            "role": None,
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

        # Get technology stack options from database
        tech_options = [tech["name"] for tech in db.get_componenents("Technology Stack")]
        tech_stack = st.multiselect("Select Technology Stack", tech_options)


        # Marketing Strategy
        pricing_strategies = [pricing["name"] for pricing in db.get_componenents("Pricing Strategy")]
        selected_strategy = st.selectbox(
            "Select Marketing Strategy", 
            pricing_strategies
        )

        # Team Selection
        st.subheader("Team Allocation")
        
        # Get team members from database
        team_members = db.get_team_members()  # Get all team members regardless of role

        # Team Member Selections
        st.subheader("Team Members")
        for i in range(len(st.session_state.team_selections)):
            # Create options list with all team members
            team_options = ["Select a team member"] + [
                f"{m['name']} | {m['role']} | {m['role_type']} | ${m['default_rate']:.2f}" 
                for m in team_members
            ]
            
            member_key = f"team_selection_{i}"
            member_selection = st.selectbox(
                "Select Team Member",
                team_options,
                key=member_key
            )
    
            # Check if selection changed
            prev_selection = st.session_state.previous_selections.get(member_key)
            if member_selection != prev_selection:
                st.session_state.previous_selections[member_key] = member_selection
                if i < len(st.session_state.team_selections):
                    if member_selection != "Select a team member":
                        # Split and take only the first three parts (name, role, role_type)
                        parts = member_selection.split(" | ")
                        st.session_state.team_selections[i] = {
                            "name": parts[0],
                            "role": parts[1],
                            "role_type": parts[2]
                    }
                    else:
                        st.session_state.team_selections[i] = {
                            "name": None,
                            "role": None,
                            "role_type": None
                        }


        # Calculate base cost and total cost with margin
        base_cost, total_cost_with_margin, profit, profit_margin_percentage = calculate_quote(
            st.session_state.team_selections, 
            timeline, 
            tech_stack, 
            complexity, 
            selected_strategy,
            db)


        st.write(f"Base Development Cost: ${base_cost:,.2f}")
        st.write(f"Total Cost (with margin): ${total_cost_with_margin:,.2f}")
        st.write(f"Profit: ${profit:,.2f}")

        # Form submit button
        submitted = st.form_submit_button("Generate Quote")
        if submitted:
            if not st.session_state.team_selections:
                st.error("Please add at least one team member.")
                return

            # Prepare team selections with rates from database
            team_selections_with_rates = []
            for member in st.session_state.team_selections:
                if member["name"] is not None:
                    team_member_data = db.get_team_member_by_name(member["name"])
                    if team_member_data:
                        team_selections_with_rates.append({
                            "name": member["name"],
                            "role": member["role"],
                            "role_type": member["role_type"],
                            "default_rate": float(team_member_data["default_rate"])
                        })

            project_details = {
                "client_name": client_name,
                "client_email": client_email,
                "pages": pages,
                "complexity": complexity,
                "tech_stack": tech_stack,
                "timeline": timeline,
                "margin_percentage": profit_margin_percentage,
                "marketing_strategy": selected_strategy,
                "marketing_cost": 0.00,
                "team_selections": team_selections_with_rates,  # Use the enriched team data
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
                    "Weekly Rate ($)": member["default_rate"],
                    "Total Cost": float(member["default_rate"]) * timeline,
                }
                for member in team_selections_with_rates  # Use the enriched team data
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
        saved_quotes = db.get_all_quotes()
        if not saved_quotes:
            st.error("No quote to save! Please generate a quote first.")
        else:
            latest_quote = saved_quotes[0]
            pdf = generate_pdf(latest_quote)
            pdf_output = pdf.output(dest='S').encode('latin-1')
            st.download_button(
                label="Download PDF",
                data=pdf_output,
                file_name=f"proposal_{latest_quote['client_name']}_{latest_quote['created_at'].strftime('%Y-%m-%d')}.pdf",
                mime="application/pdf"
            )

    if st.button("Send to Client"):
        if client_email:
            saved_quotes = db.get_all_quotes()
            if saved_quotes:
                latest_quote = saved_quotes[0]
                pdf = generate_pdf(latest_quote)
                pdf_bytes = pdf.output(dest='S').encode('latin-1')
                send_email(
                    client_email,
                    f"Project Proposal for {latest_quote['client_name']}",
                    latest_quote.get('proposal', ''),
                    latest_quote,
                    pdf_bytes
                )
        else:
            st.error("Please enter a client email address.")


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



    # Logout button
    with st.sidebar:
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.rerun()

if __name__ == "__main__":
    main()