import streamlit as st
import pandas as pd
from db import Database

def manage_pricing():
    st.title("Pricing Management")
    db = Database()

    # Add tabs for different pricing management sections
    tab1, tab2 = st.tabs(["Categories", "Components"])

    # Categories Management
    with tab1:
        st.header("Pricing Categories")
        
        # Display existing categories
        categories = db.get_pricing_categories()
        if categories:
            st.subheader("Existing Categories")
            df = pd.DataFrame(categories)
            st.dataframe(df[['name', 'description', 'active']], use_container_width=True)

        # Add new category
        st.subheader("Add New Category")
        with st.form("add_category"):
            name = st.text_input("Category Name")
            description = st.text_area("Description")
            if st.form_submit_button("Add Category"):
                db.add_pricing_category(name, description)
                st.success(f"Added category: {name}")
                st.rerun()

        # Edit existing category
        if categories:
            st.subheader("Edit Category")
            category_to_edit = st.selectbox(
                "Select Category",
                options=[c['name'] for c in categories]
            )
            category = next(c for c in categories if c['name'] == category_to_edit)
            
            with st.form("edit_category"):
                new_name = st.text_input("Name", value=category['name'])
                new_description = st.text_area("Description", value=category['description'])
                new_active = st.checkbox("Active", value=category['active'])
                
                if st.form_submit_button("Update Category"):
                    db.update_pricing_category(
                        id=category['id'],
                        name=new_name,
                        description=new_description,
                        active=new_active
                    )
                    st.success(f"Updated category: {new_name}")
                    st.rerun()

    # Components Management
    with tab2:
        st.header("Pricing Components")
        
        # Filter by category
        categories = db.get_pricing_categories()
        selected_category = st.selectbox(
            "Filter by Category",
            options=[c['name'] for c in categories]
        )
        category_id = next(c['id'] for c in categories if c['name'] == selected_category)

        # Display existing components
        components = db.get_pricing_components(category_id)
        if components:
            st.subheader("Existing Components")
            df = pd.DataFrame(components)
            st.dataframe(
                df[['name', 'base_price', 'multiplier', 'description', 'active']],
                use_container_width=True
            )

        # Add new component
        st.subheader("Add New Component")
        with st.form("add_component"):
            name = st.text_input("Component Name")
            base_price = st.number_input("Base Price", min_value=0.0, step=100.0)
            multiplier = st.number_input("Multiplier", min_value=0.1, step=0.1)
            description = st.text_area("Description")
            
            if st.form_submit_button("Add Component"):
                db.add_pricing_component(
                    category_id=category_id,
                    name=name,
                    base_price=base_price,
                    multiplier=multiplier,
                    description=description
                )
                st.success(f"Added component: {name}")
                st.rerun()

        # Edit existing component
        if components:
            st.subheader("Edit Component")
            component_to_edit = st.selectbox(
                "Select Component",
                options=[c['name'] for c in components]
            )
            component = next(c for c in components if c['name'] == component_to_edit)
            
            with st.form("edit_component"):
                new_name = st.text_input("Name", value=component['name'])
                new_price = st.number_input(
                    "Base Price",
                    value=float(component['base_price']),
                    min_value=0.0,
                    step=100.0
                )
                new_multiplier = st.number_input(
                    "Multiplier",
                    value=float(component['multiplier']),
                    min_value=1.0,
                    step=0.1
                )
                new_description = st.text_area(
                    "Description",
                    value=component['description']
                )
                new_active = st.checkbox("Active", value=component['active'])
                
                if st.form_submit_button("Update Component"):
                    db.update_pricing_component(
                        id=component['id'],
                        name=new_name,
                        base_price=new_price,
                        multiplier=new_multiplier,
                        description=new_description,
                        active=new_active
                    )
                    st.success(f"Updated component: {new_name}")
                    st.rerun()

if __name__ == "__main__":
    manage_pricing()