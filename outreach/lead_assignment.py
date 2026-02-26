import mysql.connector  # Connect to MySQL
import json

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


# Fetch speakers eligible for assignment
def fetch_unassigned_speakers(cursor):
    query = """
    SELECT 
        s.speaker_id,
        p.persona_data
    FROM speakers s
    JOIN speaker_personas p
        ON s.speaker_id = p.speaker_id
    LEFT JOIN lead_assignments la
        ON s.speaker_id = la.speaker_id
    WHERE la.speaker_id IS NULL
    """
    cursor.execute(query)
    return cursor.fetchall()


# Classify assignment based on persona
def classify_assignment(persona_json):
    seniority = persona_json.get("seniority", "UNKNOWN")

    if seniority in ["C_LEVEL", "FOUNDER", "VP_LEVEL"]:
        return "AE", "HIGH"
    elif seniority in ["DIRECTOR", "MANAGER"]:
        return "SDR", "MEDIUM"
    else:
        return "SDR", "LOW"


# Assign leads
def assign_leads():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        speakers = fetch_unassigned_speakers(cursor)

        print(f"Found {len(speakers)} unassigned speakers.")

        for speaker in speakers:

            persona_json = json.loads(speaker["persona_data"])
            role, priority = classify_assignment(persona_json)

            assigned_to = (
                "ae_team@company.com"
                if role == "AE"
                else "sdr_team@company.com"
            )

            cursor.execute("""
                INSERT INTO lead_assignments (
                    speaker_id,
                    assigned_to,
                    role,
                    priority
                )
                VALUES (%s, %s, %s, %s)
            """, (
                speaker["speaker_id"],
                assigned_to,
                role,
                priority
            ))

            print(f"Assigned speaker_id {speaker['speaker_id']} → {role} ({priority})")

        conn.commit()

    except Exception as e:
        conn.rollback()
        print("Error during lead assignment:", str(e))

    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    assign_leads()