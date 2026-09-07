# BaseCred ($CRED)

> **Decentralized On-Chain Reputation & Content Curation Protocol on Base Network**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Built on Base](https://img.shields.io/badge/Built%20on-Base-0052FF.svg)](https://base.org)
[![Network: Base Mainnet](https://img.shields.io/badge/Chain-Base%20(8453)-0052FF.svg)](https://basescan.org)

BaseCred is an open-source, community-governed reputation and curation engine built natively for the Base L2 ecosystem. It evaluates wallets across 8 verifiable on-chain footprint metrics, grants holders weekly non-stackable Spotlight Passes, and rewards community members for curating high-effort educational content and development on Base.

---

## 🌟 Key Architecture & Features

### 1. 8-Factor On-Chain Footprint Engine
BaseCred evaluates wallet addresses across 8 transparent, verifiable on-chain criteria:
- ⛽ **Gas Burnt**: Total cumulative ETH and USD burnt across Base and Ethereum L1.
- 🏛️ **Ethereum L1 Vintage**: Timestamp of the first transaction on Ethereum Mainnet (identifying OG ecosystem contributors).
- 🔷 **Base Nonce & Activity**: Total transaction count and longevity on Base.
- 📅 **Organic Consistency**: Multi-month organic activity patterns to differentiate real human users from transient farming scripts.
- 🌉 **Official Portal Bridge**: Verification of native asset bridging via the Base Portal Bridge.
- 🆔 **Basename Ownership**: Verification of registered Basenames (`.base.eth`).
- ⚡ **Base DeFi Protocols**: Historic interaction with key ecosystem protocols (Aerodrome, Uniswap, Moonwell, etc.).
- 🛡️ **Sybil Resistance Screen**: Multi-variable wallet health check (minimum balance, funding dispersion, bot-like clustering).

### 2. Weekly Base Spotlight (Curate-to-Earn)
To prevent social spam while driving high-quality attention to Base builders:
- **Strict 1 Pass / Week Quota**: Every eligible wallet receives exactly one non-stackable pass per calendar week.
- **Mandatory Quality Standard**: Endorsements are only valid on posts that explicitly tag `@base` and cover tutorials, analytics, or tooling.
- **Curate-to-Earn Rewards**: Curator receives +300 $CRED while the Creator receives +1000 $CRED.
- **2x Viral Multiplier**: If the endorsed content is retweeted or recognized by `@base`, both creator and curator receive double rewards.

### 3. P2P Tradeable Pass Marketplace
Community members who do not wish to curate content in a given week can list their Weekly Pass voucher for sale to other creators on a decentralized peer-to-peer marketplace.

### 4. Cryptographic Merkle Distribution
Prior to the Token Generation Event (TGE), final snapshots are compiled into an immutable Merkle Tree:
- Bitmap-based `MerkleDistributor.sol` ensuring ultra-low gas claim costs on Base.
- OpenZeppelin-compatible ERC-20 token (`AirdropToken.sol`) with standard 18 decimals and 100M supply.

### 5. Native Base Network Visual Identity & Farcaster Integration
- Authentic Base Network design language (Base Blue `#0052FF`, obsidian cards, monospace metric grids).
- Interactive **Farcaster Frame v2** support for native engagement within Warpcast feeds.

---

## 📁 Project Structure

```
basecred/
├── contracts/               # Solidity Smart Contracts (0.8.20+)
│   ├── AirdropToken.sol     # ERC-20 $CRED Token Contract
│   └── MerkleDistributor.sol # Gas-optimized Merkle Claim Contract
├── engine/                  # Core Computational Engine (Pure Python)
│   ├── keccak.py            # Verified Keccak-256 implementation
│   ├── merkle.py            # Cryptographic Merkle Tree builder & verifier
│   ├── fetcher.py           # On-chain Base & Ethereum RPC state fetcher
│   ├── eligibility.py       # 8-factor scoring & tier allocation
│   ├── database.py          # SQLite persistence layer (serverless compatible)
│   └── spotlight.py         # Weekly Spotlight & P2P Market logic
├── api/                     # Serverless Function Entrypoints
│   └── index.py             # Vercel / Cloud serverless router
├── public/                  # Modern Web3 Frontend
│   ├── index.html           # Base-native responsive UI
│   └── app.js               # Web3 wallet connection, evaluation, & market
├── scripts/                 # Automation & Deployment Utilities
│   ├── export_final_snapshot.py # Snapshot CSV & Merkle compiler
│   ├── deploy_to_base.py        # Smart contract deployment helper
│   ├── twitter_bot.py           # X / Twitter automation bot
│   └── generate_snapshot.py     # Batch processing script
├── MARKETING_KIT/           # Community Launch Kit & Grants
│   ├── 01_TWITTER_LAUNCH_THREAD.md
│   ├── 02_WARPCAST_POST.md
│   └── 03_BASE_BUILDER_GRANT_APPLICATION.md
├── server.py                # Standalone HTTP & API server
├── vercel.json              # Vercel 1-click deployment configuration
└── LICENSE                  # MIT Open-Source License
```

---

## 🚀 Quick Start

### Running Locally
Run the standalone server with zero external dependencies:

```bash
# Start the platform on port 3000
python3 server.py
```

Then open your browser at:
👉 **`http://localhost:3000`**

### Running Tests
Execute the verification test suite:

```bash
python3 scripts/export_final_snapshot.py
python3 scripts/twitter_bot.py
```

### Deploying to Vercel
The repository is pre-configured for instant zero-configuration deployment to Vercel:
1. Import the repository in [Vercel](https://vercel.com).
2. Click **Deploy**. The serverless Python backend and static frontend will be deployed automatically.

---

## 📄 License
This project is open-source and licensed under the [MIT License](LICENSE).
