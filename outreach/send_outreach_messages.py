import mysql.connector  # Connect to MySQL
import time
import random

# Custom Imports
# import DB_CONFIG class from settings class inside config package
from config.settings import DB_CONFIG


# Configuration
MAX_LINKEDIN_PER_RUN = 5


# Create a connection
def get_connection():
    return mysql.connector.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        database=DB_CONFIG["database"],
    )


# Fetch messages ready to send
def fetch_pending_messages(cursor):
    query = """
    SELECT 
        om.message_id,
        om.speaker_id,
        om.channel,
        om.event_phase,
        om.subject,
        om.body
    FROM outreach_messages om
    JOIN outreach_status os
        ON om.speaker_id = os.speaker_id
    WHERE om.is_sent = FALSE
      AND om.event_phase = os.event_phase
    ORDER BY om.message_id ASC
    """
    cursor.execute(query)
    return cursor.fetchall()


# Mark message as sent
def mark_message_sent(cursor, message_id):
    cursor.execute("""
        UPDATE outreach_messages
        SET is_sent = TRUE,
            sent_at = NOW()
        WHERE message_id = %s
    """, (message_id,))


# Simulate Email Send
def send_email_simulation(subject, body):
    print("\n--- Sending Email ---")
    print("Subject:", subject)
    print("Body:", body[:120], "...")
    time.sleep(random.uniform(1, 2))


# Simulate LinkedIn Send
def send_linkedin_simulation(body):
    print("\n--- Sending LinkedIn Message ---")
    print("Body:", body[:120], "...")
    time.sleep(random.uniform(1, 2))


# Send outreach messages
def send_outreach_messages():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    linkedin_sent_count = 0
    total_sent = 0

    try:
        messages = fetch_pending_messages(cursor)

        print(f"Found {len(messages)} messages ready to send.")

        for msg in messages:

            # Respect LinkedIn cap
            if msg["channel"] == "linkedin":
                if linkedin_sent_count >= MAX_LINKEDIN_PER_RUN:
                    print("\nLinkedIn daily cap reached.")
                    break

                send_linkedin_simulation(msg["body"])
                linkedin_sent_count += 1

            elif msg["channel"] == "email":
                send_email_simulation(msg["subject"], msg["body"])

            # Mark as sent
            mark_message_sent(cursor, msg["message_id"])
            total_sent += 1

        conn.commit()

        print("\nSend Summary:")
        print(f"Total messages sent: {total_sent}")
        print(f"LinkedIn messages sent: {linkedin_sent_count}")

    except Exception as e:
        conn.rollback()
        print("Error while sending outreach messages:", str(e))

    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    send_outreach_messages()