import mysql.connector # Connect to MySQL
import json # To handle json

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

# Fetch eligible speakers
def fetch_eligible_speakers(cursor):
    query = """
    SELECT 
        s.speaker_id,
        s.normalized_name,
        s.normalized_company,
        p.persona_data
    FROM speakers s
    JOIN speaker_profiles sp 
        ON s.speaker_id = sp.speaker_id
    JOIN speaker_personas p
        ON s.speaker_id = p.speaker_id
    WHERE sp.is_current = 1
    AND s.speaker_id NOT IN (
        SELECT speaker_id FROM outreach_messages
    )
    """
    cursor.execute(query)
    return cursor.fetchall()

# Classify persona
def classify_persona(persona_json):
    seniority = persona_json.get("seniority", "UNKNOWN")

    if seniority in ["C_LEVEL", "FOUNDER", "VP_LEVEL"]:
        return "strategic"
    elif seniority in ["DIRECTOR", "MANAGER"]:
        return "functional"
    else:
        return "operator"

# Generate outreach messages
def generate_outreach_messages():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        speakers = fetch_eligible_speakers(cursor)

        print(f"Found {len(speakers)} eligible speakers.")

        for speaker in speakers:

            persona_json = json.loads(speaker["persona_data"])
            persona_type = classify_persona(persona_json)

            themes = persona_json.get("personalization_themes", [])
            if not themes or len(themes) < 1:
                themes = ["pricing intelligence", "competitive benchmarking"]

            name = speaker["normalized_name"]
            company = speaker["normalized_company"] or "your organization"

            # ---------------- PRE EVENT EMAIL ----------------
            theme_1 = themes[0]

            if persona_type == "strategic":
                pre_subject = f"Thought on {theme_1} at {company}"
                pre_body = f"""
Hi {name},

I’ve been following your work around {theme_1} at {company}. 
Many teams exploring pricing intelligence and competitive benchmarking 
are facing increasing data complexity.

If relevant, I’d be happy to introduce you to a YC-backed 
company specializing in this space.

Best,
"""
            elif persona_type == "functional":
                pre_subject = f"Quick idea around {theme_1}"
                pre_body = f"""
Hi {name},

Noticed your focus on {theme_1}. 
Teams working in this area often look for better automation 
around competitor tracking and assortment insights.

Happy to connect you with a YC-backed team if helpful.

Best,
"""
            else:
                pre_subject = f"Saw your work on {theme_1}"
                pre_body = f"""
Hi {name},

Came across your work related to {theme_1}. 
Curious whether competitive benchmarking 
is something your team is currently exploring.

Let me know if relevant.

Best,
"""

            # Insert pre-event email
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
                pre_subject.strip(),
                pre_body.strip(),
                json.dumps(persona_json)
            ))

            # ---------------- PRE EVENT LINKEDIN ----------------
            pre_linkedin_body = f"""
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
                pre_linkedin_body,
                json.dumps(persona_json)
            ))

            # ---------------- DURING EVENT EMAIL ----------------
            theme_2 = themes[1] if len(themes) > 1 else theme_1

            during_subject = "Are you at TechSparks this week?"
            during_body = f"""
Hi {name},

Are you attending TechSparks this week?

Given your work at {company}, especially around {theme_2}, 
it would be great to exchange perspectives on how teams are 
approaching pricing intelligence and competitive benchmarking.

Best,
"""

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
                during_subject.strip(),
                during_body.strip(),
                json.dumps(persona_json)
            ))

            # ---------------- POST EVENT EMAIL ----------------
            post_subject = f"Following up on TechSparks – {theme_2}"
            post_body = f"""
Hi {name},

It was great seeing the discussions at TechSparks.

Given your work at {company} around {theme_2}, 
curious whether competitive benchmarking or pricing automation 
is something your team is actively exploring this year.

If helpful, I can introduce you to a YC-backed company 
that specializes in solving this.

Best,
"""

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
                "post_event",
                post_subject.strip(),
                post_body.strip(),
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