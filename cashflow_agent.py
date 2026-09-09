from google.cloud import bigquery

client = bigquery.Client(project="vittasakhi-hackathon")

TABLE = "vittasakhi-hackathon.vittasakhi_data.transactions"


def compute_cashflow_signals(persona: str) -> dict:
    query = f"""
    WITH monthly AS (
      SELECT
        FORMAT_DATE('%Y-%m', date) AS month,
        SUM(CASE WHEN transaction_type = 'income' THEN amount_inr ELSE 0 END) AS income,
        SUM(CASE WHEN transaction_type = 'expense' THEN amount_inr ELSE 0 END) AS expense
      FROM `{TABLE}`
      WHERE persona = @persona
      GROUP BY month
      ORDER BY month
    ),
    income_only AS (
      SELECT amount_inr, date
      FROM `{TABLE}`
      WHERE persona = @persona AND transaction_type = 'income'
    )
    SELECT
      (SELECT AVG(income) FROM monthly) AS avg_monthly_income,
      (SELECT AVG(expense) FROM monthly) AS avg_monthly_expense,
      (SELECT AVG(income - expense) FROM monthly) AS avg_monthly_net,
      (SELECT COUNT(*) FROM income_only) AS num_income_transactions,
      (SELECT AVG(amount_inr) FROM income_only) AS avg_income_transaction,
      (SELECT STDDEV(amount_inr) FROM income_only) AS income_stddev,
      (SELECT COUNT(DISTINCT DATE_TRUNC(date, WEEK)) FROM income_only) AS active_income_weeks,
      (SELECT MIN(date) FROM `{TABLE}` WHERE persona = @persona) AS first_date,
      (SELECT MAX(date) FROM `{TABLE}` WHERE persona = @persona) AS last_date
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("persona", "STRING", persona)]
    )
    result = list(client.query(query, job_config=job_config).result())[0]
    signals = dict(result)

    # Coefficient of variation: lower = more stable/predictable income
    if signals["avg_income_transaction"]:
        signals["income_stability_ratio"] = round(
            signals["income_stddev"] / signals["avg_income_transaction"], 3
        )
    else:
        signals["income_stability_ratio"] = None

    # Monthly trend: compare first half vs second half average net income
    trend_query = f"""
    WITH monthly AS (
      SELECT
        FORMAT_DATE('%Y-%m', date) AS month,
        SUM(CASE WHEN transaction_type = 'income' THEN amount_inr ELSE 0 END)
          - SUM(CASE WHEN transaction_type = 'expense' THEN amount_inr ELSE 0 END) AS net
      FROM `{TABLE}`
      WHERE persona = @persona
      GROUP BY month
      ORDER BY month
    )
    SELECT month, net FROM monthly
    """
    trend_rows = list(client.query(trend_query, job_config=job_config).result())
    monthly_net = [(r["month"], r["net"]) for r in trend_rows]
    signals["monthly_net_trend"] = monthly_net

    if len(monthly_net) >= 4:
        mid = len(monthly_net) // 2
        first_half_avg = sum(n for _, n in monthly_net[:mid]) / mid
        second_half_avg = sum(n for _, n in monthly_net[mid:]) / (len(monthly_net) - mid)
        if first_half_avg != 0:
            change_pct = round((second_half_avg - first_half_avg) / abs(first_half_avg) * 100, 1)
        else:
            change_pct = None
        signals["trend_direction"] = (
            "improving" if second_half_avg > first_half_avg else
            "declining" if second_half_avg < first_half_avg else "flat"
        )
        signals["trend_change_pct"] = change_pct
    else:
        signals["trend_direction"] = "insufficient_data"
        signals["trend_change_pct"] = None

    return signals


if __name__ == "__main__":
    import json

    personas = ["Asha", "Meena", "Radha", "Sunita"]
    all_signals = {}

    for p in personas:
        print(f"\n=== {p} ===")
        signals = compute_cashflow_signals(p)
        for k, v in signals.items():
            print(f"  {k}: {v}")
        all_signals[p] = signals

    with open("cashflow_signals.json", "w") as f:
        json.dump(all_signals, f, indent=2, default=str)

    print("\nSaved all signals to cashflow_signals.json")