import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import plotly.graph_objects as go
import plotly.express as px
from db import Database

def view_financial_planner():
    st.title("Financial Planning & Forecasting")
    
    # Initialize database connection
    db = Database()
    
    # Create tabs for different sections
    tab1, tab2, tab3 = st.tabs(["Monthly Entry", "Forecasting", "Financial Overview"])
    
    # Monthly Entry Tab
    with tab1:
        st.subheader("Enter Monthly Financial Data")
        
        col1, col2 = st.columns(2)
        with col1:
            # Date picker defaulting to previous month with proper format
            default_date = date.today().replace(day=1) - timedelta(days=1)
            selected_month = st.date_input(
                "Select Month",
                value=default_date,
                format="MM/DD/YYYY"  # Using supported format
            )
            # Convert the full date to first day of the month
            selected_month = selected_month.replace(day=1)
            
            # Display selected month in user-friendly format
            st.caption(f"Selected: {selected_month.strftime('%B %Y')}")
            
        with col2:
            st.markdown("&nbsp;")  # Spacing
            show_previous = st.checkbox("Show Previous Month's Data")
        
        if show_previous:
            prev_month = (selected_month - timedelta(days=1)).replace(day=1)
            prev_data = db.get_monthly_financials(
                start_date=prev_month,
                end_date=selected_month
            )
            if prev_data:
                st.info(f"Previous Month's Data ({prev_month.strftime('%B %Y')}):\n"
                       f"Revenue: ${prev_data[0]['revenue']:,.2f}\n"
                       f"Expenses: ${prev_data[0]['expenses']:,.2f}\n"
                       f"Overhead: ${prev_data[0]['overhead_costs']:,.2f}")
        
        # Financial data input
        col1, col2, col3 = st.columns(3)
        with col1:
            revenue = st.number_input("Revenue ($)", min_value=0.0, step=100.0)
        with col2:
            expenses = st.number_input("Expenses ($)", min_value=0.0, step=100.0)
        with col3:
            overhead = st.number_input("Overhead Costs ($)", min_value=0.0, step=100.0)
        
        notes = st.text_area("Notes", placeholder="Enter any relevant notes about this month's financials...")
        
        if st.button("Save Monthly Data"):
            try:
                db.add_monthly_financial(
                    selected_month,  # Already first day of month
                    revenue,
                    expenses,
                    overhead,
                    notes
                )
                st.success("Monthly financial data saved successfully!")
            except Exception as e:
                st.error(f"Error saving data: {str(e)}")
    
    # Forecasting Tab
    with tab2:
        st.subheader("Financial Forecasting")
        
        # Select month for forecasting with proper format
        forecast_date = st.date_input(
            "Select Month for Forecast",
            value=date.today().replace(day=1),
            format="MM/DD/YYYY"  # Using supported format
        )
        forecast_month = forecast_date.replace(day=1)
        st.caption(f"Forecasting for: {forecast_month.strftime('%B %Y')}")
        
        # Get forecast data
        forecast = db.get_financial_forecast(forecast_month)
        
        # Rest of the forecasting tab code remains the same
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Conservative Forecast")
            conservative = forecast['conservative']
            st.metric(
                "Projected Revenue",
                f"${conservative['revenue']:,.2f}",
                f"${conservative['profit_loss']:,.2f} profit/loss"
            )
            st.write(f"Expected Expenses: ${conservative['expenses']:,.2f}")
            st.write(f"Fixed Costs: ${conservative['overhead_costs']:,.2f}")
        
        with col2:
            st.markdown("### Optimistic Forecast")
            optimistic = forecast['optimistic']
            st.metric(
                "Projected Revenue",
                f"${optimistic['revenue']:,.2f}",
                f"${optimistic['profit_loss']:,.2f} profit/loss"
            )
            st.write(f"Expected Expenses: ${optimistic['expenses']:,.2f}")
            st.write(f"Fixed Costs: ${optimistic['overhead_costs']:,.2f}")
        
        # Breakeven Analysis
        st.markdown("### Breakeven Analysis")
        breakeven = forecast['breakeven']
        
        progress = (breakeven['current_revenue'] / breakeven['needed_revenue']) * 100 if breakeven['needed_revenue'] > 0 else 0
        st.progress(min(progress/100, 1.0))
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Current Revenue", f"${breakeven['current_revenue']:,.2f}")
        with col2:
            st.metric("Revenue Needed", f"${breakeven['needed_revenue']:,.2f}")
        with col3:
            st.metric("Revenue Gap", f"${breakeven['revenue_gap']:,.2f}")
        
        st.info(f"Potential Additional Revenue from Pending Projects: ${breakeven['potential_projects_value']:,.2f}")
    
    # Financial Overview Tab
    with tab3:
        st.subheader("Financial Overview")
        
        # Get last 12 months of financial data
        end_date = date.today().replace(day=1)
        start_date = end_date - timedelta(days=365)
        financial_history = db.get_monthly_financials(start_date, end_date)
        
        if financial_history:
            df = pd.DataFrame(financial_history)
            df['month'] = pd.to_datetime(df['month'])
            
            # Revenue vs expenses plot
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df['month'],
                y=df['revenue'],
                name="Revenue",
                line=dict(color='green')
            ))
            fig.add_trace(go.Scatter(
                x=df['month'],
                y=df['expenses'] + df['overhead_costs'],
                name="Total Costs",
                line=dict(color='red')
            ))
            fig.update_layout(
                title="Revenue vs Costs Over Time",
                xaxis_title="Month",
                yaxis_title="Amount ($)",
                hovermode='x unified'
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Monthly profit/loss chart
            fig = px.bar(
                df,
                x='month',
                y='profit_loss',
                title="Monthly Profit/Loss",
                color='profit_loss',
                color_continuous_scale=['red', 'green']
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Key metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(
                    "Average Monthly Revenue",
                    f"${df['revenue'].mean():,.2f}",
                    f"{((df['revenue'].iloc[-1] / df['revenue'].iloc[0]) - 1) * 100:.1f}% YoY"
                )
            with col2:
                st.metric(
                    "Average Monthly Profit",
                    f"${df['profit_loss'].mean():,.2f}",
                    f"{((df['profit_loss'].iloc[-1] / df['profit_loss'].iloc[0]) - 1) * 100:.1f}% YoY"
                )
            with col3:
                profit_margin = (df['profit_loss'].sum() / df['revenue'].sum()) * 100
                st.metric("Overall Profit Margin", f"{profit_margin:.1f}%")
        else:
            st.info("No historical financial data available yet. Start entering monthly data to see trends and analysis.")

if __name__ == "__main__":
    view_financial_planner()