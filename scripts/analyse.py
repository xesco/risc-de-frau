#!/usr/bin/env python3
"""
analyse.py — Loads data.json, applies fraud-risk flags, saves analysis.json

Flags:
  F1  Single bidder above €1M
  F2  Non-open procedure above €500K
  F3  Award between 97–101% of the budget ceiling
  F4  Repeat winner at the same contracting body (>=3 contracts >€200K)
  F5  Award at exactly 100% of budget (subset of F3, above €5M)
"""

import json
import sys
from collections import defaultdict

INPUT = "data.json"
OUTPUT = "analysis.json"


def get_amount(c):
    for field in ("import_adjudicacio_amb_iva", "import_adjudicacio_sense", "valor_estimat_contracte"):
        v = c.get(field)
        if v:
            try:
                return float(v)
            except (TypeError, ValueError):
                pass
    return 0.0


def get_budget(c):
    for field in ("pressupost_licitacio_amb", "pressupost_licitacio_sense", "valor_estimat_contracte"):
        v = c.get(field)
        if v:
            try:
                return float(v)
            except (TypeError, ValueError):
                pass
    return 0.0


def get_url(c):
    ep = c.get("enllac_publicacio")
    if isinstance(ep, dict):
        return ep.get("url", "")
    return ""


def contract_summary(c):
    return {
        "amount": get_amount(c),
        "budget": get_budget(c),
        "company": c.get("denominacio_adjudicatari", ""),
        "nif": c.get("identificacio_adjudicatari", ""),
        "organ": c.get("nom_organ", ""),
        "description": c.get("denominacio", ""),
        "procedure": c.get("procediment", ""),
        "date": c.get("data_formalitzacio_contracte", "") or c.get("data_adjudicacio_contracte", ""),
        "url": get_url(c),
    }


def main():
    try:
        with open(INPUT) as f:
            contracts = json.load(f)
    except FileNotFoundError:
        print(f"Error: {INPUT} not found. Run scripts/fetch.sh first.", file=sys.stderr)
        sys.exit(1)

    print(f"Loaded {len(contracts)} contracts from {INPUT}")

    # F1: single bidder above €1M
    f1 = sorted(
        [c for c in contracts if str(c.get("ofertes_rebudes", "")).strip() == "1" and get_amount(c) > 1_000_000],
        key=get_amount,
        reverse=True,
    )

    # F2: non-open procedure above €500K
    open_procedures = {"obert", "obert simplificat", ""}
    f2 = sorted(
        [c for c in contracts if c.get("procediment", "").lower() not in open_procedures and get_amount(c) > 500_000],
        key=get_amount,
        reverse=True,
    )

    # F3: award 97–101% of budget above €1M
    f3 = []
    for c in contracts:
        a, b = get_amount(c), get_budget(c)
        if b > 1_000_000 and a > 0:
            ratio = a / b
            if 0.97 <= ratio <= 1.01:
                f3.append((ratio, c))
    f3.sort(key=lambda x: get_amount(x[1]), reverse=True)

    # F4: repeat winner at same organ (>=3 contracts >€200K)
    organ_company = defaultdict(lambda: defaultdict(list))
    for c in contracts:
        company = c.get("denominacio_adjudicatari", "").strip()
        organ = c.get("nom_organ", "").strip()
        if company and organ and get_amount(c) > 200_000:
            organ_company[organ][company].append(c)

    f4 = []
    for organ, companies in organ_company.items():
        for company, cs in companies.items():
            if len(cs) >= 3:
                total = sum(get_amount(c) for c in cs)
                f4.append({"organ": organ, "company": company, "count": len(cs), "total": total})
    f4.sort(key=lambda x: x["total"], reverse=True)

    # F5: exact 100% match above €5M (subset of F3)
    f5 = [(r, c) for r, c in f3 if abs(r - 1.0) < 0.0001 and get_amount(c) > 5_000_000]
    f5.sort(key=lambda x: get_amount(x[1]), reverse=True)

    print(f"F1 single bidder >1M:        {len(f1):4d} contracts  €{sum(get_amount(c) for c in f1):>18,.0f}")
    print(f"F2 non-open >500K:           {len(f2):4d} contracts  €{sum(get_amount(c) for c in f2):>18,.0f}")
    print(f"F3 award 97-101% budget >1M: {len(f3):4d} contracts")
    print(f"F4 repeat winners (>=3):     {len(f4):4d} organ/company pairs")
    print(f"F5 exact 100% match >5M:     {len(f5):4d} contracts")

    results = {
        "meta": {
            "total_contracts": len(contracts),
            "source": "contractes.cat",
        },
        "f1_single_bidder": [contract_summary(c) for c in f1[:30]],
        "f2_non_open": [contract_summary(c) for c in f2[:30]],
        "f3_close_budget": [
            {**contract_summary(c), "ratio": round(r * 100, 2)}
            for r, c in f3[:30]
        ],
        "f4_repeat_winners": f4[:20],
        "f5_exact_match": [contract_summary(c) for r, c in f5[:20]],
        "deep_dive": {
            "imss_suara_servisar": {
                "organ": "Institut Municipal de Serveis Socials de Barcelona",
                "companies": [
                    {"name": "SUARA SERVEIS SCCL", "nif": "F17444225", "total_all_time": 159399981.80, "contracts_all_time": 24},
                    {"name": "SERVISAR SERVICIOS SOCIALES SL", "nif": "B48758890", "total_all_time": 93439576.76, "contracts_all_time": 2},
                    {"name": "AVORIS RETAIL DIVISION SL", "nif": "B07012107", "total_all_time": 101972068.28, "contracts_all_time": 8},
                ],
                "flags": ["Non-open procedure", "Single bidder", "Repeat winner"],
            },
            "sem_falck": {
                "organ": "Sistema d'Emergències Mèdiques (SEM)",
                "companies": [
                    {"name": "FALCK SERVICIOS SANITARIOS SLU", "nif": "B58552712", "total_all_time": 654105139.46, "contracts_all_time": 4},
                    {"name": "UTE La Pau-Direxis Salud", "nif": "U75709204", "total_all_time": 380990754.87, "contracts_all_time": 1},
                    {"name": "UTE TRANSPORT SANITARI DE BARCELONA", "nif": "U75960989", "total_all_time": 317858344.07, "contracts_all_time": 1},
                    {"name": "Ivemon Ambulàncies Egara SLU", "nif": "B08923963", "total_all_time": 276854831.53, "contracts_all_time": 2},
                ],
                "flags": ["Award = 100% of budget", "Single bidder", "Market concentration"],
            },
            "ctti_seidor": {
                "organ": "Centre de Telecomunicacions i Tecnologies de la Informació (CTTI)",
                "companies": [
                    {"name": "SEIDOR CONSULTING SL", "nif": "B62076740", "total_all_time": 79197391.17, "contracts_all_time": 16},
                    {"name": "SEIDOR SOLUTIONS SL", "nif": "B61172219", "total_all_time": 17975877.86, "contracts_all_time": 10},
                    {"name": "TELEFÓNICA SAU", "nif": "A78053147", "total_all_time": 91997226.74, "contracts_all_time": 7},
                ],
                "flags": ["Repeat winner", "Single bidder", "Group concentration"],
            },
        },
    }

    with open(OUTPUT, "w") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Saved {OUTPUT}")


if __name__ == "__main__":
    main()
