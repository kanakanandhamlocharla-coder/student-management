from database import get_connection

def get_students():
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM students")
    records = cursor.fetchall()
    cursor.close()
    connection.close()
    print(records)


def add_student(name, age, course, marks):

    connection = get_connection()
    cursor = connection.cursor()
    query = """
    INSERT INTO students (name, age, course, marks)
    VALUES (%s, %s, %s, %s)
    """

    values = (name, age, course, marks)

    cursor.execute(query, values)
    connection.commit()

    print("Student added successfully")
    print("New Student ID:", cursor.lastrowid)

    cursor.close()
    connection.close()


def update_student(student_id, new_marks):
    connection = get_connection()
    cursor = connection.cursor()
    query = """
    UPDATE students
    SET marks = %s
    WHERE student_id = %s
    """
    values = (new_marks, student_id)

    cursor.execute(query, values)
    connection.commit()

    print("Student updated successfully")
    print("Rows affected:", cursor.rowcount)

    cursor.close()
    connection.close()



def delete_student(student_id):
    connection = get_connection()
    cursor = connection.cursor()

    query = """
    DELETE FROM students
    WHERE student_id = %s
    """

    value = (student_id,)

    cursor.execute(query, value)
    connection.commit()

    print("Student deleted successfully")
    print("Rows affected:", cursor.rowcount)

    cursor.close()
    connection.close()

get_students()
# delete_student(33)
# update_student(1, 99.99)
# add_student("Prasad", 20, "CSE", 97.32)