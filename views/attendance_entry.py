import streamlit as st
import pandas as pd
from datetime import datetime

# --- LOAD DATA & AUTHENTICATION ---
if 'data_loaded' not in st.session_state or not st.session_state.data_loaded:
    st.warning("Please run the main app file (Home.py) first to log in.")
    st.stop()

# Get data from session state
supabase = st.session_state.supabase
user_role = st.session_state.user_role
current_user_id = st.session_state.current_user_id
servants = st.session_state.servants
students = st.session_state.students
activities = st.session_state.activities
classes = st.session_state.classes

# --- PAGE TITLE ---
st.title("📝 Attendance Entry")

# --- PERMISSION CHECK ---
if user_role not in ['Servant', 'Department Manager', 'Chief Manager', 'Priest']:
    st.error("You do not have permission to access this page.")
    st.stop()

# --- FORM LOGIC ---
servant_info = servants[servants['servant_id'] == current_user_id]
if servant_info.empty or pd.isna(servant_info['class_id'].iloc[0]):
    st.warning("You are not currently assigned to a class. Please contact an administrator.")
    st.stop()

user_class_id = servant_info['class_id'].iloc[0]
class_students_unmerged = students[students['class_id'] == user_class_id]
class_students = class_students_unmerged.merge(classes, on='class_id')

if class_students.empty:
    st.warning("There are no students assigned to your class.")
    st.stop()

# --- ATTENDANCE FORM (REFINED WITH CHECKBOXES) ---
st.info(f"You are taking attendance for **Class: {class_students['class_name'].iloc[0]}**. You have {len(class_students)} students.")
st.markdown("---")

# --- FIXED: ROBUST "Select All" LOGIC ---
# The toggle and its callback are now OUTSIDE the form.

# 1. Define the callback function. This runs whenever the toggle is clicked.
def update_all_checkboxes():
    # Get the new value of the toggle from session_state
    is_select_all_active = st.session_state.select_all_toggle
    # Update the session_state for each individual student checkbox
    for index, student in class_students.iterrows():
        st.session_state[f"student_{student['student_id']}"] = is_select_all_active

# 2. The master toggle is now placed before the form.
st.toggle(
    "Select All / Deselect All",
    value=True,
    key='select_all_toggle',
    on_change=update_all_checkboxes,
    help="Use this to quickly mark all students as present or absent."
)
# st.markdown("---")


with st.form("attendance_form"):
    col1, col2 = st.columns(2)
    with col1:
        activity_list = activities['activity_name'].tolist()
        selected_activity_name = st.selectbox("Select the Activity", options=activity_list)
    with col2:
        selected_date = st.date_input("Select the Date", value=datetime.now())

    st.markdown("---")
    st.subheader("Mark Student Presence")
    
    # Dictionary to hold the final state of each checkbox for submission
    attendance_status = {}
    
    # Display students in columns for a cleaner layout
    num_columns = 3
    cols = st.columns(num_columns)
    
    # Sort students alphabetically for consistency
    sorted_students = class_students.sort_values(by='student_name')

    for i, (index, student) in enumerate(sorted_students.iterrows()):
        student_key = f"student_{student['student_id']}"
        
        # 3. Initialize the state for each checkbox the first time the page loads
        if student_key not in st.session_state:
            st.session_state[student_key] = True # Default to selected
            
        with cols[i % num_columns]:
            # 4. The checkbox is now fully controlled by its key in session_state
            is_present = st.checkbox(
                student['student_name'],
                key=student_key
            )
            attendance_status[student['student_id']] = is_present

    submitted = st.form_submit_button("Submit Attendance")

# --- DATABASE INSERTION LOGIC (ADAPTED FOR CHECKBOXES) ---
if submitted:
    activity_id = activities[activities['activity_name'] == selected_activity_name]['activity_id'].iloc[0]
    
    # Get the list of student IDs for those who were marked as present
    present_student_ids = [student_id for student_id, present in attendance_status.items() if present]
    
    # Get the full details for the present students
    present_students_df = class_students[class_students['student_id'].isin(present_student_ids)]
    
    records_to_insert = []
    for index, student in present_students_df.iterrows():
        records_to_insert.append({
            'attendance_date': selected_date.strftime("%Y-%m-%d"),
            'student_id': int(student['student_id']),
            'activity_id': int(activity_id),
            'class_id': int(student['class_id']),
            'dep_id': int(student['dep_id']),
            'recorded_by_servant_id': int(current_user_id)
        })

    if records_to_insert:
        try:
            response = supabase.from_("Attendance").insert(records_to_insert).execute()
            if hasattr(response, 'error') and response.error:
                st.error(f"An error occurred: {response.error.message}")
            else:
                st.success(f"✅ Successfully recorded attendance for {len(records_to_insert)} students!")
                st.balloons()
        except Exception as e:
            st.error(f"A critical error occurred: {e}")
    else:
        st.warning("No students were selected as present. No attendance was recorded.")
