import os
import json
import time
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

CREDIT_REPORT_PROMPT = """
You are generating a plain-language income credibility report for an
informal woman worker in India, to be shown to a bank, SHG, or MFI
loan officer. Use ONLY the data provided below. Do NOT invent numbers
not present in the data. Do NOT assign a credit score or state whether
a loan should be approved — only describe the income pattern factually,
fairly, and clearly.

Persona: {persona}
Data (all figures in INR):
{signals}

Write a report of 150-200 words covering, in this order:
1. Overview: type of work, and the time period the data covers.
2. Income consistency: describe how regular the income is, referencing
   the number of active income weeks and the income_stability_ratio
   (lower ratio = more stable/predictable; explain what the value means
   in plain words, do not just repeat the number).
3. Cash-flow pattern: describe average monthly income vs expense and net
   position honestly, including if net income has been negative on
   average. If there is a notable month (e.g. an expense-heavy month),
   mention it neutrally as a pattern in the data rather than a red flag.
4. Trend: describe whether the recent trend (trend_direction and
   trend_change_pct) shows improvement, decline, or stability over the
   period, since recent trend matters more to lenders than one bad month.
5. Close with a neutral one-line note that this is a summary of
   extracted income/expense data for the lender's own assessment, not
   an automated approval or rejection.

Tone: clear, respectful, non-technical, and honest — do not overstate
strength or hide weakness in the data.
"""


def generate_credit_report(persona, signals):
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=CREDIT_REPORT_PROMPT.format(
            persona=persona,
            signals=json.dumps(signals, indent=2, default=str),
        ),
    )
    return response.text


if __name__ == "__main__":
    with open("cashflow_signals.json") as f:
        all_signals = json.load(f)

    if os.path.exists("credit_reports.json"):
        with open("credit_reports.json") as f:
            reports = json.load(f)
    else:
        reports = {}

    for persona, signals in all_signals.items():
        if persona in reports:
            print(f"Skipping (already done): {persona}")
            continue
        print(f"\n=== Generating report: {persona} ===")
        try:
            report = generate_credit_report(persona, signals)
            print(report)
            reports[persona] = report
            with open("credit_reports.json", "w") as f:
                json.dump(reports, f, indent=2)
            time.sleep(3)
        except Exception as e:
            print(f"Error on {persona}: {e}")
            if "429" in str(e):
                print("Daily quota hit — stopping. Resume later.")
                break

    print("\nCurrent progress saved to credit_reports.json")