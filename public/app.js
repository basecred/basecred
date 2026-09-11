/**
 * BaseCred Frontend Application Logic.
 * 1. Core On-Chain Footprint Evaluator
 * 2. Weekly Base Spotlight (Strict 1 pass/week, @base mandatory, Curate-to-Earn)
 * 3. Tradeable Pass P2P Marketplace
 */

let currentAccount = null;
let currentEligibilityData = null;
let currentEpoch = "2026-W36";
let activeTab = "footprint";

let recentAuditsList = [];
let recentAuditIndex = 0;

document.addEventListener("DOMContentLoaded", () => {
  if (window.lucide) window.lucide.createIcons();
  checkIfAlreadyConnected();
  fetchHallOfFame();
  fetchMarketListings();
  fetchRecentAudits();
  setInterval(updateTickerDisplay, 3500);
});

async function fetchRecentAudits() {
  try {
    const res = await fetch("/api/recent-audits");
    if (res.ok) {
      const data = await res.json();
      if (data.recent_audits && data.recent_audits.length > 0) {
        recentAuditsList = data.recent_audits;
        updateTickerDisplay();
      }
    }
  } catch (e) {}
}

function updateTickerDisplay() {
  if (!recentAuditsList || recentAuditsList.length === 0) return;
  const audit = recentAuditsList[recentAuditIndex % recentAuditsList.length];
  recentAuditIndex++;

  const addrEl = document.getElementById("tickerAddress");
  const scoreEl = document.getElementById("tickerScore");

  if (addrEl && scoreEl && audit) {
    const short = audit.address.slice(0, 6) + "..." + audit.address.slice(-4);
    addrEl.textContent = short;
    scoreEl.textContent = `${Number(audit.onchain_score).toLocaleString()} pts • ${audit.tier || 'Verified'}`;
  }
}


// Tab Switcher
function switchTab(tab) {
  activeTab = tab;
  const tabs = ["footprint", "spotlight", "market", "roadmap"];

  tabs.forEach(t => {
    const content = document.getElementById(`tab${capitalize(t)}Content`);
    const navBtn = document.getElementById(`navTab${capitalize(t)}`);
    if (content) {
      if (t === tab) content.classList.remove("hidden");
      else content.classList.add("hidden");
    }
    if (navBtn) {
      if (t === tab) {
        navBtn.className = "tab-active px-3.5 py-1.5 rounded-lg transition-all duration-150 whitespace-nowrap flex items-center gap-2";
      } else {
        navBtn.className = "px-3.5 py-1.5 rounded-lg text-slate-400 hover:text-white transition-all duration-150 whitespace-nowrap flex items-center gap-2";
      }
    }
  });

  if (tab === "spotlight") fetchHallOfFame();
  if (tab === "market") fetchMarketListings();
  if (window.lucide) window.lucide.createIcons();
}

