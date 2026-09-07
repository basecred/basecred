"""
BaseCred Anti-Collusion & Social Tipping Verification Engine.
Implements the 5 strict anti-spam & collusion filters for Twitter $CRED tipping.
"""
import time
import re
from typing import Dict, Any, Tuple
from engine.database import get_db

SPAM_KEYWORDS = ["tip tip tip", "airdrop airdrop", "follow back", "f4f", "dm for", "whitelist"]

def validate_and_process_tip(
    sender_address: str,
    recipient_twitter: str,
    amount: int,
    tweet_text: str
) -> Dict[str, Any]:
    sender_addr = sender_address.lower()
    recip_handle = recipient_twitter.strip().replace("@", "").lower()
    tweet_cleaned = tweet_text.strip()
    now = int(time.time())

    conn = get_db()
    cursor = conn.cursor()

    # 1. Fetch sender info
    cursor.execute("SELECT * FROM users WHERE address = ?", (sender_addr,))
    sender = cursor.fetchone()
    if not sender:
        conn.close()
        return {"success": False, "error": "Sender wallet not registered. Please evaluate your wallet first."}

    sender_twitter = (sender["twitter_handle"] or "").lower()

    # 2. Check remaining daily allowance
    if amount <= 0:
        conn.close()
        return {"success": False, "error": "Tip amount must be greater than 0."}

    remaining_allowance = sender["remaining_allowance"]
    if amount > remaining_allowance:
        conn.close()
        return {
            "success": False, 
            "error": f"Insufficient daily tip allowance. You have {remaining_allowance} $CRED remaining for today."
        }

    # 3. Rule 1: Self-Tipping Forbidden
    if sender_twitter and sender_twitter == recip_handle:
        conn.close()
        return {"success": False, "error": "Self-tipping is strictly prohibited."}

    # 4. Rule 2: Tweet Quality & Spam Filter
    if len(tweet_cleaned) < 15:
        conn.close()
        return {
            "success": False, 
            "error": "Tweet must be at least 15 characters and provide meaningful commentary or appreciation."
        }

    for spam_word in SPAM_KEYWORDS:
        if spam_word in tweet_cleaned.lower():
            conn.close()
            return {
                "success": False, 
                "error": f"Tweet flagged by anti-spam filter (contained suspicious string: '{spam_word}')."
            }

    # 5. Rule 3: Daily Cap Per Recipient (Max 35% of total daily allowance per recipient per day)
    cursor.execute("""
    SELECT COALESCE(SUM(amount), 0) FROM tips 
    WHERE sender_address = ? AND recipient_twitter = ? AND timestamp > ?
    """, (sender_addr, recip_handle, now - 86400))
    tipped_to_recipient_today = cursor.fetchone()[0]

    max_per_recipient = max(50, int(sender["daily_allowance"] * 0.4))
    if tipped_to_recipient_today + amount > max_per_recipient:
        conn.close()
        return {
            "success": False,
            "error": f"Daily limit exceeded for this recipient. You can only send up to {max_per_recipient} $CRED to @{recip_handle} per day."
        }

    # 6. Rule 4: Reciprocal Collusion Ring Detection (48h Window)
    # Check if recipient tipped sender recently
    penalty_multiplier = 1.0
    flag_reason = None
    status = "success"

    if sender_twitter:
        cursor.execute("""
        SELECT COUNT(*), COALESCE(SUM(amount), 0) FROM tips 
        WHERE sender_twitter = ? AND recipient_twitter = ? AND timestamp > ?
        """, (recip_handle, sender_twitter, now - 86400 * 2))
        reciprocal_count, reciprocal_amt = cursor.fetchone()

        if reciprocal_count >= 2:
            # Persistent circular collusion detected -> BLOCK
            conn.close()
            return {
                "success": False,
                "error": f"Circular collusion detected between @{sender_twitter} and @{recip_handle}. Tipping between these accounts is frozen."
            }
        elif reciprocal_count == 1:
            # 1st reciprocal tip detected -> 80% penalty
            penalty_multiplier = 0.20
            status = "flagged_penalized"
            flag_reason = f"Reciprocal interaction detected with @{recip_handle} within 48h. 80% penalty applied."

    # Calculate actual credits awarded to recipient
    awarded_credits = int(amount * penalty_multiplier)

    # 7. Execute Updates
    # Deduct from sender's remaining daily allowance
    new_remaining = remaining_allowance - amount
    cursor.execute("""
    UPDATE users SET remaining_allowance = ? WHERE address = ?
    """, (new_remaining, sender_addr))

    # Credit recipient if recipient has an account with that twitter handle
    cursor.execute("SELECT * FROM users WHERE twitter_handle = ?", (recip_handle,))
    recip_user = cursor.fetchone()
    if recip_user:
        cursor.execute("""
        UPDATE users SET received_tips = received_tips + ? WHERE twitter_handle = ?
        """, (awarded_credits, recip_handle))

    # Log tip record
    cursor.execute("""
    INSERT INTO tips (sender_address, sender_twitter, recipient_twitter, amount, tweet_text, status, penalty_multiplier, flag_reason, timestamp)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (sender_addr, sender_twitter or "anonymous", recip_handle, amount, tweet_cleaned, status, penalty_multiplier, flag_reason, now))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "status": status,
        "amount_sent": amount,
        "awarded_credits": awarded_credits,
        "penalty_multiplier": penalty_multiplier,
        "flag_reason": flag_reason,
        "remaining_allowance": new_remaining,
        "recipient": recip_handle,
        "timestamp": now
    }
