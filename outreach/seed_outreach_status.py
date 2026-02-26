import mysql.connector  # Connect to MySQL

# Custom Imports
# import DB_CONFIG class from settings class inside config package
from config.settings import DB_CONFIG


# Create a connection
def get_connection():
    return mysql.connector.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        database=DB_CONFIG["database"],
    )


# Seed outreach status
def seed_outreach_status():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Insert status only for speakers:
        # 1. Who have current enrichment profile
        # 2. Who do not already have outreach_status row

        insert_query = """
        INSERT INTO outreach_status (
            speaker_id,
            event_phase,
            phase_updated_at
        )
        SELECT
            s.speaker_id,
            'pre_event',
            NOW()
        FROM speakers s
        JOIN speaker_profiles sp
            ON s.speaker_id = sp.speaker_id
            AND sp.is_current = 1
        LEFT JOIN outreach_status os
            ON s.speaker_id = os.speaker_id
        WHERE os.speaker_id IS NULL
        """

        cursor.execute(insert_query)
        conn.commit()

        print(f"Inserted {cursor.rowcount} new outreach_status rows.")

    except Exception as e:
        conn.rollback()
        print("Error while seeding outreach status:", str(e))

    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    seed_outreach_status()