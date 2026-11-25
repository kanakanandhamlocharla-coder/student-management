import mysql.connector

def get_connection():
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="pandu",
        database="student_management"
    )
    return connection

if __name__ == "__main__":
    connection = get_connection()
    if connection.is_connected():
        print("Successfully Connected to MySQL Database")

    connection.close()