function capitalize(s) {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

// Wallet Auto-detect
async function checkIfAlreadyConnected() {
  if (typeof window.ethereum !== "undefined") {
    try {
      const accounts = await window.ethereum.request({ method: "eth_accounts" });
      if (accounts.length > 0) setupAccount(accounts[0]);
    } catch (e) {}
  }
}

async function connectWallet() {
  if (typeof window.ethereum === "undefined") {
    alert("Please install a Web3 wallet (MetaMask, Coinbase Wallet, Rabby).");
    window.open("https://metamask.io/download/", "_blank");
    return;
  }
  try {
    const accounts = await window.ethereum.request({ method: "eth_requestAccounts" });
    if (accounts.length > 0) setupAccount(accounts[0]);
  } catch (err) {
    console.error("Connection failed:", err);
  }
}

function setupAccount(account) {
  currentAccount = account;
  const shortAddr = account.slice(0, 6) + "..." + account.slice(-4);
  
  const btnText = document.getElementById("connectWalletText");
  if (btnText) btnText.textContent = shortAddr;
  
  const mobileBtn = document.getElementById("mobileConnectBtn");
  if (mobileBtn) mobileBtn.textContent = shortAddr;

  const useBtn = document.getElementById("useConnectedBtn");
  if (useBtn) useBtn.classList.remove("hidden");

  const input = document.getElementById("addressInput");
  if (input && !input.value) input.value = account;
}

function useConnectedWallet() {
  if (currentAccount) {
    const input = document.getElementById("addressInput");
    if (input) {
      input.value = currentAccount;
      checkWalletEligibility();
    }
  }
}

function setSampleAddress(addr) {
  const input = document.getElementById("addressInput");
  if (input) {
    input.value = addr;
    checkWalletEligibility();
  }
}

async function pasteFromClipboard() {
  try {
    const text = await navigator.clipboard.readText();
    if (text && text.trim()) {
      document.getElementById("addressInput").value = text.trim();
      checkWalletEligibility();
    }
  } catch (e) {
    const input = document.getElementById("addressInput");
    if (input) input.focus();
  }
}

// Support Basename (.base.eth) and ENS (.eth) resolution
async function resolveAddressOrName(inputVal) {
  const val = (inputVal || "").trim().toLowerCase();
  if (val.startsWith("0x") && val.length === 42) return val;

  // Instant fast-path for prominent ecosystem Basenames
  const known = {
    "vitalik.base.eth": "0xd8da6bf26964af9d7eed9e03e53415d37aa96045",
    "vitalik.eth": "0xd8da6bf26964af9d7eed9e03e53415d37aa96045",
    "jesse.base.eth": "0x221245c38676a0868f76fa780fe98df00411a141",
    "jessepollak.base.eth": "0x221245c38676a0868f76fa780fe98df00411a141",
    "coinbase.base.eth": "0x4b48841d4b322d4b12e2f1059ca7154055c53792"
  };
  if (known[val]) return known[val];

  if (val.endsWith(".base.eth") || val.endsWith(".eth")) {
    try {
      const provider = new ethers.JsonRpcProvider("https://mainnet.base.org");
      const resolved = await provider.resolveName(val);
      if (resolved && resolved.startsWith("0x") && resolved.length === 42) return resolved;
    } catch (e) {}

    try {
      const ethProvider = new ethers.JsonRpcProvider("https://eth.llamarpc.com");
      const resolvedEth = await ethProvider.resolveName(val);
      if (resolvedEth && resolvedEth.startsWith("0x") && resolvedEth.length === 42) return resolvedEth;
    } catch (e) {}
  }
  return null;
}

// -------------------------------------------------------------
// CORE: ON-CHAIN FOOTPRINT EVALUATOR
// -------------------------------------------------------------
async function checkWalletEligibility() {
  const input = document.getElementById("addressInput");
  const rawAddr = (input.value || "").trim();

  if (!rawAddr) {
    alert("Please enter a Base address or Basename (.base.eth).");
    return;
  }

  const checkBtn = document.getElementById("checkBtn");
  const checkBtnText = document.getElementById("checkBtnText");
  const scanner = document.getElementById("loadingScanner");
  const resultsContainer = document.getElementById("resultsContainer");

  let targetAddr = rawAddr;
  if (!targetAddr.startsWith("0x") || targetAddr.length !== 42) {
    checkBtn.disabled = true;
    checkBtnText.textContent = "Resolving Basename / ENS...";
    scanner.classList.remove("hidden");
    const resolved = await resolveAddressOrName(targetAddr);
    if (resolved) {
      targetAddr = resolved;
    } else {
      scanner.classList.add("hidden");
      alert(`Could not resolve Basename "${rawAddr}". Please enter a valid 42-character 0x... EVM address.`);
      checkBtn.disabled = false;
      checkBtnText.textContent = "Evaluate Footprint & Claim Weekly Pass";
      return;
    }
  }

  checkBtn.disabled = true;
  checkBtnText.textContent = "Auditing Footprint...";
  resultsContainer.classList.add("hidden");
  scanner.classList.remove("hidden");

  try {
    const resp = await fetch(`/api/check?address=${encodeURIComponent(targetAddr)}`);
    if (resp.ok) {
      const data = await resp.json();
      currentEligibilityData = data;
      renderFootprintResults(data);
      fetchRecentAudits();
      scanner.classList.add("hidden");
      resultsContainer.classList.remove("hidden");
      if (window.lucide) window.lucide.createIcons();
      resultsContainer.scrollIntoView({ behavior: "smooth", block: "start" });
      return;
    }
  } catch (err) {
    console.log("Evaluation query fallback...", err);
  } finally {
    checkBtn.disabled = false;
    checkBtnText.textContent = "Evaluate Footprint & Claim Weekly Pass";
  }
}


function renderFootprintResults(data) {
  const f = data.factors || {};

  document.getElementById("evaluatedAddress").textContent = data.account;
  document.getElementById("tierBadge").textContent = data.tier_name || "Tier 1: Base Pioneer";
  document.getElementById("tokenAmountDisplay").textContent = Number(data.onchain_credits || 10000).toLocaleString();
  
  const passes = data.weekly_passes !== undefined ? data.weekly_passes : 1;
  document.getElementById("weeklyPassDisplay").textContent = `${passes} Available`;
  document.getElementById("spotlightPassCount").innerHTML = `${passes} <span class="text-sm font-sans text-slate-400">Available</span>`;
  document.getElementById("epochDisplay").textContent = `Epoch: ${data.current_epoch || '2026-W36'}`;

  // Factor Metrics
  if (f.gas) {
    document.getElementById("gasScorePill").textContent = `${f.gas.score} / ${f.gas.max}`;
    document.getElementById("gasAmountDisplay").textContent = `${f.gas.eth_gas} ETH`;
    document.getElementById("gasUsdDisplay").textContent = `~$${f.gas.usd_gas} USD burnt`;
    document.getElementById("gasProgressBar").style.width = `${Math.min(100, (f.gas.score / f.gas.max) * 100)}%`;
    document.getElementById("gasBadge").textContent = f.gas.badge;
  }
  if (f.eth_age) {
    document.getElementById("ethAgeScorePill").textContent = `${f.eth_age.score} / ${f.eth_age.max}`;
    document.getElementById("ethAgeDisplay").textContent = `${f.eth_age.years} Years`;
    document.getElementById("ethTxDisplay").textContent = `${f.eth_age.tx_count} L1 txs (${f.eth_age.days} days)`;
    document.getElementById("ethAgeProgressBar").style.width = `${Math.min(100, (f.eth_age.score / f.eth_age.max) * 100)}%`;
    document.getElementById("ethBadge").textContent = f.eth_age.badge;
  }
  if (f.base_activity) {
    document.getElementById("baseScorePill").textContent = `${f.base_activity.score} / ${f.base_activity.max}`;
    document.getElementById("baseTxDisplay").textContent = `${f.base_activity.tx_count} Base Nonce`;
    document.getElementById("baseAgeDisplay").textContent = `${f.base_activity.days} days on Base`;
    document.getElementById("baseProgressBar").style.width = `${Math.min(100, (f.base_activity.score / f.base_activity.max) * 100)}%`;
    document.getElementById("baseBadge").textContent = f.base_activity.badge;
  }
  if (f.consistency) {
    document.getElementById("consistencyScorePill").textContent = `${f.consistency.score} / ${f.consistency.max}`;
    document.getElementById("consistencyMonthsDisplay").textContent = `${f.consistency.active_months} Active Mos`;
    document.getElementById("consistencyProgressBar").style.width = `${Math.min(100, (f.consistency.score / f.consistency.max) * 100)}%`;
    document.getElementById("consistencyBadge").textContent = f.consistency.badge;
  }
  if (f.bridge) {
    document.getElementById("bridgeScorePill").textContent = `${f.bridge.score} / ${f.bridge.max}`;
    document.getElementById("bridgeStatusDisplay").textContent = f.bridge.used ? "Verified ✅" : "Not Bridged ❌";
    document.getElementById("bridgeAmountDisplay").textContent = f.bridge.used ? `${f.bridge.bridged_eth} ETH via Portal` : "No official bridge found";
    document.getElementById("bridgeProgressBar").style.width = `${f.bridge.used ? 100 : 10}%`;
    document.getElementById("bridgeBadge").textContent = f.bridge.badge;
  }
  if (f.basename) {
    document.getElementById("basenameScorePill").textContent = `${f.basename.score} / ${f.basename.max}`;
    document.getElementById("basenameDisplay").textContent = f.basename.registered ? "Registered 🆔" : "None ❌";
    document.getElementById("basenameLabelDisplay").textContent = f.basename.registered ? f.basename.name_label : "No .base.eth domain";
    document.getElementById("basenameProgressBar").style.width = `${f.basename.registered ? 100 : 10}%`;
    document.getElementById("basenameBadge").textContent = f.basename.badge;
  }
  if (f.defi_protocols) {
    document.getElementById("defiScorePill").textContent = `${f.defi_protocols.score} / ${f.defi_protocols.max}`;
    const protList = f.defi_protocols.protocols || [];
    document.getElementById("defiCountDisplay").textContent = `${protList.length} Protocols`;
    document.getElementById("defiListDisplay").textContent = protList.length > 0 ? protList.join(" • ") : "No key protocols";
    document.getElementById("defiProgressBar").style.width = `${Math.min(100, (f.defi_protocols.score / f.defi_protocols.max) * 100)}%`;
    document.getElementById("defiBadge").textContent = f.defi_protocols.badge;
  }
  if (f.sybil_meter) {
    document.getElementById("sybilScorePill").textContent = `${f.sybil_meter.score} / 100`;
    document.getElementById("sybilHealthDisplay").textContent = f.sybil_meter.passed ? "Human Verified 🛡️" : "Suspicious ⚠️";
    document.getElementById("sybilFlagsDisplay").textContent = f.sybil_meter.passed ? "Organic on-chain pattern" : (f.sybil_meter.flags.join(", ") || "Irregular");
    document.getElementById("sybilProgressBar").style.width = `${f.sybil_meter.score}%`;
    document.getElementById("sybilBadge").textContent = f.sybil_meter.passed ? "✅ Human Identity Passed" : "❌ Disqualified";
  }
}

function shareScoreOnTwitter() {
  if (!currentEligibilityData) {
    alert("Please evaluate a wallet footprint first!");
    return;
  }
  const score = currentEligibilityData.total_score || 1020;
  const tier = currentEligibilityData.tier_name || "Tier 1: Base Pioneer";
  const f = currentEligibilityData.factors || {};
  const gasInfo = f.gas ? `${f.gas.eth_gas} ETH burnt` : "Active on Base";
  
  const tweetText = `My on-chain score is ${score} pts (${tier}) on @BaseCred ($CRED)! 🔵\n\n⛽ ${gasInfo}\n\nVerify your Base footprint & claim your weekly pass:\n👉 https://basecred.onrender.com`;
  
  const intentUrl = `https://twitter.com/intent/tweet?text=${encodeURIComponent(tweetText)}`;
  window.open(intentUrl, "_blank");
}

// -------------------------------------------------------------
// WEEKLY SPOTLIGHT ENDORSEMENT LOGIC
// -------------------------------------------------------------
async function submitEndorsement() {
  const curatorAddr = currentAccount || (currentEligibilityData ? currentEligibilityData.account : "0x710bda43e60471b47376c67d142145b4bf37715b");
  const creator = document.getElementById("endorseCreatorInput").value.trim().replace("@", "");
  const tweetUrl = document.getElementById("endorseUrlInput").value.trim();
  const tweetText = document.getElementById("endorseTextInput").value.trim();
  const simRt = document.getElementById("simBaseRtCheckbox").checked;

  const resBox = document.getElementById("endorseResultBox");
  resBox.classList.remove("hidden");

  try {
    const res = await fetch("/api/spotlight/endorse", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        curator_address: curatorAddr,
        creator_twitter: creator,
        tweet_url: tweetUrl,
        tweet_text: tweetText,
        simulate_base_rt: simRt
      })
    });
    const data = await res.json();

    if (data.success) {
      resBox.className = "p-4 rounded-xl border border-emerald-500/50 bg-emerald-950/30 text-xs font-mono space-y-1 text-emerald-300";
      resBox.innerHTML = `
        <div class="font-bold flex items-center gap-1.5"><i data-lucide="award" class="w-4 h-4 text-amber-400"></i><span>Weekly Spotlight Endorsement Confirmed!</span></div>
        <p>${data.message}</p>
        ${data.is_base_retweeted ? '<p class="text-amber-300 font-bold">🔥 2x Viral Multiplier Applied! (Recognized by @base)</p>' : ''}
        <p class="text-slate-400">Weekly Spotlight Pass for Epoch ${data.epoch} consumed (1/1 used).</p>
      `;
      document.getElementById("spotlightPassCount").innerHTML = `0 <span class="text-sm font-sans text-slate-400">Available</span>`;
      document.getElementById("weeklyPassDisplay").textContent = `0 Available`;
      triggerConfetti();
      fetchHallOfFame();
    } else {
      resBox.className = "p-4 rounded-xl border border-rose-500/50 bg-rose-950/30 text-xs font-mono space-y-1 text-rose-300";
      resBox.innerHTML = `
        <div class="font-bold flex items-center gap-1.5"><i data-lucide="alert-circle" class="w-4 h-4 text-rose-400"></i><span>Endorsement Rejected</span></div>
        <p>${data.error}</p>
      `;
    }
  } catch (err) {
    resBox.className = "p-4 rounded-xl border border-rose-500/50 bg-rose-950/30 text-xs font-mono space-y-1 text-rose-300";
    resBox.innerHTML = `<p>Failed to submit endorsement.</p>`;
  }
  if (window.lucide) window.lucide.createIcons();
}

