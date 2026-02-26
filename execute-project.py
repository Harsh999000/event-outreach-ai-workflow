import subprocess
import sys
import time


def run_step(title, command):
    print("\n" + "=" * 70)
    print(f"STEP: {title}")
    print("=" * 70)

    result = subprocess.run(command, shell=True)

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

    # Default mode
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

    # 1. Scrape Event Data
    run_step(
        "Scrape Event 2024",
        "python scraper/scraper_2024.py"
    )

    run_step(
        "Scrape Event 2025",
        "python scraper/scraper_2025.py"
    )

    # 2. Canonical Identity Layer
    run_step(
        "Canonicalize Speakers",
        "python database/canonicalization/canonicalize_speakers.py"
    )

    # 3. Seed Enrichment Jobs
    run_step(
        "Seed LinkedIn Enrichment Jobs",
        "python database/enrichment/seed_jobs.py"
    )

    # 4. Enrichment Dispatcher (Full Mode Only)
    if mode == "full":
        run_step(
            "Run Enrichment Dispatcher",
            "python database/enrichment/dispatcher.py"
        )
    else:
        print("\nSkipping Dispatcher (Demo Mode)\n")

    # 5. Lead Assignment
    run_step(
        "Assign Leads",
        "python outreach/lead_assignment.py"
    )

    # 6. Seed Outreach Lifecycle
    run_step(
        "Seed Outreach Status",
        "python outreach/seed_outreach_status.py"
    )

    # 7. Generate Outreach Messages
    run_step(
        "Generate Outreach Messages",
        "python outreach/generate_outreach_messages.py"
    )

    # 8. Advance Outreach Phase
    run_step(
        "Advance Outreach Phase",
        "python outreach/advance_outreach_phase.py"
    )

    # 9. Send Outreach Messages (Simulation)
    run_step(
        "Send Outreach Messages",
        "python outreach/send_outreach_messages.py"
    )

    print("\n" + "=" * 70)
    print("PIPELINE EXECUTED SUCCESSFULLY")
    print("=" * 70)