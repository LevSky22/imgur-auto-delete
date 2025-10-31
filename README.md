# Imgur Bulk Deletion Tool

A cross-platform Python tool for bulk deleting Imgur posts with an interactive setup and dry-run support. Processes posts in visual order (top-left first) and handles both individual images and albums.

- **Real-world usage**: I successfully processed 500 deletions in a single headless session with no issues


## Features

- **Interactive Setup**: Auto-detects username and provides guided configuration
- **Dry-Run Mode**: Test the deletion process without actually deleting anything
- **Smart Processing**: Handles both individual images and albums intelligently
- **Visual Ordering**: Processes posts in top-left grid order for predictable results
- **Session Management**: Saves login session to avoid repeated authentication
- **Config Persistence**: Remembers your settings between runs
- **Headless/Headful**: Works with or without visible browser window
- **Safe Interruption**: Press Ctrl+C at any time to stop safely

## Requirements

- Python 3.7+
- Playwright

## Installation

1. **Download the script**:
   - Download `main.py` into a folder where you want your settings saved
   - The script will create configuration files in the same directory

2. **Open terminal/PowerShell**:
   - **Windows**: Open PowerShell or Command Prompt
   - **macOS/Linux**: Open Terminal
   - Navigate to the folder containing `main.py`:
   ```bash
   cd path/to/your/folder
   ```

3. **Install Python dependencies**:
   ```bash
   python -m pip install playwright
   ```
   
   **Note for Windows users**: If `python` doesn't work, try `py`:
   ```bash
   py -m pip install playwright
   ```

4. **Install Playwright browser binaries**:
   ```bash
   python -m playwright install
   ```
   
   **Note for Windows users**: If `python` doesn't work, try `py`:
   ```bash
   py -m playwright install
   ```

## Usage

### First Time Setup

1. **Run the script** (in terminal/PowerShell):
   ```bash
   python main.py
   ```
   
   **Note for Windows users**: Depending on your PATH configuration, you may need to use `py` instead of `python`:
   ```bash
   py main.py
   ```

2. **Login**:
   - A browser window will open (must be visible - headless login is not possible)
   - Log in to your Imgur account (including 2FA if enabled)
   - Press ENTER in the terminal when logged in
   - Your session will be saved to `imgur_storage_state.json`
   
   **Note**: Login must be done in a visible browser window due to:
   - Imgur no longer provides API/OAuth access for automated login
   - 2FA requires manual input
   - Anti-bot protection (captchas, security checks)
   - However, once logged in, the session can be used for headless deletion runs

3. **Configure**:
   - Username will be auto-detected from your session
   - Choose between DRY RUN (safe testing) or DELETION MODE (actual deletion)
   - Set maximum number of items to process
   - Choose headless or visible browser mode
   - Your configuration will be saved for future runs

### How It Works

- **Individual Images**: Deletes using the "Delete image" button directly
- **Albums**: Deletes the album container (ungroups it), making images appear as individual posts
- **Processing Order**: Starts from top-left and processes in visual grid order
- **Navigation**: Automatically returns to the posts grid after each deletion

### Dry-Run Mode

In dry-run mode, the script:
- Opens modals and interacts with the UI (to verify everything works)
- Clicks "Cancel" instead of confirming deletions
- Shows what *would* be deleted without actually deleting anything

This lets you verify the script works correctly on your account before doing real deletions.

### Running on VPS / Remote Servers

**Login**: Must be done on a machine with a visible browser window (headless login is not possible due to Imgur's security measures).

**Headless deletion on VPS**: Once you have a valid `imgur_storage_state.json` file from a local login, you *may* be able to:
1. Transfer the session file (`imgur_storage_state.json`) to your VPS
2. Transfer the script files (`main.py`, optional: `imgur_delete_config.json`)
3. Run the script in headless mode on the VPS

**Note**: This is unconfirmed and may depend on:
- Session token validity and expiration
- IP-based security restrictions (if any)
- Cookie security flags

If the session expires, you'll need to log in again locally and transfer a fresh session file.

## Configuration

Settings are saved in `imgur_delete_config.json`:
- Username
- Storage file path
- Dry-run preference
- Max items limit
- Headless mode preference

On subsequent runs, you can use saved settings without re-entering them.

## File Structure

```
imgur-auto-delete/
├── main.py                      # Main script
├── imgur_storage_state.json    # Saved login session (auto-generated)
├── imgur_delete_config.json    # Saved configuration (auto-generated)
└── README.md                   # This file
```

## Safety Features

- **Dry-run mode** for safe testing
- **Confirmation prompts** before real deletions
- **Ctrl+C interruption** support at any time
- **Configurable limits** to prevent accidental mass deletion

## Notes

- The script processes posts in visual grid order (top-left first)
- Albums are ungrouped (post container deleted), not individual images deleted
- Individual images within albums will appear as separate posts after ungrouping
- The script respects rate limits with built-in delays between operations

## Troubleshooting

**"No more posts found"**: The page may need more time to load. The script will retry by scrolling.

**Login issues**: Delete `imgur_storage_state.json` and log in again when prompted.

**Browser not found**: Make sure you ran `playwright install` in your terminal/PowerShell.

**Commands not working**: Make sure you're running commands in terminal (macOS/Linux) or PowerShell/Command Prompt (Windows), not in a text editor.

## License

See [LICENSE](LICENSE) file for details. This tool is provided "as is" for personal account management only. Use at your own risk.