async function fetchHallOfFame() {
  try {
    const res = await fetch("/api/spotlight/hall-of-fame");
    const data = await res.json();
    const container = document.getElementById("hallOfFameContainer");
    if (!container || !data.hall_of_fame) return;

    container.innerHTML = "";
    data.hall_of_fame.forEach((creator, idx) => {
      const card = document.createElement("div");
      card.className = "base-card rounded-xl p-4 border border-[#1E2533] space-y-2 text-xs";
      const medal = idx === 0 ? "🥇" : idx === 1 ? "🥈" : idx === 2 ? "🥉" : `#${idx+1}`;
      
      card.innerHTML = `
        <div class="flex items-center justify-between">
          <span class="font-bold text-white font-mono flex items-center gap-1.5">
            <span>${medal}</span>
            <span class="text-blue-400">@${creator.creator_twitter}</span>
          </span>
          <span class="px-2 py-0.5 rounded bg-amber-500/15 text-amber-300 font-mono font-bold border border-amber-500/30">
            ${creator.endorsement_count} Endorsements (${Number(creator.total_spotlight_credits).toLocaleString()} $CRED)
          </span>
        </div>
        <p class="text-slate-400 text-[11px] truncate">"${creator.tweet_text}"</p>
        <div class="flex items-center justify-between pt-1 border-t border-[#1E2533]">
          ${creator.is_base_retweeted ? '<span class="text-[10px] text-amber-300 font-bold flex items-center gap-1"><i data-lucide="sparkles" class="w-3 h-3"></i>Retweeted by @base</span>' : '<span class="text-[10px] text-slate-500">Verified Base Content</span>'}
          <a href="${creator.tweet_url}" target="_blank" class="text-[10px] text-blue-400 hover:text-blue-300 flex items-center gap-1">
            <span>View Thread</span><i data-lucide="external-link" class="w-2.5 h-2.5"></i>
          </a>
        </div>
      `;
      container.appendChild(card);
    });
  } catch (err) {
    console.warn("Could not fetch hall of fame:", err);
  }
}

