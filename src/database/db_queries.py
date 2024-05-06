import uuid

import psycopg2.extras


def find_user_by_username(conn, username):
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
        cursor.execute("SELECT * FROM useraccount WHERE username=%s", (username,))
        return cursor.fetchone()


def generate_unique_user_id_str(cursor):
    while True:
        unique_id = str(uuid.uuid4())
        cursor.execute("SELECT COUNT(*) FROM useraccount WHERE id = %s", (unique_id,))
        if cursor.fetchone()[0] == 0:  # UUID is not in the database
            return unique_id


def insert_new_user(conn, user_id, username, hashed_password, is_dataset_user):
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
        insert_query = """
        INSERT INTO useraccount (id, username, password, is_dataset_user)
        VALUES (%s, %s, %s, %s);
        """
        cursor.execute(insert_query, (user_id, username, hashed_password, is_dataset_user))
        conn.commit()
