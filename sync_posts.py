#!/usr/bin/env python3
"""
Sync latest blog posts from creditkaagapay.com to CashOyo via Post Push API.
"""

import json
import os
import sys
import requests
from datetime import datetime

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
WP_API = "https://www.creditkaagapay.com/wp-json/wp/v2"
CASHOYO_API = "https://service-test.mocasa.com/app/cashoyo/post/push"
CASHOYO_SECRET = os.environ.get("CASHOYO_SECRET", "")
AUTHOR_NAME = "Credit Kaagapay"
PUSHED_FILE = os.path.join(os.path.dirname(__file__) or ".", "pushed.json")


def load_pushed():
    """Load record of already-pushed article URLs."""
    if os.path.exists(PUSHED_FILE):
        try:
            with open(PUSHED_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_pushed(data):
    """Save pushed record to disk."""
    with open(PUSHED_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def fetch_latest_posts(count=10):
    """Fetch latest blog posts from WordPress REST API."""
    params = {
        "per_page": count,
        "orderby": "date",
        "order": "desc",
        "_embed": "wp:featuredmedia",  # include featured image in response
    }
    resp = requests.get(f"{WP_API}/posts", params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def get_featured_image_url(post):
    """Extract featured image URL from embedded WP response."""
    try:
        media = post["_embedded"]["wp:featuredmedia"][0]
        return media.get("source_url", "")
    except (KeyError, IndexError, TypeError):
        return ""


def format_publish_time(wp_date_str):
    """Convert WP date string to yyyy-MM-dd HH:mm:ss format."""
    try:
        dt = datetime.fromisoformat(wp_date_str)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return ""


def push_to_cashoyo(post):
    """Push a single post to CashOyo API. Returns True on success."""
    title = post.get("title", {}).get("rendered", "")
    content = post.get("content", {}).get("rendered", "")
    link = post.get("link", "")
    cover_url = get_featured_image_url(post)
    publish_time = format_publish_time(post.get("date", ""))

    payload = {
        "secret": CASHOYO_SECRET,
        "title": title,
        "content": content,
        "author": AUTHOR_NAME,
        "coverImageUrl": cover_url,
        "url": link,
        "publishTime": publish_time,
    }

    print(f"  Pushing: {title[:60]}...")
    try:
        resp = requests.post(CASHOYO_API, json=payload, timeout=30)
        result = resp.json()
        if result.get("code") == 0:
            print(f"  ✅ Success")
            return True
        else:
            print(f"  ❌ Failed: code={result.get('code')}, msg={result.get('msg')}")
            return False
    except Exception as e:
        print(f"  ❌ Request error: {e}")
        return False


def main():
    if not CASHOYO_SECRET:
        print("❌ CASHOYO_SECRET not set")
        sys.exit(1)

    # Load pushed records
    pushed = load_pushed()
    print(f"📋 Already pushed: {len(pushed)} articles")

    # Fetch latest posts
    print(f"\n📡 Fetching latest posts from creditkaagapay.com...")
    posts = fetch_latest_posts(10)
    print(f"   Found {len(posts)} posts")

    # Filter out already-pushed posts
    new_posts = [p for p in posts if p.get("link", "") not in pushed]
    if not new_posts:
        print("\n✅ No new posts to push. All up to date.")
        return

    print(f"\n🚀 {len(new_posts)} new post(s) to push:\n")

    success_count = 0
    for post in new_posts:
        link = post.get("link", "")
        title = post.get("title", {}).get("rendered", "")

        if push_to_cashoyo(post):
            pushed[link] = {
                "title": title,
                "pushed_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            }
            success_count += 1

    # Save updated records
    save_pushed(pushed)
    print(f"\n📊 Result: {success_count}/{len(new_posts)} pushed successfully")
    print(f"   Total pushed records: {len(pushed)}")

    if success_count < len(new_posts):
        sys.exit(1)


if __name__ == "__main__":
    main()