// -------------------------------------------------------------
// P2P PASS MARKETPLACE LOGIC
// -------------------------------------------------------------
async function fetchMarketListings() {
  try {
    const res = await fetch("/api/market/listings");
    const data = await res.json();
    const grid = document.getElementById("marketListingsGrid");
    if (!grid || !data.listings) return;

    grid.innerHTML = "";
    if (data.listings.length === 0) {
      grid.innerHTML = `<p class="text-xs text-slate-500 col-span-full py-4 text-center">No active pass listings on the market. Be the first to list!</p>`;
      return;
    }

    data.listings.forEach(item => {
      const card = document.createElement("div");
      card.className = "base-card rounded-xl p-4 border border-[#1E2533] space-y-3 text-xs";
      const shortSeller = item.seller_address.slice(0, 6) + "..." + item.seller_address.slice(-4);

      card.innerHTML = `
        <div class="flex items-center justify-between">
          <span class="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-300 font-bold text-[10px] border border-emerald-500/30">Weekly Pass Voucher</span>
          <span class="text-slate-400 font-mono text-[10px]">${item.epoch}</span>
        </div>
        <div>
          <p class="text-slate-400 text-[11px] font-mono">Seller: @${item.seller_twitter} (${shortSeller})</p>
          <p class="text-lg font-extrabold text-white font-mono mt-0.5">${item.price_eth} <span class="text-xs text-blue-400">ETH</span></p>
        </div>
        <button onclick="buyMarketPass(${item.id})" class="w-full py-2.5 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-[#06080C] font-extrabold text-xs transition flex items-center justify-center gap-1.5 active:scale-95">
          <i data-lucide="shopping-cart" class="w-3.5 h-3.5"></i>
          <span>Buy Spotlight Pass</span>
        </button>
      `;
      grid.appendChild(card);
    });
    if (window.lucide) window.lucide.createIcons();
  } catch (err) {
    console.warn("Could not fetch market listings:", err);
  }
}

