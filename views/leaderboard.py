import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# --- LOAD DATA FROM SESSION STATE ---
if 'data_loaded' not in st.session_state or not st.session_state.data_loaded:
    st.warning("Please run the main app file (Home.py) first to log in.")
    st.stop()

students = st.session_state.students
attendance = st.session_state.attendance
classes = st.session_state.classes
departments = st.session_state.departments

# --- PAGE TITLE ---
st.title("🏆 Student Leaderboard")
st.markdown("Discover the most active students based on their attendance within a specific period.")
st.markdown("---")

# --- DATA PREPARATION ---
# Ensure attendance dates are in datetime format
attendance['attendance_date'] = pd.to_datetime(attendance['attendance_date'])
students_full_details = students.merge(classes, on='class_id').merge(departments, on='dep_id')

# --- DYNAMIC FILTERS ---
st.header("Leaderboard Filters")

col1, col2 = st.columns(2)

with col1:
    # 1. Time Period Filter
    time_period = st.selectbox(
        "Select a Time Period:",
        options=["This Month", "Last 30 Days", "Last 90 Days", "All Time"],
        index=0
    )

with col2:
    # 2. Department Filter
    department_list = ["All Departments"] + sorted(departments['dep_name'].unique().tolist())
    selected_department = st.selectbox(
        "Filter by Department:",
        department_list
    )

# --- ANALYSIS & DISPLAY ---
st.markdown("---")
st.header(f"Results for: {time_period} | {selected_department}")

# --- Logic to filter data based on the selected time period ---
now = datetime.now()
if time_period == "This Month":
    cutoff_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    filtered_attendance = attendance[attendance['attendance_date'] >= cutoff_date]
elif time_period == "Last 30 Days":
    cutoff_date = now - timedelta(days=30)
    filtered_attendance = attendance[attendance['attendance_date'] >= cutoff_date]
elif time_period == "Last 90 Days":
    cutoff_date = now - timedelta(days=90)
    filtered_attendance = attendance[attendance['attendance_date'] >= cutoff_date]
else: # All Time
    filtered_attendance = attendance

# Filter by department if one is selected
if selected_department != "All Departments":
    dept_id = departments[departments['dep_name'] == selected_department]['dep_id'].iloc[0]
    student_ids_in_dept = students_full_details[students_full_details['dep_id'] == dept_id]['student_id'].tolist()
    filtered_attendance = filtered_attendance[filtered_attendance['student_id'].isin(student_ids_in_dept)]


if filtered_attendance.empty:
    st.warning("No attendance data found for the selected filters.")
else:
    # Calculate attendance counts on the filtered data
    attendance_counts = filtered_attendance.groupby('student_id').size().reset_index(name='total_attendance')
    
    # Merge with student details to get names and other info
    leaderboard_data = students_full_details.merge(attendance_counts, on='student_id')

    if leaderboard_data.empty:
        st.warning("No students with attendance found in the selected scope.")
    else:
        # Get the top 10 students
        top_10_students = leaderboard_data.sort_values(by='total_attendance', ascending=False).head(10)

        # --- Display as a formatted table ---
        st.subheader("Rankings")
        display_df = top_10_students[['student_name', 'class_name', 'total_attendance']].copy()
        display_df.rename(columns={
            'student_name': 'Student Name', 'class_name': 'Class', 'total_attendance': 'Total Attendance'
        }, inplace=True)
        display_df.insert(0, 'Rank', range(1, len(display_df) + 1))
        
        st.dataframe(display_df.set_index('Rank'), use_container_width=True)

        # --- Display as a bar chart ---
        st.subheader("Visual Comparison")
        fig = px.bar(
            top_10_students.sort_values(by='total_attendance', ascending=True),
            x='total_attendance', y='student_name', orientation='h',
            title=f"Top 10 Most Active Students",
            labels={'total_attendance': 'Total Attendance Count', 'student_name': 'Student'},
            template='plotly_white', text='total_attendance'
        )
        fig.update_traces(textposition='outside')
        fig.update_layout(yaxis_title="", showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
