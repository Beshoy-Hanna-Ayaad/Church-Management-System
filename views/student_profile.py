import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- LOAD DATA FROM SESSION STATE ---
if 'data_loaded' not in st.session_state or not st.session_state.data_loaded:
    st.warning("Please run the main app file (Home.py) first to log in.")
    st.stop()

students = st.session_state.students
attendance = st.session_state.attendance
activities = st.session_state.activities
classes = st.session_state.classes
departments = st.session_state.departments
user_role = st.session_state.user_role
current_user_id = st.session_state.current_user_id
servants = st.session_state.servants

# --- PAGE TITLE ---
st.title("👤 Student Profile Viewer")
st.markdown("A detailed look at individual student engagement and attendance history.")
st.markdown("---")

# --- DATA PREPARATION & PERMISSIONS ---
# (This section is unchanged)
if not (students.empty or classes.empty or departments.empty):
    students_full_details = students.merge(classes, on='class_id').merge(departments, on='dep_id')
else:
    st.error("Missing core data (students, classes, or departments).")
    st.stop()
if user_role in ['Chief Manager', 'Priest']:
    visible_students = students_full_details
elif user_role == 'Department Manager':
    user_managed_dept = departments[departments['manager_id'] == current_user_id]
    if not user_managed_dept.empty:
        user_dept_id = user_managed_dept['dep_id'].iloc[0]
        visible_students = students_full_details[students_full_details['dep_id'] == user_dept_id]
    else: visible_students = pd.DataFrame()
elif user_role == 'Servant':
    servant_info = servants[servants['servant_id'] == current_user_id]
    if not servant_info.empty and pd.notna(servant_info['class_id'].iloc[0]):
        user_class_id = servant_info['class_id'].iloc[0]
        visible_students = students_full_details[students_full_details['class_id'] == user_class_id]
    else: visible_students = pd.DataFrame()
else: visible_students = pd.DataFrame()
if visible_students.empty:
    st.warning(f"As a **{user_role}**, you do not have any students assigned to your view.")
    st.stop()

# --- UNIFIED STUDENT SEARCH & SELECTION ---
st.header("Search for a Student")
student_list = ["-- Select a Student --"] + sorted(visible_students['student_name'].unique().tolist())
selected_student_name = st.selectbox(
    "Search and select a student:", student_list,
    help="Click the box and start typing to filter the list of students."
)

