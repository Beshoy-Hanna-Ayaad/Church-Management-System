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

# --- PAGE TITLE ---
st.title("⚖️ Opportunity Roster")
st.markdown("A data-driven tool to help make fair selections for special activities.")
st.markdown("---")

# --- DATA PREPARATION ---
# Ensure your 'Activity' table has the 'activity_type' column for this to work.
if 'activity_type' not in activities.columns:
    st.error("Database Error: The 'Activity' table is missing the required 'activity_type' column.")
    st.info("Please add this column in your Supabase dashboard and assign activities as 'Core' or 'Selective'.")
    st.stop()

attendance['attendance_date'] = pd.to_datetime(attendance['attendance_date'])
students_full_details = students.merge(classes, on='class_id').merge(departments, on='dep_id')

# --- FILTERS ---
st.header("Select an Opportunity")
filter_container = st.container(border=True)
with filter_container:
    col1, col2 = st.columns(2)
    with col1:
        # 1. Department Filter
        dept_list = ["-- Select a Department --"] + sorted(departments['dep_name'].unique().tolist())
        selected_department = st.selectbox("Department", dept_list)
    with col2:
        # 2. Dependent Class Filter
        if selected_department != "-- Select a Department --":
            dept_id = departments[departments['dep_name'] == selected_department]['dep_id'].iloc[0]
            available_classes = classes[classes['dep_id'] == dept_id]
            class_list = ["-- Select a Class --"] + sorted(available_classes['class_name'].unique().tolist())
        else:
            class_list = ["-- Select a Class --"]
        selected_class = st.selectbox("Class", class_list)

    # 3. Selective Activity Filter
    selective_activities = activities[activities['activity_type'] == 'Selective']
    if not selective_activities.empty:
        activity_list = ["-- Select an Opportunity --"] + sorted(selective_activities['activity_name'].unique().tolist())
        selected_activity = st.selectbox("Selective Activity", activity_list)
    else:
        st.warning("No 'Selective' activities found. Please update the 'activity_type' in the Activity table.")
        selected_activity = "-- Select an Opportunity --"


# --- ANALYSIS & DISPLAY ---
st.markdown("---")
if selected_class != "-- Select a Class --" and selected_activity != "-- Select an Opportunity --":
    st.header(f"Priority Roster for '{selected_activity}'")

    # 1. Get the full list of students for the selected class
    class_id = classes[classes['class_name'] == selected_class]['class_id'].iloc[0]
    students_in_class = students_full_details[students_full_details['class_id'] == class_id]

    # 2. Get all attendance records for ALL selective activities
    selective_activity_ids = selective_activities['activity_id'].tolist()
    selective_attendance = attendance[attendance['activity_id'].isin(selective_activity_ids)]
    
    # 3. Find the last participation date for each student in ANY selective activity
    last_participation = selective_attendance.groupby('student_id')['attendance_date'].max().reset_index()
    last_participation.rename(columns={'attendance_date': 'last_participation_date'}, inplace=True)

    # 4. The crucial LEFT JOIN to include students who have never participated
    roster_df = pd.merge(
        students_in_class,
        last_participation,
        on='student_id',
        how='left'
    )
    
    # 5. The Multi-Level Sort for Prioritization
    # Level 1: Prioritize students with no participation date (NaT - Not a Time)
    # Level 2: For those who have participated, sort by the oldest date first
    roster_df = roster_df.sort_values(by='last_participation_date', ascending=True, na_position='first')

    # 6. Prepare the final display table
    roster_df['Last Participation Date'] = roster_df['last_participation_date'].dt.strftime('%Y-%m-%d').fillna('(Never Participated)')
    
    # Add a visual priority indicator
    def get_priority(date_val):
        if pd.isna(date_val):
            return "🟢 High"
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
    st.info("Please select a department, class, and a selective activity to generate the roster.")
