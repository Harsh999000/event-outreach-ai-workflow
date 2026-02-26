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


# Advance outreach phase (safe single-step advancement)
def advance_outreach_phase():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Advance each speaker exactly ONE lifecycle step
        cursor.execute("""
            UPDATE outreach_status
            SET event_phase =
                CASE
                    WHEN event_phase = 'pre_event' THEN 'during_event'
                    WHEN event_phase = 'during_event' THEN 'post_event'
                    WHEN event_phase = 'post_event' THEN 'closed'
                    ELSE event_phase
                END,
                phase_updated_at = NOW()
            WHERE event_phase IN ('pre_event', 'during_event', 'post_event')
        """)

        moved_rows = cursor.rowcount

        conn.commit()

        print("Outreach Phase Advancement Complete.")
        print(f"Total records advanced: {moved_rows}")

    except Exception as e:
        conn.rollback()
        print("Error while advancing outreach phase:", str(e))

    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    advance_outreach_phase()