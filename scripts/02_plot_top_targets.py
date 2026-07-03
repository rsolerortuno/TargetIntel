from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parents[1]

input_file = PROJECT_ROOT / "results" / "top_targets_melanoma_io_weighted_v0_2.csv"
output_file = PROJECT_ROOT / "figures" / "top20_targets_melanoma_io_weighted_v0_2.png"

df = pd.read_csv(input_file)

top20 = df.head(20).copy()
top20 = top20.sort_values("final_score", ascending=True)

plt.figure(figsize=(8, 7))
plt.barh(top20["target_symbol"], top20["final_score"])
plt.xlabel("Final TargetIntel score")
plt.ylabel("Target")
plt.title("Top 20 melanoma targets weighted by immuno-oncology relevance")
plt.tight_layout()
plt.savefig(output_file, dpi=300)

print(f"Saved figure to: {output_file}")
