# Church-Management-System

This project is a full-stack, end-to-end data platform designed to provide real-time analytics, data management, and pastoral care tools for a church community. It was born from a simple observation: without a system to track participation, communities can unintentionally overlook quieter members and fail to challenge talented ones, hindering both fairness and personal growth. This platform was built to replace guesswork with data-driven empathy.

Live Demo Link

The Problem Solved
This application addresses several critical, real-world challenges common in community organizations:

Inefficient Tracking: Replaces manual, inconsistent attendance tracking with a reliable, real-time system.

Unintentional Bias: Provides data to ensure special opportunities are distributed equitably, not just to the most visible members.

Lack of Proactive Care: Moves beyond simple reporting to proactively identify students who are showing signs of disengagement, enabling timely support.

Key Features
The application is a multi-page Streamlit app organized into three core, role-based sections:

📈 Data Analysis
Dashboard: A strategic overview of key metrics and distributions across all departments.

Attendance Analysis: A powerful tool with a snapshot view for class comparison and an animated bar chart race to visualize engagement trends over time.

Student Profile: A 360-degree view of an individual, featuring at-a-glance KPIs, "last seen" dates for core activities, and a historical trend chart.

Target Analysis: An interactive tool where Priests can define dynamic monthly targets and visualize each student's progress.

Students at Risk: A proactive pastoral tool using a dynamic rules engine to identify students showing signs of disengagement.

Opportunity Roster: A data-driven tool to engineer fairness by recommending students for special activities based on their participation history.

📝 Data Collection
Attendance Entry: A streamlined, role-specific form with a clean checkbox interface to make daily attendance recording effortless for servants.

⚙️ Data Management
Admin Panel: A secure, permission-gated hub for authorized leaders to manage the student lifecycle (e.g., moving classes), update activities, and ensure long-term data integrity.

Tech Stack
Backend & Database: Supabase (PostgreSQL)

Web Framework & UI: Python, Streamlit

Data Manipulation: Pandas

Data Visualization: Plotly

Version Control: Git / GitHub

Database Schema
The system is built on a normalized relational database designed for both data integrity and fast, multi-level analysis. The schema is centered around a transactional Attendance table, creating a "star schema" that is highly optimized for analytical queries.

(You can upload your ChurchDB.drawio.png file to a site like Imgur and paste the link here)

Future Vision
This project is built on a strong foundation with a clear roadmap for future enhancements:

The Pastoral Care Loop: Introducing an Interactions table to power a secure notes system, closing the loop between identifying an at-risk student and tracking the real-world actions taken to support them.

Multi-Tenant Architecture: Architecting the system with a Church table to transform the platform into a scalable, multi-tenant SaaS application capable of serving thousands of communities securely and independently.

Getting Started (Local Setup)
Clone the repository:

git clone [https://github.com/Beshoy-Hanna-Ayaad/Church-Management-System.git](https://github.com/Beshoy-Hanna-Ayaad/Church-Management-System.git)
cd Church-Management-System

Install dependencies:

pip install -r requirements.txt

Set up your secrets: Create a file at .streamlit/secrets.toml and add your Supabase credentials:

SUPABASE_URL = "YOUR_SUPABASE_URL"
SUPABASE_KEY = "YOUR_SUPABASE_SERVICE_ROLE_KEY"

Run the app:

streamlit run app.py