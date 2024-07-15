from flask import Flask, render_template
from flask import Flask, request, render_template_string
import sqlite3
from dotenv import load_dotenv
load_dotenv()  # Load all the environment variables

import os
import sqlite3
import google.generativeai as genai

app = Flask(__name__)

# Function to execute SQL query and return results
def execute_query(query):
    conn = sqlite3.connect('student_management.db')
    cursor = conn.cursor()
    try:
        cursor.execute(query)
        conn.commit()
        if query.strip().lower().startswith("select"):
            results = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            return columns, results
        return None, "Query executed successfully."
    except Exception as e:
        return None, str(e)
    finally:
        conn.close()


# Configure GenAI Key
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Function to load Google Gemini model and provide queries as response
def get_gemini_response(question, prompt):
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content([prompt[0], question])
    return response.text

# Function to retrieve schema information from the database
def get_schema(db):
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    schema = {}

    # Retrieve table names
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cur.fetchall()

    # Retrieve column names and types for each table
    for table in tables:
        table_name = table[0]
        cur.execute(f"PRAGMA table_info({table_name});")
        columns = cur.fetchall()
        schema[table_name] = [(col[1], col[2]) for col in columns]

    conn.close()
    return schema

# Function to retrieve query results from the database
def read_sql_query(sql, db):
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    conn.commit()
    conn.close()
    return rows

# Define your Prompt
prompt = [
    """
    You are an expert in converting English questions to SQL query!
    The SQL database has multiple tables and columns. Use the schema provided to generate accurate SQL queries.
    Below given the detailed explanation of the tables, their variables, and the relationships between those 
    tables in the student management database: 
    
    1. Students Table
Description: This table stores information about each student.
StudentID: A unique identifier for each student (Primary Key).
FirstName: The first name of the student.
LastName: The last name of the student.
DateOfBirth: The date of birth of the student.
Email: The email address of the student (must be unique).
PhoneNumber: The contact number of the student.
Address: The residential address of the student.

2. Courses Table
Description: This table stores information about each course offered.
CourseID: A unique identifier for each course (Primary Key).
CourseName: The name of the course.
CourseCode: A unique code for the course.
Credits: The number of credits the course is worth.

3. Enrollments Table
Description: This table links students to the courses they are enrolled in. It represents the many-to-many relationship between students and courses.
EnrollmentID: A unique identifier for each enrollment record (Primary Key).
StudentID: The ID of the student (Foreign Key referencing Students table).
CourseID: The ID of the course (Foreign Key referencing Courses table).
EnrollmentDate: The date when the student enrolled in the course.
Grade: The grade the student received in the course (optional).

4. Teachers Table
Description: This table stores information about each teacher.
TeacherID: A unique identifier for each teacher (Primary Key).
FirstName: The first name of the teacher.
LastName: The last name of the teacher.
Email: The email address of the teacher (must be unique).
PhoneNumber: The contact number of the teacher.
Department: The department the teacher belongs to.

5. Course_Teachers Table
Description: This table links teachers to the courses they are teaching. It represents the many-to-many relationship between teachers and courses.
CourseTeacherID: A unique identifier for each record (Primary Key).
CourseID: The ID of the course (Foreign Key referencing Courses table).
TeacherID: The ID of the teacher (Foreign Key referencing Teachers table).
AssignmentDate: The date when the teacher was assigned to the course.

Relationships Between Tables
Students and Enrollments:
One-to-Many Relationship: One student can enroll in many courses, but each enrollment record corresponds to one student.
Foreign Key: StudentID in the Enrollments table references StudentID in the Students table.

Courses and Enrollments:
One-to-Many Relationship: One course can have many students enrolled, but each enrollment record corresponds to one course.
Foreign Key: CourseID in the Enrollments table references CourseID in the Courses table.

Teachers and Course_Teachers:
One-to-Many Relationship: One teacher can teach many courses, but each record in the Course_Teachers table corresponds to one teacher.
Foreign Key: TeacherID in the Course_Teachers table references TeacherID in the Teachers table.

Courses and Course_Teachers:
One-to-Many Relationship: One course can be taught by many teachers, but each record in the Course_Teachers table corresponds to one course.
Foreign Key: CourseID in the Course_Teachers table references CourseID in the Courses table.


    Provide the SQL command without ''' in the beginning or end and without the word 'sql' in the output.
    """
]



@app.route("/")
def index():
    return render_template("index.html")


@app.route('/application', methods=['GET', 'POST'])
def application():
    query = ""
    result = None
    columns = None
    question=""
    if request.method == 'POST':
        question = request.form['query']
        query = get_gemini_response(question, prompt)
        columns, result = execute_query(query)
    return render_template("application.html", question=question, result=result, columns=columns, query=query)


if __name__ == '__main__':
    app.run(debug=True)