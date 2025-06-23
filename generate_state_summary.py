import os
import json

input_base = "data/data/aggregated/transaction/country/india/state"
output_base = "state_summary"

states = os.listdir(input_base)
years = [str(y) for y in range(2018, 2025)]
quarters = ['1', '2', '3', '4']

for year in years:
    for quarter in quarters:
        result = {"data": {"states": {}}}

        for state in states:
            filepath = os.path.join(input_base, state, year, f"{quarter}.json")
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    data = json.load(f)

                txn_count = 0
                txn_amount = 0
                for item in data["data"].get("transactionData", []):
                    for instrument in item.get("paymentInstruments", []):
                        txn_count += instrument.get("count", 0)
                        txn_amount += instrument.get("amount", 0)

                # Format state name (title case with spaces)
                display_name = state.replace("-", " ").title()
                result["data"]["states"][display_name] = {
                    "transactionCount": txn_count,
                    "transactionAmount": txn_amount
                }

        # Save the combined file
        out_dir = os.path.join(output_base, year)
        os.makedirs(out_dir, exist_ok=True)
        out_file = os.path.join(out_dir, f"{quarter}.json")
        with open(out_file, 'w') as f:
            json.dump(result, f, indent=2)

        print(f"✅ Saved {out_file}")
