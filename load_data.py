from google.cloud import bigquery
import json
from datetime import timedelta

client = bigquery.Client(project="vittasakhi-hackathon")

# --- Set dataset expiration (sandbox-mode requirement) ---
dataset_ref = client.dataset("vittasakhi_data")
dataset = client.get_dataset(dataset_ref)
dataset.default_table_expiration_ms = int(timedelta(days=30).total_seconds() * 1000)
dataset.default_partition_expiration_ms = int(timedelta(days=30).total_seconds() * 1000)
client.update_dataset(dataset, ["default_table_expiration_ms", "default_partition_expiration_ms"])
print("Dataset updated with 30-day expiration — sandbox mode compatible.")

# --- Prepare table ---
table_id = "vittasakhi-hackathon.vittasakhi_data.transactions"
schema = [
    bigquery.SchemaField("transaction_id", "STRING"),
    bigquery.SchemaField("date", "DATE"),
    bigquery.SchemaField("persona", "STRING"),
    bigquery.SchemaField("occupation", "STRING"),
    bigquery.SchemaField("transaction_type", "STRING"),
    bigquery.SchemaField("category", "STRING"),
    bigquery.SchemaField("description", "STRING"),
    bigquery.SchemaField("amount_inr", "FLOAT"),
    bigquery.SchemaField("payment_method", "STRING"),
    bigquery.SchemaField("recurring", "STRING"),
    bigquery.SchemaField("balance_inr", "FLOAT"),
]
table = bigquery.Table(table_id, schema=schema)
table = client.create_table(table, exists_ok=True)
print("Table ready:", table_id)

# --- Load data using a LOAD JOB instead of streaming insert ---
with open("synthetic_transaction_ground_truth.json") as f:
    data = json.load(f)

rows = data["transactions"]

# Write rows to a temporary newline-delimited JSON file (required format for load jobs)
with open("temp_load.jsonl", "w") as f:
    for row in rows:
        f.write(json.dumps(row) + "\n")

job_config = bigquery.LoadJobConfig(
    source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
    schema=schema,
    write_disposition="WRITE_TRUNCATE",  # overwrites table each run — good for re-running during dev
)

with open("temp_load.jsonl", "rb") as f:
    load_job = client.load_table_from_file(f, table_id, job_config=job_config)

load_job.result()  # waits for the job to finish

print(f"Loaded {load_job.output_rows} rows successfully via load job.")