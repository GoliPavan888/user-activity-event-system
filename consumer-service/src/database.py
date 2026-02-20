import mysql.connector
from datetime import datetime
import json

from .config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME


def format_timestamp(ts: str):
    # Convert ISO format to MySQL format
    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def insert_event(event):
    conn = mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
    )

    cursor = conn.cursor()

    formatted_ts = format_timestamp(event["timestamp"])

    query = """
        INSERT INTO user_activities (user_id, event_type, timestamp, metadata)
        VALUES (%s, %s, %s, %s)
    """
    cursor.execute(
        query,
        (
            event["user_id"],
            event["event_type"],
            formatted_ts,
            json.dumps(event.get("metadata", {})),
        ),
    )

    conn.commit()
    cursor.close()
    conn.close()
