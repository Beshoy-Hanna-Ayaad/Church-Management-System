import streamlit as st
import pandas as pd

# --- LOAD DATA & AUTHENTICATION ---
if 'data_loaded' not in st.session_state or not st.session_state.data_loaded:
    st.warning("Please run the main app file (Home.py) first to log in.")
    st.stop()

# Get data from session state
supabase = st.session_state.supabase
user_role = st.session_state.user_role
students = st.session_state.students
classes = st.session_state.classes
activities = st.session_state.activities
servants = st.session_state.servants

# --- PAGE TITLE & PERMISSIONS ---
st.title("⚙️ Data Management Panel")

if user_role not in ['Chief Manager', 'Department Manager', 'Priest']:
    st.error("You do not have sufficient privileges to access this page.")
    st.stop()

st.info("This panel allows you to perform administrative actions. Please be careful.")
st.markdown("---")

# --- HELPER FUNCTION FOR DATA REFRESH ---
# This is crucial for showing changes immediately after an update.
def refresh_data():
    st.session_state.activities = pd.DataFrame(supabase.from_("Activity").select("*").execute().data)
    st.rerun()

# --- UI with Tabs for each management task ---
tab1, tab2, tab3 = st.tabs(["🎓 Student Management", "⛪ Class Management", "📝 Activity Management"])

# --- Tab 1 & 2 (Unchanged) ---
with tab1:
    st.header("Update Student's Class")
    # ... (existing student management code)
with tab2:
    st.header("Manage Classes")
    st.write("Future implementation for creating, updating, or deleting classes.")

# --- Tab 3: Activity Management (Fully Implemented) ---
with tab3:
    st.header("Manage Activities")
    st.markdown("---")

    # --- Section 1: Display Current Activities ---
    st.subheader("Existing Activities")
    if not activities.empty:
        st.dataframe(
            activities[['activity_name']].rename(columns={'activity_name': 'Activity Name'}),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No activities have been created yet.")
    
    st.markdown("---")
    
    # --- Section 2: Add or Delete ---
    col1, col2 = st.columns(2)

    # --- Add New Activity Form ---
    with col1:
        with st.container(border=True):
            st.subheader("Add a New Activity")
            with st.form("add_activity_form"):
                new_activity_name = st.text_input("New Activity Name")
                add_submitted = st.form_submit_button("Add Activity")
                
                if add_submitted:
                    if not new_activity_name.strip():
                        st.warning("Activity name cannot be empty.")
                    elif new_activity_name in activities['activity_name'].tolist():
                        st.warning(f"Activity '{new_activity_name}' already exists.")
                    else:
                        try:
                            supabase.from_("Activity").insert({'activity_name': new_activity_name}).execute()
                            st.success(f"Activity '{new_activity_name}' added!")
                            refresh_data() # Refresh data to show the new activity
                        except Exception as e:
                            st.error(f"An error occurred: {e}")

    # --- Delete Existing Activity Form ---
    with col2:
        with st.container(border=True):
            st.subheader("Delete an Activity")
            if not activities.empty:
                with st.form("delete_activity_form"):
                    activity_to_delete = st.selectbox(
                        "Select Activity to Delete",
                        options=activities['activity_name'].tolist()
                    )
                    st.warning("⚠️ Deleting an activity cannot be undone.", icon="🚨")
                    confirm_delete = st.checkbox(f"I am sure I want to delete '{activity_to_delete}'.")
                    
                    delete_submitted = st.form_submit_button("Delete Activity")
                    
                    if delete_submitted:
                        if not confirm_delete:
                            st.error("You must check the confirmation box to delete.")
                        else:
                            try:
                                # Get the ID of the activity to delete
                                activity_id = activities[activities['activity_name'] == activity_to_delete]['activity_id'].iloc[0]
                                # IMPORTANT: You would first need to handle related records in the 'Attendance' table.
                                # For this prototype, we assume it's okay, but in production, you would need to
                                # either delete related attendance or prevent deletion if records exist.
                                supabase.from_("Activity").delete().eq('activity_id', int(activity_id)).execute()
                                st.success(f"Activity '{activity_to_delete}' has been deleted.")
                                refresh_data() # Refresh data to remove the activity from the list
                            except Exception as e:
                                st.error(f"An error occurred: {e}")
            else:
                st.info("There are no activities to delete.")