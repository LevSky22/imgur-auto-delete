# Cross-platform, Ctrl+C to stop. Interactive setup with auto-detected username.
# Processes Imgur posts (Public + Hidden) in visual order (top-left first).

import json
import re
import time
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError

# ANSI colors (works in modern Windows Terminal/PowerShell, macOS, Linux).
# If not supported, the escapes will be ignored by the terminal.
RESET = "\033[0m"
BOLD  = "\033[1m"
RED   = "\033[31m"
GRN   = "\033[32m"
YEL   = "\033[33m"
BLU   = "\033[34m"

def find_storage_files():
    """Find all potential storage state files in current directory."""
    candidates = []
    for f in Path(".").glob("*storage*.json"):
        candidates.append(str(f))
    # Also check common names
    for name in ["imgur_storage_state.json", "storage_state.json"]:
        if Path(name).exists() and name not in candidates:
            candidates.append(name)
    return candidates

def extract_username_from_storage(storage_file):
    """Extract username from storage state JSON."""
    try:
        with open(storage_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Check origins for username pattern (e.g., "https://username.imgur.com")
        for origin_data in data.get("origins", []):
            origin = origin_data.get("origin", "")
            match = re.search(r"https://([^.]+)\.imgur\.com", origin)
            if match:
                return match.group(1)
        
        # Check cookies for domain patterns
        for cookie in data.get("cookies", []):
            domain = cookie.get("domain", "")
            if ".imgur.com" in domain:
                match = re.search(r"([^.]+)\.imgur\.com", domain)
                if match:
                    username = match.group(1)
                    if username not in ("www", "i", "api", "m"):
                        return username
    except Exception:
        pass
    return None

def prompt_yes_no(prompt, default=False):
    """Interactive yes/no prompt."""
    default_text = "[Y/n]" if default else "[y/N]"
    while True:
        try:
            response = input(f"{prompt} {default_text}: ").strip().lower()
        except KeyboardInterrupt:
            raise  # Re-raise to be caught by main handler
        if not response:
            return default
        if response in ("y", "yes"):
            return True
        if response in ("n", "no"):
            return False
        print(f"{YEL}Please enter 'y' or 'n'{RESET}")

def prompt_int(prompt, default, min_val=1, max_val=None):
    """Interactive integer prompt."""
    while True:
        try:
            response = input(f"{prompt} [{default}]: ").strip()
        except KeyboardInterrupt:
            raise  # Re-raise to be caught by main handler
        if not response:
            return default
        try:
            val = int(response)
            if val < min_val:
                print(f"{YEL}Must be at least {min_val}{RESET}")
                continue
            if max_val is not None and val > max_val:
                print(f"{YEL}Must be at most {max_val}{RESET}")
                continue
            return val
        except ValueError:
            print(f"{YEL}Please enter a valid number{RESET}")

CONFIG_FILE = "imgur_delete_config.json"

def load_config():
    """Load saved configuration if it exists."""
    if Path(CONFIG_FILE).exists():
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None
    return None

def save_config(username, storage_file, dry_run, max_items, headless):
    """Save configuration to file."""
    config = {
        "username": username,
        "storage_file": storage_file,
        "dry_run": dry_run,
        "max_items": max_items,
        "headless": headless
    }
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        print(f"{GRN}✓ Configuration saved to '{CONFIG_FILE}'{RESET}\n")
    except Exception as e:
        print(f"{YEL}⚠ Could not save config: {e}{RESET}")

def do_login(storage_file="imgur_storage_state.json"):
    """Perform interactive login and save session."""
    print(f"\n{BOLD}{BLU}╔══════════════════════════════════════════════════════════════╗{RESET}")
    print(f"{BOLD}{BLU}║              Imgur Login & Session Save                   ║{RESET}")
    print(f"{BOLD}{BLU}╚══════════════════════════════════════════════════════════════╝{RESET}\n")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        print(f"{GRN}Opening Imgur sign-in page...{RESET}")
        page.goto("https://imgur.com/signin", wait_until="domcontentloaded")

        print(
            f"\n{BOLD}🖱️  Please log in manually in the opened browser window{RESET}"
            f"\n   (complete 2FA if needed)."
            f"\n   When you're fully logged in (e.g., you can see your profile avatar),"
            f"\n   come back here and press ENTER.\n"
        )

        try:
            input(f"{BLU}➡️  Press ENTER once you have finished logging in: {RESET}")
        except KeyboardInterrupt:
            print(f"\n\n{YEL}⛔ Login cancelled by user. Exiting.{RESET}")
            browser.close()
            return False

        # Save cookies + localStorage to file
        context.storage_state(path=storage_file)
        print(f"\n{GRN}✅ Session saved to '{storage_file}'.{RESET}")
        browser.close()
        return True

def interactive_setup():
    """Interactive setup session to configure deletion parameters."""
    print(f"\n{BOLD}{BLU}╔══════════════════════════════════════════════════════════════╗{RESET}")
    print(f"{BOLD}{BLU}║         Imgur Bulk Deletion - Interactive Setup            ║{RESET}")
    print(f"{BOLD}{BLU}╚══════════════════════════════════════════════════════════════╝{RESET}\n")
    
    # Check for saved config and use as defaults
    saved_config = load_config()
    defaults = {
        "username": None,
        "storage_file": None,
        "dry_run": True,
        "max_items": 10,
        "headless": False
    }
    
    if saved_config:
        print(f"{GRN}✓ Found saved configuration in '{CONFIG_FILE}'{RESET}")
        print(f"{BOLD}Saved settings:{RESET}")
        print(f"  👤  Username: {BOLD}{saved_config.get('username', 'N/A')}{RESET}")
        print(f"  🚩  Mode:     {YEL}🧪 DRY RUN{RESET}" if saved_config.get('dry_run', True) else f"  🚩  Mode:     {RED}🗑️  DELETION MODE{RESET}")
        print(f"  🧮  Limit:    {saved_config.get('max_items', 'N/A')} item(s)")
        print(f"  🖥️  Headless: {'Yes' if saved_config.get('headless', False) else 'No'}")
        print(f"  📁  Storage:  {saved_config.get('storage_file', 'N/A')}\n")
        
        # Validate storage file still exists
        saved_storage = saved_config.get("storage_file")
        if saved_storage and Path(saved_storage).exists():
            if prompt_yes_no("Use these saved settings without editing?", default=True):
                return (
                    saved_config.get("username"),
                    saved_storage,
                    saved_config.get("dry_run", True),
                    saved_config.get("max_items", 10),
                    saved_config.get("headless", False)
                )
            else:
                print(f"{BLU}Using saved values as defaults. Edit as needed.{RESET}\n")
        else:
            print(f"{YEL}⚠ Saved storage file not found. Will reconfigure.{RESET}\n")
        
        # Load saved values as defaults
        defaults.update({
            "username": saved_config.get("username"),
            "storage_file": saved_storage if saved_storage and Path(saved_storage).exists() else None,
            "dry_run": saved_config.get("dry_run", True),
            "max_items": saved_config.get("max_items", 10),
            "headless": saved_config.get("headless", False)
        })
    
    # Find storage files
    storage_files = find_storage_files()
    if not storage_files:
        print(f"{YEL}⚠️  No storage state file found.{RESET}\n")
        if prompt_yes_no("Would you like to log in now?", default=True):
            default_file = "imgur_storage_state.json"
            if do_login(default_file):
                storage_files = [default_file]
            else:
                raise SystemExit(f"{RED}Login cancelled or failed.{RESET}")
        else:
            raise SystemExit(f"{RED}Session file required. Run 'save_session.py' first or choose to login.{RESET}")
    
    # Use saved storage file as default if available, otherwise first found
    if defaults["storage_file"] and defaults["storage_file"] in storage_files:
        storage_file = defaults["storage_file"]
        print(f"{GRN}✓ Using saved storage file: {storage_file}{RESET}")
        if len(storage_files) > 1:
            if not prompt_yes_no("Use a different storage file?", default=False):
                pass  # keep using saved one
            else:
                print(f"{YEL}Available storage files:{RESET}")
                for i, f in enumerate(storage_files, 1):
                    marker = " ← current" if f == storage_file else ""
                    print(f"  {i}. {f}{marker}")
                while True:
                    try:
                        choice = int(input(f"\nSelect file [1-{len(storage_files)}]: ").strip())
                        if 1 <= choice <= len(storage_files):
                            storage_file = storage_files[choice - 1]
                            break
                        print(f"{YEL}Invalid choice{RESET}")
                    except ValueError:
                        print(f"{YEL}Please enter a number{RESET}")
                    except KeyboardInterrupt:
                        raise  # Re-raise to be caught by main handler
    else:
        storage_file = storage_files[0]
        if len(storage_files) > 1:
            print(f"{YEL}Multiple storage files found:{RESET}")
            for i, f in enumerate(storage_files, 1):
                print(f"  {i}. {f}")
            while True:
                try:
                    choice = int(input(f"\nSelect file [1-{len(storage_files)}]: ").strip())
                    if 1 <= choice <= len(storage_files):
                        storage_file = storage_files[choice - 1]
                        break
                    print(f"{YEL}Invalid choice{RESET}")
                except ValueError:
                    print(f"{YEL}Please enter a number{RESET}")
                except KeyboardInterrupt:
                    raise  # Re-raise to be caught by main handler
    
    print(f"{GRN}✓ Using storage file: {storage_file}{RESET}\n")
    
    # Extract username - use saved as default if available
    username = extract_username_from_storage(storage_file)
    if not username:
        default_username = defaults["username"] or ""
        prompt_text = f"{BLU}Enter your Imgur username" + (f" [{default_username}]" if default_username else "") + f": {RESET}"
        try:
            username = input(prompt_text).strip() or default_username
        except KeyboardInterrupt:
            raise  # Re-raise to be caught by main handler
        if not username:
            raise SystemExit(f"{RED}Username is required.{RESET}")
    else:
        # If saved username exists and matches detected, use it as default
        if defaults["username"] and defaults["username"].lower() == username.lower():
            print(f"{GRN}✓ Detected username: {BOLD}{username}{RESET} (matches saved config)")
            if not prompt_yes_no("Use this username?", default=True):
                default_username = defaults["username"] or username
                try:
                    username = input(f"{BLU}Enter your Imgur username [{default_username}]: {RESET}").strip() or default_username
                except KeyboardInterrupt:
                    raise  # Re-raise to be caught by main handler
        else:
            print(f"{GRN}✓ Detected username: {BOLD}{username}{RESET}")
            if defaults["username"]:
                print(f"{BLU}  (Saved username was: {defaults['username']}){RESET}")
            if not prompt_yes_no("Use this username?", default=True):
                default_username = defaults["username"] or username
                try:
                    username = input(f"{BLU}Enter your Imgur username [{default_username}]: {RESET}").strip() or default_username
                except KeyboardInterrupt:
                    raise  # Re-raise to be caught by main handler
        
        if not username:
            raise SystemExit(f"{RED}Username is required.{RESET}")
    
    # Get options with saved values as defaults
    print(f"\n{BOLD}Configuration Options:{RESET}\n")
    
    dry_run = prompt_yes_no(
        f"{YEL}🧪 Enable DRY RUN mode? (no deletions, just simulation)",
        default=defaults["dry_run"]
    )
    
    if not dry_run:
        print(f"\n{RED}{BOLD}⚠️  WARNING: DELETION MODE ENABLED ⚠️{RESET}")
        print(f"{RED}This will PERMANENTLY DELETE your posts!{RESET}\n")
        confirm_del = prompt_yes_no(f"{RED}Are you SURE you want to proceed with REAL deletions?", default=True)
        if not confirm_del:
            print(f"{YEL}Switching to DRY RUN mode for safety.{RESET}\n")
            dry_run = True
    
    max_items = prompt_int(
        f"{BLU}Maximum number of items to process",
        default=defaults["max_items"],
        min_val=1
    )
    
    # Default headless to True for dry runs (no need to see browser)
    # Use saved preference if available, otherwise default to dry_run value
    if defaults["headless"] is not None:
        headless_default = defaults["headless"]
    else:
        headless_default = dry_run  # True for dry runs, False for real deletions
    
    headless_prompt = f"{BLU}Run in headless mode? (no browser window)"
    if dry_run:
        headless_prompt += f" {GRN}[recommended for dry runs]{RESET}"
    headless = prompt_yes_no(headless_prompt, default=headless_default)
    
    print(f"\n{BOLD}{GRN}✓ Configuration complete!{RESET}\n")
    print(f"{BOLD}Summary:{RESET}")
    print(f"  👤  Username: {BOLD}{username}{RESET}")
    print(f"  🚩  Mode:     {YEL}🧪 DRY RUN{RESET}" if dry_run else f"  🚩  Mode:     {RED}🗑️  DELETION MODE{RESET}")
    print(f"  🧮  Limit:    {max_items} item(s)")
    print(f"  🖥️  Headless: {'Yes' if headless else 'No'}")
    print(f"  📁  Storage:  {storage_file}\n")
    
    final_confirm = prompt_yes_no(f"{BOLD}Proceed with these settings?", default=True)
    if not final_confirm:
        raise SystemExit(f"{YEL}Cancelled by user.{RESET}")
    
    # Automatically save config when proceeding
    save_config(username, storage_file, dry_run, max_items, headless)
    
    return username, storage_file, dry_run, max_items, headless

def print_banner(username, dry_run, max_to_process, headless):
    """Print execution banner."""
    mode = f"{YEL}🧪 DRY RUN ENABLED{RESET}" if dry_run else f"{RED}🗑️  DELETION MODE (IRREVERSIBLE){RESET}"
    print(
        f"\n{BOLD}{BLU}============================== Imgur Bulk {('Dry-Run' if dry_run else 'Delete')} =============================={RESET}\n"
        f"  👤  Username: {BOLD}{username}{RESET}\n"
        f"  🚩  Mode:     {mode}\n"
        f"  🧮  Limit:    {max_to_process} item(s) this run\n"
        f"  🖥️  Headless: {'Yes' if headless else 'No'}\n\n"
        f"{GRN}{BOLD}👉 Press Ctrl+C in this terminal at ANY time to stop safely.{RESET}\n"
        f"{BLU}==========================================================================={RESET}\n"
    )

def get_posts_url(username):
    return f"https://imgur.com/user/{username}/posts"
POST_HREF_PAT = re.compile(r"^/(gallery/|a/|post/|image/|[A-Za-z0-9]{5,})")
BAD_PREFIXES = (
    "/upload", "/notifications", "/settings", "/account/",
    "/user/", "/t/", "/topics", "/privacy", "/terms", "/arcade",
)

def polite_sleep(sec: float):
    time.sleep(sec)

# Default config values (used if not running interactively)
SETTLE_DELAY = 0.4        # seconds to let SPA settle after nav

def safe_goto(page, url, timeout_ms=30000):
    """Navigate robustly without relying on 'networkidle' (SPAs rarely idle)."""
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
    except TimeoutError:
        page.goto(url, timeout=timeout_ms)
    polite_sleep(SETTLE_DELAY)

def select_all_tab(page):
    """Switch to the 'All' tab so Public + Hidden appear."""
    # 1) role=tab "All"
    try:
        tab = page.get_by_role("tab", name=re.compile(r"^\s*all\s*$", re.I)).first
        if tab and tab.is_visible():
            tab.click(timeout=1500)
            polite_sleep(0.5)
            return
    except Exception:
        pass
    # 2) text "All"
    for sel in ["a:has-text('All')", "button:has-text('All')", "text=/^\\s*All\\s*$/i"]:
        try:
            el = page.locator(sel).first
            if el and el.is_visible():
                el.click(timeout=1500)
                polite_sleep(0.5)
                return
        except Exception:
            pass

def go_to_posts_all(page, username):
    safe_goto(page, get_posts_url(username))
    select_all_tab(page)
    polite_sleep(0.4)

def scroll_to_top(page):
    page.evaluate("() => window.scrollTo(0, 0)")
    polite_sleep(0.2)

def find_post_links_sorted(page):
    """
    Return [(href, x, y)] for visible grid items, sorted top-left first.
    Filters non-post links and de-dupes by href.
    """
    sel = (
        'a[href^="/gallery/"], a[href^="/a/"], a[href^="/post/"], '
        'a[href^="/image/"], a[href^="/"][href*="/"]'
    )
    items = []
    anchors = page.locator(sel)
    count = anchors.count()
    for i in range(count):
        a = anchors.nth(i)
        try:
            if not a.is_visible():
                continue
        except Exception:
            continue
        href = (a.get_attribute("href") or "").split("#")[0].split("?")[0]
        if not href.startswith("/") or href.startswith(BAD_PREFIXES):
            continue
        if not POST_HREF_PAT.search(href):
            continue
        # Bounding box for ordering (can be None if detached)
        try:
            box = a.bounding_box()
        except Exception:
            box = None
        if not box:
            continue
        items.append((href, box["x"], box["y"]))

    # Sort top-left first (y then x), then de-dupe
    items.sort(key=lambda t: (round(t[2]), round(t[1])))
    seen, ordered = set(), []
    for href, x, y in items:
        if href not in seen:
            seen.add(href)
            ordered.append((href, x, y))
    return ordered

def safe_click(page, locator, description="element", dry_run=False, timeout=2000):
    """
    Conditionally click an element - only clicks if not in dry_run mode.
    Returns True if clicked (or would click in dry-run), False otherwise.
    """
    try:
        if locator.is_visible(timeout=timeout):
            if dry_run:
                print(f" [DRY-RUN] Would click {description}")
                return True
            else:
                locator.click(timeout=timeout)
                return True
    except Exception:
        pass
    return False

def delete_post_container(page, dry_run):
    """
    Delete a post/album container by clicking "Delete post" button.
    Returns True if deletion was initiated, False otherwise.
    """
    polite_sleep(0.5)  # Wait for page to settle
    
    delete_post_clicked = False
    
    # Try multiple selectors for the delete post button
    delete_post_selectors = [
        'button:has-text("Delete post")',
        'text="Delete post"',
        '[role="button"]:has-text("Delete post")',
        'button[aria-label*="Delete post" i]',
        'a:has-text("Delete post")',
        '*:has-text("Delete post"):visible',
    ]
    
    for selector in delete_post_selectors:
        try:
            delete_post_btn = page.locator(selector).first
            if safe_click(page, delete_post_btn, f"'Delete post' button ({selector})", dry_run):
                if dry_run:
                    print(f" [DRY-RUN] {GRN}✓ Found and clicked 'Delete post' button{RESET}")
                else:
                    print(f" {GRN}✓ Found and clicked 'Delete post' button{RESET}")
                polite_sleep(1.0)
                delete_post_clicked = True
                break
        except Exception:
            continue
    
    # Also try role-based
    if not delete_post_clicked:
        try:
            delete_post_btn = page.get_by_role("button", name=re.compile("Delete post", re.I)).first
            if safe_click(page, delete_post_btn, "'Delete post' button (role-based)", dry_run):
                if dry_run:
                    print(f" [DRY-RUN] {GRN}✓ Found and clicked 'Delete post' button (role-based){RESET}")
                else:
                    print(f" {GRN}✓ Found and clicked 'Delete post' button (role-based){RESET}")
                polite_sleep(1.0)
                delete_post_clicked = True
        except Exception:
            pass
    
    if delete_post_clicked:
        # Wait for modal to appear
        polite_sleep(1.5)
        
        # Look for confirmation button in modal
        confirmation_clicked = False
        confirmation_selectors = [
            ('role', 'button', 'Delete Post Only'),
            ('role', 'button', 'Delete Post'),
            ('selector', 'button:has-text("Delete Post Only")'),
            ('selector', 'button:has-text("Delete Post")'),
        ]
        
        for selector_type, *args in confirmation_selectors:
            try:
                if selector_type == 'role':
                    btn = page.get_by_role('button', name=args[0]).first
                else:  # selector
                    btn = page.locator(args[0]).first
                
                if safe_click(page, btn, f"'{args[0]}' button in modal", dry_run):
                    confirmation_clicked = True
                    if dry_run:
                        print(f" [DRY-RUN] {GRN}✓ Deleted post/album{RESET}")
                    else:
                        print(f" {GRN}✓ Deleted post/album{RESET}")
                    polite_sleep(1.0)
                    break
            except Exception:
                continue
        
        return confirmation_clicked or delete_post_clicked  # Return True if any action succeeded
    
    return False

def delete_one(page, href, dry_run, username=None):
    """
    Delete an image or post from Imgur.
    Returns: (success: bool, images_deleted: int)
    For single images: returns (True, 1) or (False, 0)
    For albums: returns (True, 0) when post is ungrouped (no images deleted), or (False, 0) on failure
    """
    url = "https://imgur.com" + href
    safe_goto(page, url, timeout_ms=20000)
    polite_sleep(0.8)  # Give page time to fully load

    # Determine if this is an image (single) or post/album
    # Albums: /a/xxxxx or /gallery/xxxxx
    # Direct images: /xxxxxxx (7 char ID, no /a/ prefix) or /image/xxxxx
    is_album = href.startswith("/a/") or href.startswith("/gallery/")
    is_image = "/image/" in href or (href.startswith("/") and len(href.split("/")[-1]) == 7 and not is_album)
    
    deleted = False
    
    if is_image:
        # For image pages: "Delete image" is directly available
        # Flow (from codegen): Click "Delete image" → Click "Yes, Delete It" → Navigate back to /posts
        if dry_run:
            print(f" [DRY-RUN] Image page detected: {url}")
        else:
            print(f" {BLU}Individual image page - using 'Delete image' button{RESET}")
        
        # Step 1: Click the "Delete image" button (role-based, as per codegen)
        try:
            delete_btn = page.get_by_role("button", name="Delete image").first
            if not delete_btn.is_visible(timeout=3000):
                if dry_run:
                    print(f" [DRY-RUN] {YEL}⚠ 'Delete image' button not visible{RESET}")
                else:
                    print(f" {YEL}⚠ 'Delete image' button not visible{RESET}")
                return False, 0
            
            if dry_run:
                # In dry-run, actually click to open modal
                try:
                    delete_btn.click(timeout=3000)
                    print(f" [DRY-RUN] {GRN}✓ Clicked 'Delete image' button (opened modal){RESET}")
                    polite_sleep(0.6)  # Brief wait for modal to appear
                except Exception as e:
                    print(f" [DRY-RUN] {YEL}⚠ Could not click 'Delete image' button: {e}{RESET}")
                    return False, 0
            else:
                if safe_click(page, delete_btn, "'Delete image' button", dry_run):
                    print(f" {GRN}✓ Clicked 'Delete image' button{RESET}")
                    polite_sleep(0.6)  # Brief wait for modal to appear
                else:
                    print(f" {YEL}⚠ Could not click 'Delete image' button{RESET}")
                    return False, 0
        except Exception as e:
            if dry_run:
                print(f" [DRY-RUN] {YEL}⚠ Could not find 'Delete image' button: {e}{RESET}")
            else:
                print(f" {YEL}⚠ Could not find 'Delete image' button: {e}{RESET}")
            return False, 0
        
        # Step 2: In dry-run, click Cancel; otherwise click "Yes, Delete It"
        if dry_run:
            # In dry-run mode, click Cancel to close the modal without deleting
            polite_sleep(0.6)  # Wait for modal to appear
            cancel_clicked = False
            cancel_selectors = [
                'button:has-text("Cancel")',
                'text="Cancel"',
                '[role="button"]:has-text("Cancel")',
                'button[aria-label*="Cancel" i]',
                'button:has-text("Close")',
                '[role="dialog"] button:has-text("Cancel")',
            ]
            
            for selector in cancel_selectors:
                try:
                    cancel_btn = page.locator(selector).first
                    if cancel_btn.is_visible(timeout=2000):
                        # In dry-run, actually click Cancel to close modal
                        cancel_btn.click(timeout=2000)
                        print(f" [DRY-RUN] {GRN}✓ Clicked 'Cancel' - modal closed (simulated deletion){RESET}")
                        polite_sleep(0.3)
                        cancel_clicked = True
                        break
                except Exception:
                    continue
            
            # Also try role-based
            if not cancel_clicked:
                try:
                    cancel_btn = page.get_by_role("button", name=re.compile("Cancel", re.I)).first
                    if cancel_btn.is_visible(timeout=2000):
                        # In dry-run, actually click Cancel to close modal
                        cancel_btn.click(timeout=2000)
                        print(f" [DRY-RUN] {GRN}✓ Clicked 'Cancel' - modal closed (simulated deletion){RESET}")
                        polite_sleep(0.3)
                        cancel_clicked = True
                except Exception:
                    pass
            
            if not cancel_clicked:
                print(f" [DRY-RUN] {YEL}⚠ Could not find 'Cancel' button - modal may close on its own{RESET}")
                polite_sleep(0.3)
            
            # Return success since we simulated the deletion flow
            return True, 1
        else:
            # Live mode: Click "Yes, Delete It" button
            try:
                confirm_btn = page.get_by_role("button", name="Yes, Delete It").first
                if not confirm_btn.is_visible(timeout=3000):
                    print(f" {YEL}⚠ 'Yes, Delete It' button not visible{RESET}")
                    return False, 0
                
                if safe_click(page, confirm_btn, "'Yes, Delete It' button", dry_run):
                    print(f" {GRN}✓ Clicked 'Yes, Delete It' - deleting image{RESET}")
                    polite_sleep(0.3)  # Brief wait for click to register
                else:
                    print(f" {YEL}⚠ Could not click 'Yes, Delete It' button{RESET}")
                    return False, 0
            except Exception as e:
                print(f" {YEL}⚠ Could not find 'Yes, Delete It' button: {e}{RESET}")
                return False, 0
        
        # Deletion initiated - main loop will navigate back to /posts
        return True, 1
    
    elif is_album:
        # For albums: Delete the post container (ungroup the album)
        # This only deletes the post grouping - it does NOT delete individual images
        polite_sleep(1.2)  # Let album page fully load
        
        print(f" {BLU}Analyzing album page: {page.url}{RESET}")
        
        # Count images in album for reporting purposes
        image_count = None
        try:
            three_dots_all = page.locator('text="..."').all()
            detected_image_count = len(three_dots_all)
            if detected_image_count > 0:
                print(f" {BLU}Album contains {detected_image_count} image(s) - deleting post container...{RESET}")
                image_count = detected_image_count
        except Exception:
            pass
        
        # Delete the post container - this ungroups the album
        # The images themselves are not deleted, only the post/album grouping
        print(f" {BLU}Deleting post container to ungroup album...{RESET}")
        deleted = delete_post_container(page, dry_run)
        
        if deleted:
            # IMPORTANT: We return True, 0 because:
            # - True: Post container deletion (ungrouping) succeeded
            # - 0: No images were deleted (only the post grouping was removed)
            if dry_run:
                print(f" [DRY-RUN] {BLU}✓ Album post deleted (ungrouped){RESET}")
            else:
                print(f" {BLU}✓ Album post deleted (ungrouped){RESET}")
            return True, 0
        else:
            print(f" {YEL}⚠ Could not ungroup album/post container{RESET}")
            return False, 0
    else:
        # For other post types: Try three dots → Delete image
        # Strategy 1: Find three dots menu button
        three_dots_selectors = [
            'button[aria-label*="more" i]',
            'button[aria-label*="More" i]',
            'button[aria-label*="options" i]',
            '[aria-label*="more options" i]',
            'button:has([class*="more"])',
            'button:has([class*="menu"])',
            'button:has([class*="dots"])',
            '[role="button"]:has([class*="more"])',
            'button:has-text("⋯")',
            'button:has-text("...")',
        ]
        
        three_dots_clicked = False
        for selector in three_dots_selectors:
            try:
                btn = page.locator(selector).first
                if safe_click(page, btn, f"three dots menu ({selector})", dry_run, timeout=1500):
                    polite_sleep(0.8)
                    three_dots_clicked = True
                    break
            except Exception:
                continue
        
        if not three_dots_clicked:
            try:
                buttons = page.locator('button').all()
                for btn in buttons:
                    try:
                        aria_label = btn.get_attribute("aria-label") or ""
                        if "more" in aria_label.lower() or "menu" in aria_label.lower() or "options" in aria_label.lower():
                            if safe_click(page, btn, "three dots menu (button scan)", dry_run, timeout=500):
                                polite_sleep(0.8)
                                three_dots_clicked = True
                                break
                    except Exception:
                        continue
            except Exception:
                pass
        
        if three_dots_clicked:
            # Find "Delete image" in context menu
            delete_image_selectors = [
                'text="Delete image"',
                'button:has-text("Delete image")',
                '[role="menuitem"]:has-text("Delete image")',
                '[role="menu"] button:has-text("Delete image")',
                'a:has-text("Delete image")',
                '*:has-text("Delete image"):visible',
            ]
            
            clicked_delete_image = False
            for selector in delete_image_selectors:
                try:
                    delete_btn = page.locator(selector).first
                    if safe_click(page, delete_btn, f"'Delete image' button ({selector})", dry_run, timeout=1500):
                        polite_sleep(1.0)  # Wait for modal
                        clicked_delete_image = True
                        break
                except Exception:
                    continue
            
            if not clicked_delete_image:
                try:
                    delete_btn = page.get_by_role("menuitem", name=re.compile("Delete image", re.I)).first
                    if safe_click(page, delete_btn, "'Delete image' button (menuitem role)", dry_run, timeout=1500):
                        polite_sleep(1.0)
                        clicked_delete_image = True
                except Exception:
                    pass
            
            if not clicked_delete_image:
                print(f" {YEL}⚠ Could not find 'Delete image' option in menu{RESET}")
                return False, 0
            
            # Modal should now be open - click "Delete from account" (not "Remove from post")
            delete_from_account_selectors = [
                'button.DeleteImageDialog-confirm--accountRemove',  # Specific class from Imgur
                'button:has-text("Delete from account")',
                'text="Delete from account"',
                '[role="dialog"] button:has-text("Delete from account")',
                'button[aria-label*="Delete from account" i]',
                '[role="dialog"] button:has([class*="red"])',
                '[role="dialog"] button:has([class*="danger"])',
            ]
            
            for selector in delete_from_account_selectors:
                try:
                    delete_account_btn = page.locator(selector).first
                    if safe_click(page, delete_account_btn, f"'Delete from account' button ({selector})", dry_run):
                        if dry_run:
                            print(f" [DRY-RUN] {GRN}✓ Clicking 'Delete from account'{RESET}")
                        else:
                            print(f" {GRN}✓ Clicking 'Delete from account'{RESET}")
                        polite_sleep(1.0)
                        deleted = True
                        break
                except Exception:
                    continue
            
            if not deleted:
                try:
                    delete_account_btn = page.get_by_role("button", name=re.compile("Delete from account", re.I)).first
                    if safe_click(page, delete_account_btn, "'Delete from account' button (role regex)", dry_run):
                        if dry_run:
                            print(f" [DRY-RUN] {GRN}✓ Clicking 'Delete from account' via role{RESET}")
                        else:
                            print(f" {GRN}✓ Clicking 'Delete from account' via role{RESET}")
                        polite_sleep(1.0)
                        deleted = True
                except Exception:
                    print(f" {YEL}⚠ Could not find 'Delete from account' button in modal{RESET}")
        else:
            print(f" {YEL}⚠ Could not find three dots menu for {url}{RESET}")
            return False, 0
    
    if not deleted:
        print(f" {YEL}⚠ Could not find delete option for {url}{RESET}")
        return False, 0
    
    # Wait for confirmation dialog/modal to appear
    polite_sleep(0.8)
    
    # Strategy 2: Confirm deletion
    confirm_selectors = [
        'button:has-text("Yes, Delete It")',
        'button:has-text("Delete")',
        'button:has-text("Confirm")',
        'button[data-action="confirm"]',
        '[role="dialog"] button:has-text("Delete")',
        '[role="dialog"] button:has-text("Confirm")',
    ]
    
    confirmed = False
    for selector in confirm_selectors:
        try:
            cbtn = page.locator(selector).first
            if safe_click(page, cbtn, f"confirmation button ({selector})", dry_run):
                polite_sleep(1.0)  # Wait for deletion to process
                confirmed = True
                break
        except Exception:
            continue
    
    # Also try role-based confirmation
    if not confirmed:
        for label in ["Yes, Delete It", "Delete", "Confirm"]:
            try:
                cbtn = page.get_by_role("button", name=re.compile(label, re.I)).first
                if safe_click(page, cbtn, f"confirmation button (role: {label})", dry_run):
                    polite_sleep(1.0)
                    confirmed = True
                    break
            except Exception:
                continue
    
    if not confirmed:
        # Maybe it deleted on first click, or confirmation wasn't needed
        # Wait and check if deletion succeeded
        polite_sleep(2.0)
        current_url = page.url
        
        # Check for error/success indicators in page content
        try:
            page_content = page.content().lower()
            if "404" in page_content or "not found" in page_content or "deleted" in page_content:
                return True, 1  # Probably deleted (count as 1)
        except Exception:
            pass
        
        # Check if URL changed (redirected away from post)
        if url not in current_url:
            # Check if we're redirected to a valid page (not 404)
            try:
                page.wait_for_load_state("domcontentloaded", timeout=3000)
                if "404" not in page.content().lower():
                    return True, 1  # Redirected to valid page, probably deleted (count as 1)
            except Exception:
                pass
    
    # Final verification: try to navigate back to the URL and see if it still exists
    if confirmed or deleted:
        polite_sleep(1.5)  # Give deletion time to process
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=5000)
            polite_sleep(0.5)
            content_lower = page.content().lower()
            # If we see 404 or "not found", it's deleted
            if "404" in content_lower or "not found" in content_lower or "page doesn't exist" in content_lower:
                return True, 1  # Deleted (count as 1)
            # If we're still on the post page, deletion might have failed
            if url in page.url:
                print(f" {YEL}⚠ Deletion may have failed - post still accessible at {url}{RESET}")
                return False, 0
        except TimeoutError:
            # Timeout might mean 404/redirect
            return True, 1  # Probably deleted (count as 1)
        except Exception:
            # Other errors - assume it might have worked
            pass
    
    # Return success status and count
    if confirmed or deleted:
        return True, 1  # Single image/post deletion = 1 item
    else:
        return False, 0

