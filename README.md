# 🗑️ Imgur Bulk Deletion Tool

> A cross-platform Python tool for bulk deleting Imgur posts with interactive setup and dry-run support. Free, open-source alternative to paid deletion services.

## ✨ Why This Exists

Imgur doesn't offer bulk deletion—your only option is nuking your entire account or paying for third-party tools. This script gives you a free, safe way to delete posts in bulk while maintaining full control.

**Battle-tested**: Successfully processed 500+ deletions in a single headless session with zero issues.

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🎯 **Interactive Setup** | Auto-detects username and guides you through configuration |
| 🧪 **Dry-Run Mode** | Test deletions safely without actually removing anything |
| 🧠 **Smart Processing** | Handles individual images and albums intelligently |
| 📊 **Visual Ordering** | Processes posts top-left first for predictable results |
| 💾 **Session Management** | Saves login to avoid repeated authentication |
| ⚙️ **Config Persistence** | Remembers your settings between runs |
| 👻 **Headless/Headful** | Run with or without visible browser window |
| 🛑 **Safe Interruption** | Press Ctrl+C anytime to stop safely |

## 📋 Requirements

- Python 3.7+
- Playwright

## 🚀 Installation

### 1. Download the Script
- Download `main.py` to a folder of your choice
- Configuration files will be created automatically in the same directory

### 2. Open Terminal
- **Windows**: PowerShell or Command Prompt
- **macOS/Linux**: Terminal

Navigate to your folder:
```bash
cd path/to/your/folder
```

### 3. Install Dependencies
```bash
python -m pip install playwright
python -m playwright install
```

> **Windows users**: If `python` doesn't work, use `py` instead:
> ```bash
> py -m pip install playwright
> py -m playwright install
> ```

## 🎮 Usage

### First Run

**1. Launch the script:**
```bash
python main.py   # or: py main.py
```

**2. Login (visible browser required):**
- Browser opens automatically
- Log in to Imgur (including 2FA if enabled)
- Press ENTER in terminal when done
- Session saved to `imgur_storage_state.json`

> **Why visible browser?** Imgur blocks automated login (no API/OAuth), requires 2FA, and has anti-bot protection. Once logged in, the session works for headless runs.

**3. Configure your run:**
- ✅ Username auto-detected from session
- ✅ Choose **DRY RUN** (test) or **DELETION MODE** (real)
- ✅ Set max items to process per run
- ✅ Enable/disable headless mode
- ✅ Settings saved automatically for next time

---

### 🔍 How It Works

| Type | Behavior |
|------|----------|
| **Individual Images** | Clicks "Delete image" button directly |
| **Albums** | Deletes album container (ungroups), images become individual posts |
| **Processing Order** | Top-left first, visual grid order |
| **Navigation** | Auto-returns to posts grid after each deletion |

### 🧪 Dry-Run Mode (Recommended First!)

Dry-run simulates deletions without actually removing anything:
- ✅ Opens modals and interacts with UI
- ✅ Clicks "Cancel" instead of confirming
- ✅ Shows exactly what *would* be deleted

**Always test with dry-run first** to verify the script works on your account.

### 🖥️ VPS / Remote Server Usage

**Login** must be done locally (requires visible browser).

**For headless deletion on VPS:**
1. Log in locally and get `imgur_storage_state.json`
2. Transfer session file + `main.py` to VPS
3. Run in headless mode

> ⚠️ **Unconfirmed**: May depend on session expiration, IP restrictions, or cookie flags. If session expires, re-login locally and transfer fresh file.

## ⚙️ Configuration

Settings auto-save to `imgur_delete_config.json`:
- Username
- Storage file path
- Dry-run preference
- Max items limit
- Headless mode

Reuse saved settings on next run or edit as needed.

## 📁 File Structure

```
imgur-auto-delete/
├── main.py                      # Main script
├── imgur_storage_state.json    # Login session (auto-generated, gitignored)
├── imgur_delete_config.json    # Config settings (auto-generated, gitignored)
└── README.md                   # Documentation
```

## 🛡️ Safety Features

- 🧪 **Dry-run mode** — test without deleting
- ⚠️ **Confirmation prompts** — double-check before real deletions
- 🛑 **Ctrl+C support** — stop safely anytime
- 🎚️ **Configurable limits** — prevent accidental mass deletion

## 📝 Important Notes

- Posts processed in **top-left visual order**
- Albums are **ungrouped** (post container deleted, images remain)
- Album images appear as **individual posts** after ungrouping
- Built-in delays respect rate limits

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| **"No more posts found"** | Page needs time to load. Script auto-retries by scrolling. |
| **Login issues** | Delete `imgur_storage_state.json` and re-login when prompted. |
| **Browser not found** | Run `playwright install` (or `py -m playwright install`). |
| **Commands not working** | Use actual terminal/PowerShell, not a text editor. |
| **Session expired** | Delete `imgur_storage_state.json` and login again. |

## 📄 License

See [LICENSE](LICENSE) for details. This tool is provided "as is" for personal account management only. **Use at your own risk.**

---

<div align="center">

**Made with 🧠 for privacy-conscious Imgur users**

If this saved you time (or money), consider ⭐ starring the repo!

</div>
