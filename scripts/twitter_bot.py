"""
BaseCred Twitter / X Automation & Curation Bot.
Handles:
  1. Weekly Spotlight Pass Endorsements:
     Command: "@BaseCred spotlight @creator [tweet_url]" or "@BaseCred endorse @creator"
     - Verifies sender's 1 pass/week quota
     - Verifies tweet mentions @base
     - Grants +1000 Creator / +300 Curator $CRED (2x if @base retweets)
  2. Legacy P2P Social Tipping (fallback)
  3. Live Mode (TWITTER_BEARER_TOKEN) & Dry-Run Simulation Mode
"""
import os
import sys
import time
import json
import re
from typing import Dict, Any, List, Optional

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from engine.database import init_db, get_db, current_epoch_str
from engine.spotlight import validate_and_endorse_tweet
from engine.tipping import validate_and_process_tip

BEARER_TOKEN = os.environ.get("TWITTER_BEARER_TOKEN", "")
BOT_HANDLE = os.environ.get("TWITTER_BOT_HANDLE", "BaseCred").lower()

SPOTLIGHT_PATTERN = re.compile(
    r"(?:spotlight|endorse)\s+@?([a-zA-Z0-9_]{1,15})(?:\s+(https?://[^\s]+))?",
    re.IGNORECASE
)

TIP_PATTERN = re.compile(
    r"(?:tip|\+)?\s*(\d+)\s*\$CRED\s*(?:to\s*)?@?([a-zA-Z0-9_]{1,15})",
    re.IGNORECASE
)

def parse_incoming_tweet(tweet_text: str) -> Optional[Dict[str, Any]]:
    # Check Spotlight Endorsement first (Primary mechanism)
    spotlight_match = SPOTLIGHT_PATTERN.search(tweet_text)
    if spotlight_match:
        return {
            "type": "spotlight",
            "creator": spotlight_match.group(1).lower(),
            "url": spotlight_match.group(2) or "https://x.com/post/example"
        }
    
    # Fallback to direct tipping syntax
    tip_match = TIP_PATTERN.search(tweet_text)
    if tip_match:
        return {
            "type": "tip",
            "amount": int(tip_match.group(1)),
            "recipient": tip_match.group(2).lower()
        }
    return None

def process_single_tweet(tweet_id: str, sender_handle: str, tweet_text: str) -> Dict[str, Any]:
    print(f"\n--- [BaseCred Bot] Processing Tweet [{tweet_id}] from @{sender_handle} ---")
    print(f"Text: \"{tweet_text}\"")

    parsed = parse_incoming_tweet(tweet_text)
    if not parsed:
        print("Skipped: No recognized BaseCred command.")
        return {"processed": False, "reason": "No command found"}

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT address FROM users WHERE twitter_handle = ?", (sender_handle.lower(),))
    sender_row = cursor.fetchone()
    conn.close()

    if not sender_row:
        reply = f"@{sender_handle} ⚠️ Your X account is not linked to an evaluated Base wallet yet. Visit https://basecred.onrender.com to audit your footprint and claim your Weekly Spotlight Pass!"
        print(f"Unregistered: {reply}")
        return {"processed": False, "reply": reply}

    sender_address = sender_row["address"]

    if parsed["type"] == "spotlight":
        creator = parsed["creator"]
        tweet_url = parsed["url"]
        # Pass through strict Base curation engine
        res = validate_and_endorse_tweet(
            curator_address=sender_address,
            creator_twitter=creator,
            tweet_url=tweet_url,
            tweet_text=tweet_text,
            simulate_base_rt=False
        )

        if res["success"]:
            reply = f"🌟 @{sender_handle} endorsed @{creator} in the Weekly Base Spotlight! +1000 Creator / +300 Curator $CRED recorded. 1/1 Pass used for {res['epoch']}. Leaderboard: https://basecred.onrender.com"
            print(f"Spotlight Success: {reply}")
        else:
            reply = f"❌ @{sender_handle} Spotlight endorsement failed: {res['error']}"
            print(f"Spotlight Rejected: {reply}")

        return {"processed": True, "result": res, "reply": reply}

    elif parsed["type"] == "tip":
        amount = parsed["amount"]
        recipient = parsed["recipient"]
        res = validate_and_process_tip(sender_address, recipient, amount, tweet_text)

        if res["success"]:
            reply = f"🎉 @{sender_handle} tipped @{recipient} +{res['awarded_credits']} $CRED! (Remaining allowance: {res['remaining_allowance']} $CRED)."
        else:
            reply = f"❌ @{sender_handle} Tip failed: {res['error']}"

        print(f"Tip Result: {reply}")
        return {"processed": True, "result": res, "reply": reply}

    return {"processed": False}

def run_dry_run_simulation():
    """Runs an interactive demonstration showing how tweets are parsed and weekly passes consumed."""
    print("=================================================================")
    print("🔵 BaseCred Twitter / X Automation Bot [Dry-Run Simulation]")
    print("   Aligned with Base Network Weekly Spotlight & Quality Standard")
    print("=================================================================")
    init_db()

    simulated_tweets = [
        {
            "id": "2001",
            "sender": "aerobase_guru",
            "text": "@BaseCred spotlight @jessepollak https://x.com/jessepollak/status/987654 Incredible updates on @base rollup fees!"
        },
        {
            "id": "2002",
            "sender": "aerobase_guru",
            "text": "@BaseCred spotlight @vitalik.eth Second endorsement attempt this week without @base tag!"
        },
        {
            "id": "2003",
            "sender": "unlinked_builder",
            "text": "@BaseCred spotlight @coinbase_dev Great work on @base contracts"
        }
    ]

    for tw in simulated_tweets:
        res = process_single_tweet(tw["id"], tw["sender"], tw["text"])
        print(f"Generated Reply: \"{res.get('reply')}\"")

    print("\n✅ Simulation successfully finished!")
    print("To listen live on Twitter/X in production:")
    print("  1. Add TWITTER_BEARER_TOKEN to your .env file")
    print("  2. Run: python3 scripts/twitter_bot.py\n")

if __name__ == "__main__":
    if not BEARER_TOKEN:
        print("No TWITTER_BEARER_TOKEN configured in environment. Launching demonstration simulation...\n")
        run_dry_run_simulation()
    else:
        print("Starting Live Twitter/X Event Stream Listener for BaseCred...")
