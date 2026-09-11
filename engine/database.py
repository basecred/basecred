"""
BaseCred SQLite Database Manager.
Modular architecture:
- Core: On-chain footprint and verified $CRED allocations
- Weekly Spotlight: 1 pass per calendar week for endorsing @base content creators
- Tradeable Market: P2P micro-market to buy/sell weekly Spotlight Passes
"""
import sqlite3
import os
import time
import shutil
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

DB_PATH = os.environ.get("DB_PATH")
if not DB_PATH:
    if os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
        DB_PATH = "/tmp/basecred.db"
    else:
        DB_PATH = "data/basecred.db"

def get_db():
    if DB_PATH.startswith("/tmp/") and not os.path.exists(DB_PATH) and os.path.exists("data/basecred.db"):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        try:
            shutil.copyfile("data/basecred.db", DB_PATH)
        except Exception:
            pass
    else:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def current_epoch_str() -> str:
    """Returns current ISO calendar week string, e.g. '2026-W36'"""
    now = datetime.now(timezone.utc)
    year, week, _ = now.isocalendar()
    return f"{year}-W{week:02d}"

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # Core Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        address TEXT PRIMARY KEY,
        twitter_handle TEXT,
        onchain_score INTEGER DEFAULT 0,
        onchain_credits INTEGER DEFAULT 0,
        curator_credits INTEGER DEFAULT 0,
        creator_credits INTEGER DEFAULT 0,
        weekly_passes INTEGER DEFAULT 1,
        last_pass_epoch TEXT,
        tier TEXT DEFAULT 'Tier 3: Active Explorer',
        created_at INTEGER
    )
    """)

    # Weekly Spotlight Endorsements (1 per week per user)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS spotlight_endorsements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        curator_address TEXT,
        curator_twitter TEXT,
        creator_twitter TEXT,
        tweet_url TEXT,
        tweet_text TEXT,
        mentions_base BOOLEAN DEFAULT 1,
        mentions_basecred BOOLEAN DEFAULT 1,
        is_base_retweeted BOOLEAN DEFAULT 0,
        multiplier REAL DEFAULT 1.0,
        curator_points INTEGER DEFAULT 300,
        creator_points INTEGER DEFAULT 1000,
        epoch TEXT,
        timestamp INTEGER
    )
    """)

    # Tradeable Spotlight Pass Marketplace
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS market_listings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        seller_address TEXT,
        seller_twitter TEXT,
        price_eth REAL,
        status TEXT DEFAULT 'active', -- 'active', 'sold', 'cancelled'
        buyer_address TEXT,
        epoch TEXT,
        created_at INTEGER
    )
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_spotlight_epoch ON spotlight_endorsements(epoch);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_market_status ON market_listings(status);")

    # Seed initial community demo records if empty
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        _seed_demo_data(cursor)

    conn.commit()
    conn.close()