async function listPassOnMarket() {
  const sellerAddr = currentAccount || (currentEligibilityData ? currentEligibilityData.account : null);
  if (!sellerAddr) {
    alert("Please connect your wallet or evaluate your footprint first.");
    return;
  }
  const price = parseFloat(document.getElementById("listPriceInput").value);
  if (isNaN(price) || price <= 0) {
    alert("Please enter a valid ETH price.");
    return;
  }

  try {
    const res = await fetch("/api/market/list", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ seller_address: sellerAddr, price_eth: price })
    });
    const data = await res.json();
    if (data.success) {
      alert(data.message);
      document.getElementById("spotlightPassCount").innerHTML = `0 <span class="text-sm font-sans text-slate-400">Available</span>`;
      document.getElementById("weeklyPassDisplay").textContent = `0 Available`;
      fetchMarketListings();
    } else {
      alert("Error: " + data.error);
    }
  } catch (err) {
    alert("Failed to list pass.");
  }
}

async function buyMarketPass(listingId) {
  const buyerAddr = currentAccount || (currentEligibilityData ? currentEligibilityData.account : "0x710bda43e60471b47376c67d142145b4bf37715b");
  if (!confirm("Confirm purchasing this Weekly Spotlight Pass voucher?")) return;

  try {
    const res = await fetch("/api/market/buy", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ buyer_address: buyerAddr, listing_id: listingId })
    });
    const data = await res.json();
    if (data.success) {
      alert(data.message);
      triggerConfetti();
      document.getElementById("spotlightPassCount").innerHTML = `1 <span class="text-sm font-sans text-slate-400">Available</span>`;
      document.getElementById("weeklyPassDisplay").textContent = `1 Available`;
      fetchMarketListings();
    } else {
      alert("Error: " + data.error);
    }
  } catch (err) {
    alert("Failed to purchase pass.");
  }
}

function triggerConfetti() {
  if (typeof confetti === "function") {
    confetti({ particleCount: 70, spread: 60, origin: { y: 0.6 } });
  }
}
