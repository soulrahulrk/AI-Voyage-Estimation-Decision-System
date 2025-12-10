# AI Voyage Estimation & Decision System

**Rule-based maritime voyage profit & risk estimation with FastAPI + MCP-style tool orchestration.**

---

## Overview

Maritime shipping companies often estimate voyage economics manually in spreadsheets—slow, error-prone, and opaque. This system automates voyage estimation using deterministic business rules, not probabilistic ML. It calculates distance, fuel cost, profit margins, and provides GO/NO-GO decisions based on configurable profit zones and risk thresholds.

Built to demonstrate: business-rule modeling, MCP-style tool orchestration (distance → fuel → decision), failure-safe flows with manual overrides, and clean full-stack integration.

---

## Key Capabilities

**MCP-Style Tool Orchestration**  
Three loosely-coupled tools (Distance, Fuel, Decision) executed in sequence. Each tool can fail independently; the system retries once, then prompts for manual input if needed. Clean separation allows individual tool testing and future replacement (e.g., hooking to real port APIs).

**Profit & Risk Analysis**  
Implements profit zones (≥15% = STRONG GO, 5–15% = CAUTION, 0–5% = RISKY, <0 = DO NOT SAIL). Flags fuel-heavy voyages (>65% expense = risky, >75% = reject), high-speed warnings, port-heavy routes, and freight-below-fuel scenarios.

**Business-Safe Failure Handling**  
Distance tool fails (route not in map) → retry → user enters manual distance. Fuel tool fails (invalid inputs) → retry → user enters manual fuel cost. Decision engine fails → system returns raw numbers + "MANUAL REVIEW REQUIRED". Never silent failures.

**Production-Like UX**  
Frontend form validates empty fields, negatives, and fuel price = 0 (hard reject). Warnings for speed >20 or freight <$50k (soft). Color-coded banners (yellow = tool failure, red = loss voyage, orange = risky). Dashboard shows key metrics, profit zone tag, fuel/port expense ratios, and actionable suggestions.

---

## Tech Stack

- **Backend:** Python 3.10+, FastAPI, Uvicorn, Pydantic v2  
- **Frontend:** HTML5, CSS3, Vanilla JavaScript (no React/Vue—intentional for simplicity)  
- **Architecture:** MCP-style toolchain with retry/fallback logic, RESTful API, CORS-enabled  
- **Style:** Deterministic calculations only. No ML, no randomness, no black-box inference. Pure rule-based "agentic" decisions.

---

## Architecture & Flow

1. **User Input:** Frontend form collects ports, speed, fuel consumption, fuel price, port charges, freight income, currency. Validates on submit.
2. **API Call:** `POST /estimate` sends JSON payload to FastAPI backend.
3. **Distance Tool:** Looks up nautical miles from predefined route map. If route missing → raises `DistanceToolFailure` → retry once → still fails → returns 400 with `needs_manual_distance: true`.
4. **Fuel Tool:** Calculates voyage days (distance / speed), total fuel used (consumption × days), total fuel cost. If invalid inputs → raises `FuelToolFailure` → retry → fails → returns 400 with `needs_manual_fuel_cost: true`.
5. **Decision Engine:** Computes profit %, maps to profit zone, calculates fuel/port expense ratios, generates decision tag and business suggestions. If failure → fallback to raw numbers + `final_decision: "MANUAL REVIEW REQUIRED"`.
6. **Response:** Backend returns JSON with all metrics, warnings, risk flags, banners. Frontend renders dashboard with color-coded decision tag, key numbers, and suggestions list.

---

## API Documentation

### Endpoint: `POST /estimate`

**Request Body:**

```json
{
  "start_port": "Singapore",
  "end_port": "Rotterdam",
  "speed": 14.5,
  "fuel_consumption": 25.0,
  "fuel_price": 580.0,
  "port_charges": 120000.0,
  "freight_income": 320000.0,
  "currency": "USD",
  "manual_distance": null,
  "manual_fuel_cost": null
}
```

**Response Body (Success):**

```json
{
  "distance_nm": 9800.0,
  "voyage_days": 28.74,
  "total_fuel_used": 718.5,
  "total_fuel_cost": 416730.0,
  "total_expense": 536730.0,
  "net_profit": -216730.0,
  "profit_percent": -40.37,
  "profit_zone": "DO NOT SAIL",
  "fuel_percent_of_expense": 77.65,
  "port_percent_of_expense": 22.35,
  "final_decision": "DO NOT SAIL",
  "suggestions": [
    "Renegotiate freight or adjust fuel plan",
    "Revisit commercial terms or routing"
  ],
  "risk_flags": [
    "Voyage loss expected",
    "Fuel cost dominates (>75% of expense)",
    "Freight below fuel cost"
  ],
  "warnings": [],
  "banners": ["Loss-making voyage detected"],
  "needs_manual_distance": false,
  "needs_manual_fuel_cost": false,
  "currency": "USD"
}
```

