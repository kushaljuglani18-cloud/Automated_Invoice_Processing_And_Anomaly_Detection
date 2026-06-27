# visualize.py
# Generates the report visualizations: box plot + scatter plot

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Load our processed data
df = pd.read_csv("output/processed_invoices.csv")

os.makedirs("output", exist_ok=True)


def plot_boxplot(df):
    """
    Box plot: shows the spread of invoice amounts PER VENDOR.
    Outliers appear as invidual dots beyond the 'whiskers'.
    """
    plt.figure(figsize=(10, 6))
    sns.boxplot(data=df, x='vendor', y='grand_total')
    plt.title('Invoice Amount Distribution by Vendor')
    plt.xlabel('Vendor')
    plt.ylabel('Grand Total ($)')
    plt.xticks(rotation=20)
    plt.tight_layout()
    plt.savefig('output/boxplot_by_vendor.png', dpi=150)
    plt.close()
    print("Saved: output/boxplot_by_vendor.png")


def plot_scatter(df):
    """
    Scatter plot: every invoice as a point, colored by whether
    it was flagged as an anomaly. Makes outliers visually obvious.
    """
    plt.figure(figsize=(10, 6))

    normal = df[df['is_anomaly'] == False]
    anomaly = df[df['is_anomaly'] == True]

    plt.scatter(normal['invoice_id'], normal['grand_total'],
                color='steelblue', label='Normal', s=80)
    plt.scatter(anomaly['invoice_id'], anomaly['grand_total'],
                color='red', label='Anomaly', s=120, marker='X')
    
    plt.title('Invoice Amounts with Flagged Anomalies')
    plt.xlabel('Invoice ID')
    plt.ylabel('Grand Total ($)')
    plt.legend()
    plt.tight_layout()
    plt.savefig('output/scatter_anomalies.png', dpi=150)
    plt.close()
    print("Saved: output/scatter_anomalies.png")


plot_boxplot(df)
plot_scatter(df)
print("\nAll visualizations created!")