import subprocess
import sys
import time


def run_step(title, module_path):
    print("\n" + "=" * 70)
    print(f"STEP: {title}")
    print("=" * 70)

    result = subprocess.run(
        [sys.executable, "-m", module_path]
    )

    if result.returncode != 0:
        print(f"\nERROR during: {title}")
        sys.exit(1)

    print(f"COMPLETED: {title}")
    time.sleep(1)


def print_mode(mode):
    print("\n" + "#" * 70)
    print(f"RUNNING PIPELINE IN {mode.upper()} MODE")
    print("#" * 70 + "\n")


if __name__ == "__main__":

    mode = "demo"

    if len(sys.argv) > 1:
        if sys.argv[1] == "--full":
            mode = "full"
        elif sys.argv[1] == "--demo":
            mode = "demo"
        else:
            print("Invalid argument. Use --full or --demo")
            sys.exit(1)

    print_mode(mode)
    print("Starting End-to-End GTM Automation Pipeline...\n")

    # 1. Scrape Event Data (Full Mode Only)
    if mode == "full":
        run_step(
            "Scrape Event 2024",
            "scraper.scraper_2024"
        )

        run_step(
            "Scrape Event 2025",
            "scraper.scraper_2025"
        )
    else:
        print("\nSkipping Scraping (Demo Mode)\n")

    # 2. Canonical Identity Layer
    run_step(
        "Canonicalize Speakers",
        "database.canonicalization.canonicalize_speakers"
    )

    # 3. Seed Enrichment Jobs (Full Mode Only)
    if mode == "full":
        run_step(
            "Seed LinkedIn Enrichment Jobs",
            "database.enrichment.seed_jobs"
        )

        run_step(
            "Run Enrichment Dispatcher",
            "database.enrichment.dispatcher"
        )
    else:
        print("\nSkipping Enrichment Seeding & Dispatcher (Demo Mode)\n")

    # 4. Lead Assignment
    run_step(
        "Assign Leads",
        "outreach.lead_assignment"
    )

    # 5. Seed Outreach Lifecycle
    run_step(
        "Seed Outreach Status",
        "outreach.seed_outreach_status"
    )

    # 6. Generate Outreach Messages
    run_step(
        "Generate Outreach Messages",
        "outreach.generate_outreach_messages"
    )

    # 7. Advance Outreach Phase
    run_step(
        "Advance Outreach Phase",
        "outreach.advance_outreach_phase"
    )

    # 8. Send Outreach Messages (Simulation)
    run_step(
        "Send Outreach Messages",
        "outreach.send_outreach_messages"
    )

    print("\n" + "=" * 70)
    print("PIPELINE EXECUTED SUCCESSFULLY")
    print("=" * 70)