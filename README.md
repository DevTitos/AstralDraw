# Astral Draw 🚀 – The Future of Community-Owned Lottery & Governance

![Astral Draw Banner](https://via.placeholder.com/1200x600/050510/0ff?text=Astral+Draw+-+Cosmic+Lottery+of+the+Future)

**Astral Draw** is a blockchain-powered lottery platform on **Hedera Hashgraph**, reimagining traditional lotteries into a **community-owned, sustainable wealth generation ecosystem**. Every participant benefits — whether they win the jackpot or contribute to long-term community projects.

> "We're not just changing how people play the lottery — we're changing what it means to win."

---

## 📌 Pitch Deck & Certification

- **Pitch Deck:** [Astral Draw Presentation PDF](https://yourlinktopitchdeck.com)  
- **Hackathon Certification:** [Certification Link](https://drive.google.com/file/d/1eX8qYF11P2WMPhzK4EZ2ZMIOdi6Gvh1e/view)  
- **Video Demo (7 min):** [Demo Link](https://yourlinktovideo.com)
- **Hosted Project URL:** [Demo Link](http://astraldraw.onrender.com/)

---

## 🌟 Features

### Triple-Win Economic Model
```
Ticket Price Distribution:
├── 50% → Jackpot Pool (Instant Winners)
├── 30% → Community Project Treasury (Long-term Investment)
├── 10% → Platform Operations (Sustainability)
└── 10% → NFT Governance Rewards (Ecosystem Growth)
```

### Tiered Governance NFT System
- **Celestial Board (Top 10 Members):** Strategic decision-making, proposal curation, treasury oversight
- **Stellar Assembly (1,000 Members):** Proposal drafting, primary voting, community representation
- **Cosmic Community (Unlimited):** Idea submission, sentiment signaling, project dividends

### Project Investment & Profit Sharing
- Community-vetted projects funded from ticket sales
- Profits distributed as:
  - Buyback & burn of **ASTRA tokens**
  - Participant airdrops (consolation rewards)
  - Reinvestment into treasury (compound growth)

### Transparent & Verifiable
- Built on **Hedera Hashgraph**
- Every draw on-chain with **HTS/HSC**
- Real-time verification via **Hashscan**
- Provably fair RNG

---

## 🛠️ Tech Stack

### Backend
- **Django (Python)** – Core logic, API, and admin interface
- **Hedera Hashgraph** – Token, NFT, and consensus services (HTS, HSC, HSC)
- **Celery + Redis** – Background tasks (draws, airdrops)
- **PostgreSQL** – Database

### Frontend
- **HTML5, CSS3, JS**
- **Bootstrap** – Responsive, mobile-first UI
- **WebSockets** – Real-time ticketing and project updates
- **Progressive Web App Ready**

### DevOps
- **Docker** (optional)
- **GitHub Actions** – CI/CD
- **build.sh** – Setup automation

---

## ⚡ Quick Start

Clone the repository:

```bash
git clone https://github.com/DevTitos/AstralDraw.git
cd AstralDraw
```

### 1️⃣ Setup Python Environment
```bash
python3 -m venv myenv
source myenv/bin/activate
```

### 2️⃣ Build & Install Dependencies
```bash
chmod +x build.sh
./build.sh
```

> `build.sh` contents:
```bash
#!/usr/bin/env bash
# build.sh

set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --noinput
python manage.py migrate
```

### 3️⃣ Run Development Server
```bash
python3 manage.py runserver
```

Open [http://localhost:8000](http://localhost:8000) to access the platform.

---

## 🗂️ Repository Structure

```
astral-draw/
├── AstralDraw/        # Django main app
├── projects/           # Community project management
├── hiero/         # HCS, FT, NFT, governance and mirror node
├── core/            # Lottery ticket & draw logic
├── static/             # CSS, JS, images
├── templates/          # HTML templates
├── requirements.txt
├── build.sh            # Build & setup automation
└── README.md
```

---

## 🌟 Roadmap & Hackathon Milestones

1. **MVP Launch** – Fully functional lottery and governance system  
2. **NFT Governance Sale** – Celestial Board & Stellar Assembly launch  
3. **Community Projects** – First project investments live  
4. **Real-time Dashboard** – Ticket sales, draws, and rewards tracking  
5. **Mobile PWA** – Cross-device support for global access

---

## 💰 Tokenomics (ASTRA)

- **Total Supply:** 1,000,000,000 ASTRA
- **Distribution:**
  - 40% Community Rewards & Airdrops
  - 25% Ecosystem Development
  - 15% Team & Advisors (3-year vesting)
  - 10% Liquidity & Market Making
  - 5% Strategic Reserve
  - 5% Public Sale
- **Value Mechanisms:** Buyback & burn, staking rewards, utility for tickets & NFTs, scarcity through continuous burns

---

## 🔐 Security & Compliance

- Multi-sig wallets & treasury protection  
- Smart contract audits planned  
- Bug bounty program ongoing  
- KYC/AML integration  
- Age verification & tax compliance

---

## 📈 Business & Growth Strategy

- Multi-draw types, mobile app, and cross-chain integration  
- White-label lottery solutions  
- DeFi integration and yield farming  
- International expansion and regulatory compliance

---

## 🤝 Connect With Us

- **Website:** [astraldraw.com](https://astraldraw.com)  
- **Twitter:** [@AstralDraw](https://twitter.com/AstralDraw)  
- **Telegram:** [t.me/astraldraw](https://t.me/astraldraw)  
- **GitHub:** [github.com/astraldraw](https://github.com/astraldraw)  

---

### 🏆 Hackathon Edge

- True **community-owned lottery**  
- **Sustainable wealth** for all participants  
- Enterprise-grade **Hedera blockchain**  
- **Tiered governance NFT system** with real voting power  
- Provably fair **random number generation**

---

**Astral Draw Team** 🚀  
*"Changing what it means to win."*