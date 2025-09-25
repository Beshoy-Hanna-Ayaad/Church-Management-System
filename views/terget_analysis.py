import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- LOAD DATA & AUTHENTICATION ---
if 'data_loaded' not in st.session_state or not st.session_state.data_loaded:
    st.warning("Please run the main app file (Home.py) first to log in.")
    st.stop()

# Get data from session state
students = st.session_state.students
attendance = st.session_state.attendance
classes = st.session_state.classes
departments = st.session_state.departments
user_role = st.session_state.user_role # Get the current user's role
activities = st.session_state.activities

# --- PAGE TITLE ---
st.title("🎯 Target Achievement Analysis")
st.markdown("Track student participation against dynamically set, activity-specific monthly targets.")
st.markdown("---")

# --- DATA PREPARATION ---
attendance['attendance_date'] = pd.to_datetime(attendance['attendance_date'])
attendance['month_year'] = attendance['attendance_date'].dt.strftime('%Y-%B')
students_full_details = students.merge(classes, on='class_id').merge(departments, on='dep_id')

# --- FILTERS (UNCHANGED) ---
st.header("Select a Group to Analyze")
filter_container = st.container(border=True)
with filter_container:
    col1, col2 = st.columns(2)
    with col1:
        dept_list = ["-- Select a Department --"] + sorted(departments['dep_name'].unique().tolist())
        selected_department = st.selectbox("Department", dept_list)
    with col2:
        if selected_department != "-- Select a Department --":
            dept_id = departments[departments['dep_name'] == selected_department]['dep_id'].iloc[0]
            available_classes = classes[classes['dep_id'] == dept_id]
            class_list = ["-- Select a Class --"] + sorted(available_classes['class_name'].unique().tolist())
        else:
            class_list = ["-- Select a Class --"]
        selected_class = st.selectbox("Class", class_list)

    month_list = ["-- Select a Month --"] + sorted(attendance['month_year'].unique(), key=lambda m: pd.to_datetime(m, format='%Y-%B'), reverse=True)
    selected_month = st.selectbox("Month", month_list)

# --- DYNAMIC TARGET SETTER (NEW & IMPROVED) ---
st.markdown("---")
st.header("Define Monthly Targets")
target_container = st.container(border=True)

with target_container:
    # Initialize the dictionary of targets in session_state if it doesn't exist
    if 'activity_targets' not in st.session_state:
        st.session_state.activity_targets = {activity: 1 for activity in activities['activity_name']}

    if user_role == 'Priest':
        st.info("As a Priest, you can set the minimum required attendance for each activity this month.")
        # Use more columns for better layout if there are many activities
        num_target_cols = min(len(activities), 4)
        target_cols = st.columns(num_target_cols)
        
        activity_names = activities['activity_name'].tolist()
        for i, activity_name in enumerate(activity_names):
            with target_cols[i % num_target_cols]:
                target_count = st.number_input(
                    label=activity_name,
                    min_value=0, step=1,
                    value=st.session_state.activity_targets.get(activity_name, 1),
                    key=f"target_{activity_name}"
                )
                st.session_state.activity_targets[activity_name] = target_count
    else:
        st.info("The following targets, set by a Priest, are being used for this analysis:")
        active_targets = {k: v for k, v in st.session_state.activity_targets.items() if v > 0}
        if not active_targets:
            st.write("No specific targets are set for this month.")
        else:
            target_summary = " | ".join([f"**{activity}**: ≥{count}" for activity, count in active_targets.items()])
            st.markdown(target_summary)

# --- ANALYSIS & VISUALIZATION ---
st.markdown("---")
if selected_class != "-- Select a Class --" and selected_month != "-- Select a Month --":
    st.header(f"Results for {selected_class} in {selected_month}")

    # 1. Calculate the TOTAL target by summing the individual activity targets
    total_monthly_target = sum(st.session_state.activity_targets.values())

    if total_monthly_target == 0:
        st.warning("No targets have been set. Please ask a Priest to set at least one activity target above.")
    else:
        st.info(f"The combined target for this month is **{total_monthly_target}** total attendances.")
        
        # 2. Isolate the data
        class_id = classes[classes['class_name'] == selected_class]['class_id'].iloc[0]
        students_in_class = students_full_details[students_full_details['class_id'] == class_id]
        month_attendance = attendance[attendance['month_year'] == selected_month]
        
        if students_in_class.empty:
            st.warning("This class has no students.")
        else:
            num_columns = 4; cols = st.columns(num_columns)
            # 3. Loop through each student
            for i, (idx, student) in enumerate(students_in_class.iterrows()):
                student_id, student_name = student['student_id'], student['student_name']
                
                # 4. Calculate their TOTAL attendance count for the month
                student_month_attendance = month_attendance[month_attendance['student_id'] == student_id]
                total_attendance_count = len(student_month_attendance)
                
                # Dynamic Color Logic
                if total_attendance_count >= total_monthly_target: bar_color = "green"
                elif total_attendance_count >= total_monthly_target * 0.5: bar_color = "orange"
                else: bar_color = "red"

                # --- 5. THE FINAL GAUGE CHART ---
                fig = go.Figure(go.Indicator(
                    mode="gauge+number+delta",
                    value=total_attendance_count,
                    title={'text': student_name, 'font': {'size': 16}},
                    number={'suffix': " Attendances"},
                    delta={'reference': total_monthly_target, 'increasing': {'color': "green"}, 'decreasing': {'color': "red"}},
                    gauge={
                        'axis': {'range': [None, max(total_monthly_target, total_attendance_count) * 1.2]}, # Dynamic axis
                        'bar': {'color': bar_color},
                        'threshold': {
                            'line': {'color': "black", 'width': 4}, 
                            'thickness': 0.9, 
                            'value': total_monthly_target
                        }
                    }
                ))
                fig.update_layout(height=250, margin=dict(l=10, r=10, t=40, b=10))
                with cols[i % num_columns]:
                    with st.container(border=True):
                        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Please select a department, class, and month to see the target analysis.")
