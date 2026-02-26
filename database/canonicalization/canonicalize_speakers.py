import re # resular expression - pattern matching language for text
import hashlib # SHA 256 hashing library
from datetime import datetime # datetime from datetime
from zoneinfo import ZoneInfo # ZoneInfo from datetime to get IST

# Custom Imports
# Fetch Connection - From package - database, file db_connection.py, function create_connection
from database.db_connection import create_connection

# Variables
PROCESS_NAME = "Canonicalization"

# Generate identity hash
def generate_identity_hash(name, company):
    identity_string = f"{name}|{company if company else ''}"
    return hashlib.sha256(identity_string.encode()).hexdigest()

# Normalize text helpers
HONORIFICS = [
    "mr", "ms", "mrs", "dr", "prof",
    "shri", "honble", "hon'ble", "minister"
]

# normalize text - remove special char and white spaces. change to lowercase
def normalize_text(text):
    if not text:
        return None
    text = text.lower()
    # remove special chars by replacing with ""
    text = re.sub(r"[.'’]", "", text)
    # remove whitespaces by replacing with ""
    text = re.sub(r"\s+", " ", text)
    return text.strip()

# normalize name
def normalize_name(name):
    name = normalize_text(name)
    for word in HONORIFICS:
        # # remove honorifics by replacing with ""
        name = re.sub(rf"\b{word}\b", "", name)
    # remove whitespaces by replacing with ""
    name = re.sub(r"\s+", " ", name)
    return name.strip()

# Extract Company
def extract_company(designation):
    if not designation:
        return None

    # change to lower
    d = designation.lower()

    # remove extra things apart from company name
    if " at " in d:
        return normalize_text(d.split(" at ")[-1])

    if "|" in d:
        return normalize_text(d.split("|")[-1])

    if "-" in d:
        return normalize_text(d.split("-")[-1])

    if "," in d:
        return normalize_text(d.split(",")[-1])

    return None

# Canonicalization Process
def canonicalize():

    print(f"\nStarting {PROCESS_NAME} process...\n")

    # create connection
    connection = create_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        # fetch unmapped raw rows
        query_fetch = """
        SELECT r.id, r.name, r.designation_raw, r.event_year
        FROM speakers_raw r
        LEFT JOIN speaker_raw_map m ON r.id = m.raw_id
        WHERE m.raw_id IS NULL;
        """

        cursor.execute(query_fetch)
        rows = cursor.fetchall()

        if not rows:
            print("No new raw records found.")
            return

        print(f"Found {len(rows)} raw records to process.\n")

        processed_count = 0

        for row in rows:
            normalized_name = normalize_name(row["name"])
            normalized_company = extract_company(row["designation_raw"])
            identity_hash = generate_identity_hash(
                normalized_name,
                normalized_company
            )

            # Check if identity already exists
            cursor.execute(
                """
                SELECT speaker_id, first_seen_year, last_seen_year
                FROM speakers
                WHERE identity_hash = %s;
                """,
                (identity_hash,)
            )

            # fetch next row from results of last execute (just above)
            speaker = cursor.fetchone()

            if speaker:
                speaker_id = speaker["speaker_id"]

                # Update last_seen_year if required
                if row["event_year"] > speaker["last_seen_year"]:
                    cursor.execute(
                        """
                        UPDATE speakers
                        SET last_seen_year = %s
                        WHERE speaker_id = %s;
                        """,
                        (row["event_year"], speaker_id)
                    )
            else:
                cursor.execute(
                    """
                    INSERT INTO speakers (
                        normalized_name,
                        normalized_company,
                        identity_hash,
                        first_seen_year,
                        last_seen_year
                    )
                    VALUES (%s, %s, %s, %s, %s);
                    """,
                    (
                        normalized_name,
                        normalized_company,
                        identity_hash,
                        row["event_year"],
                        row["event_year"]
                    )
                )
                speaker_id = cursor.lastrowid

            # Insert mapping
            cursor.execute(
                """
                INSERT INTO speaker_raw_map (
                    speaker_id,
                    raw_id,
                    event_year
                )
                VALUES (%s, %s, %s);
                """,
                (
                    speaker_id,
                    row["id"],
                    row["event_year"]
                )
            )

            processed_count += 1

        # commit changes
        connection.commit()

        print(f"Total processed: {processed_count}")
        print("Canonicalization completed successfully.\n")

    except Exception as e:
        connection.rollback()
        print(f"Error during canonicalization: {e}")
        raise

    finally:
        cursor.close()
        connection.close()

# Entry Point
if __name__ == "__main__":
    canonicalize()