# --- PROFILE DISPLAY ---
if selected_student_name and selected_student_name != "-- Select a Student --":
    student_details = visible_students[visible_students['student_name'] == selected_student_name].iloc[0]
    student_id = student_details['student_id']

    st.markdown("---")
    st.header(f"Profile: {student_details['student_name']}")
    
    # Get all attendance data for the selected student
    student_attendance = attendance[attendance['student_id'] == student_id].copy()
    student_attendance['attendance_date'] = pd.to_datetime(student_attendance['attendance_date'])
    student_attendance_merged = student_attendance.merge(activities, on='activity_id')
    
    # --- AT-A-GLANCE SUMMARY SECTION ---
    st.subheader("At-a-Glance Summary")
    
    if student_attendance.empty:
        st.warning(f"{selected_student_name} has no recorded attendance.")
    else:
        summary_cols = st.columns(3)
        with summary_cols[0]:
            with st.container(border=True):
                st.metric("Total Attendance (All Time)", str(len(student_attendance)))
        with summary_cols[1]:
            with st.container(border=True):
                last_seen_date = student_attendance['attendance_date'].max().strftime('%Y-%m-%d')
                st.metric("Last Seen (Any Activity)", last_seen_date)
        with summary_cols[2]:
            with st.container(border=True):
                favorite_activity = student_attendance_merged['activity_name'].mode().iloc[0]
                st.metric("Favorite Activity", favorite_activity)

        # --- CORE ACTIVITY ENGAGEMENT ---
        st.subheader("Core Activity Engagement")
        
        core_activities = ['Sunday Meeting', 'Quddas (Liturgy)']
        core_activity_cols = st.columns(len(core_activities))
        
        for i, activity_name in enumerate(core_activities):
            with core_activity_cols[i]:
                with st.container(border=True):
                    activity_attendance = student_attendance_merged[student_attendance_merged['activity_name'] == activity_name]
                    if not activity_attendance.empty:
                        last_seen = activity_attendance['attendance_date'].max()
                        days_since_seen = (datetime.now() - last_seen).days
                        st.metric(label=f"Last Seen: {activity_name}", value=last_seen.strftime('%Y-%m-%d'), delta=f"{days_since_seen} days ago", delta_color="off")
                    else:
                        st.metric(label=f"Last Seen: {activity_name}", value="Never Attended", delta=" ", delta_color="off")
        
        # --- ENGAGEMENT TREND OVER TIME (FIXED FOR ZERO ATTENDANCE) ---
        st.subheader("Engagement Trend Over Time")
        with st.container(border=True):
            student_attendance_merged['month_year'] = student_attendance_merged['attendance_date'].dt.strftime('%Y-%B')
            
            # --- NEW LOGIC TO HANDLE ZEROS ---
            # 1. Create a complete timeline of all months for this student
            min_date = student_attendance_merged['attendance_date'].min()
            max_date = datetime.now()
            all_months_range = pd.date_range(start=min_date, end=max_date, freq='MS').strftime('%Y-%B').tolist()
            
            # 2. Get all activities the student has ever attended
            all_student_activities = student_attendance_merged['activity_name'].unique().tolist()
            
            # 3. Create a "scaffold" DataFrame with all possible month/activity combinations
            scaffold = pd.MultiIndex.from_product([all_months_range, all_student_activities], names=['month_year', 'activity_name']).to_frame(index=False)
            
            # 4. Aggregate the actual attendance data
            trend_data_actual = student_attendance_merged.groupby(['month_year', 'activity_name']).size().reset_index(name='monthly_count')
            
            # 5. Merge the scaffold with the actual data (LEFT JOIN)
            trend_data_complete = pd.merge(scaffold, trend_data_actual, on=['month_year', 'activity_name'], how='left')
            
            # 6. Fill missing values (where the student didn't attend) with 0
            trend_data_complete['monthly_count'] = trend_data_complete['monthly_count'].fillna(0).astype(int)
            
            # 7. Sort correctly for the chart
            trend_data_complete['month_datetime'] = pd.to_datetime(trend_data_complete['month_year'], format='%Y-%B')
            trend_data_complete = trend_data_complete.sort_values('month_datetime')
            sorted_month_names = trend_data_complete['month_year'].unique().tolist()
            # --- END OF NEW LOGIC ---

            if trend_data_complete.empty:
                st.info("Not enough data to display a trend.")
            else:
                fig_trend = px.line(
                    trend_data_complete, # Use the new complete DataFrame
                    x='month_year',
                    y='monthly_count',
                    color='activity_name',
                    markers=True,
                    title=f"Monthly Attendance by Activity for {selected_student_name}",
                    category_orders={"month_year": sorted_month_names}
                )
                fig_trend.update_layout(
                    xaxis_title="Month",
                    yaxis_title="Monthly Attendance Count",
                    legend_title="Activity"
                )
                
                st.plotly_chart(fig_trend, use_container_width=True)


    st.markdown("---")
    
    # --- DETAILED BREAKDOWN (Existing Filters and Charts) ---
    if not student_attendance.empty:
        if 'month_year' not in student_attendance_merged.columns:
            student_attendance_merged['month_year'] = student_attendance_merged['attendance_date'].dt.strftime('%Y-%B')

        st.header("Detailed Breakdown by Period")
        filter_container = st.container(border=True)
        with filter_container:
            col_filter1, col_filter2 = st.columns(2)
            with col_filter1:
                available_months = sorted(student_attendance_merged['month_year'].unique(), key=lambda m: pd.to_datetime(m, format='%Y-%B'), reverse=True)
                selected_months = st.multiselect("Filter by Month(s):", options=available_months, default=available_months, key=f"month_filter_{student_id}")
            with col_filter2:
                attended_activities = student_attendance_merged['activity_name'].unique().tolist()
                selected_activities = st.multiselect("Filter by Activity:", options=attended_activities, default=attended_activities, key=f"activity_filter_{student_id}")
        
        filtered_attendance = student_attendance_merged
        if selected_months: filtered_attendance = filtered_attendance[filtered_attendance['month_year'].isin(selected_months)]
        if selected_activities: filtered_attendance = filtered_attendance[filtered_attendance['activity_name'].isin(selected_activities)]
        else: filtered_attendance = pd.DataFrame(columns=student_attendance_merged.columns)
            
        st.subheader("Filtered Results")
        if filtered_attendance.empty:
            st.warning("No attendance records match the current filter settings.")
        else:
            st.metric("Total Attendance (in filtered period)", str(len(filtered_attendance)))
            col_a, col_b = st.columns(2)
            with col_a:
                st.subheader("Activity Participation")
                activity_counts = filtered_attendance['activity_name'].value_counts().reset_index()
                activity_counts.columns = ['Activity', 'Count']
                fig = px.bar(activity_counts, x='Activity', y='Count', title=f"Activities Attended by {selected_student_name}", template='plotly_white', color='Activity')
                st.plotly_chart(fig, use_container_width=True)
            with col_b:
                st.subheader("Attendance History")
                history_df = filtered_attendance[['attendance_date', 'activity_name']].sort_values(by='attendance_date', ascending=False)
                st.dataframe(history_df, use_container_width=True)
