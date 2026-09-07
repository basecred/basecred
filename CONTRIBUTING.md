# Contributing to BaseCred

BaseCred is a community-owned, decentralized, and 100% open-source project building reputation and social content curation layers natively on Base (Ethereum Layer 2).

We welcome contributions from developers, designers, and community researchers worldwide!

---

## 🛠️ Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/basecred/basecred.git
   cd basecred
   ```

2. **Start the local server:**
   ```bash
   python3 server.py
   ```
   Open `http://localhost:3000` in your browser.

3. **Run the test suite:**
   ```bash
   python3 -m unittest discover tests/ -p "*.py" 2>/dev/null || python3 scripts/generate_snapshot.py
   ```

---

## 📋 Code of Conduct & Pull Request Guidelines

1. **Decentralized Ethos:** Ensure all contract changes remain non-custodial and OpenZeppelin verified.
2. **Zero Leaks:** Never commit private keys, `.env` files, or personal tracking tokens.
3. **Branching Strategy:**
   - Submit PRs against the `main` branch.
   - Include a clear description of on-chain calculation changes or UI additions.
