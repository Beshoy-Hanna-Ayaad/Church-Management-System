import streamlit as st
import pandas as pd
import plotly.express as px

# --- LOAD DATA FROM SESSION STATE ---
if 'data_loaded' not in st.session_state or not st.session_state.data_loaded:
    st.warning("Please run the main app file (Home.py) first to log in.")
    st.stop()

attendance = st.session_state.attendance
activities = st.session_state.activities
departments = st.session_state.departments
classes = st.session_state.classes
students = st.session_state.students

# --- PAGE TITLE ---
st.title("📈 Attendance Analysis")
st.markdown("---")

# --- DATA PREPARATION ---
if not attendance.empty:
    attendance['attendance_date'] = pd.to_datetime(attendance['attendance_date'])
    attendance['month_year'] = attendance['attendance_date'].dt.strftime('%Y-%B')
    attendance_merged = attendance.merge(activities, on='activity_id') \
                                  .merge(classes.drop(columns=['dep_id']), on='class_id') \
                                  .merge(departments, on='dep_id') \
                                  .merge(students, on='student_id') # Added students for name
else:
    st.error("No attendance data found in the database.")
    st.stop()

# --- SECTION 1: COMPARATIVE ANALYSIS (Unchanged) ---
st.header("📊 Comparative Analysis (Snapshot in Time)")
st.markdown("Compare attendance between classes for a specific activity and month.")
# ... (The existing bar chart code goes here)
filter_container = st.container(border=True)
with filter_container:
    col1, col2 = st.columns(2)
    with col1:
        dept_list = ["-- Select a Department --"] + sorted(departments['dep_name'].unique().tolist())
        selected_department = st.selectbox("Department", dept_list, key="bar_dept")
    with col2:
        activity_list = ["-- Select an Activity --"] + sorted(activities['activity_name'].unique().tolist())
        selected_activity = st.selectbox("Activity", activity_list, key="bar_activity")
    col3, col4 = st.columns(2)
    with col3:
        if selected_department != "-- Select a Department --":
            dept_id = departments[departments['dep_name'] == selected_department]['dep_id'].iloc[0]
            available_classes = classes[classes['dep_id'] == dept_id]
            class_list_options = sorted(available_classes['class_name'].unique().tolist())
            selected_classes = st.multiselect("Select Classes to Compare", options=class_list_options, default=class_list_options, key="bar_classes")
        else:
            selected_classes = st.multiselect("Select Classes to Compare", options=[], disabled=True, key="bar_classes")
    with col4:
        month_list = ["-- Select a Month --"] + sorted(attendance['month_year'].unique(), key=lambda m: pd.to_datetime(m, format='%Y-%B'), reverse=True)
        selected_month = st.selectbox("Month", month_list, key="bar_month")
if selected_department != "-- Select a Department --" and selected_activity != "-- Select an Activity --" and selected_month != "-- Select a Month --":
    if not selected_classes: st.warning("Please select at least one class to compare.")
    else:
        filtered_df = attendance_merged[(attendance_merged['dep_name'] == selected_department) & (attendance_merged['activity_name'] == selected_activity) & (attendance_merged['month_year'] == selected_month) & (attendance_merged['class_name'].isin(selected_classes))]
        if filtered_df.empty: st.warning("No attendance records found for the selected criteria.")
        else:
            class_attendance_counts = filtered_df['class_name'].value_counts().reset_index(); class_attendance_counts.columns = ['Class', 'Total Attendance']
            students_per_class = students.merge(classes, on='class_id')['class_name'].value_counts().reset_index(); students_per_class.columns = ['Class', 'Total Students']
            final_counts = class_attendance_counts.merge(students_per_class, on='Class')
            final_counts['Participation (%)'] = round((final_counts['Total Attendance'] / final_counts['Total Students']) * 100, 1)
            final_counts['Chart Text'] = final_counts.apply(lambda row: f"{row['Total Attendance']} / {row['Total Students']} ({row['Participation (%)']:.0f}%)", axis=1)
            fig = px.bar(final_counts, x='Class', y='Total Attendance', title=f"Attendance for '{selected_activity}' in {selected_month}", text='Chart Text', template='plotly_white', color='Class')
            fig.update_traces(textposition='outside'); max_val = final_counts['Total Attendance'].max()
            fig.update_layout(showlegend=False, yaxis_range=[0, max_val * 1.25], xaxis_title=None, yaxis_title="Total Attendance Count"); st.plotly_chart(fig, use_container_width=True)
else: st.info("Please select a department, activity, and month to see the comparison.")

