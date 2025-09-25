import streamlit as st
import pandas as pd
from datetime import datetime

# --- LOAD DATA & AUTHENTICATION ---
if 'data_loaded' not in st.session_state or not st.session_state.data_loaded:
    st.warning("Please run the main app file (Home.py) first to log in.")
    st.stop()

# Get data from session state
students = st.session_state.students
attendance = st.session_state.attendance
classes = st.session_state.classes
departments = st.session_state.departments
activities = st.session_state.activities
user_role = st.session_state.user_role
current_user_id = st.session_state.current_user_id
servants = st.session_state.servants

# --- PAGE TITLE ---
st.title("⚖️ Opportunity Roster")
st.markdown("A data-driven tool to help make fair selections for special activities.")
st.markdown("---")

# --- DATA PREPARATION ---
if 'activity_type' not in activities.columns:
    st.error("Database Error: The 'Activity' table is missing the required 'activity_type' column.")
    st.info("Please add this column in your Supabase dashboard and assign activities as 'Core' or 'Selective'.")
    st.stop()

attendance['attendance_date'] = pd.to_datetime(attendance['attendance_date'])
students_full_details = students.merge(classes, on='class_id').merge(departments, on='dep_id')

# --- ROLE-BASED FILTERING LOGIC ---
st.header("Select an Opportunity")
filter_container = st.container(border=True)

selected_department = None
selected_class = None

with filter_container:
    # --- For Admins (Priest, Chief Manager) ---
    if user_role in ['Priest', 'Chief Manager']:
        col1, col2 = st.columns(2)
        with col1:
            dept_list = ["-- Select a Department --"] + sorted(departments['dep_name'].unique().tolist())
            selected_department = st.selectbox("Department", dept_list)
        with col2:
            if selected_department and selected_department != "-- Select a Department --":
                dept_id = departments[departments['dep_name'] == selected_department]['dep_id'].iloc[0]
                available_classes = classes[classes['dep_id'] == dept_id]
                class_list = ["-- Select a Class --"] + sorted(available_classes['class_name'].unique().tolist())
            else:
                class_list = ["-- Select a Class --"]
            selected_class = st.selectbox("Class", class_list)

    # --- For Department Managers ---
    elif user_role == 'Department Manager':
        user_managed_dept = departments[departments['manager_id'] == current_user_id]
        if not user_managed_dept.empty:
            manager_dept_name = user_managed_dept['dep_name'].iloc[0]
            manager_dept_id = user_managed_dept['dep_id'].iloc[0]
            st.info(f"Showing data for your department: **{manager_dept_name}**")
            selected_department = manager_dept_name # Lock the department
            
            available_classes = classes[classes['dep_id'] == manager_dept_id]
            class_list = ["-- Select a Class --"] + sorted(available_classes['class_name'].unique().tolist())
            selected_class = st.selectbox("Select a Class from your department", class_list)
        else:
            st.warning("You are not assigned as a manager to any department.")

    # --- For Servants ---
    elif user_role == 'Servant':
        servant_info = servants[servants['servant_id'] == current_user_id]
        if not servant_info.empty and pd.notna(servant_info['class_id'].iloc[0]):
            servant_class_id = servant_info['class_id'].iloc[0]
            servant_class_info = classes[classes['class_id'] == servant_class_id]
            class_name = servant_class_info['class_name'].iloc[0]
            
            st.info(f"Showing roster for your assigned class: **{class_name}**")
            selected_class = class_name # Lock the class
        else:
            st.warning("You are not assigned to a class.")

    # --- Selective Activity Filter (Common to all roles) ---
    selective_activities = activities[activities['activity_type'] == 'Selective']
    if not selective_activities.empty:
        activity_list = ["-- Select an Opportunity --"] + sorted(selective_activities['activity_name'].unique().tolist())
        selected_activity = st.selectbox("Selective Activity", activity_list)
    else:
        st.warning("No 'Selective' activities found.")
        selected_activity = None


# --- ANALYSIS & DISPLAY ---
st.markdown("---")
# The logic now depends on having a valid class selected, regardless of role
if selected_class and selected_class not in ["-- Select a Class --"] and selected_activity and selected_activity != "-- Select an Opportunity --":
    st.header(f"Priority Roster for '{selected_activity}'")

    # The rest of the analysis code is unchanged because it correctly
    # uses the 'selected_class' variable, which is now set by our role-based logic.
    class_id = classes[classes['class_name'] == selected_class]['class_id'].iloc[0]
    students_in_class = students_full_details[students_full_details['class_id'] == class_id]
    selective_activity_ids = selective_activities['activity_id'].tolist()
    selective_attendance = attendance[attendance['activity_id'].isin(selective_activity_ids)]
    
    if selective_attendance.empty:
        st.info("There is no participation history for any selective activities yet. Therefore, all students are considered equally high priority.")
    
    last_participation = selective_attendance.groupby('student_id')['attendance_date'].max().reset_index()
    last_participation.rename(columns={'attendance_date': 'last_participation_date'}, inplace=True)

    roster_df = pd.merge(students_in_class, last_participation, on='student_id', how='left')
    roster_df = roster_df.sort_values(by='last_participation_date', ascending=True, na_position='first')

    roster_df['Last Participation Date'] = roster_df['last_participation_date'].dt.strftime('%Y-%m-%d').fillna('(Never Participated)')
    
    def get_priority(date_val):
        if pd.isna(date_val): return "🟢 High"
        days_since = (datetime.now() - date_val).days
        if days_since > 90: return "🟡 Medium"
        return "🔴 Low"
    roster_df['Priority'] = roster_df['last_participation_date'].apply(get_priority)

    display_df = roster_df[['student_name', 'Last Participation Date', 'Priority']]
    display_df.rename(columns={'student_name': 'Student Name'}, inplace=True)
    display_df.insert(0, 'Rank', range(1, len(display_df) + 1))
    
    st.dataframe(
        display_df.set_index('Rank'),
        use_container_width=True,
        column_config={
            "Priority": st.column_config.TextColumn(
                "Priority",
                help="🟢 High: Never participated. 🟡 Medium: Participated over 90 days ago. 🔴 Low: Participated recently."
            )
        }
    )
else:
    st.info("Please select all filters to generate the roster.")

