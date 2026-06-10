# Setup Instructions — Danielle's Lead Gen & Cold Email System

A step-by-step guide to get the system running from scratch.

---

## 1. Clone the repo and install dependencies

```bash
git clone <your-repo-url>
cd danielle-npsbleads
pip install -r requirements.txt
```

---

## 2. Create a Gmail App Password

Gmail App Passwords let you authenticate via SMTP without using your main Google password.

1. Go to your Google Account: https://myaccount.google.com/
2. Click **Security** in the left sidebar.
3. Under "How you sign in to Google", enable **2-Step Verification** if it isn't already on.
4. After enabling 2FA, go back to Security and search for **App passwords** (or visit https://myaccount.google.com/apppasswords).
5. Under "Select app", choose **Mail**. Under "Select device", choose **Other (custom name)** and type `OutreachBot`.
6. Click **Generate**. Copy the 16-character password shown — you won't see it again.
7. Paste it into `.env` as `GMAIL_APP_PASSWORD` (no spaces).

---

## 3. Create a Google Sheets service account

1. Go to the Google Cloud Console: https://console.cloud.google.com/
2. Create a new project (or select an existing one).
3. Enable these APIs:
   - **Google Sheets API** (https://console.cloud.google.com/apis/library/sheets.googleapis.com)
   - **Google Drive API** (https://console.cloud.google.com/apis/library/drive.googleapis.com)
4. Go to **IAM & Admin → Service Accounts** and click **Create Service Account**.
5. Name it (e.g., `outreach-bot`) and click **Create and Continue**.
6. Skip the optional role/user fields and click **Done**.
7. Click on the newly created service account, go to the **Keys** tab, and click **Add Key → Create new key**.
8. Choose **JSON** and download the file.
9. Move the downloaded JSON file into this project directory and rename it `service_account.json`.
10. Note the service account's email address — it looks like `outreach-bot@your-project.iam.gserviceaccount.com`.

---

## 4. Create the Google Sheet and share it

1. Go to https://sheets.google.com and create a new blank spreadsheet.
2. Name it **Leads** (or anything you like).
3. Copy the Spreadsheet ID from the URL:
   ```
   https://docs.google.com/spreadsheets/d/THIS_IS_THE_ID/edit
   ```
4. Share the spreadsheet with the service account email (from step 3.10) and give it **Editor** access.
5. Paste the Spreadsheet ID into `.env` as `GOOGLE_SHEETS_ID`.

> The system will automatically create the **Leads** tab with the correct column headers on first run.

---

## 5. Configure your .env file

```bash
cp .env.example .env
```

Open `.env` in a text editor and fill in:

```
GMAIL_ADDRESS=danniadamsprojects@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx    # your 16-char app password
GOOGLE_SHEETS_ID=1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms  # your sheet ID
GOOGLE_SERVICE_ACCOUNT_JSON=service_account.json
FOLLOW_UP_DAYS_MIN=4
FOLLOW_UP_DAYS_MAX=6
DAILY_LEAD_TARGET=12
```

Do **not** commit `.env` or `service_account.json` to version control — they contain secrets.

---

## 6. Run the system

### Find leads and send today's emails:
```bash
python main.py daily
```

### Send follow-up emails to leads who haven't replied:
```bash
python main.py followup
```

### Print a dashboard summary:
```bash
python main.py status
```

Logs are written to `outreach.log` in the project directory as well as to the terminal.

---

## 7. Set up cron jobs (automated daily runs)

Open your crontab:
```bash
crontab -e
```

Add these two lines (adjust the path to your project):

```cron
# Send new outreach emails every weekday at 9 AM
0 9 * * 1-5 cd /path/to/danielle-npsbleads && python main.py daily >> /path/to/danielle-npsbleads/cron.log 2>&1

# Check and send follow-ups every weekday at 10 AM
0 10 * * 1-5 cd /path/to/danielle-npsbleads && python main.py followup >> /path/to/danielle-npsbleads/cron.log 2>&1
```

Replace `/path/to/danielle-npsbleads` with the actual absolute path on your machine.

**Tip:** If you use a virtual environment, activate it in the cron command:
```cron
0 9 * * 1-5 cd /path/to/danielle-npsbleads && /path/to/venv/bin/python main.py daily >> cron.log 2>&1
```

---

## 8. (Optional) Add a Google Maps API key for more leads

Google Maps / Places API provides high-quality business listings with websites.

1. Go to https://console.cloud.google.com/apis/library/places-backend.googleapis.com and enable the **Places API**.
2. Go to **APIs & Services → Credentials** and create an API key.
3. Add to `.env`:
   ```
   GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here
   ```
4. The `find_leads_google_maps()` function in `lead_finder.py` will now be called automatically during the daily job.

---

## 9. (Optional) Add Anthropic API key for AI-personalized emails

Once you have a Claude API key you can generate uniquely personalized emails instead of using templates.

1. Sign up at https://console.anthropic.com/ and create an API key.
2. Add to `.env`:
   ```
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   ```
3. In `email_templates.py`, uncomment the `build_initial_email_ai()` function at the bottom of the file.
4. In `main.py`, replace the `build_initial_email(lead)` call with `build_initial_email_ai(lead)`.
5. Install the Anthropic SDK:
   ```bash
   pip install anthropic
   ```

---

## 10. Manually adding leads (LinkedIn / RFP boards)

Paste leads directly into `leads_manual.csv` using this format:

```csv
name,org,email,industry,notes
Jane Smith,Orlando Food Bank,jane@orlandofoodbank.org,Nonprofit,Runs annual fundraising campaigns
Bob Lee,Lee Plumbing LLC,bob@leeplumbing.com,Small Business,Family-run since 2005
```

- `name` — contact's full name (used for personalization)
- `org` — organization or business name
- `email` — contact email (required)
- `industry` — e.g. "Nonprofit", "Small Business", "Healthcare"
- `notes` — one sentence of context, used as the opening observation in the email

These leads are picked up automatically the next time you run `python main.py daily`.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `SMTPAuthenticationError` | Double-check `GMAIL_APP_PASSWORD` — no spaces, and 2FA must be enabled |
| `gspread.exceptions.SpreadsheetNotFound` | Make sure the sheet is shared with the service account email |
| `FileNotFoundError: service_account.json` | Ensure the JSON file is in the project root and `GOOGLE_SERVICE_ACCOUNT_JSON` matches the filename |
| Emails landing in spam | The spacing (8-25 min) helps, but also verify the Gmail account has a complete profile and sent history |
| No leads found | Try adding leads to `leads_manual.csv` as a fallback while scraping sources are debugged |
