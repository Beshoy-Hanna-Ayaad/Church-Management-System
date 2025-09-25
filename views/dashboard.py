import streamlit as st
import pandas as pd
import plotly.express as px

st.title('🏠 Leadership Dashboard')
st.markdown("----")


# --- LOAD DATA FROM SESSION STATE ---
if 'data_loaded' not in st.session_state or not st.session_state.data_loaded:
    st.warning("Please run the main app file (Home.py) first to load data.")
    st.stop()

departments = st.session_state.departments
servants = st.session_state.servants
classes = st.session_state.classes
students = st.session_state.students
activities = st.session_state.activities


# --- KPI CARDS (Unchanged) ---
st.subheader("Key Performance Indicators")
col1, col2, col3, col4, col5 = st.columns(5) 
with col1:
    cont = st.container(border=True)
    total_deps = len(departments) if not departments.empty else 0
    cont.metric("Total Departments", total_deps)
with col2:
    cont = st.container(border=True)
    total_classes = len(classes) if not classes.empty else 0
    cont.metric("Total Classes", total_classes)
with col3:
    cont = st.container(border=True)
    total_servants = len(servants) if not servants.empty else 0
    cont.metric("Total Servants", total_servants)
with col4:
    cont = st.container(border=True)
    total_students = len(students) if not students.empty else 0
    cont.metric("Total Students", total_students)
with col5:
    cont = st.container(border=True)
    total_activities = len(activities) if not activities.empty else 0
    cont.metric("Total Activities", total_activities)


st.markdown("----")

# --- OVERALL DISTRIBUTION CHARTS (Unchanged) ---
st.subheader("Overall Distribution Across All Departments")
col_a, col_b = st.columns(2)

with col_a:
    with st.container(border=True):
        st.markdown("###### Student Distribution")
        if not students.empty and not classes.empty and not departments.empty:
            students_merged = students.merge(classes, on='class_id').merge(departments, on='dep_id')
            student_counts = students_merged['dep_name'].value_counts().reset_index()
            student_counts.columns = ['Department', 'Number of Students']
            fig_students = px.bar(
                student_counts, x='Number of Students', y='Department', orientation='h',
                title='Students per Department', text='Number of Students', template='plotly_white'
            )
            fig_students.update_traces(textposition='outside')
            fig_students.update_layout(showlegend=False, yaxis_title=None)
            st.plotly_chart(fig_students, use_container_width=True)
        else:
            st.warning("Insufficient data for student distribution.")

with col_b:
    with st.container(border=True):
        st.markdown("###### Servant Distribution")
        if not servants.empty and not classes.empty and not departments.empty:
            servants_merged = servants.dropna(subset=['class_id']).merge(classes, on='class_id').merge(departments, on='dep_id')
            servant_counts = servants_merged['dep_name'].value_counts().reset_index()
            servant_counts.columns = ['Department', 'Number of Servants']
            fig_servants = px.bar(
                servant_counts, x='Number of Servants', y='Department', orientation='h',
                title='Servants per Department', text='Number of Servants', template='plotly_white'
            )
            fig_servants.update_traces(textposition='outside')
            fig_servants.update_layout(showlegend=False, yaxis_title=None)
            st.plotly_chart(fig_servants, use_container_width=True)
        else:
            st.warning("Insufficient data for servant distribution.")


st.markdown("----")

# --- REFINED: DETAILED DISTRIBUTION ANALYSIS (CHART) ---
st.subheader("Detailed Distribution by Class")
cont = st.container(border=True)

with cont:
    col1, col2 = st.columns(2)
    
    with col1:
        dep_names = ["-- Select Department --"] + sorted(departments['dep_name'].unique().tolist())
        selected_dep_chart = st.selectbox("Select a Department to Visualize", dep_names, key="chart_dep")

    with col2:
        person_type_chart = st.radio("Show distribution for:", ["Students", "Servants"], key="chart_person", horizontal=True)

    if selected_dep_chart != "-- Select Department --":
        if person_type_chart == "Students":
            source_df = students.merge(classes, on='class_id').merge(departments, on='dep_id')
            count_col_name, grouping_col = "Number of Students", 'class_name'
        else: # Servants
            source_df = servants.dropna(subset=['class_id']).merge(classes, on='class_id').merge(departments, on='dep_id')
            count_col_name, grouping_col = "Number of Servants", 'class_name'

        filtered_df = source_df[source_df['dep_name'] == selected_dep_chart]
        
        if not filtered_df.empty:
            counts = filtered_df[grouping_col].value_counts().reset_index()
            counts.columns = [grouping_col, count_col_name]
            
            fig = px.bar(
                counts, x=count_col_name, y=grouping_col, orientation='h',
                title=f'{person_type_chart} Distribution in {selected_dep_chart}',
                text=count_col_name, template='plotly_white'
            )
            fig.update_traces(textposition='outside')
            fig.update_layout(yaxis_title="Classes", showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No data found for the selected filters.")
    else:
        st.info("Please select a department to see the class-level distribution.")

st.markdown("----")

# --- NEW: DETAILED ROSTER VIEW (LIST) ---
st.subheader("Detailed Roster View")
cont_roster = st.container(border=True)
with cont_roster:
    col_r1, col_r2, col_r3 = st.columns(3)

    with col_r1:
        selected_dep_roster = st.selectbox("Select a Department", dep_names, key="roster_dep")
    
    with col_r2:
        if selected_dep_roster != "-- Select Department --":
            dept_id = departments[departments['dep_name'] == selected_dep_roster]['dep_id'].iloc[0]
            available_classes = classes[classes['dep_id'] == dept_id]
            class_names = ["-- All Classes --"] + sorted(available_classes['class_name'].unique().tolist())
        else:
            class_names = ["-- Select Department First --"]
        selected_class_roster = st.selectbox("Select a Class (optional)", class_names, key="roster_class")

    with col_r3:
        person_type_roster = st.radio("Show list of:", ["Students", "Servants"], key="roster_person", horizontal=True)

    if selected_dep_roster != "-- Select Department --":
        if person_type_roster == "Students":
            roster_source_df = students.merge(classes, on='class_id').merge(departments, on='dep_id')
            name_col = 'student_name'
        else: # Servants
            roster_source_df = servants.dropna(subset=['class_id']).merge(classes, on='class_id').merge(departments, on='dep_id')
            name_col = 'servant_name'
        
        roster_filtered = roster_source_df[roster_source_df['dep_name'] == selected_dep_roster]
        
        if selected_class_roster not in ["-- All Classes --", "-- Select Department First --"]:
            roster_filtered = roster_filtered[roster_filtered['class_name'] == selected_class_roster]

        if not roster_filtered.empty:
            display_roster = roster_filtered[[name_col, 'class_name']].sort_values(by=name_col).reset_index(drop=True)
            display_roster.rename(columns={name_col: 'Name', 'class_name': 'Class'}, inplace=True)
            
            with st.expander(f"Show {person_type_roster} List ({len(display_roster)})", expanded=True):
                st.dataframe(display_roster, use_container_width=True)
        else:
            st.warning("No people found for the selected filters.")