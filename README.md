# Upwork Job Alert Script

This Python script provides real-time alerts for new job postings on Upwork.

## 🔍 Functionality:
The script monitors Upwork feeds and generates macOS notifications for jobs posted within the last hour. Clicking on the notification will open the specific job in a new browser tab.

## 🌐 Planned Integrations:
Future updates may include support for alerts via Slack, Discord, Telegram, or email.

## 📈 Usage:
1. Install the required packages:

    ```bash
    pip install -r requirements.txt
    ```

2. Update `config.json` with your feed URLs.
3. Run the script:

    ```bash
    python upwork_job_feed_notifier.py
    ```

The script will check for new job postings every 5 minutes and notify you via macOS notifications.

## Contributing:
Fork the repository and submit pull requests. Feedback and suggestions are welcome.

---
