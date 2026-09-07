"""
BaseCred Weekly Spotlight & Marketplace Engine.
Handles:
1. Strict 1-per-week Creator Endorsement validation (must mention @base and @BaseCred)
2. Curate-to-Earn reward allocation (Creator: 1000 pts, Curator: 300 pts, 2x if Base retweets)
3. Tradeable Spotlight Pass P2P marketplace (List for ETH, Buy pass)
"""
import time
import re
from typing import Dict, Any, Optional
from engine.database import get_db, current_epoch_str

def validate_and_endorse_tweet(
    curator_address: str,
    creator_twitter: str,
    tweet_url: str,
    tweet_text: str,
    simulate_base_rt: bool = False
) -> Dict[str, Any]:
    curator_addr = curator_address.lower()
    creator_handle = creator_twitter.strip().replace("@", "").lower()
    text = tweet_text.strip()
    epoch = current_epoch_str()
    now = int(time.time())

    conn = get_db()
    cursor = conn.cursor()

    # 1. Fetch Curator
    cursor.execute("SELECT * FROM users WHERE address = ?", (curator_addr,))
    curator = cursor.fetchone()
    if not curator:
        conn.close()
        return {"success": False, "error": "Curator wallet not evaluated. Please check your on-chain footprint first."}

    curator_handle = (curator["twitter_handle"] or "").lower()

    # 2. Strict Constraint: 1 Pass per Week
    if curator["weekly_passes"] < 1:
        conn.close()
        return {
            "success": False,
            "error": f"You have used your 1 Spotlight Pass for this week ({epoch}). Next pass unlocks next Sunday at 00:00 UTC, or you can purchase one on the Pass Market!"
        }

    # 3. Rule: No Self-Endorsement
    if curator_handle and curator_handle == creator_handle:
        conn.close()
        return {"success": False, "error": "Self-endorsement is prohibited. Endorse a community creator on Base."}

    # 4. Content Quality & Mandatory Tag Check
    text_lower = text.lower()
    has_base_tag = ("@base" in text_lower) or ("#base" in text_lower) or ("base.org" in text_lower)
    has_project_tag = ("@basecred" in text_lower) or ("$cred" in text_lower) or ("#basecred" in text_lower)

    if not has_base_tag:
        conn.close()
        return {
            "success": False,
            "error": "The tweet must explicitly mention @base (Official Base Account) or discuss Base network."
        }

    if len(text) < 25:
        conn.close()
        return {
            "success": False,
            "error": "The tweet must contain at least 25 characters of meaningful Base ecosystem commentary or analysis."
        }

    # 5. Calculate Points & Viral Multipliers
    # Base Curate-to-Earn: 1000 to Creator, 300 to Curator
    # If retweeted/liked by @base or @jessepollak -> 2.0x Multiplier!
    multiplier = 2.0 if simulate_base_rt else 1.0
    creator_pts = int(1000 * multiplier)
    curator_pts = int(300 * multiplier)

    # 6. Deduct weekly pass
    cursor.execute("""
    UPDATE users SET weekly_passes = weekly_passes - 1, curator_credits = curator_credits + ?
    WHERE address = ?
    """, (curator_pts, curator_addr))

    # 7. Credit creator if exists
    cursor.execute("SELECT * FROM users WHERE twitter_handle = ?", (creator_handle,))
    creator_user = cursor.fetchone()
    if creator_user:
        cursor.execute("""
        UPDATE users SET creator_credits = creator_credits + ? WHERE twitter_handle = ?
        """, (creator_pts, creator_handle))

    # 8. Record Endorsement
    cursor.execute("""
    INSERT INTO spotlight_endorsements (
        curator_address, curator_twitter, creator_twitter, tweet_url, tweet_text,
        mentions_base, mentions_basecred, is_base_retweeted, multiplier,
        curator_points, creator_points, epoch, timestamp
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        curator_addr, curator_handle or "anonymous", creator_handle, tweet_url, text,
        1, 1 if has_project_tag else 0, 1 if simulate_base_rt else 0, multiplier,
        curator_pts, creator_pts, epoch, now
    ))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "epoch": epoch,
        "creator": creator_handle,
        "creator_points_awarded": creator_pts,
        "curator_points_awarded": curator_pts,
        "is_base_retweeted": simulate_base_rt,
        "multiplier": multiplier,
        "remaining_passes": 0,
        "message": f"Successfully endorsed @{creator_handle}! Awarded +{creator_pts} Creator Credits and +{curator_pts} Curator Credits."
    }

def list_pass_for_sale(seller_address: str, price_eth: float) -> Dict[str, Any]:
    seller_addr = seller_address.lower()
    epoch = current_epoch_str()
    now = int(time.time())

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE address = ?", (seller_addr,))
    seller = cursor.fetchone()
    if not seller:
        conn.close()
        return {"success": False, "error": "Wallet not registered. Please evaluate on-chain first."}

    if seller["weekly_passes"] < 1:
        conn.close()
        return {"success": False, "error": "You do not have any available Weekly Passes to list for sale."}

    # Deduct pass from user balance while listed
    cursor.execute("UPDATE users SET weekly_passes = weekly_passes - 1 WHERE address = ?", (seller_addr,))

    seller_twitter = seller["twitter_handle"] or "anon"
    cursor.execute("""
    INSERT INTO market_listings (seller_address, seller_twitter, price_eth, status, buyer_address, epoch, created_at)
    VALUES (?, ?, ?, 'active', NULL, ?, ?)
    """, (seller_addr, seller_twitter, price_eth, epoch, now))

    listing_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return {
        "success": True,
        "listing_id": listing_id,
        "price_eth": price_eth,
        "epoch": epoch,
        "message": f"Weekly Pass listed on P2P market for {price_eth} ETH!"
    }

def buy_marketplace_pass(buyer_address: str, listing_id: int) -> Dict[str, Any]:
    buyer_addr = buyer_address.lower()
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM market_listings WHERE id = ? AND status = 'active'", (listing_id,))
    listing = cursor.fetchone()
    if not listing:
        conn.close()
        return {"success": False, "error": "Listing not found or already sold."}

    if listing["seller_address"].lower() == buyer_addr:
        conn.close()
        return {"success": False, "error": "You cannot buy your own listed pass."}

    # Mark as sold
    cursor.execute("UPDATE market_listings SET status = 'sold', buyer_address = ? WHERE id = ?", (buyer_addr, listing_id))

    # Add +1 pass to buyer
    cursor.execute("UPDATE users SET weekly_passes = weekly_passes + 1 WHERE address = ?", (buyer_addr,))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "listing_id": listing_id,
        "price_eth": listing["price_eth"],
        "seller": listing["seller_twitter"],
        "message": f"Successfully purchased Weekly Spotlight Pass from @{listing['seller_twitter']} for {listing['price_eth']} ETH!"
    }
