import json
import logging
import os
from datetime import datetime, timedelta
from re import findall
import time
import webbrowser
import subprocess
from functools import partial
from threading import Thread
from urllib.parse import urlparse
import feedparser
import tzlocal
from bs4 import BeautifulSoup
from mac_notifications import client


def fetch_and_notify_jobs():
    # Get the absolute path of the script file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    processed_jobs_file = os.path.join(script_dir, "processed_jobs.json")
    configs_file = os.path.join(script_dir, "config.json")

    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
        filename=f"{script_dir}/upwork_scraper.log",
    )
    logger = logging.getLogger(__name__)

    # Load configurations from config.json file
    logger.debug("Reading config file")
    with open(configs_file, "r") as f:
        config = json.load(f)

    feed_urls = config["feed_url"]

    # Set your local timezone
    local_tz = tzlocal.get_localzone()

    # Load processed jobs from the JSON file
    if os.path.exists(processed_jobs_file):
        with open(processed_jobs_file, "r") as f:
            processed_jobs = json.load(f)
    else:
        processed_jobs = []

    # Fetch new jobs from the RSS feed and display notifications
    logger.debug("Fetching jobs from the RSS feed")
    for feed_url in feed_urls:
        # Parse the RSS feed
        feed = feedparser.parse(feed_url)

        # Loop through the entries in the feed (most recent first)
        for entry in reversed(feed.entries):
            # Check if this job has already been processed
            job_id = findall(r"(?<=_)%([a-zA-Z0-9]+)", entry.link)[0]
            if job_id in processed_jobs:
                continue
            logger.debug("New job was found")

            # Convert the published time to your local timezone
            published_time = datetime.strptime(
                entry.published, "%a, %d %b %Y %H:%M:%S %z"
            )
            published_time = published_time.astimezone(local_tz)

            # Calculate the relative time since the job was published
            now = datetime.now(local_tz)
            relative_time = now - published_time

            # Only process jobs posted within the last hour
            if relative_time > timedelta(hours=1):
                continue

            if relative_time.days > 1:
                relative_time_str = f"{relative_time.days} days"
            else:
                total_seconds = relative_time.total_seconds()
                hours = int(total_seconds // 3600)
                minutes = int((total_seconds % 3600) // 60)
                relative_time_str = f"{hours}h {minutes}m"

            posted_on = (
                f'{relative_time_str} ago ({published_time.strftime("%Y-%m-%d %H:%M")})'
            )

            # Parse the RSS entry
            soup = BeautifulSoup(entry.content[0]["value"], "html.parser")

            # Get payment type
            budget = soup.find("b", string="Budget")
            hourly_rate = soup.find("b", string="Hourly Range")
            try:
                rate = (
                    budget.find_next_sibling(string=True)
                    if budget
                    else hourly_rate.find_next_sibling(string=True)  # type: ignore
                )
                rate = rate.replace(":", "").replace("\n", "").strip()  # type: ignore
                rate = (
                    f"Budget {rate}"
                    if budget
                    else f"Hourly {rate}" if hourly_rate else "N/A"
                )
            except Exception as e:
                logger.debug(f"Rate is not available for {entry.link.strip()}: {e}")
                rate = "N/A"

            # Get job category
            category = (
                soup.find("b", string="Category")
                .find_next_sibling(string=True)  # type: ignore
                .replace(":", "")  # type: ignore
                .strip()  # type: ignore
                .replace(" ", "_")
                .replace("-", "_")
                .replace("/", "_")
                .replace("&", "and")
            )

            # Get customer country
            try:
                country = (
                    soup.find("b", string="Country")
                    .find_next_sibling(string=True)  # type: ignore
                    .replace(":", "")  # type: ignore
                    .strip()  # type: ignore
                )
            except Exception as e:
                country = "N/A"

            # Get required skill and format them as hashtags
            try:
                skills = (
                    soup.find("b", string="Skills")
                    .find_next_sibling(string=True)  # type: ignore
                    .replace(":", "")  # type: ignore
                    .strip()  # type: ignore
                )
            except Exception as e:
                skills = "N/A"
            try:
                skills_hashtags = " ".join(
                    [
                        "#"
                        + word.strip()
                        .replace(" ", "_")
                        .replace("-", "_")
                        .replace("/", "_")
                        .replace("&", "and")
                        for word in skills.split(", ")[:10]
                    ]
                ).strip()
            except Exception as e:
                skills_hashtags = "N/A"

            # Get the 1st sentence of the summary
            summary = (
                (entry.summary.split(".")[0] + ".")
                .replace("<br>", "\n")
                .replace("<br/>", "\n")
                .replace("<br />", "\n")
                .replace("<br >", "\n")
                .replace("\n\n", "\n")
            )

            # Build the message to display
            message = f'{entry.title.replace(" - Upwork", "")}\n#{category}\n💲 {rate}\n📄 {summary}\n🕑 {posted_on}\n🌍 {country}\n{skills_hashtags}'

            print("\n\n")
            print(message)
            print("\n\n")
            notify("New Job Posted", message, entry.link)

            # Add the job ID to the list of processed jobs
            processed_jobs.append(job_id)

    # Save the processed jobs to the JSON file
    with open(processed_jobs_file, "w") as f:
        json.dump(processed_jobs, f)


def notify(title: str, text: str, link: str):
    # Use terminal-notifier for notifications
    applescript = f"""
    terminal-notifier -title "{title}" -message "{text}" -open "{link}"
    """
    # Execute command
    subprocess.call(applescript, shell=True)

    print("Notification sent. Link will open when notification is clicked.")


def open_link(link: str):
    # Open the link in the default web browser
    subprocess.call(["open", link])


# Run the script every 5 minutes
while True:
    fetch_and_notify_jobs()
    print("Waiting...")
    time.sleep(300)
