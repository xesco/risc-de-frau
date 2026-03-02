# Risc de Frau en Contractació Pública Catalana

Automated analysis of the 1,000 highest-value public contracts published on [contractes.cat](https://contractes.cat) during 2025. The report flags procedural anomalies statistically associated with fraud risk — it does **not** accuse any company or public body of wrongdoing.

🔗 **Live report**: [xesco.github.io/risc-de-frau](https://xesco.github.io/risc-de-frau)

---

## What it contains

The report applies five risk flags to the dataset:

- **F1 · Single bidder above €1M** — contracts awarded with only one offer received and a value over €1,000,000
- **F2 · Non-open procedure above €500K** — contracts awarded via negotiated, restricted, or similar procedure without open competition, above €500,000
- **F3 · Award between 97–101% of the budget ceiling** — may indicate prior knowledge of the maximum budget (top 30 by value shown)
- **F4 · Repeat winner at the same contracting body** — supplier winning 3 or more contracts above €200K from the same organ, suggesting possible market dependency
- **F5 · Award at exactly 100% of budget** — a subset of F3 for contracts above €5M where the award exactly matches the ceiling

It also includes three in-depth sections on the most significant findings:

- **IMSS / SUARA / SERVISAR** — Barcelona's social services agency and its concentrated supplier base
- **SEM / Falck** — Emergency medical transport and €654M awarded to a single operator
- **CTTI / Seidor** — Catalonia's IT infrastructure agency and the Seidor group's dominant position

---

## Data sources and tools

- **[contractes.cat](https://contractes.cat)** — Registre Públic de Contractes de Catalunya, Generalitat de Catalunya. The authoritative public register of Catalan public procurement data.
- **[`@gerardgimenezadsuar/contractes-cli`](https://www.npmjs.com/package/@gerardgimenezadsuar/contractes-cli)** by Gerard Giménez Adsuar — the npm CLI that provides programmatic access to the contractes.cat API and made this analysis possible.

---

## Regenerating the report

Clone the repo, install the CLI, and run three scripts:

```bash
git clone https://github.com/xesco/risc-de-frau.git
cd risc-de-frau

# 1. Install the CLI
npm install -g @gerardgimenezadsuar/contractes-cli

# 2. Fetch the top 1000 contracts (takes ~1 min)
bash scripts/fetch.sh

# 3. Run the fraud-risk analysis
python3 scripts/analyse.py

# 4. Generate the HTML report
python3 scripts/build.py
```

Open `index.html` in any browser. No server required.

The fetch script accepts optional arguments for year and number of pages:

```bash
bash scripts/fetch.sh 2024 10   # fetch top 500 contracts for 2024
```

Each section in the report also shows the exact CLI command used to generate it — click **"Consulta CLI utilitzada"** under any table or chart.

---

## License

Report and analysis code: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Data © Generalitat de Catalunya, licensed under [Open Data Commons](https://opendata-commons.org/).

---

## ⚠️ Disclaimer

This report flags **procedural anomalies**, not proven fraud. Flagged companies and public bodies are not accused of any illegal or unethical conduct — many contracts have entirely legitimate explanations. The purpose is transparency and informed public debate.