def main():
    try:
        # Interactive setup
        username, storage_file, dry_run, max_to_process, headless = interactive_setup()
        
        print_banner(username, dry_run, max_to_process, headless)
    except KeyboardInterrupt:
        print(f"\n\n{YEL}⛔ Setup interrupted by user. Exiting.{RESET}")
        return
    except SystemExit:
        raise  # Let SystemExit propagate (used for intentional exits)
    except Exception as e:
        print(f"\n{RED}❌ Error during setup: {e}{RESET}")
        return

    try:
        if not Path(storage_file).exists():
            raise SystemExit(f"{RED}Missing {storage_file}. Run your login script first.{RESET}")

        with sync_playwright() as p:
            # Add stealth-like args to reduce detection (apply to both headless and headful)
            launch_args = {
                "args": [
                    "--disable-blink-features=AutomationControlled",
                ]
            }
            # Add headless-specific args
            if headless:
                launch_args["args"].append("--disable-dev-shm-usage")
            browser = p.chromium.launch(headless=headless, **launch_args)
            
            # Set a more realistic viewport and user agent
            context = browser.new_context(
                storage_state=storage_file,
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()

            processed = 0
            seen_heights = set()

            try:
                go_to_posts_all(page, username)
                scroll_to_top(page)

                while processed < max_to_process:
                    links = find_post_links_sorted(page)
                    if not links:
                        # Try to load more via infinite scroll
                        last_h = page.evaluate("() => document.body.scrollHeight")
                        if last_h in seen_heights:
                            print("No more posts found. Exiting.")
                            break
                        seen_heights.add(last_h)
                        page.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
                        polite_sleep(1.2)
                        continue

                    for href, x, y in links:
                        print(f"Processing {href} at ({int(x)},{int(y)}) ...")
                        ok, images_count = delete_one(page, href, dry_run, username)
                        if ok:
                            # Albums (images_count == 0) count as 1 item processed
                            if images_count == 0:
                                processed += 1
                                print(f" -> {'Simulated' if dry_run else (GRN + 'Deleted' + RESET)} post (total: {processed})")
                            else:
                                processed += images_count  # Add actual number of images deleted
                                if images_count == 1:
                                    print(f" -> {'Simulated' if dry_run else (GRN + 'Deleted' + RESET)} image (total: {processed})")
                                else:
                                    print(f" -> {'Simulated' if dry_run else (GRN + 'Deleted' + RESET)} {images_count} image(s) (total: {processed})")
                        else:
                            processed += 1  # Count attempt even if failed
                            print(f" -> {YEL}Failed{RESET} (total attempts: {processed})")

                        polite_sleep(0.3)

                        # Always return to grid and ensure All tab; go back to top for stable order
                        go_to_posts_all(page, username)
                        scroll_to_top(page)

                        if processed >= max_to_process:
                            break

                    # Attempt to pull more items for the next pass
                    last_h = page.evaluate("() => document.body.scrollHeight")
                    if last_h in seen_heights:
                        print("No further content loaded. Finished.")
                        break
                    seen_heights.add(last_h)
                    page.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
                    polite_sleep(0.6)

                print(f"\n{GRN}✅ Done. {'Simulated' if dry_run else 'Actual'} items processed: {processed}{RESET}")

            except KeyboardInterrupt:
                print(f"\n{YEL}⛔ Interrupted by user.{RESET} {'Simulated' if dry_run else 'Actual'} items processed: {processed}")
            finally:
                # Suppress all exceptions (including KeyboardInterrupt) during cleanup
                try:
                    context.close()
                except (KeyboardInterrupt, Exception):
                    pass
                try:
                    browser.close()
                except (KeyboardInterrupt, Exception):
                    pass
                print(f"{BLU}Browser closed. Exiting cleanly.{RESET}")
    except KeyboardInterrupt:
        print(f"\n\n{YEL}⛔ Interrupted by user. Exiting.{RESET}")
    except SystemExit:
        raise  # Let SystemExit propagate
    except Exception as e:
        print(f"\n{RED}❌ Error: {e}{RESET}")

if __name__ == "__main__":
    main()
