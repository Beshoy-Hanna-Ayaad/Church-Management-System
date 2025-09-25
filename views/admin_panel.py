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
def refresh_data():
    # Now this will fetch the updated activities table including the new column
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

    # --- Section 1: Display Current Activities (UPDATED) ---
    st.subheader("Existing Activities")
    if not activities.empty:
        # UPDATED: Now displays the activity_type as well
        display_activities = activities[['activity_name', 'activity_type']].rename(
            columns={'activity_name': 'Activity Name', 'activity_type': 'Type'}
        )
        st.dataframe(
            display_activities,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No activities have been created yet.")
    
    st.markdown("---")
    
    # --- Section 2: Add or Delete ---
    col1, col2 = st.columns(2)

    # --- Add New Activity Form (UPDATED) ---
    with col1:
        with st.container(border=True):
            st.subheader("Add a New Activity")
            with st.form("add_activity_form"):
                new_activity_name = st.text_input("New Activity Name")
                # NEW: Added a selectbox to set the activity type
                new_activity_type = st.selectbox(
                    "Activity Type",
                    options=['Core', 'Selective'],
                    help="**Core:** Regular activities. **Selective:** Special opportunities."
                )
                add_submitted = st.form_submit_button("Add Activity")
                
                if add_submitted:
                    if not new_activity_name.strip():
                        st.warning("Activity name cannot be empty.")
                    elif new_activity_name in activities['activity_name'].tolist():
                        st.warning(f"Activity '{new_activity_name}' already exists.")
                    else:
                        try:
                            # UPDATED: The insert now includes the activity_type
                            supabase.from_("Activity").insert({
                                'activity_name': new_activity_name,
                                'activity_type': new_activity_type
                            }).execute()
                            st.success(f"Activity '{new_activity_name}' added!")
                            refresh_data() # Refresh data to show the new activity
                        except Exception as e:
                            st.error(f"An error occurred: {e}")

    # --- Delete Existing Activity Form (Unchanged, but now safer) ---
    with col2:
        with st.container(border=True):
            st.subheader("Delete an Activity")
            if not activities.empty:
                with st.form("delete_activity_form"):
                    activity_to_delete = st.selectbox(
                        "Select Activity to Delete",
                        options=activities['activity_name'].tolist()
                    )
                    st.warning("⚠️ Deleting an activity can affect historical records. Proceed with caution.", icon="🚨")
                    confirm_delete = st.checkbox(f"I am sure I want to delete '{activity_to_delete}'.")
                    
                    delete_submitted = st.form_submit_button("Delete Activity")
                    
                    if delete_submitted:
                        if not confirm_delete:
                            st.error("You must check the confirmation box to delete.")
                        else:
                            try:
                                activity_id = activities[activities['activity_name'] == activity_to_delete]['activity_id'].iloc[0]
                                supabase.from_("Activity").delete().eq('activity_id', int(activity_id)).execute()
                                st.success(f"Activity '{activity_to_delete}' has been deleted.")
                                refresh_data()
                            except Exception as e:
                                st.error(f"An error occurred: {e}")
            else:
                st.info("There are no activities to delete.")

