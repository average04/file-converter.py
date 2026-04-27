# iPhone Backup Tool — Design Spec

**Date:** 2026-04-28
**Status:** Approved

---

## Overview

A desktop application that backs up an iPhone's full data (iTunes-style) to a local Windows PC. The app connects via USB or WiFi on the same network, presents a native desktop window (no browser required), and saves backups to a configurable folder.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Desktop window | PyWebView |
| Web server / backend | Flask |
| iPhone communication | pymobiledevice3 |
| Executable bundling | PyInstaller |
| UI | HTML / CSS / JS (served by Flask) |

**How it starts:** PyInstaller bundles everything into a single `.exe`. On launch, Flask starts in a background thread, then PyWebView opens a native window pointing at `localhost`. The user sees a desktop app — no browser tab, no terminal visible.

---

## Connection Methods

- **USB** — device detected automatically when plugged in; polling every 3 seconds
- **WiFi** — device discovered via mDNS on the local network; requires "Sync over Wi-Fi" to be enabled once in iTunes/Finder

Both modes are supported simultaneously. The dashboard shows which connection type is active via a badge.

---

## Screens

### 1. Dashboard
- Connected iPhone details: name, model, iOS version, storage used/total
- Connection type badge: USB or WiFi
- "Start Backup" button (disabled if no device connected)
- "Connect your iPhone" prompt with instructions when no device is found

### 2. Backup
- Destination folder display (default or user-selected override)
- "Change folder" button (opens native folder picker)
- Progress bar with percentage and estimated time remaining
- Cancel button
- Success/error state after completion

### 3. History
- List of past backups: device name, date, backup size
- Stored in `backup_history.json` next to the `.exe`

### 4. Settings
- Default backup folder (defaults to `C:\Users\<username>\Documents\iPhoneBackups`, resolved at runtime)
- WiFi discovery toggle (on/off)
- Persisted in `settings.json` next to the `.exe`

---

## Core Services

### DeviceDetector
- Runs in a background thread
- Polls USB every 3 seconds via `pymobiledevice3`
- Listens for WiFi devices via mDNS
- Pushes device connect/disconnect events to the UI via Flask Server-Sent Events (SSE)

### BackupService
- Triggered by user clicking "Start Backup"
- Runs `pymobiledevice3` full backup protocol (iTunes-compatible)
- Streams progress back to UI via SSE
- Saves backup to the selected destination folder, or the default (`Documents/iPhoneBackups`) if none chosen
- On completion, appends an entry to `backup_history.json`

### SettingsManager
- Reads/writes `settings.json`
- Exposes default backup path and WiFi toggle
- Used by Flask routes and BackupService

---

## Data Flow

```
iPhone (USB or WiFi)
    → DeviceDetector (pymobiledevice3)
        → Flask SSE → PyWebView UI (live device status)

User clicks "Start Backup"
    → Flask route → BackupService (pymobiledevice3)
        → progress events → UI progress bar
            → saves to disk → History updated
```

---

## Error Handling

| Scenario | Behavior |
|---|---|
| Device disconnects mid-backup | Show error, offer retry or cancel |
| No device connected | Dashboard shows setup instructions |
| Trust dialog not accepted on iPhone | Prompt user to unlock and tap "Trust This Computer" |
| Backup folder missing or full | Warn before starting, suggest alternative path |
| App already running | Prevent second instance from opening |

---

## File Structure

```
iphone-backup/
├── main.py                  # Entry point: starts Flask + PyWebView
├── requirements.txt
├── settings.json            # Runtime config (gitignored)
├── backup_history.json      # Backup log (gitignored)
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── routes/
│   │   ├── device.py        # /api/device endpoints + SSE
│   │   ├── backup.py        # /api/backup endpoints
│   │   └── settings.py      # /api/settings endpoints
│   ├── services/
│   │   ├── device_detector.py
│   │   ├── backup_service.py
│   │   └── settings_manager.py
│   ├── templates/
│   │   ├── base.html
│   │   ├── index.html       # Dashboard
│   │   ├── backup.html
│   │   ├── history.html
│   │   └── settings.html
│   └── static/
│       ├── css/
│       └── js/
```

---

## Out of Scope (for now)

- iCloud sync
- Selective backup (individual files/apps)
- Backup encryption
- Mac/Linux support
- Backup restore
