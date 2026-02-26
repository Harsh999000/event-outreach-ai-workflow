import mysql.connector # Connect to MySQL

# Custom Imports
# import DB_CONFIG calss from settings class inside config package
from config.settings import DB_CONFIG

# Define job status
ACTIVE_JOB_STATUSES = ("pending", "dispatched", "retry_scheduled")

# create a connection
def get_connection():
    return mysql.connector.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        database=DB_CONFIG["database"],
    )

# Seed linkedin
def seed_linkedin_enrichment_jobs():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Insert jobs only for speakers:
        # 1. Without current profile
        # 2. Without active enrichment job
        insert_query = """
        INSERT INTO enrichment_jobs (
            speaker_id,
            job_type,
            status,
            attempt_count,
            max_attempts
        )
        SELECT
            s.speaker_id,
            'linkedin_resolution',
            'pending',
            0,
            5
        FROM speakers s
        LEFT JOIN speaker_profiles sp
            ON s.speaker_id = sp.speaker_id
            AND sp.is_current = TRUE
        LEFT JOIN enrichment_jobs ej
            ON s.speaker_id = ej.speaker_id
            AND ej.status IN ('pending', 'dispatched', 'retry_scheduled')
        WHERE sp.speaker_id IS NULL
        AND ej.job_id IS NULL
        """

        cursor.execute(insert_query)
        conn.commit()

        print(f"Inserted {cursor.rowcount} new enrichment jobs.")

    except Exception as e:
        conn.rollback()
        print("Error while seeding enrichment jobs:", str(e))

    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    seed_linkedin_enrichment_jobs()