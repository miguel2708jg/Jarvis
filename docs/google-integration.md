# Connecting Jarvis to Gmail

Jarvis uses Google OAuth only for Gmail. Calendar events are stored locally in SQLite through `backend/services/calendar_service.py` and do not require Google Calendar credentials, Google Calendar API, or a calendar token file.

## 1. What Google OAuth Is Used For

Gmail tools use OAuth 2.0 so Jarvis can list, read, search, and send email from your account after you grant permission.

```text
credentials.json          OAuth consent screen        token_gmail.json
(who your app is)    ->    (you click Allow)      ->   (saved Gmail token)
```

Jarvis uses the standard Google Python client libraries listed in `requirements.txt`:

- `google-api-python-client`
- `google-auth-oauthlib`
- `google-auth`

## 2. Google Cloud Console Setup

1. Go to `console.cloud.google.com`.
2. Create or select a project for Jarvis.
3. Enable the Gmail API.
4. Configure the OAuth consent screen as an External app in test mode.
5. Add your Gmail address as a test user.
6. Create an OAuth client ID with application type Desktop app.
7. Download the JSON file and rename it to `credentials.json`.
8. Put `credentials.json` in the project root beside `backend/`.

`credentials.json` is already ignored by `.gitignore`. Never commit it.

## 3. Gmail Environment Variables

Add these to `.env`:

```env
GMAIL_CREDENTIALS_FILE=credentials.json
GMAIL_TOKEN_FILE=token_gmail.json
```

The first Gmail-related request opens a browser for OAuth consent, then saves `token_gmail.json`. Later Gmail requests reuse and refresh that token automatically.

## 4. Gmail Scopes

| Scope | Why |
|---|---|
| `gmail.readonly` | List, read, and search email |
| `gmail.send` | Send email |

## 5. Calendar Behavior

Calendar no longer uses Google OAuth. The calendar API and tools write to the local SQLite database configured by `DATABASE_PATH` or `DATA_DIR`.

Available local calendar operations:

```text
GET    /calendar
POST   /calendar
GET    /calendar/{id}
PUT    /calendar/{id}
DELETE /calendar/{id}
```

The `calendar_id` argument is still accepted by tools and API routes for compatibility, but it is ignored because events are local.

## 6. Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| Browser does not open for Gmail | `GMAIL_CREDENTIALS_FILE` missing or path is wrong | Check `.env` and confirm `credentials.json` exists in the project root |
| `invalid_grant` | Gmail token was revoked or corrupted | Delete `token_gmail.json` and authenticate again |
| `insufficient authentication scopes` | Token was created with old scopes | Delete `token_gmail.json` and authenticate again |
| Calendar asks for Google credentials | Backend is running old code | Restart the backend so it loads the local SQLite calendar service |
