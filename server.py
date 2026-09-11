"""
BaseCred Web & API Server.
Modular architecture:
1. Core: On-chain footprint & verified $CRED scoring (8 criteria)
2. Weekly Spotlight: Strict 1-per-week creator endorsement for @base content
3. Tradeable Marketplace: P2P pass trading for creators and community
"""
import os
import sys
import json
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler
from engine.fetcher import fetch_wallet_onchain_state
from engine.eligibility import calculate_eligibility
from engine.merkle import MerkleTree
from engine.database import (
    init_db, get_or_register_user, link_twitter_account,
    get_hall_of_fame, get_recent_endorsements, get_active_market_listings,
    get_db_stats, get_recent_audits, current_epoch_str
)
from engine.spotlight import (
    validate_and_endorse_tweet, list_pass_for_sale, buy_marketplace_pass
)

PORT = int(os.environ.get("PORT", 3000))
SNAPSHOT_FILE = "data/merkle_tree.json"

init_db()

SNAPSHOT_DATA = {}
if os.path.exists(SNAPSHOT_FILE):
    try:
        with open(SNAPSHOT_FILE, "r") as f:
            SNAPSHOT_DATA = json.load(f)
    except Exception as e:
        print("Warning loading snapshot:", e)

class BaseCredHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="public", **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/favicon.ico":
            self.send_response(302)
            self.send_header("Location", "/favicon.svg")
            self.end_headers()
            return

        if path == "/api/stats":

            db_stats = get_db_stats()
            self.send_json({
                "project_name": "BaseCred",
                "token_symbol": "$CRED",
                "current_epoch": current_epoch_str(),
                "rule_limit": "1 Spotlight Pass per Week",
                "target_chain": "Base Mainnet (8453)",
                "merkle_root": SNAPSHOT_DATA.get("merkle_root", "0x0"),
                "total_eligible_wallets": max(db_stats["total_users"], SNAPSHOT_DATA.get("total_eligible_wallets", 10)),
                "total_credits_allocated": max(db_stats["total_credits"], SNAPSHOT_DATA.get("total_tokens_allocated", 90000))
            })
            return


        elif path == "/api/spotlight/hall-of-fame":
            fame = get_hall_of_fame()
            recent = get_recent_endorsements(limit=10)
            self.send_json({
                "epoch": current_epoch_str(),
                "hall_of_fame": fame,
                "recent_endorsements": recent
            })
            return

        elif path == "/api/market/listings":
            listings = get_active_market_listings()
            self.send_json({
                "epoch": current_epoch_str(),
                "listings": listings
            })
            return

        elif path == "/api/check":
            query = urllib.parse.parse_qs(parsed.query)
            address = query.get("address", [""])[0].strip().lower()

            if not address or not address.startswith("0x") or len(address) != 42:
                self.send_json({"error": "Invalid EVM address."}, status=400)
                return

            try:
                state = fetch_wallet_onchain_state(address)
                elig = calculate_eligibility(state)

                allocated_credits = elig["allocated_tokens"]
                tier_name = elig["tier_name"]
                total_score = elig["total_score"]

                user_db = get_or_register_user(address, total_score, allocated_credits, tier_name)

                response_obj = {
                    "account": address,
                    "is_eligible": elig["is_eligible"],
                    "tier_name": tier_name,
                    "tier_level": elig["tier_level"],
                    "total_score": total_score,
                    "onchain_credits": allocated_credits,
                    "curator_credits": user_db.get("curator_credits", 0),
                    "creator_credits": user_db.get("creator_credits", 0),
                    "total_credits": allocated_credits + user_db.get("curator_credits", 0) + user_db.get("creator_credits", 0),
                    "weekly_passes": user_db.get("weekly_passes", 1),
                    "current_epoch": current_epoch_str(),
                    "twitter_handle": user_db.get("twitter_handle"),
                    "factors": elig["factors"]
                }
                self.send_json(response_obj)
            except Exception as e:
                self.send_json({"error": str(e)}, status=500)
            return

        elif path == "/api/leaderboard":
            fame = get_hall_of_fame()
            self.send_json({"leaderboard": fame})
            return

        elif path == "/api/feed":
            recent = get_recent_endorsements(limit=10)
            self.send_json({"feed": recent})
            return

        elif path == "/api/recent-audits":
            audits = get_recent_audits(limit=6)
            self.send_json({"recent_audits": audits})
            return

        return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        content_len = int(self.headers.get("Content-Length", 0))
        post_body = self.rfile.read(content_len).decode("utf-8") if content_len > 0 else "{}"

        try:
            payload = json.loads(post_body)
        except Exception:
            payload = {}

        if path == "/api/link-twitter":
            address = payload.get("address", "").strip().lower()
            twitter_handle = payload.get("twitter_handle", "").strip()
            if not address or not twitter_handle:
                self.send_json({"success": False, "error": "Missing address or twitter handle."}, status=400)
                return
            updated = link_twitter_account(address, twitter_handle)
            self.send_json({"success": True, "user": updated})
            return

        elif path == "/api/spotlight/endorse":
            curator_addr = payload.get("curator_address", "").strip().lower()
            creator = payload.get("creator_twitter", "").strip()
            tweet_url = payload.get("tweet_url", "").strip()
            tweet_text = payload.get("tweet_text", "").strip()
            sim_base_rt = bool(payload.get("simulate_base_rt", False))

            result = validate_and_endorse_tweet(curator_addr, creator, tweet_url, tweet_text, sim_base_rt)
            status_code = 200 if result.get("success") else 400
            self.send_json(result, status=status_code)
            return

        elif path == "/api/market/list":
            seller_addr = payload.get("seller_address", "").strip().lower()
            price_eth = float(payload.get("price_eth", 0.002))

            result = list_pass_for_sale(seller_addr, price_eth)
            status_code = 200 if result.get("success") else 400
            self.send_json(result, status=status_code)
            return

        elif path == "/api/market/buy":
            buyer_addr = payload.get("buyer_address", "").strip().lower()
            listing_id = int(payload.get("listing_id", 0))

            result = buy_marketplace_pass(buyer_addr, listing_id)
            status_code = 200 if result.get("success") else 400
            self.send_json(result, status=status_code)
            return

        elif path == "/api/frame":
            # Interactive Farcaster Frame v2 Handler for Warpcast
            untrusted = payload.get("untrustedData", {})
            button_index = untrusted.get("buttonIndex", 1)
            fid = untrusted.get("fid", "anon")
            
            frame_html = f"""<!DOCTYPE html>
<html>
<head>
  <meta property="fc:frame" content="vNext" />
  <meta property="fc:frame:image" content="https://basecred.onrender.com/og-frame.png" />
  <meta property="fc:frame:button:1" content="🌐 Launch Full Web App" />
  <meta property="fc:frame:button:1:action" content="link" />
  <meta property="fc:frame:button:1:target" content="https://basecred.onrender.com" />
  <meta property="fc:frame:button:2" content="🌟 Weekly Spotlight" />
  <meta property="fc:frame:button:2:action" content="post" />
  <meta property="fc:frame:post_url" content="https://basecred.onrender.com/api/frame" />
</head>
<body>
  <p>BaseCred Frame Active | FID: {fid}</p>
</body>
</html>"""
            self.send_html(frame_html)
            return

        self.send_json({"error": "Endpoint not found"}, status=404)

    def send_json(self, data, status=200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def send_html(self, html_str, status=200):
        body = html_str.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

def run():
    server_address = ("", PORT)
    httpd = HTTPServer(server_address, BaseCredHandler)
    print(f"==================================================")
    print(f"🚀 BaseCred Platform running at http://localhost:{PORT}")
    print(f"   Core: On-Chain Creds | Sub: Weekly Spotlight & Pass Market")
    print(f"==================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        httpd.server_close()

if __name__ == "__main__":
    run()

