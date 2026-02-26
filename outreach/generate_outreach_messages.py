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


def fetch_eligible_speakers(cursor):
    query = """
    SELECT 
        s.speaker_id,
        s.normalized_name,
        s.normalized_company,
        sp.persona_summary,
        sp.context_summary,
        sp.personalization_themes
    FROM speakers s
    JOIN speaker_profiles sp 
        ON s.speaker_id = sp.speaker_id
    WHERE sp.is_current = 1
      AND sp.persona_summary IS NOT NULL
      AND s.speaker_id NOT IN (
        SELECT speaker_id FROM outreach_messages
      )
    """
    cursor.execute(query)
    return cursor.fetchall()


def generate_outreach_messages():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        speakers = fetch_eligible_speakers(cursor)

        print(f"Found {len(speakers)} eligible speakers.")

        for speaker in speakers:

            themes = json.loads(speaker["personalization_themes"]) \
                if speaker["personalization_themes"] else []

            if not themes:
                themes = ["pricing intelligence", "competitive benchmarking"]

            name = speaker["normalized_name"]
            company = speaker["normalized_company"] or "your organization"

            theme_1 = themes[0]
            theme_2 = themes[1] if len(themes) > 1 else theme_1

            persona_json = {
                "persona_summary": speaker["persona_summary"],
                "context_summary": speaker["context_summary"],
                "personalization_themes": themes
            }

            # PRE EVENT EMAIL
            pre_subject = f"Thought on {theme_1} at {company}"
            pre_body = f"""
Hi {name},

I’ve been following your work around {theme_1} at {company}. 
Many teams exploring pricing intelligence and competitive benchmarking 
are facing increasing data complexity.

If relevant, I’d be happy to introduce you to a YC-backed 
company specializing in this space.

Best,
""".strip()

            cursor.execute("""
                INSERT INTO outreach_messages (
                    speaker_id,
                    channel,
                    event_phase,
                    subject,
                    body,
                    persona_snapshot
                )
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                speaker["speaker_id"],
                "email",
                "pre_event",
                pre_subject,
                pre_body,
                json.dumps(persona_json)
            ))

            # PRE EVENT LINKEDIN
            linkedin_body = f"""
Hi {name}, noticed you're speaking at TechSparks — especially around {theme_1}. 
Would love to connect before the event.
""".strip()

            cursor.execute("""
                INSERT INTO outreach_messages (
                    speaker_id,
                    channel,
                    event_phase,
                    subject,
                    body,
                    persona_snapshot
                )
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                speaker["speaker_id"],
                "linkedin",
                "pre_event",
                None,
                linkedin_body,
                json.dumps(persona_json)
            ))

            # DURING EVENT EMAIL
            during_subject = "Are you at TechSparks this week?"
            during_body = f"""
Hi {name},

Are you attending TechSparks this week?

Given your work at {company}, especially around {theme_2}, 
it would be great to exchange perspectives.

Best,
""".strip()

            cursor.execute("""
                INSERT INTO outreach_messages (
                    speaker_id,
                    channel,
                    event_phase,
                    subject,
                    body,
                    persona_snapshot
                )
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                speaker["speaker_id"],
                "email",
                "during_event",
                during_subject,
                during_body,
                json.dumps(persona_json)
            ))

            print(f"Generated outreach messages for speaker_id {speaker['speaker_id']}")

        conn.commit()

    except Exception as e:
        conn.rollback()
        print("Error while generating outreach messages:", str(e))

    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    generate_outreach_messages()