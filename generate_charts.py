"""
generate_charts.py
-------------------
Standalone script that reproduces the cleaning logic from
`Electoral bond Project.ipynb` and renders a set of static comparison
charts (saved to ./charts) summarising the Electoral Bond dataset
released by the State Bank of India / Election Commission of India.

Usage:
    python generate_charts.py

Requires: pandas, matplotlib (see requirements.txt)
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

OUT_DIR = "charts"
os.makedirs(OUT_DIR, exist_ok=True)

CR = 1e7  # 1 crore = 10,000,000 INR

plt.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "axes.edgecolor": "#333333",
    "axes.titleweight": "bold",
    "font.size": 10,
})


def crore_formatter(x, _pos):
    return f"{x:,.0f}"


def load_data():
    """Load and clean donor.csv / party.csv the same way the notebook does:
    merge consecutive identical (date, name) rows and express amounts in crores.
    """
    donor_raw = pd.read_csv("donor.csv").dropna()
    party_raw = pd.read_csv("party.csv").dropna()

    donor_raw.columns = ["date", "donor", "denomination"]
    party_raw.columns = ["date", "party", "denomination"]

    donor = donor_raw.groupby(["date", "donor"], as_index=False, sort=False).agg(
        count=("denomination", "size"), denomination=("denomination", "sum")
    )
    party = party_raw.groupby(["date", "party"], as_index=False, sort=False).agg(
        count=("denomination", "size"), denomination=("denomination", "sum")
    )

    donor["date"] = pd.to_datetime(donor["date"], format="%d/%b/%Y")
    party["date"] = pd.to_datetime(party["date"], format="%d/%b/%Y")

    donor["donation_cr"] = donor["denomination"] / CR
    party["funds_cr"] = party["denomination"] / CR

    return donor, party


def plot_top_donors(donor, n=15):
    top = donor.groupby("donor")["donation_cr"].sum().sort_values(ascending=False).head(n)
    fig, ax = plt.subplots(figsize=(9, 7))
    ax.barh(top.index[::-1], top.values[::-1], color="#c0392b")
    ax.set_xlabel("Total bonds purchased (₹ crore)")
    ax.set_title(f"Top {n} Electoral Bond Purchasers (Apr 2019 – Jan 2024)")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(crore_formatter))
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "top_donors.png"), dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_top_parties(party, n=15):
    top = party.groupby("party")["funds_cr"].sum().sort_values(ascending=False).head(n)
    fig, ax = plt.subplots(figsize=(9, 7))
    ax.barh(top.index[::-1], top.values[::-1], color="#2874a6")
    ax.set_xlabel("Total bonds encashed (₹ crore)")
    ax.set_title(f"Top {n} Recipient Political Parties (Apr 2019 – Jan 2024)")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(crore_formatter))
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "top_parties.png"), dpi=150)
    plt.close(fig)


def plot_monthly_trend(donor, party):
    d = donor.set_index("date")["donation_cr"].resample("ME").sum()
    p = party.set_index("date")["funds_cr"].resample("ME").sum()
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(d.index, d.values, marker="o", label="Bonds purchased", color="#c0392b")
    ax.plot(p.index, p.values, marker="o", label="Bonds encashed", color="#2874a6")
    ax.set_ylabel("₹ crore / month")
    ax.set_title("Monthly Electoral Bond Purchases vs. Encashments")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "monthly_trend.png"), dpi=150)
    plt.close(fig)


def plot_donor_concentration(donor, n=10):
    total = donor["donation_cr"].sum()
    top = donor.groupby("donor")["donation_cr"].sum().sort_values(ascending=False)
    top_n_share = top.head(n).sum() / total * 100
    rest_share = 100 - top_n_share
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.pie(
        [top_n_share, rest_share],
        labels=[f"Top {n} donors\n({top_n_share:.1f}%)", f"All other donors\n({rest_share:.1f}%)"],
        colors=["#c0392b", "#d5dbdb"],
        autopct=lambda p: f"{p:.1f}%",
        startangle=90,
    )
    ax.set_title(f"Donor Concentration: Top {n} vs. Rest (by value)")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "donor_concentration.png"), dpi=150)
    plt.close(fig)


def plot_party_share(party, n=8):
    total = party["funds_cr"].sum()
    top = party.groupby("party")["funds_cr"].sum().sort_values(ascending=False)
    top_n = top.head(n)
    others = total - top_n.sum()
    values = list(top_n.values) + [others]
    labels = [name.title() for name in top_n.index] + ["Others"]
    fig, ax = plt.subplots(figsize=(9, 7))
    wedges, _, autotexts = ax.pie(
        values,
        autopct=lambda p: f"{p:.1f}%" if p > 2 else "",
        startangle=90,
        pctdistance=0.8,
        colors=plt.cm.tab20.colors,
        wedgeprops={"linewidth": 1, "edgecolor": "white"},
    )
    ax.set_title("Share of Total Electoral Bond Funds Received, by Party")
    ax.legend(wedges, labels, loc="center left", bbox_to_anchor=(1.0, 0.5), fontsize=9, frameon=False)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "party_share.png"), dpi=150, bbox_inches="tight")
    plt.close(fig)


def main():
    donor, party = load_data()
    print(f"Loaded {len(donor)} donor records / {len(party)} party records after cleaning.")
    print(f"Total value purchased: Rs. {donor['donation_cr'].sum():,.2f} crore")
    print(f"Total value encashed:  Rs. {party['funds_cr'].sum():,.2f} crore")

    plot_top_donors(donor)
    plot_top_parties(party)
    plot_monthly_trend(donor, party)
    plot_donor_concentration(donor)
    plot_party_share(party)

    print(f"\nSaved 5 charts to ./{OUT_DIR}/")


if __name__ == "__main__":
    main()
