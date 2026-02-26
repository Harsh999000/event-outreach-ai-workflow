import mysql.connector
import json
from config.settings import DB_CONFIG


def get_connection():
    return mysql.connector.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        database=DB_CONFIG["database"],
    )


def fetch_unassigned_speakers(cursor):
    query = """
    SELECT 
        s.speaker_id,
        sp.persona_summary,
        sp.context_summary,
        sp.personalization_themes
    FROM speakers s
    JOIN speaker_profiles sp
        ON s.speaker_id = sp.speaker_id
    LEFT JOIN lead_assignments la
        ON s.speaker_id = la.speaker_id
    WHERE la.speaker_id IS NULL
      AND sp.is_current = 1
      AND sp.persona_summary IS NOT NULL
    """
    cursor.execute(query)
    return cursor.fetchall()


def classify_assignment(persona_json):
    seniority = persona_json.get("seniority", "UNKNOWN")

    if seniority in ["C_LEVEL", "FOUNDER", "VP_LEVEL"]:
        return "AE", "HIGH"
    elif seniority in ["DIRECTOR", "MANAGER"]:
        return "SDR", "MEDIUM"
    else:
        return "SDR", "LOW"


def assign_leads():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        speakers = fetch_unassigned_speakers(cursor)

        print(f"Found {len(speakers)} unassigned speakers.")

        for speaker in speakers:

            persona_json = {
                "persona_summary": speaker["persona_summary"],
                "context_summary": speaker["context_summary"],
                "personalization_themes": json.loads(speaker["personalization_themes"]) 
                    if speaker["personalization_themes"] else [],
                "seniority": "UNKNOWN"
            }

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