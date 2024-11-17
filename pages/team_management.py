import streamlit as st
from db import Database
import pandas as pd

st.set_page_config(
    page_title="Team Management",
    page_icon="👥",
    layout="wide"
)

def reset_form_fields():
    if 'form_submitted' in st.session_state and st.session_state.form_submitted:
        st.session_state['name_input'] = ""
        st.session_state['role_input'] = ""
        st.session_state.form_submitted = False

def is_duplicate_member(db, name, role, role_type):
    existing_members = db.get_team_members(role_type)
    return any(
        member['name'].lower() == name.lower() and
        member['role_type'].lower() == role.lower()
        for member in existing_members
    )

def handle_team_table(members, role_type, db):
    if not members:
        st.info(f"No {role_type.lower()}s added yet.")
        return

    # Create DataFrame with an additional column for delete checkbox
    df = pd.DataFrame(members)
    display_df = df[['id', 'name', 'role', 'default_rate']].copy()
    display_df = display_df.rename(columns={
        'name': 'Name',
        'role': 'Role',
        'default_rate': 'Rate ($/hour)'
    })

    # Add delete column to the editor
    editor_config = {
        'Delete': st.column_config.CheckboxColumn(
            default=False,
            help="Select to delete"
        )
    }

    display_df['Delete'] = False

    edited_df = st.data_editor(
        display_df,
        hide_index=True,
        column_config=editor_config,
        use_container_width=True,
        key=f"{role_type.lower()}_table"
    )

    # Handle deletions
    rows_to_delete = edited_df[edited_df['Delete']]['id'].tolist()
    if rows_to_delete:
        if st.button(f"Delete Selected {role_type}s"):
            for id in rows_to_delete:
                db.delete_team_member(id)
            st.success(f"Selected {role_type.lower()}s deleted!")
            st.rerun()

    # Handle edits/updates
    for i, row in edited_df.iterrows():
        original = members[i]
        if (row['Name'] != original['name'] or
            row['Role'] != original['role'] or
            row['Rate ($/hour)'] != original['default_rate']):
            db.update_team_member(
                original['id'],
                row['Name'],
                row['Role'],
                role_type,
                row['Rate ($/hour)']
            )

def main():
    st.title("Team Management")

    db = Database()

    if 'form_submitted' not in st.session_state:
        st.session_state.form_submitted = False

    reset_form_fields()

    # Add new team member form
    with st.expander("Add New Team Member", expanded=True):
        with st.form("new_team_member"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input(
                    "Name",
                    key="name_input",
                    value=st.session_state.get('name_input', '')
                )
                role_type = st.selectbox("Role Type", ["Developer", "Designer"])
            with col2:
                role = st.text_input(
                    "Role Title",
                    key="role_input",
                    value=st.session_state.get('role_input', '')
                )
                default_rate = st.number_input(
                    "Default Rate ($/hour)",
                    min_value=0,
                    value=100,
                    key="rate_input"
                )

            submitted = st.form_submit_button("Add Team Member")
            if submitted:
                if not name or not role:
                    st.error("Please fill in both name and role!")
                elif is_duplicate_member(db, name, role, role_type):
                    st.error(f"A {role_type} named {name} with role {role} already exists!")
                else:
                    db.add_team_member(name, role, role_type, default_rate)
                    st.success(f"Added {name} to the team!")
                    st.session_state.form_submitted = True
                    st.rerun()

    # Display team members in tables
    st.header("Current Team Members")

    # Developers Table
    st.subheader("Developers")
    developers = db.get_team_members("Developer")
    handle_team_table(developers, "Developer", db)

    # Designers Table
    st.subheader("Designers")
    designers = db.get_team_members("Designer")
    handle_team_table(designers, "Designer", db)

if __name__ == "__main__":
    main()