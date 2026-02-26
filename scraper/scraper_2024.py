import requests # Http
from bs4 import BeautifulSoup # Parse HTML
import hashlib # SHA 256 hashing library
from datetime import datetime # datetime from datetime
from zoneinfo import ZoneInfo # ZoneInfo from datetime to get IST

# Custom Imports
# Fetch Connection - From package - database, file db.py, function get_connection
from database.db_connection import create_connection

# Variables
URL = "https://techsparks.yourstory.com/2024"
EVENT_YEAR = 2024
EVENT_NAME = "TechSparks"

# Generate batch id for scraping
def generate_batch_id():
    now_ist = datetime.now(ZoneInfo("Asia/Kolkata"))
    return f"TS{EVENT_YEAR}_{now_ist.strftime('%Y%m%d%H%M%S')}"

# Generate hash
def generate_hash(name, designation, year):
    raw_string = f"TS{name}|{designation}|{year}"
    return hashlib.sha256(raw_string.encode()).hexdigest()

# Scrape Data
def scrape():
    # fetch function
    def fetch():
        print("Accessing URL\n")
        try:
            response = requests.get(URL, timeout = 15)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch page: {e}")
            return None
    
    # parse speaker blocks function
    def parse_speaker_blocks(html):
        print("Starting parsing HTML for spaker blocks")
        try:
            soup = BeautifulSoup(html, "html.parser")
            # the page source have speaker name in ts_speaker class hence .ts_speaker
            # '.' means class
            speaker_blocks = soup.select(".speaker__cms")
            return speaker_blocks
        except Exception as e:
            print(f"Unable to parse the page: {e}")
            return None
    
    # call fetch function and store in variable html
    html = fetch()
    # if not - check for empty string
    if not html:
        return None
    
    # fetch successfull
    print("Fetch Successful")

    # call parseSpeakerBlocks function
    speaker_blocks = parse_speaker_blocks(html)
    # is None - Strictly check if something is there or not
    if speaker_blocks is None:
        print("Parse Failed")
        return None
    
    if not speaker_blocks:
        print("Parse successful but no speakers found")

    # Parse successful and data found
    print(f"Found {len(speaker_blocks)} speakers")

    def store_speaker_list(speaker_blocks):
        # Generate batch id
        batch_id = generate_batch_id()

        # scarped at
        scraped_at = datetime.now(ZoneInfo("Asia/Kolkata"))

        # count of speakers processed, including duplicates
        count_speakers = 0

        # create connection - it runs once and will close connection at the end
        # so this is not very resource heavy
        connection = create_connection()

        # create cursor
        cursor = connection.cursor()

        # Loop to fetch specific entry and store in database
        for block in speaker_blocks:
            # fetch name and description
            name_tag = block.select_one(".speaker-name")
            desc_tag = block.select_one(".speaker-des")

            # remove white space from start and end
            name = name_tag.get_text(strip = True) if name_tag else None
            designation = desc_tag.get_text(strip = True) if desc_tag else None
            
            # skip if name not present
            if not name:
                continue

            # generate hash
            data_hash = generate_hash(name, designation, EVENT_YEAR)

            # SQL Query
            query = """
            INSERT INTO speakers_raw (
                name,
                designation_raw,
                event_year,
                event_name,
                source_url,
                ingestion_batch_id,
                data_hash,
                scraped_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                ingestion_batch_id = VALUES(ingestion_batch_id),
                scraped_at = VALUES(scraped_at);
            """

            # Execute cursor
            cursor.execute(
                query,
                (
                    name,
                    designation,
                    EVENT_YEAR,
                    EVENT_NAME,
                    URL,
                    batch_id,
                    data_hash,
                    scraped_at,
                ),
            )

            # increase counter
            count_speakers += 1

        # write all the pending changes to disk
        connection.commit()

        # close cursor and the connection
        cursor.close()
        connection.close()

        print(f"Batch ID: {batch_id}")
        print(f"Total processed: {count_speakers}")
        print("Scrape completed.")
    
    # call function store_speaker_list(speaker_blocks)
    store_speaker_list(speaker_blocks)


if __name__ == "__main__":
    scrape()


