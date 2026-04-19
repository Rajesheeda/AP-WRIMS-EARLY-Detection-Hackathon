from utils.data_loader import load_all_dates
from utils.risk_engine import compute_all_risks

all_data = load_all_dates()
risks = compute_all_risks(all_data)

print(f"{'Date':<10} | {'Score':<6} | {'Level':<10}")
print("-" * 30)
for date, result in risks.items():
    print(f"{date:<10} | {result['score']:<6} | {result['level']:<10}")
