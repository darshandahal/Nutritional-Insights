# backend/data_analysis.py
from pathlib import Path
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "All_Diets.csv"
OUT_TABLES = ROOT / "outputs" / "tables"
OUT_PLOTS = ROOT / "outputs" / "plots"
OUT_TABLES.mkdir(parents=True, exist_ok=True)
OUT_PLOTS.mkdir(parents=True, exist_ok=True)

def find_col(df, names):
    for n in names:
        for c in df.columns:
            if n.lower() in c.lower():
                return c
    return None

def compute_insights(force_recompute=False):
    """
    Load CSV, compute avg macros, top5 protein per diet, most common cuisine.
    Save CSVs and plots to outputs. Return dictionaries for API use.
    """
    df = pd.read_csv(DATA_PATH)

    prot_col = find_col(df, ["protein"])
    carb_col = find_col(df, ["carb", "carbohydrate"])
    fat_col  = find_col(df, ["fat"])

    if not (prot_col and carb_col and fat_col):
        raise RuntimeError("Could not detect Protein/Carb/Fat columns.")

    # Clean
    for c in (prot_col, carb_col, fat_col):
        df[c] = pd.to_numeric(df[c].astype(str).str.replace(",", ""), errors="coerce")
    means = df[[prot_col, carb_col, fat_col]].mean()
    df[[prot_col, carb_col, fat_col]] = df[[prot_col, carb_col, fat_col]].fillna(means)

    # New metrics
    df["Protein_to_Carbs_ratio"] = df[prot_col] / df[carb_col].replace({0: np.nan})
    df["Carbs_to_Fat_ratio"] = df[carb_col] / df[fat_col].replace({0: np.nan})

    # Average macros by diet
    avg_macros = df.groupby("Diet_type")[[prot_col, carb_col, fat_col]].mean().round(2)
    avg_file = OUT_TABLES / "avg_macros.csv"
    avg_macros.to_csv(avg_file)

    # Top 5 protein-rich recipes per diet
    top5 = df.sort_values(by=prot_col, ascending=False).groupby("Diet_type").head(5).reset_index(drop=True)
    top5_file = OUT_TABLES / "top5_protein_per_diet.csv"
    top5.to_csv(top5_file, index=False)

    # Most common cuisine
    common_cuisine = df.groupby("Diet_type")["Cuisine_type"].agg(lambda s: s.mode().iloc[0] if not s.mode().empty else "")
    common_file = OUT_TABLES / "most_common_cuisines.csv"
    common_cuisine.to_csv(common_file)

    # Save plots (bar + heatmap + scatter)
    try:
        # bar
        avg_long = avg_macros.reset_index().melt(id_vars="Diet_type", var_name="Macro", value_name="Value")
        plt.figure(figsize=(10,6))
        sns.barplot(data=avg_long, x="Diet_type", y="Value", hue="Macro")
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        (OUT_PLOTS / "avg_macros_bar.png").unlink(missing_ok=True)
        plt.savefig(OUT_PLOTS / "avg_macros_bar.png", dpi=150)
        plt.close()

        # heatmap
        plt.figure(figsize=(8, max(4, len(avg_macros)*0.35)))
        sns.heatmap(avg_macros, annot=True, fmt=".2f")
        plt.tight_layout()
        plt.savefig(OUT_PLOTS / "avg_macros_heatmap.png", dpi=150)
        plt.close()

        # scatter top5
        plt.figure(figsize=(10,6))
        sns.scatterplot(data=top5, x=carb_col, y=prot_col, hue="Cuisine_type", size=fat_col, alpha=0.8, legend='brief')
        plt.tight_layout()
        plt.savefig(OUT_PLOTS / "top5_scatter.png", dpi=150)
        plt.close()
    except Exception as e:
        print("Warning: plot save failed:", e)

    # Return simple JSON-serializable dicts
    return {
        "avg_macros": avg_macros.reset_index().to_dict(orient="records"),
        "top5": top5.to_dict(orient="records"),
        "most_common_cuisines": common_cuisine.reset_index().to_dict(orient="records")
    }

if __name__ == "__main__":
    compute_insights()
    print("Computed insights and saved outputs.")
