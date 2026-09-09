import json

with open('synthetic_transaction_ground_truth.json') as f:
    data = json.load(f)

jan = [t for t in data['transactions']
       if t['persona'] == 'Asha'
       and t['date'].startswith('2026-01')
       and t['transaction_type'] == 'expense']

for t in sorted(jan, key=lambda x: -x['amount_inr'])[:5]:
    print(t)