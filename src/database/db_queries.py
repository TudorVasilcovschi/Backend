import psycopg2.extras


def find_user_by_username(conn, username):
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
        cursor.execute("SELECT * FROM useraccount WHERE username=%s", (username,))
        return cursor.fetchone()


def insert_new_user(conn, username, hashed_password):
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
        try:
            # Prepare the INSERT statement
            # Ensure that the column names match those in your actual database schema
            insert_query = """
            INSERT INTO useraccount (username, password)
            VALUES (%s, %s) RETURNING id;
            """
            # Execute the INSERT statement
            cursor.execute(insert_query, (username, hashed_password))
            # Commit the transaction
            conn.commit()
            # Retrieve and return the id of the newly inserted user
            new_user_id = cursor.fetchone()[0]
            return new_user_id
        except psycopg2.Error as e:
            # If an error occurs, rollback the transaction
            conn.rollback()
            return None
