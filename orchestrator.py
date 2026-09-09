import os
import json
import asyncio
from dotenv import load_dotenv

from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.runners import InMemoryRunner
from google.genai import types

from extract import extract_from_image
from cashflow_agent import compute_cashflow_signals
from credit_agent import generate_credit_report as _generate_credit_report_raw

load_dotenv()

MODEL = "gemini-3.6-flash"


def extraction_tool(image_path: str) -> dict:
    """Extracts structured transaction data (date, amount, description,
    transaction_type, payment_method) from a photo of a ledger page or
    UPI payment screenshot. This is the ONLY thing this tool does -
    it does not compute cash-flow signals or generate reports.

    Args:
        image_path: Path to the image file to read.

    Returns:
        A dict with a 'transactions' key containing a list of extracted transactions.
    """
    result = extract_from_image(image_path)
    return {"transactions": result}


def cashflow_tool(persona: str) -> dict:
    """Computes income consistency, cash-flow, and trend signals for a
    given worker (persona) from their REAL transaction history stored in
    BigQuery (the full 6-month history, not just one image's worth of data).

    Args:
        persona: The worker's name, e.g. 'Asha', 'Meena', 'Radha', 'Sunita'.

    Returns:
        A dict of computed financial signals for that worker.
    """
    signals = compute_cashflow_signals(persona)
    # Convert date objects etc. to plain strings so this is JSON-serializable
    return json.loads(json.dumps(signals, default=str))


def credit_report_tool(persona: str, signals: dict) -> str:
    """Generates a plain-language credit-readiness report for a worker,
    given their computed cash-flow signals. Never invents numbers not
    present in the signals, and never assigns a credit score.

    Args:
        persona: The worker's name.
        signals: The dict of computed cash-flow signals for that worker.

    Returns:
        A plain-language report string.
    """
    return _generate_credit_report_raw(persona, signals)


extraction_agent = LlmAgent(
    name="ExtractionAgent",
    model=MODEL,
    instruction=(
        "Your ONLY job is to call extraction_tool with the given image path "
        "and return its raw JSON result. Do NOT compute cash-flow signals, "
        "do NOT generate a credit report, do NOT add commentary or analysis "
        "of any kind. Call the tool exactly once and output only its result."
    ),
    tools=[extraction_tool],
    output_key="extracted_data",
)

cashflow_agent = LlmAgent(
    name="CashFlowAgent",
    model=MODEL,
    instruction=(
        "Your ONLY job is to call cashflow_tool with the persona's name and "
        "return its raw result. Do NOT generate a credit report, do NOT add "
        "commentary. Call the tool exactly once with the persona name "
        "mentioned in the conversation and output only its result."
    ),
    tools=[cashflow_tool],
    output_key="cashflow_signals",
)

credit_readiness_agent = LlmAgent(
    name="CreditReadinessAgent",
    model=MODEL,
    instruction=(
        "Your ONLY job is to call credit_report_tool using the persona name "
        "and the cashflow_signals produced by the previous agent (available "
        "in session state), and return its result as your final answer. "
        "Do not modify the report or add your own commentary."
    ),
    tools=[credit_report_tool],
    output_key="credit_report",
)

root_agent = SequentialAgent(
    name="VittaSakhiPipeline",
    sub_agents=[extraction_agent, cashflow_agent, credit_readiness_agent],
    description="Runs extraction, cash-flow analysis, and credit-readiness reporting in sequence.",
)


async def run_pipeline(persona: str, image_path: str):
    runner = InMemoryRunner(agent=root_agent, app_name="vittasakhi")
    session = await runner.session_service.create_session(
        app_name="vittasakhi", user_id="demo_user"
    )

    user_message = types.Content(
        role="user",
        parts=[types.Part(text=f"persona={persona}, image_path={image_path}")],
    )

    async for event in runner.run_async(
        user_id="demo_user", session_id=session.id, new_message=user_message
    ):
        if event.is_final_response() and event.content and event.content.parts:
            print(f"\n[{event.author}]:\n{event.content.parts[0].text}\n")


if __name__ == "__main__":
    asyncio.run(run_pipeline("Asha", "sample_images/ledger_01_Asha.jpg"))

async def run_pipeline_and_collect(persona: str, image_path: str) -> dict:
    runner = InMemoryRunner(agent=root_agent, app_name="vittasakhi")
    session = await runner.session_service.create_session(
        app_name="vittasakhi", user_id="demo_user"
    )
    user_message = types.Content(
        role="user",
        parts=[types.Part(text=f"persona={persona}, image_path={image_path}")],
    )

    outputs = {}
    async for event in runner.run_async(
        user_id="demo_user", session_id=session.id, new_message=user_message
    ):
        if event.is_final_response() and event.content and event.content.parts:
            outputs[event.author] = event.content.parts[0].text

    return {
        "persona": persona,
        "extracted_data": outputs.get("ExtractionAgent", ""),
        "cashflow_signals": outputs.get("CashFlowAgent", ""),
        "credit_report": outputs.get("CreditReadinessAgent", ""),
    }