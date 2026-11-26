from mysql.connector.errors import IntegrityError

from database import get_connection


def get_students_from_database(page, limit, sort_by, sort_order):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) AS total FROM students")
    total = cursor.fetchone()["total"]

    offset = (page - 1) * limit

    query = f"""
    SELECT * FROM students
    ORDER BY {sort_by} {sort_order}
    LIMIT %s OFFSET %s
    """
    cursor.execute(query, (limit, offset))
    records = cursor.fetchall()

    cursor.close()
    connection.close()

    total_pages = max(1, (total + limit - 1) // limit)

    return {
        "students": records,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": total_pages
    }




def add_student_to_database(student):
    connection = get_connection()
    cursor = connection.cursor()

    query = """
            INSERT INTO students(roll_number, name, age, course, marks)
            VALUES
            (%s, %s, %s, %s, %s)
            """
    values = (student.roll_number, student.name, student.age, student.course, student.marks)

    try:
        cursor.execute(query, values)
        connection.commit()

        new_student_id = cursor.lastrowid

        return new_student_id

    except IntegrityError:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()



def update_student_in_database(student_id, student):
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("SELECT student_id FROM students WHERE student_id = %s", (student_id,))
        existing_student = cursor.fetchone()
        if existing_student is None:
            return False

        query = """
        UPDATE students 
        SET roll_number = %s, name = %s, age = %s, course = %s, marks = %s
        WHERE student_id = %s
        """
        values = (
            student.roll_number,
            student.name,
            student.age,
            student.course,
            student.marks,
            student_id
        )

        cursor.execute(query, values)
        connection.commit()

        return True

    except IntegrityError:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


def update_student_fields_in_database(student_id, updates):

    allowed_fields = {
        "roll_number",
        "name",
        "age",
        "course",
        "marks"
    }

    if not updates:
        raise ValueError("No fields provided for update.")

    if not all(field in allowed_fields for field in updates):
        raise ValueError("Invalid field provided for update.")

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            "SELECT student_id FROM students WHERE student_id = %s",
            (student_id,)
        )
        existing_student = cursor.fetchone()

        if existing_student is None:
            return False

        set_clause = ", ".join(f"{field} = %s" for field in updates)

        query = f"""
        UPDATE students
        SET {set_clause}
        WHERE student_id = %s
        """

        values = tuple(updates.values()) + (student_id,)

        cursor.execute(query, values)
        connection.commit()
        return True

    # Checks for the duplicate roll numbers.
    except IntegrityError:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()



def delete_student_from_database(student_id):
    connection = get_connection()
    cursor = connection.cursor()
    try:
        query = "DELETE FROM students WHERE student_id = %s"
        values = (student_id,)
        cursor.execute(query, values)
        connection.commit()
        if cursor.rowcount == 0:
            return False
        return True

    finally:
        cursor.close()
        connection.close()




def search_student_from_database(keyword):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        query = """
        SELECT * FROM students
        WHERE name LIKE %s OR roll_number = %s
        """
        values = (f"%{keyword}%", keyword)

        cursor.execute(query, values)
        records = cursor.fetchall()
        return records

    finally:
        cursor.close()
        connection.close()


def get_dashboard_stats():
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        query = """
            SELECT
                COUNT(*) AS total_students,
                COUNT(DISTINCT course) AS total_courses,
                ROUND(AVG(marks), 2) AS average_marks,
                MAX(marks) AS highest_marks
            FROM students
            """

        cursor.execute(query)
        result = cursor.fetchone()
        return result

    finally:
        cursor.close()
        connection.close()

def get_course_distribution():

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        query = """
        SELECT course, COUNT(*) AS student_count
        FROM students
        GROUP BY course
        ORDER BY student_count DESC
        """

        cursor.execute(query)

        return cursor.fetchall()

    finally:
        cursor.close()
        connection.close()