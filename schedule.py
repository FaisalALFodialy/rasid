from datetime import datetime, timedelta
from back_end import RasidJob, CATEGORY_ID_MAP
from database import fetch_all_users

# Helper to match schedule
def should_run_now(schedule):
    if not schedule:
        return False

    now = datetime.now()
    start_date = datetime.strptime(schedule["start_date"], "%Y-%m-%d")
    start_time = datetime.strptime(schedule["start_time"], "%H:%M:%S").time()

    # Ensure it's the right day
    if now.date() < start_date.date():
        return False

    # Match time (within 5-minute window)
    if abs((datetime.combine(now.date(), start_time) - now).total_seconds()) > 300:
        return False

    # Check frequency
    frequency = schedule["frequency"]
    last_run_str = schedule.get("last_updated")
    if last_run_str:
        last_run = datetime.fromisoformat(last_run_str)
        if frequency == "Every Day" and (now.date() == last_run.date()):
            return False
        elif frequency == "Every Week" and (now - last_run < timedelta(days=7)):
            return False
        elif frequency == "Every Month" and (now - last_run < timedelta(days=30)):
            return False

    return True


# Run web scraping for each valid user
def main():
    users = fetch_all_users()
    for email, info in users.items():
        schedule = info.get("schedule")
        if should_run_now(schedule):
            try:
                print(f"Running scraping for: {email}")
                job = RasidJob(
                    sender_email="rasid.projects.news@gmail.com",
                    password="sveiheahhbzidbnf",
                    receiver_emails=[email],
                    category=info["category"]
                )
                job.run()
            except Exception as e:
                print(f"Error scraping for {email}: {e}")

if __name__ == "__main__":
    main()
