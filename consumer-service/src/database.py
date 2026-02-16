import mysql.connector
import json

from .db_config import (
    MYSQL_HOST,
    MYSQL_PORT,
    MYSQL_USER,
    MYSQL_PASSWORD,
    MYSQL_DB,
)


def get_connection():
    return mysql.connector.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB,
    )


def insert_event(event):
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        INSERT INTO user_activities
        (user_id, event_type, timestamp, metadata)
        VALUES (%s, %s, %s, %s)
    """

    cursor.execute(
        query,
        (
            event["user_id"],
            event["event_type"],
            event["timestamp"],
            json.dumps(event.get("metadata")),
        ),
    )

    conn.commit()

    cursor.close()
    conn.close()
