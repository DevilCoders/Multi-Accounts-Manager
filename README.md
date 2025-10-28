# Multi-Accounts-Manager

A desktop application built with PyQt6 that lets you manage credentials for popular services in a single place.

## Features

- Tabs for Facebook, Instagram, Telegram, Snapchat, Gmail, Rambler, Twitter, Yandex Mail, and Threads.
- Add, edit, and delete account credentials per service, including notes, tags, and automatic "last updated" tracking.
- Built-in password generator with configurable strength and inline strength analysis/feedback.
- Search bar and optional password reveal toggle per service for quick filtering.
- Clipboard shortcuts and context menu for copying usernames or passwords without leaving the app.
- Import/export accounts to CSV for secure backups or migrations.
- Change passwords quickly via a dedicated dialog with confirmation and guidance.
- Data stored locally in a JSON file (defaults to `accounts_data.json` next to the executable).

## Getting started

1. Create a virtual environment and install dependencies:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Launch the GUI:

   ```bash
   python main.py
   ```

The first launch will create an empty `accounts_data.json` file. Each tab maintains its own list of credentials. Passwords are masked in the table for privacy—enable the **Show passwords** toggle when you need to inspect them. Use the built-in generator whenever you need a strong password.

### Importing and exporting CSV files

- Use **Export CSV** from a service tab (or right-click a row) to back up the currently visible accounts. Tags are stored as a comma-separated list in the exported file.
- Use **Import CSV** to merge credentials from a CSV. Existing usernames will be updated in-place while new usernames are appended.
