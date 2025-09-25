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
user_role = st.session_state.user_role
activities = st.session_state.activities

# --- PAGE TITLE ---
st.title("⚠️ Students at Risk Analysis")
st.markdown("Identify students who have been absent from core activities for a defined period.")
st.markdown("---")

# --- DATA PREPARATION ---
attendance['attendance_date'] = pd.to_datetime(attendance['attendance_date'])
students_full_details = students.merge(classes, on='class_id').merge(departments, on='dep_id')

# --- DYNAMIC RISK THRESHOLD BUILDER ---
st.header("Define Risk Thresholds")

# For this analysis, we will focus on a few user-defined core activities.
CORE_ACTIVITIES = ['Sunday Meeting', 'Quddas (Liturgy)']

# Initialize thresholds in session state if they don't exist
if 'risk_thresholds' not in st.session_state:
    st.session_state.risk_thresholds = {
        'Sunday Meeting': 30,
        'Quddas (Liturgy)': 45
    }

# Display the interactive editor only to Priests
if user_role == 'Priest':
    st.info("As a Priest, you can set the number of days of absence that flags a student as 'at-risk' for each core activity.")
    threshold_cols = st.columns(len(CORE_ACTIVITIES))
    for i, activity_name in enumerate(CORE_ACTIVITIES):
        with threshold_cols[i]:
            # MODIFIED: Changed from st.slider to st.number_input for easier entry
            days = st.number_input(
                f"'{activity_name}' Risk Threshold (days)",
                min_value=1, max_value=365, step=1,
                value=st.session_state.risk_thresholds.get(activity_name, 30),
                key=f"threshold_{activity_name}"
            )
            st.session_state.risk_thresholds[activity_name] = days
else:
    # Other roles see a read-only view
    st.info("The following risk thresholds, set by a Priest, are being used for this analysis:")
    with st.container(border=True):
        for activity, days in st.session_state.risk_thresholds.items():
            st.markdown(f"- **{activity}:** Flagged after **{days} days** of absence.")


# # --- DEPARTMENT FILTER ---
# st.markdown("---")
# st.header("Filter by Department")
department_list = ["All Departments"] + sorted(departments['dep_name'].unique().tolist())
selected_department = st.selectbox("Select a Department to analyze:", department_list)

# --- ANALYSIS & DISPLAY ---
st.markdown("---")
st.header("Analysis Results")

# Filter data based on selected department
if selected_department != "All Departments":
    dept_id = departments[departments['dep_name'] == selected_department]['dep_id'].iloc[0]
    department_students = students_full_details[students_full_details['dep_id'] == dept_id]
    department_attendance = attendance[attendance['student_id'].isin(department_students['student_id'].tolist())]
else:
    department_students = students_full_details
    department_attendance = attendance

at_risk_students = []

# --- REFINED AND MORE ROBUST LOGIC ---

# 1. Find the last attendance date for every student FOR EACH activity they have attended
last_seen_by_activity = department_attendance.groupby(['student_id', 'activity_id'])['attendance_date'].max().reset_index()
last_seen_by_activity = last_seen_by_activity.merge(activities, on='activity_id')


# 2. Loop through the dynamically set risk rules
for activity_name, threshold_days in st.session_state.risk_thresholds.items():
    
    # Isolate the data for the current activity rule
    activity_specific_last_seen = last_seen_by_activity[
        last_seen_by_activity['activity_name'] == activity_name
    ]

    # --- FIXED: LOGIC TO FIND STUDENTS WHO HAVE NEVER ATTENDED ---
    # a. Get all student IDs in the current department filter
    all_student_ids_in_scope = set(department_students['student_id'])
    
    # b. Get student IDs who have attended this activity at least once
    attended_student_ids = set(activity_specific_last_seen['student_id'])
    
    # c. Find the difference to get those who never attended
    never_attended_ids = all_student_ids_in_scope - attended_student_ids

    # d. Add these students to the at-risk list
    for student_id in never_attended_ids:
        at_risk_students.append({
            'student_id': student_id,
            'reason': f"Never attended '{activity_name}'"
        })
    # --- END OF FIX ---

    # --- Original logic for students who HAVE attended ---
    # Calculate how many days have passed since each student's last attendance
    activity_specific_last_seen['days_since_seen'] = (datetime.now() - activity_specific_last_seen['attendance_date']).dt.days

    # Find students who have breached the threshold for THIS activity
    breached_students = activity_specific_last_seen[
        activity_specific_last_seen['days_since_seen'] > threshold_days
    ]

    # Add them to our master list of at-risk students
    for index, row in breached_students.iterrows():
        at_risk_students.append({
            'student_id': row['student_id'],
            'reason': f"Absent from '{activity_name}' for {row['days_since_seen']} days (>{threshold_days} day threshold)"
        })

# --- DISPLAY RESULTS (Works with the new, more complete data) ---
if not at_risk_students:
    st.success("✅ No students were flagged as at-risk based on the current parameters.")
else:
    risk_df = pd.DataFrame(at_risk_students)
    risk_df = risk_df.merge(students_full_details, on='student_id')
    
    st.warning(f"Found {risk_df['student_id'].nunique()} students who may need follow-up.")

    display_df = risk_df.groupby('student_id').agg({
        'student_name': 'first',
        'class_name': 'first',
        'dep_name': 'first',
        'reason': lambda x: '; '.join(list(set(x))) # Use set to avoid duplicates
    }).reset_index()

    st.dataframe(
        display_df[['student_name', 'class_name', 'dep_name', 'reason']],
        use_container_width=True, hide_index=True,
        column_config={
            "student_name": "Student Name",
            "class_name": "Class",
            "dep_name": "Department",
            "reason": "Reason Flagged"
        }
    )