**Response Body (Tool Failure):**

```json
{
  "distance_nm": null,
  "voyage_days": null,
  "...": "...",
  "final_decision": "MANUAL INPUT REQUIRED",
  "suggestions": ["Enter distance manually and resubmit"],
  "banners": ["Distance tool failed. Provide manual distance to continue."],
  "needs_manual_distance": true,
  "needs_manual_fuel_cost": false
}
```

---

## Profit Zones & Decision Logic

### Profit Zones

| Zone               | Profit %       | Decision Tag       |
| ------------------ | -------------- | ------------------ |
| **STRONG GO**      | ≥15%           | Green light        |
| **GO WITH CAUTION**| 5% to <15%     | Proceed carefully  |
| **RISKY**          | 0% to <5%      | Marginal economics |
| **DO NOT SAIL**    | <0%            | Loss-making        |

### Key Decision Rules

- **Loss voyage (profit < 0):** Automatic `DO NOT SAIL`.
- **Fuel >75% of expense:** `DO NOT SAIL` (unless freight renegotiated).
- **Fuel >65% of expense:** Tag as `RISKY`, suggest slow steaming or renegotiation.
- **Speed >18 knots:** Warning about high fuel burn.
- **Port charges >20% of expense:** Flag port-heavy route.
- **Freight < Fuel cost:** Economically weak voyage; suggest freight renegotiation.

### Business Suggestions

Generated dynamically based on flags:

- Fuel-heavy → "Monitor bunker market and consider slow steaming"
- Low profit → "Seek additional cargo or adjust port calls"
- Loss → "Revisit commercial terms or routing"
- Freight < Fuel → "Renegotiate freight rate or adjust speed"

---

## Failure Handling & Manual Overrides

**Distance Tool Failure**  
Route not in predefined map → Retry once → Still fails → Return `needs_manual_distance: true` + yellow banner. User enters distance in frontend, resubmits with `manual_distance` field populated.

**Fuel Tool Failure**  
Invalid speed/consumption/price (e.g., zero, negative) → Retry once → Still fails → Return `needs_manual_fuel_cost: true` + red banner. User enters fuel cost manually, resubmits.

**Decision Engine Failure**  
Rare edge cases (e.g., zero expense) → Retry once → Falls back to raw calculations + `final_decision: "MANUAL REVIEW REQUIRED"` + gray banner. User reviews raw numbers offline.

*This is intentional design for safety, not a bug.* The system never silently fails or returns nonsense data.

---

## Running Locally

### Prerequisites

