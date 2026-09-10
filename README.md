\# VittaSakhi — Digital Work \& Credit Identity Agent for Women



\*\*A multi-agent AI system that turns informal women workers' scattered income records into a structured, verifiable "work identity" they can use to access formal credit and financial services.\*\*



Built for the Patchamomma 2026 Google Cloud hackathon.



🔗 \*\*Live demo:\*\* https://vittasakhi-hackathon.web.app

🔗 \*\*Backend API:\*\* https://vittasakhi-backend.onrender.com

🔗 \*\*Repo:\*\* https://github.com/Anjali-Agrawall/vittasakhi



> ⚠️ This is a hackathon prototype. There is no authentication layer, and all data is synthetic. See \[Known Limitations](#known-limitations) below.



\---



\## The Problem



Nearly 90% of India's workforce operates in the informal sector. Women in home-based and informal work — domestic help, tailoring, tiffin/catering services, beauty services — are disproportionately excluded from formal credit despite having steady, real income.



The core problem isn't a lack of income; it's a lack of \*\*legible\*\* income. Their earnings live in UPI screenshots, handwritten ledgers, and word-of-mouth customer relationships — none of which formal lenders or microfinance institutions can currently read or trust.



\## What VittaSakhi Does



VittaSakhi turns a woman's existing informal records into a structured, credible financial profile — \*\*without ever deciding whether she should get a loan.\*\* It makes invisible income visible and legible, and leaves the actual lending decision to human lenders.



A user uploads a photo of a ledger page or UPI payment screenshot. Three specialized AI agents then process it in sequence:



```

\[Photo upload]

&#x20;     │

&#x20;     ▼

┌─────────────────┐

│ Extraction Agent│  Gemini reads the image → structured transaction JSON

└────────┬────────┘

&#x20;        ▼

┌─────────────────┐

│  BigQuery        │  Full 6-month transaction history stored \& queried

└────────┬────────┘

&#x20;        ▼

┌─────────────────┐

│ Cash-Flow Agent  │  SQL computes income consistency, trend, net position

└────────┬────────┘

&#x20;        ▼

┌─────────────────┐

│ Credit-Readiness │  Gemini turns the numbers into a plain-language

│     Agent        │  report a lender/SHG/MFI officer can actually read

└─────────────────┘

```



All three agents are orchestrated with \*\*Google's Agent Development Kit (ADK)\*\* as a `SequentialAgent`, with each stage's output feeding the next via shared session state.



\## Why Multi-Agent, Not One Big Prompt



\- \*\*Separation of concerns.\*\* Extraction (vision), analysis (math/SQL), and communication (natural language) are fundamentally different kinds of work. Each agent is scoped to do exactly one of these and nothing else — enforced explicitly in each agent's instructions, so the Extraction Agent can't "helpfully" hallucinate a credit report using incomplete data, for example.

\- \*\*Auditability.\*\* A lender can inspect what the Cash-Flow Agent \*computed\* (real BigQuery numbers) separately from what the Credit-Readiness Agent \*said\* about them (Gemini's prose). This is not a black box guessing creditworthiness — it's structured data plus an honest summary of that data.

\- \*\*The Credit-Readiness Agent is explicitly prompted to never assign a credit score or make a lending recommendation\*\* — only to describe the income pattern factually, including negative or unflattering signals rather than hiding them. This is core to the product's ethical positioning: VittaSakhi makes data legible, humans decide.



\## Tech Stack



| Component | Technology | Why |

|---|---|---|

| Multimodal extraction \& report generation | \*\*Gemini API\*\* (`gemini-3.6-flash`) | Reads messy handwritten/screenshot images directly in one call; generates natural, multilingual-capable prose |

| Structured data storage \& analytics | \*\*BigQuery\*\* | Serverless, built for exactly this kind of aggregate time-series analysis over transaction history |

| Multi-agent orchestration | \*\*Google ADK\*\* (`LlmAgent`, `SequentialAgent`) | Purpose-built framework for chaining specialized agents with shared state |

| Backend API | \*\*FastAPI\*\*, deployed on \*\*Render\*\* | Lightweight Python API wrapping the agent pipeline |

| Frontend | Static HTML/CSS/JS, deployed on \*\*Firebase Hosting\*\* | Fast, free, mobile-first |

| Data | \*\*Synthetic transaction data\*\* (627 records, 4 personas, 6 months) | Avoids using real financial data; ground truth lets us verify extraction accuracy |



\## Results



\- \*\*Extraction accuracy:\*\* 100% field-level accuracy on spot-checked test images (dates, amounts, transaction type, payment method all correctly extracted from both ledger-page-style and UPI-screenshot-style images).

\- \*\*4 synthetic personas\*\* with realistic 6-month income/expense histories, including seasonal variation and a range of income stability profiles.

\- \*\*Full pipeline runs live\*\* end-to-end from a public URL — see the demo link above.



\## Repository Structure



```

├── app.py                    # FastAPI backend, exposes /process endpoint

├── orchestrator.py           # ADK multi-agent pipeline (Extraction → Cash-Flow → Credit-Readiness)

├── extract.py                # Extraction Agent logic (Gemini vision)

├── cashflow\_agent.py         # Cash-Flow Agent logic (BigQuery SQL)

├── credit\_agent.py           # Credit-Readiness Agent logic (Gemini language)

├── generate\_images.py        # Generates synthetic ledger/UPI-screenshot sample images

├── load\_data.py              # Loads synthetic ground-truth data into BigQuery

├── index.html                # Frontend (persona picker, upload, results display)

├── sample\_images/            # 32 synthetic test images (16 ledgers + 16 UPI screenshots)

├── synthetic\_transaction\_ground\_truth.json  # 627 synthetic transactions, 4 personas

└── requirements.txt

```



\## Running Locally



1\. Clone the repo and install dependencies:

&#x20;  ```

&#x20;  pip install -r requirements.txt

&#x20;  ```

2\. Create a `.env` file with your Gemini API key:

&#x20;  ```

&#x20;  GEMINI\_API\_KEY=your\_key\_here

&#x20;  ```

3\. Authenticate with Google Cloud (for BigQuery access):

&#x20;  ```

&#x20;  gcloud auth application-default login

&#x20;  gcloud config set project YOUR\_PROJECT\_ID

&#x20;  ```

4\. Load the synthetic data into BigQuery:

&#x20;  ```

&#x20;  python load\_data.py

&#x20;  ```

5\. Start the backend:

&#x20;  ```

&#x20;  uvicorn app:app --reload --port 8000

&#x20;  ```

6\. Open `index.html` in a browser (update `API\_URL` in the script to `http://127.0.0.1:8000` for local testing).



\## Known Limitations



This is a hackathon prototype, and these are deliberate, acknowledged scope cuts made for the build timeline — not oversights:



\- \*\*No authentication.\*\* Firebase Authentication is set up on the project but not yet wired into the app. In production, each user's data would be scoped to their own account.

\- \*\*Synthetic data only.\*\* No real financial data is used or was ever intended to be used for this prototype, both for privacy reasons and to allow verification against known ground truth.

\- \*\*Free-tier constraints.\*\* The Gemini API free tier (20 requests/day) and Render's free-tier cold starts (\~50s spin-up after inactivity) are active constraints on this deployment — a production version would run on paid tiers.

\- \*\*Single-image upload per request.\*\* The current flow processes one uploaded image at a time; a production version would support an ongoing upload history per user, feeding a continuously updating BigQuery record.



\## Ethical Note



VittaSakhi does not decide creditworthiness and never outputs a credit score or loan recommendation. The Credit-Readiness Agent is explicitly instructed to describe income patterns factually — including unflattering ones — and to leave the lending decision to the human financial institution reviewing the report.

