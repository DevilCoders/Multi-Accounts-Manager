# Multi-Accounts-Manager

A desktop application built with PyQt6 that lets you manage credentials for popular services in a single place.

## Features

- Tabs for Facebook, Instagram, Telegram, Snapchat, Gmail, Rambler, Twitter, Yandex Mail, and Threads.
- Add, edit, and delete account credentials per service.
- Built-in password generator with configurable strength.
- Change passwords quickly via a dedicated dialog.
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

The first launch will create an empty `accounts_data.json` file. Each tab maintains its own list of credentials. Passwords are masked in the table for privacy. Use the built-in generator whenever you need a strong password.
