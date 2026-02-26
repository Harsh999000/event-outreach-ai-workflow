import requests
import mysql.connector
import time
import random

# Custom Imports
from config.settings import DB_CONFIG


N8N_WEBHOOK_URL = "http://localhost:5678/webhook/linkedin-resolution"
BATCH_SIZE = 1

# Sleep settings
BASE_DELAY_MIN = 20
BASE_DELAY_MAX = 35
FAILURE_DELAY_MIN = 60
FAILURE_DELAY_MAX = 120


def get_connection():
    return mysql.connector.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        database=DB_CONFIG["database"],
    )


def fetch_pending_jobs(cursor):
    """
    Fetch jobs that are:
    - pending
    - OR retry_scheduled but cooled down for 5 minutes
    """
    query = """
    SELECT ej.job_id, ej.speaker_id,
           s.normalized_name, s.normalized_company
    FROM enrichment_jobs ej
    JOIN speakers s ON ej.speaker_id = s.speaker_id
    WHERE ej.attempt_count < ej.max_attempts
      AND (
            ej.status = 'pending'
            OR (
                ej.status = 'retry_scheduled'
                AND ej.started_at IS NOT NULL
                AND ej.started_at < NOW() - INTERVAL 5 MINUTE
            )
          )
    ORDER BY ej.job_id ASC
    LIMIT %s
    """
    cursor.execute(query, (BATCH_SIZE,))
    return cursor.fetchall()


def mark_as_running(cursor, job_id):
    cursor.execute("""
        UPDATE enrichment_jobs
        SET status = 'running',
            attempt_count = attempt_count + 1,
            started_at = NOW(),
            last_error = NULL
        WHERE job_id = %s
    """, (job_id,))


def mark_complete(cursor, job_id):
    cursor.execute("""
        UPDATE enrichment_jobs
        SET status = 'complete',
            completed_at = NOW()
        WHERE job_id = %s
    """, (job_id,))


def mark_retry(cursor, job_id, error_message):
    cursor.execute("""
        UPDATE enrichment_jobs
        SET status = 'retry_scheduled',
            last_error = %s
        WHERE job_id = %s
    """, (error_message[:1000], job_id))


def insert_speaker_profile(cursor, result):
    speaker_id = result["speaker_id"]

    # Deactivate old profile
    cursor.execute("""
        UPDATE speaker_profiles
        SET is_current = 0
        WHERE speaker_id = %s AND is_current = 1
    """, (speaker_id,))

    # Compute next version
    cursor.execute("""
        SELECT COALESCE(MAX(enrichment_version), 0) + 1 AS next_version
        FROM speaker_profiles
        WHERE speaker_id = %s
    """, (speaker_id,))
    row = cursor.fetchone()
    next_version = row["next_version"]

    # Insert new profile
    cursor.execute("""
        INSERT INTO speaker_profiles
        (speaker_id, linkedin_url, confidence_score, source, enrichment_version, is_current)
        VALUES (%s, %s, %s, %s, %s, 1)
    """, (
        speaker_id,
        result.get("linkedin_url"),
        result.get("confidence_score"),
        "linkedin_resolution_v2",
        next_version
    ))


def clean_company_field(company_raw):
    if not company_raw:
        return company_raw
    parts = [p.strip() for p in company_raw.split(",")]
    return parts[-1] if parts else company_raw


def dispatch_jobs():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    total_processed = 0
    total_failed = 0

    try:
        while True:
            jobs = fetch_pending_jobs(cursor)

            if not jobs:
                print("\nNo eligible jobs found. Exiting dispatcher.")
                break

            print(f"\nProcessing {len(jobs)} enrichment jobs...")

            for job in jobs:
                job_id = job["job_id"]

                try:
                    mark_as_running(cursor, job_id)
                    conn.commit()

                    clean_company = clean_company_field(job["normalized_company"])

                    payload = {
                        "job_id": job["job_id"],
                        "speaker_id": job["speaker_id"],
                        "normalized_name": job["normalized_name"],
                        "normalized_company": clean_company,
                    }

                    response = requests.post(
                        N8N_WEBHOOK_URL,
                        json=payload,
                        timeout=30
                    )
                    response.raise_for_status()

                    result = response.json()

                    if not result.get("linkedin_url"):
                        raise Exception("Missing linkedin_url in enrichment response")

                    insert_speaker_profile(cursor, result)
                    mark_complete(cursor, job_id)
                    conn.commit()

                    total_processed += 1
                    print(f"Job {job_id} completed successfully.")

                    # Base pacing delay
                    sleep_time = random.uniform(BASE_DELAY_MIN, BASE_DELAY_MAX)
                    print(f"Sleeping {int(sleep_time)} seconds (base pacing)...")
                    time.sleep(sleep_time)

                except Exception as e:
                    conn.rollback()
                    mark_retry(cursor, job_id, repr(e))
                    conn.commit()

                    total_failed += 1
                    print(f"Job {job_id} failed. Scheduled for retry.")

                    # Backoff delay on failure
                    sleep_time = random.uniform(FAILURE_DELAY_MIN, FAILURE_DELAY_MAX)
                    print(f"Sleeping {int(sleep_time)} seconds (failure backoff)...")
                    time.sleep(sleep_time)

        print("\nBatch run summary:")
        print(f"Total completed: {total_processed}")
        print(f"Total failed: {total_failed}")

    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    dispatch_jobs()