- **Python 3.10 or higher** ([Download here](https://www.python.org/downloads/))
- **Git** ([Download here](https://git-scm.com/downloads))
- Modern web browser (Chrome, Firefox, Edge, Safari)

### Quick Start (5 minutes)

**Step 1: Clone the repository**

```bash
git clone https://github.com/soulrahulrk/AI-Voyage-Estimation-Decision-System.git
cd AI-Voyage-Estimation-Decision-System
```

**Step 2: Create and activate virtual environment**

**On Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**On macOS/Linux (Bash/Zsh):**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Step 3: Install dependencies**

```bash
pip install -r requirements.txt
```

This installs FastAPI, Uvicorn, and Pydantic. Takes ~30 seconds.

**Step 4: Start the servers**

### Option A: Quick Start (Windows Users - Recommended)

Simply double-click `start_all.bat` in the project root folder, or run:

```powershell
.\start_all.bat
```

This will:
- ✅ Start the backend server on port 8000
- ✅ Start the frontend server on port 5500
- ✅ Automatically open the application in your default browser
- ✅ Keep both servers running in separate windows

To stop: Close the two command windows that opened.

### Option B: Manual Start (All Platforms)

**Terminal 1 - Backend:**
```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```powershell
# Windows
cd frontend
python -m http.server 5500

# macOS/Linux
cd frontend
python3 -m http.server 5500
```

✅ Backend: `http://localhost:8000` (API docs: `http://localhost:8000/docs`)  
✅ Frontend: `http://localhost:5500`

**Step 5: Open in browser**

Navigate to `http://localhost:5500` and you'll see the voyage estimation form.

---

### Troubleshooting

**"python: command not found"**  
- On macOS/Linux, use `python3` instead of `python`
- Verify installation: `python --version` or `python3 --version`

**"cannot be loaded because running scripts is disabled"** (Windows PowerShell)  
Run this once as Administrator:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Port already in use**  
- Backend (8000): Change to `--port 8001` in the uvicorn command
- Frontend (5500): Change to `python -m http.server 5501`

**"ModuleNotFoundError: No module named 'fastapi'"**  
- Make sure virtual environment is activated (you should see `(.venv)` in your terminal)
- Re-run `pip install -r requirements.txt`

**Frontend not displaying / Connection refused**  
- Use `start_all.bat` (Windows) for persistent server windows
- Verify both servers are running: `netstat -ano | findstr "8000 5500"`
- Check firewall isn't blocking local ports

### Example Test Case

**Input:**

- Start Port: `Singapore`  
- End Port: `Rotterdam`  
- Speed: `14` knots  
- Fuel Consumption: `25` tons/day  
- Fuel Price: `$580` per ton  
- Port Charges: `$120,000`  
- Freight Income: `$320,000`  
- Currency: `USD`

**Expected Result:** `DO NOT SAIL` (loss-making, fuel >75% expense).

---

## Why This Project Matters

**Problem:** Shipping companies manually estimate voyage economics in Excel. Formulas hidden, errors frequent, risk analysis inconsistent across teams. No audit trail.

**Solution:** This system centralizes business rules, automates calculations, surfaces risk flags immediately, and provides audit-ready decision logs. Ship operators get instant GO/NO-GO decisions with commercial justification.

**Future Extensions:** Plug into real port distance APIs (e.g., Sea-Distances.org), integrate live bunker prices, store voyage history for trend analysis, add LLM-based "ask why" explanations for decisions.

---

## What This Demonstrates About My Skills

**Business-Rule Modeling**  
Translated domain knowledge (profit zones, fuel thresholds, port costs) into clean, testable logic. Not just CRUD—actual business intelligence.

**Backend Architecture & Tool Orchestration**  
Designed MCP-style toolchain with clear separation of concerns. Each tool is independently testable, replaceable, and has defined failure modes. Retry logic, fallback paths, and manual override support built in from day one.

**Failure-Safe Design**  
Every tool can fail; system handles it gracefully. No silent errors, no "contact admin" dead ends. User always has a path forward (manual input or raw data review).

**Full-Stack Integration**  
Backend (FastAPI + Pydantic) talks to frontend (vanilla JS) via clean REST API. Frontend validates, shows contextual banners, renders dashboard. End-to-end flow from form to decision in <1 second.

**Production Thinking**  
CORS configured, input validation strict, error messages actionable, API responses structured for frontend consumption. Not a toy—architected like something I'd deploy.

---

## Limitations & Next Steps

### Current Limitations

- **Hard-coded distance map:** 18 predefined routes. Missing routes fail (by design, but limits real use).
- **No persistence:** No database, no auth, no voyage history. Every request is stateless.
- **Demo-scale only:** Not load-tested, no rate limiting, no multi-tenancy.

### Realistic Next Steps

- **Real port distance data:** Hook into Sea-Distances.org API or use Haversine formula + port coordinates.
- **Voyage history storage:** Add PostgreSQL/MongoDB to log decisions, enable trend analysis ("we rejected 12 voyages last month due to fuel costs").
- **Live bunker prices:** Integrate Bunkerworld or similar API for real-time fuel pricing.
- **LLM-based assistant:** Add "Explain this decision" button that uses GPT-4 to generate natural-language justification from raw data + rules.
- **Multi-currency support:** Expand beyond USD/EUR/INR with live FX rates.

---

## File Structure

```
voyage-ship-calculator/
├── backend/
│   ├── __init__.py
│   ├── main.py                # FastAPI app, endpoints, orchestration logic
│   ├── distance_tool.py       # Distance lookup with predefined route map
│   ├── fuel_tool.py           # Fuel & cost calculations
│   ├── decision_engine.py     # Profit zones, rules, decision tag generation
│   └── test_decision_engine.py # Unit tests for decision logic (9 tests)
├── frontend/
│   ├── index.html             # Form + dashboard UI
│   ├── style.css              # Responsive layout, color-coded banners
│   └── script.js              # Form validation, API calls, dashboard rendering
├── start_all.bat              # Windows: Launch both servers + open browser
├── start_backend.bat          # Windows: Backend server only
├── start_frontend.bat         # Windows: Frontend server only
├── requirements.txt           # FastAPI, Uvicorn, Pydantic, pytest
├── .gitignore                 # Python, venv, IDE exclusions
└── README.md
```

---

## License

MIT License. Free to use, modify, and learn from.

---

## Contact

Built by **Rahul** as a portfolio demo project.  
GitHub: [Your GitHub Profile]  
LinkedIn: [Your LinkedIn Profile]

For questions or collaboration: [Your Email]