def _seed_demo_data(cursor):
    now = int(time.time())
    epoch = current_epoch_str()

    demo_users = [
        ("0xd8da6bf26964af9d7eed9e03e53415d37aa96045", "vitalik.eth", 1020, 10000, 600, 2000, 0, epoch, "Tier 1: Base Pioneer & Whale", now - 86400*3),
        ("0x710bda43e60471b47376c67d142145b4bf37715b", "aerobase_guru", 820, 5000, 300, 3000, 1, epoch, "Tier 2: Core Ecosystem Pioneer", now - 86400*2),
        ("0x4b48841d4b322d4b12e2f1059ca7154055c53792", "coinbase_builder", 650, 5000, 300, 1000, 0, epoch, "Tier 2: Core Ecosystem Pioneer", now - 86400*2),
        ("0x983110309620d911731ac0932219af06091b6744", "defi_samurai", 540, 2500, 300, 0, 1, epoch, "Tier 3: Active Explorer", now - 86400*1),
        ("0x111111125421ca6dc452d289314280a0f8842a65", "base_onchain", 480, 2500, 0, 0, 1, epoch, "Tier 3: Active Explorer", now - 86400*1),
    ]

    for u in demo_users:
        cursor.execute("""
        INSERT INTO users (address, twitter_handle, onchain_score, onchain_credits, curator_credits, creator_credits, weekly_passes, last_pass_epoch, tier, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, u)

    # Demo Weekly Spotlight Endorsements
    demo_endorsements = [
        ("0xd8da6bf26964af9d7eed9e03e53415d37aa96045", "vitalik.eth", "aerobase_guru", "https://x.com/aerobase_guru/status/1890123", "Deep dive thread into Base Layer 2 rollup compression and sub-cent fees. Building the future with @base and @BaseCred!", 1, 1, 1, 2.0, 600, 2000, epoch, now - 3600*8),
        ("0x4b48841d4b322d4b12e2f1059ca7154055c53792", "coinbase_builder", "aerobase_guru", "https://x.com/aerobase_guru/status/1890123", "Incredible breakdown of Aerodrome slipstream pools on @base. Tagging @BaseCred for weekly spotlight!", 1, 1, 0, 1.0, 300, 1000, epoch, now - 3600*4),
    ]

    for e in demo_endorsements:
        cursor.execute("""
        INSERT INTO spotlight_endorsements (curator_address, curator_twitter, creator_twitter, tweet_url, tweet_text, mentions_base, mentions_basecred, is_base_retweeted, multiplier, curator_points, creator_points, epoch, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, e)

    # Demo Tradeable Market Listings
    demo_listings = [
        ("0x111111125421ca6dc452d289314280a0f8842a65", "base_onchain", 0.0025, "active", None, epoch, now - 3600*2),
        ("0x983110309620d911731ac0932219af06091b6744", "defi_samurai", 0.0030, "active", None, epoch, now - 1800),
    ]

    for l in demo_listings:
        cursor.execute("""
        INSERT INTO market_listings (seller_address, seller_twitter, price_eth, status, buyer_address, epoch, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, l)

def get_or_register_user(address: str, onchain_score: int, allocated_credits: int, tier: str) -> Dict[str, Any]:
    clean_addr = address.lower()
    conn = get_db()
    cursor = conn.cursor()
    epoch = current_epoch_str()

    cursor.execute("SELECT * FROM users WHERE address = ?", (clean_addr,))
    row = cursor.fetchone()

    if row is None:
        now = int(time.time())
        cursor.execute("""
        INSERT INTO users (address, twitter_handle, onchain_score, onchain_credits, curator_credits, creator_credits, weekly_passes, last_pass_epoch, tier, created_at)
        VALUES (?, ?, ?, ?, 0, 0, 1, ?, ?, ?)
        """, (clean_addr, None, onchain_score, allocated_credits, epoch, tier, now))
        conn.commit()
        cursor.execute("SELECT * FROM users WHERE address = ?", (clean_addr,))
        row = cursor.fetchone()
    else:
        # Reset weekly pass if new week started
        if row["last_pass_epoch"] != epoch:
            cursor.execute("""
            UPDATE users SET weekly_passes = 1, last_pass_epoch = ? WHERE address = ?
            """, (epoch, clean_addr))
            conn.commit()
            cursor.execute("SELECT * FROM users WHERE address = ?", (clean_addr,))
            row = cursor.fetchone()

    res = dict(row)
    conn.close()
    return res

def link_twitter_account(address: str, twitter_handle: str) -> Dict[str, Any]:
    clean_addr = address.lower()
    clean_handle = twitter_handle.strip().replace("@", "").lower()
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("UPDATE users SET twitter_handle = ? WHERE address = ?", (clean_handle, clean_addr))
    conn.commit()
    cursor.execute("SELECT * FROM users WHERE address = ?", (clean_addr,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else {}

def get_hall_of_fame(epoch: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_db()
    cursor = conn.cursor()
    target_epoch = epoch or current_epoch_str()

    cursor.execute("""
    SELECT 
        creator_twitter,
        COUNT(*) as endorsement_count,
        SUM(creator_points) as total_spotlight_credits,
        MAX(is_base_retweeted) as is_base_retweeted,
        tweet_url,
        tweet_text
    FROM spotlight_endorsements
    WHERE epoch = ?
    GROUP BY creator_twitter
    ORDER BY total_spotlight_credits DESC
    LIMIT 10
    """, (target_epoch,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def get_recent_endorsements(limit: int = 15) -> List[Dict[str, Any]]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM spotlight_endorsements
    ORDER BY timestamp DESC
    LIMIT ?
    """, (limit,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def get_active_market_listings() -> List[Dict[str, Any]]:
    conn = get_db()
    cursor = conn.cursor()
    epoch = current_epoch_str()
    cursor.execute("""
    SELECT * FROM market_listings
    WHERE status = 'active' AND epoch = ?
    ORDER BY price_eth ASC
    """, (epoch,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def get_db_stats() -> Dict[str, Any]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT 
        COUNT(*) as total_users,
        COALESCE(SUM(onchain_credits + curator_credits + creator_credits), 0) as total_credits
    FROM users
    """)
    row = cursor.fetchone()
    conn.close()
    return {
        "total_users": row["total_users"] if row else 0,
        "total_credits": row["total_credits"] if row else 0
    }

def get_recent_audits(limit: int = 6) -> List[Dict[str, Any]]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT address, twitter_handle, onchain_score, tier, created_at
    FROM users
    ORDER BY created_at DESC
    LIMIT ?
    """, (limit,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


