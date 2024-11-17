import streamlit as st
from db import Database
from datetime import datetime, timedelta

def financial_management():
    st.title("Financial Management")

    # Initialize database connection
    db = Database()

    # Get previous months
    today = datetime.now()
    previous_months = []
    for i in range(1, 13):
        month_date = today - timedelta(days=i * 30)
        previous_months.append(month_date.strftime("%B %Y"))

    # Allow user to select previous month
    selected_month = st.selectbox("Select Previous Month", previous_months)

    # Get revenue for selected month
    previous_revenue = st.number_input(f"Enter {selected_month} Revenue (USD)", min_value=0.0, step=1.0)

    # Calculate profit margin based on previous month's revenue
    previous_profit_margin = db.get_previous_month_revenue(selected_month)
    if previous_profit_margin is None:
        if previous_revenue <= 999:
            profit_margin = 100
        elif previous_revenue >= 1000 and previous_revenue <= 9999:
            profit_margin = 60
        else:
            profit_margin = 50
    else:
        profit_margin = previous_profit_margin

    st.write(f"Calculated Profit Margin: {profit_margin}%")

    # Save previous month's revenue to the database
    if st.button("Save Previous Month's Revenue"):
        if db.update_previous_month_revenue(selected_month, previous_revenue, profit_margin):
            st.success("Previous month's revenue updated successfully!")
        else:
            # If the update fails, try to insert a new record
            if db.save_previous_month_revenue(selected_month, previous_revenue, profit_margin):
                st.success("Previous month's revenue saved successfully!")
            else:
                st.error("Failed to save previous month's revenue.")

    # Display previous month's revenue
    previous_months_data = db.get_all_previous_month_revenue()
    if previous_months_data:
        st.subheader("Previous Month's Revenue")
        st.table(previous_months_data)

if __name__ == "__main__":
    financial_management()