# --- SECTION 2: TREND ANALYSIS (Unchanged) ---
st.markdown("---")
st.header("📉 Trend Analysis Over Time")
# ... (The trend analysis code goes here)
st.markdown("See how class attendance has trended and ranked over several months for a specific activity.")
trend_container = st.container(border=True)
with trend_container:
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        trend_dept_list = ["-- Select a Department --"] + sorted(departments['dep_name'].unique().tolist())
        trend_selected_dept = st.selectbox("Select a Department", trend_dept_list, key="trend_dept")
    with col_t2:
        trend_activity_list = ["-- Select an Activity --"] + sorted(activities['activity_name'].unique().tolist())
        trend_selected_activity = st.selectbox("Select an Activity", trend_activity_list, key="trend_activity")
    if trend_selected_dept != "-- Select a Department --" and trend_selected_activity != "-- Select an Activity --":
        trend_filtered_df = attendance_merged[(attendance_merged['dep_name'] == trend_selected_dept) & (attendance_merged['activity_name'] == trend_selected_activity)]
        if trend_filtered_df.empty: st.warning("No attendance data for the selected filters.")
        else:
            trend_counts = trend_filtered_df.groupby(['month_year', 'class_name']).size().reset_index(name='attendance_count')
            trend_counts['month_datetime'] = pd.to_datetime(trend_counts['month_year'], format='%Y-%B'); trend_counts = trend_counts.sort_values('month_datetime')
            tab1, tab2 = st.tabs(["📈 Line Chart (Trend)", "🏆 Bar Chart Race (Ranking)"])
            with tab1:
                fig_trend = px.line(trend_counts, x='month_year', y='attendance_count', color='class_name', markers=True, title=f'Monthly Trend for "{trend_selected_activity}"')
                fig_trend.update_layout(xaxis_title="Month", yaxis_title="Total Attendance Count", legend_title="Class"); st.plotly_chart(fig_trend, use_container_width=True)
            with tab2:
                st.info("Click the Play button to see how class rankings change over time.")
                fig_race = px.bar(trend_counts, x="attendance_count", y="class_name", color="class_name", orientation='h', animation_frame="month_year", animation_group="class_name", text="attendance_count", title=f'Monthly Ranking for "{trend_selected_activity}"')
                max_range = trend_counts['attendance_count'].max() * 1.1; fig_race.update_layout(xaxis_range=[0, max_range], showlegend=False, yaxis_title=None); fig_race.update_yaxes(categoryorder="total ascending")
                fig_race.layout.updatemenus[0].buttons[0].args[1]['frame']['duration'] = 1200; fig_race.layout.updatemenus[0].buttons[0].args[1]['transition']['duration'] = 500
                st.plotly_chart(fig_race, use_container_width=True)


# --- SECTION 3: STUDENT-LEVEL ANALYSIS (REFINED) ---
st.markdown("---")
st.header("👤 Student-Level Performance")
st.markdown("Analyze the attendance of each student within a class for a specific activity and month.")
student_container = st.container(border=True)

with student_container:
    # Four filters as requested
    scol1, scol2 = st.columns(2)
    with scol1:
        s_dept_list = ["-- Select a Department --"] + sorted(departments['dep_name'].unique().tolist())
        s_selected_dept = st.selectbox("Department", s_dept_list, key="student_dept")
    with scol2:
        if s_selected_dept != "-- Select a Department --":
            s_dept_id = departments[departments['dep_name'] == s_selected_dept]['dep_id'].iloc[0]
            s_available_classes = classes[classes['dep_id'] == s_dept_id]
            s_class_list = ["-- Select a Class --"] + sorted(s_available_classes['class_name'].unique().tolist())
        else:
            s_class_list = ["-- Select Department First --"]
        s_selected_class = st.selectbox("Class", s_class_list, key="student_class")

    scol3, scol4 = st.columns(2)
    with scol3:
        s_month_list = ["-- Select a Month --"] + sorted(attendance['month_year'].unique(), key=lambda m: pd.to_datetime(m, format='%Y-%B'), reverse=True)
        s_selected_month = st.selectbox("Month", s_month_list, key="student_month")
    with scol4:
        s_activity_list = ["-- Select an Activity --"] + sorted(activities['activity_name'].unique().tolist())
        s_selected_activity = st.selectbox("Activity", s_activity_list, key="student_activity")

    # --- FIXED: More robust check to prevent running with placeholder values ---
    # This condition now ensures every filter has a real, non-placeholder selection.
    is_ready_to_run = (
        s_selected_dept != "-- Select a Department --" and
        s_selected_class not in ["-- Select a Class --", "-- Select Department First --"] and
        s_selected_month != "-- Select a Month --" and
        s_selected_activity != "-- Select an Activity --"
    )

    if is_ready_to_run:
        
        # 1. Get the full list of students for the selected class
        class_id_filter = classes[classes['class_name'] == s_selected_class]['class_id'].iloc[0]
        all_students_in_class = students[students['class_id'] == class_id_filter][['student_id', 'student_name']]

        # 2. Filter attendance data to the specific context (month, class, activity)
        filtered_attendance = attendance_merged[
            (attendance_merged['class_name'] == s_selected_class) &
            (attendance_merged['month_year'] == s_selected_month) &
            (attendance_merged['activity_name'] == s_selected_activity)
        ]

        # 3. Count attendance for students who were present
        student_attendance_counts = filtered_attendance['student_name'].value_counts().reset_index()
        student_attendance_counts.columns = ['student_name', 'Attendance Count']

        # 4. Merge the full student list with their attendance counts (LEFT JOIN)
        final_student_data = pd.merge(
            all_students_in_class,
            student_attendance_counts,
            on='student_name',
            how='left'
        )
        # Fill NaN with 0 for students who didn't attend at all
        final_student_data['Attendance Count'] = final_student_data['Attendance Count'].fillna(0).astype(int)

        # Sort for ranking
        final_student_data = final_student_data.sort_values(by='Attendance Count', ascending=False)
        
        # --- REFINED: Create the horizontal bar chart ---
        
        # Calculate a dynamic height for the chart to ensure readability
        num_students = len(final_student_data)
        chart_height = max(400, num_students * 35) # Base height of 400px, plus 35px per student
        
        fig_student_level = px.bar(
            final_student_data,
            x='Attendance Count',
            y='student_name',
            orientation='h',
            title=f"Student Attendance for '{s_selected_activity}'",
            text='Attendance Count', # Show only the raw count
            template='plotly_white',
            height=chart_height # Use the new dynamic height
        )
        fig_student_level.update_traces(textposition='outside')
        fig_student_level.update_layout(
            yaxis_title=None,
            xaxis_title="Number of Times Attended",
            yaxis={'categoryorder':'total ascending'}
        )
        st.plotly_chart(fig_student_level, use_container_width=True)

    else:
        st.info("Please select a department, class, month, and activity to see the student-level breakdown.")
