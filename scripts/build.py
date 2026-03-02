#!/usr/bin/env python3
"""
build.py — Loads analysis.json + data.json, generates index.html
"""

import json
import sys
from collections import Counter

ANALYSIS_INPUT = "analysis.json"
DATA_INPUT = "data.json"
OUTPUT = "index.html"


def load_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: {path} not found.", file=sys.stderr)
        sys.exit(1)


def get_amount(c):
    for field in ("import_adjudicacio_amb_iva", "import_adjudicacio_sense", "valor_estimat_contracte"):
        v = c.get(field)
        if v:
            try:
                return float(v)
            except (TypeError, ValueError):
                pass
    return 0.0


def query_block(cmd, note=None):
    note_html = f'<p class="text-slate-500 text-xs mt-2">{note}</p>' if note else ""
    return f"""<details class="query-block mt-4">
  <summary class="cursor-pointer text-xs text-slate-500 hover:text-slate-300 select-none flex items-center gap-1.5">
    <span class="query-arrow">▶</span> Consulta CLI utilitzada
  </summary>
  <div class="query-body mt-2 relative">
    <pre class="query-pre"><code>{cmd}</code></pre>
    <button class="copy-btn" onclick="copyCode(this)">Copia</button>
    {note_html}
  </div>
</details>"""


Q_BASE = query_block(
    "for page in $(seq 1 20); do\n  contractes search-contracts --year 2025 --sort amount-desc --page $page --raw\ndone",
    "Recupera els 1.000 contractes de major valor de 2025 (20 pàgines × 50 resultats). Les flags F1–F4 s'apliquen com a filtre posterior sobre aquest conjunt.",
)

DEEP_DIVE_QUERIES = {
    "imss": 'contractes organ-top-companies --organ "Institut Municipal de Serveis Socials" --limit 10 --raw',
    "sem": "contractes organ-top-companies --organ \"Sistema d'Emergències Mèdiques (SEM)\" --limit 10 --raw",
    "ctti": 'contractes organ-top-companies --organ "Centre de Telecomunicacions i Tecnologies de la Informació de la Generalitat de Catalunya (CTTI)" --limit 10 --raw',
}


def main():
    analysis = load_json(ANALYSIS_INPUT)
    raw = load_json(DATA_INPUT)

    proc_counter = Counter()
    for c in raw:
        p = c.get("procediment", "") or "No especificat"
        proc_counter[p] += 1

    proc_labels = json.dumps([k for k, v in proc_counter.most_common(6)])
    proc_values = json.dumps([v for k, v in proc_counter.most_common(6)])
    data_json = json.dumps(analysis, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="ca">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Risc de Frau en Contractació Pública Catalana — 2025</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
  <style>
    body {{ font-family: 'Inter', system-ui, sans-serif; background: #0f172a; color: #e2e8f0; }}
    .card {{ background: #1e293b; border: 1px solid #334155; border-radius: 0.75rem; padding: 1.5rem; }}
    .flag-badge {{ display: inline-block; padding: 0.15rem 0.6rem; border-radius: 9999px; font-size: 0.7rem; font-weight: 700; letter-spacing: 0.05em; }}
    .flag-red {{ background: #7f1d1d; color: #fca5a5; }}
    .flag-orange {{ background: #7c2d12; color: #fdba74; }}
    .flag-yellow {{ background: #713f12; color: #fde047; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 0.85rem; }}
    th {{ background: #0f172a; color: #94a3b8; text-align: left; padding: 0.5rem 0.75rem; font-weight: 600; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; position: sticky; top: 0; }}
    td {{ padding: 0.5rem 0.75rem; border-bottom: 1px solid #1e293b; color: #cbd5e1; vertical-align: top; }}
    tr:hover td {{ background: #1e3a5f22; }}
    .amount {{ text-align: right; font-variant-numeric: tabular-nums; font-weight: 600; color: #38bdf8; }}
    .ratio {{ text-align: center; font-variant-numeric: tabular-nums; }}
    .muted {{ color: #64748b; font-size: 0.78rem; }}
    .section-title {{ font-size: 1.2rem; font-weight: 700; color: #f1f5f9; margin-bottom: 0.25rem; }}
    .section-sub {{ color: #64748b; font-size: 0.85rem; margin-bottom: 1rem; }}
    .deep-dive-header {{ background: linear-gradient(135deg, #1e3a5f, #1e293b); border: 1px solid #2563eb44; border-radius: 0.75rem; padding: 1.25rem 1.5rem; margin-bottom: 1rem; }}
    a {{ color: #60a5fa; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .scroll-table {{ overflow-x: auto; max-height: 480px; overflow-y: auto; border-radius: 0.5rem; border: 1px solid #334155; }}
    .query-block {{ border-top: 1px solid #1e293b; padding-top: 0.75rem; }}
    .query-block summary {{ font-family: 'JetBrains Mono', 'Fira Code', monospace; }}
    .query-block[open] .query-arrow {{ display: inline-block; transform: rotate(90deg); }}
    .query-pre {{ background: #0f172a; border: 1px solid #334155; border-radius: 0.5rem; padding: 1rem; font-size: 0.78rem; font-family: 'JetBrains Mono', 'Fira Code', 'Courier New', monospace; color: #7dd3fc; overflow-x: auto; white-space: pre; line-height: 1.6; }}
    .query-body {{ position: relative; }}
    .copy-btn {{ position: absolute; top: 0.5rem; right: 0.5rem; background: #1e293b; border: 1px solid #334155; color: #94a3b8; font-size: 0.7rem; padding: 0.2rem 0.6rem; border-radius: 0.3rem; cursor: pointer; transition: all 0.15s; }}
    .copy-btn:hover {{ background: #334155; color: #e2e8f0; }}
    .copy-btn.copied {{ border-color: #22c55e; color: #22c55e; }}
  </style>
</head>
<body class="min-h-screen">

<!-- HEADER -->
<div class="bg-gradient-to-r from-slate-900 via-blue-950 to-slate-900 border-b border-slate-700 px-6 py-10">
  <div class="max-w-6xl mx-auto">
    <div class="flex items-start gap-4">
      <div class="text-4xl">🔍</div>
      <div>
        <h1 class="text-3xl font-bold text-white">Risc de Frau en Contractació Pública Catalana</h1>
        <p class="text-slate-400 mt-1">Anàlisi automatitzada dels 1.000 contractes de major valor publicats a <strong class="text-slate-300">contractes.cat</strong> durant 2025</p>
        <div class="flex gap-3 mt-3 flex-wrap">
          <span class="flag-badge flag-red">🚨 5 indicadors de risc</span>
          <span class="flag-badge" style="background:#1e3a5f;color:#93c5fd">Font: Registre Públic de Contractes de Catalunya</span>
          <span class="flag-badge" style="background:#1e293b;color:#64748b">Actualitzat: 2025</span>
        </div>
      </div>
    </div>
  </div>
</div>

<div class="max-w-6xl mx-auto px-4 py-10 space-y-12">

<!-- SUMMARY CARDS -->
<div>
  <h2 class="text-xs font-bold text-slate-500 uppercase tracking-widest mb-4">Resum executiu</h2>
  <div class="grid grid-cols-2 md:grid-cols-5 gap-4" id="summary-cards"></div>
</div>

<!-- CHARTS -->
<div class="grid grid-cols-1 md:grid-cols-2 gap-6">
  <div class="card">
    <div class="section-title">Distribució per procediment</div>
    <div class="section-sub">Nombre de contractes per tipus de procediment</div>
    <canvas id="chartProc" height="220"></canvas>
    {Q_BASE}
  </div>
  <div class="card">
    <div class="section-title">Valor total per indicador de risc</div>
    <div class="section-sub">Euros en contractes que activen cada flag (milions €)</div>
    <canvas id="chartFlags" height="220"></canvas>
    {Q_BASE}
  </div>
</div>

<!-- FLAG 1 -->
<div class="card">
  <div class="flex items-start justify-between flex-wrap gap-2 mb-1">
    <div>
      <div class="section-title">🚩 F1 — Licitador únic per sobre d'1M€</div>
      <div class="section-sub">Contractes adjudicats amb una sola oferta rebuda i import superior a 1.000.000 €</div>
    </div>
    <span class="flag-badge flag-red" id="f1-badge"></span>
  </div>
  <div class="scroll-table">
    <table id="f1-table">
      <thead><tr><th>Import</th><th>Empresa</th><th>Òrgan contractant</th><th>Procediment</th><th>Objecte</th></tr></thead>
      <tbody></tbody>
    </table>
  </div>
  {Q_BASE}
</div>

<!-- FLAG 2 -->
<div class="card">
  <div class="flex items-start justify-between flex-wrap gap-2 mb-1">
    <div>
      <div class="section-title">🚩 F2 — Procediment no obert per sobre de 500K€</div>
      <div class="section-sub">Contractes adjudicats per via negociada, restringida o similar sense concurrència oberta</div>
    </div>
    <span class="flag-badge flag-orange" id="f2-badge"></span>
  </div>
  <div class="scroll-table">
    <table id="f2-table">
      <thead><tr><th>Import</th><th>Empresa</th><th>Òrgan contractant</th><th>Procediment</th><th>Objecte</th></tr></thead>
      <tbody></tbody>
    </table>
  </div>
  {Q_BASE}
</div>

<!-- FLAG 3 -->
<div class="card">
  <div class="flex items-start justify-between flex-wrap gap-2 mb-1">
    <div>
      <div class="section-title">🚩 F3 — Adjudicació entre el 97% i el 101% del pressupost base</div>
      <div class="section-sub">Possiblement indica coneixement previ del pressupost màxim (top 30 per import)</div>
    </div>
    <span class="flag-badge flag-yellow" id="f3-badge"></span>
  </div>
  <div class="scroll-table">
    <table id="f3-table">
      <thead><tr><th>Import adjudicat</th><th>% pressupost</th><th>Empresa</th><th>Òrgan contractant</th><th>Objecte</th></tr></thead>
      <tbody></tbody>
    </table>
  </div>
  {Q_BASE}
</div>

<!-- FLAG 4 -->
<div class="card">
  <div class="flex items-start justify-between flex-wrap gap-2 mb-1">
    <div>
      <div class="section-title">🚩 F4 — Guanyador repetit al mateix òrgan (≥3 contractes >200K€)</div>
      <div class="section-sub">Indica possible dependència o manca de concurrència real</div>
    </div>
    <span class="flag-badge flag-orange" id="f4-badge"></span>
  </div>
  <div class="scroll-table">
    <table id="f4-table">
      <thead><tr><th>Total acumulat</th><th>Nº contractes</th><th>Empresa</th><th>Òrgan contractant</th></tr></thead>
      <tbody></tbody>
    </table>
  </div>
  {Q_BASE}
</div>

<!-- DEEP DIVES -->
<div>
  <h2 class="text-xs font-bold text-slate-500 uppercase tracking-widest mb-6">Anàlisi en profunditat</h2>
  <div class="space-y-6" id="deep-dives"></div>
</div>

<!-- METHODOLOGY -->
<div class="card border-slate-700">
  <div class="section-title text-slate-400">Metodologia i limitacions</div>
  <div class="mt-3 text-sm text-slate-500 space-y-2">
    <p>Les dades provenen del <strong class="text-slate-400">Registre Públic de Contractes de Catalunya</strong> a través de la API pública de <a href="https://contractes.cat">contractes.cat</a>. S'han analitzat els <strong class="text-slate-400">1.000 contractes de major valor</strong> publicats l'any 2025.</p>
    <p>Els indicadors de risc detecten <strong class="text-slate-400">patrons estadísticament anòmals</strong>, no proven irregularitat legal. Algunes adjudicacions per licitador únic o procediment negociat estan legalment justificades (urgència, patent, mercat limitat, etc.).</p>
    <p>Per a les tarifes socials i sanitàries, preus propers al 100% del pressupost base pot reflectir simplement un mercat de tarifa regulada sense marge de negociació.</p>
    <p class="text-slate-600">Codi font: <a href="https://github.com/xesco/risc-de-frau">github.com/xesco/risc-de-frau</a> — Llicència: CC BY 4.0</p>
  </div>
</div>

</div>

<script>
const DATA = {data_json};

const fmt = n => new Intl.NumberFormat('ca-ES', {{style:'currency', currency:'EUR', maximumFractionDigits:0}}).format(n);
const fmtM = n => (n/1e6).toFixed(1) + 'M€';
const trunc = (s, n=55) => s && s.length > n ? s.slice(0,n)+'…' : (s||'—');

function copyCode(btn) {{
  const code = btn.closest('.query-body').querySelector('code').textContent;
  navigator.clipboard.writeText(code).then(() => {{
    btn.textContent = '✓ Copiat';
    btn.classList.add('copied');
    setTimeout(() => {{ btn.textContent = 'Copia'; btn.classList.remove('copied'); }}, 2000);
  }});
}}

// Summary cards
const cards = [
  {{ label: 'Contractes analitzats', value: DATA.meta.total_contracts.toLocaleString('ca-ES'), icon: '📋', color: 'text-slate-300' }},
  {{ label: 'F1 · Licitador únic >1M€', value: DATA.f1_single_bidder.length + '+', icon: '🚨', color: 'text-red-400', sub: fmtM(DATA.f1_single_bidder.reduce((s,c)=>s+c.amount,0)) }},
  {{ label: 'F2 · Procediment no obert >500K', value: DATA.f2_non_open.length + '+', icon: '🔒', color: 'text-orange-400', sub: fmtM(DATA.f2_non_open.reduce((s,c)=>s+c.amount,0)) }},
  {{ label: 'F3 · Adjudicació ≈ pressupost', value: DATA.f3_close_budget.length + '+', icon: '🎯', color: 'text-yellow-400', sub: 'rang 97–101%' }},
  {{ label: 'F4 · Guanyadors repetits', value: DATA.f4_repeat_winners.length, icon: '🔁', color: 'text-blue-400', sub: 'parelles empresa/òrgan' }},
];
document.getElementById('summary-cards').innerHTML = cards.map(c => `
  <div class="card text-center">
    <div class="text-3xl mb-2">${{c.icon}}</div>
    <div class="text-xl font-bold ${{c.color}}">${{c.value}}</div>
    ${{c.sub ? `<div class="text-xs text-slate-500 mt-0.5">${{c.sub}}</div>` : ''}}
    <div class="text-xs text-slate-500 mt-1">${{c.label}}</div>
  </div>`).join('');

// Charts
const chartColors = ['#3b82f6','#06b6d4','#8b5cf6','#ec4899','#f59e0b','#64748b'];
new Chart(document.getElementById('chartProc'), {{
  type: 'doughnut',
  data: {{
    labels: {proc_labels},
    datasets: [{{ data: {proc_values}, backgroundColor: chartColors, borderWidth: 2, borderColor: '#0f172a' }}]
  }},
  options: {{ plugins: {{ legend: {{ labels: {{ color: '#94a3b8', font: {{ size: 11 }} }} }} }}, cutout: '60%' }}
}});

new Chart(document.getElementById('chartFlags'), {{
  type: 'bar',
  data: {{
    labels: ['F1 · Licitador únic', 'F2 · No obert', 'F3 · ≈ Pressupost', 'F4 · Repetits'],
    datasets: [{{ data: [
      DATA.f1_single_bidder.reduce((s,c)=>s+c.amount,0)/1e6,
      DATA.f2_non_open.reduce((s,c)=>s+c.amount,0)/1e6,
      DATA.f3_close_budget.reduce((s,c)=>s+c.amount,0)/1e6,
      DATA.f4_repeat_winners.reduce((s,c)=>s+c.total,0)/1e6,
    ], backgroundColor: ['#7f1d1d','#7c2d12','#713f12','#1e3a5f'], borderRadius: 6 }}]
  }},
  options: {{
    plugins: {{ legend: {{ display: false }} }},
    scales: {{
      x: {{ ticks: {{ color: '#94a3b8' }}, grid: {{ color: '#1e293b' }} }},
      y: {{ ticks: {{ color: '#94a3b8', callback: v => v+'M' }}, grid: {{ color: '#334155' }} }}
    }}
  }}
}});

// F1 table
document.getElementById('f1-badge').textContent = DATA.f1_single_bidder.length + ' contractes · ' + fmtM(DATA.f1_single_bidder.reduce((s,c)=>s+c.amount,0));
document.querySelector('#f1-table tbody').innerHTML = DATA.f1_single_bidder.map(c => `<tr>
  <td class="amount">${{fmt(c.amount)}}</td>
  <td>${{c.url ? `<a href="${{c.url}}" target="_blank">🔗</a> ` : ''}}<span class="font-medium text-slate-200">${{trunc(c.company,45)}}</span><br><span class="muted">${{c.nif}}</span></td>
  <td class="muted">${{trunc(c.organ,45)}}</td>
  <td><span class="flag-badge ${{c.procedure.includes('Negociat')?'flag-red':'flag-orange'}}">${{c.procedure||'—'}}</span></td>
  <td class="muted">${{trunc(c.description,55)}}</td>
</tr>`).join('');

// F2 table
document.getElementById('f2-badge').textContent = DATA.f2_non_open.length + ' contractes · ' + fmtM(DATA.f2_non_open.reduce((s,c)=>s+c.amount,0));
document.querySelector('#f2-table tbody').innerHTML = DATA.f2_non_open.map(c => `<tr>
  <td class="amount">${{fmt(c.amount)}}</td>
  <td>${{c.url ? `<a href="${{c.url}}" target="_blank">🔗</a> ` : ''}}<span class="font-medium text-slate-200">${{trunc(c.company,45)}}</span><br><span class="muted">${{c.nif}}</span></td>
  <td class="muted">${{trunc(c.organ,45)}}</td>
  <td><span class="flag-badge flag-red">${{c.procedure}}</span></td>
  <td class="muted">${{trunc(c.description,55)}}</td>
</tr>`).join('');

// F3 table
document.getElementById('f3-badge').textContent = DATA.f3_close_budget.length + ' contractes';
document.querySelector('#f3-table tbody').innerHTML = DATA.f3_close_budget.map(c => `<tr>
  <td class="amount">${{fmt(c.amount)}}</td>
  <td class="ratio"><span class="flag-badge ${{Math.abs(c.ratio-100)<0.01?'flag-red':'flag-yellow'}}">${{c.ratio}}%</span></td>
  <td>${{c.url ? `<a href="${{c.url}}" target="_blank">🔗</a> ` : ''}}<span class="font-medium text-slate-200">${{trunc(c.company,45)}}</span></td>
  <td class="muted">${{trunc(c.organ,45)}}</td>
  <td class="muted">${{trunc(c.description,55)}}</td>
</tr>`).join('');

// F4 table
document.getElementById('f4-badge').textContent = DATA.f4_repeat_winners.length + ' parelles empresa/òrgan';
document.querySelector('#f4-table tbody').innerHTML = DATA.f4_repeat_winners.map(x => `<tr>
  <td class="amount">${{fmt(x.total)}}</td>
  <td class="ratio"><span class="flag-badge flag-orange">${{x.count}}×</span></td>
  <td class="font-medium text-slate-200">${{trunc(x.company,50)}}</td>
  <td class="muted">${{trunc(x.organ,50)}}</td>
</tr>`).join('');

// Deep dives
const deepDives = [
  {{
    id: 'imss', icon: '🏥',
    title: 'Institut Municipal de Serveis Socials de Barcelona',
    subtitle: 'Concentració extrema en serveis socials via procediment negociat sense publicitat',
    flags: ['Negociat sense publicitat','Licitador únic','Guanyador repetit'],
    flagColors: ['flag-red','flag-red','flag-orange'],
    summary: `L'IMSS ha adjudicat contractes milionaris a un cercle reduït d'empreses exclusivament via <strong>procediment negociat sense publicitat</strong>, la via de menys concurrència prevista per la llei. En els darrers anys, <strong>SUARA SERVEIS SCCL</strong> ha acumulat <strong>+159M€</strong> (24 contractes) i <strong>SERVISAR SERVICIOS SOCIALES SL</strong> <strong>+93M€</strong> (2 contractes), ambdues amb un únic ofertant. Destaca també <strong>AVORIS RETAIL DIVISION SL</strong> amb +101M€ en 8 contractes.`,
    companies: DATA.deep_dive.imss_suara_servisar.companies,
    note: 'SUARA és una cooperativa de serveis socials; la relació orgànica amb les entitats contractants mereixeria escrutini independent.',
    query: `contractes organ-top-companies --organ "Institut Municipal de Serveis Socials" --limit 10 --raw`,
  }},
  {{
    id: 'sem', icon: '🚑',
    title: "Sistema d'Emergències Mèdiques (SEM)",
    subtitle: 'Mercat captiu de transport sanitari amb adjudicacions al 100% del pressupost',
    flags: ['Adjudicació = 100% pressupost','Licitador únic','Concentració de mercat'],
    flagColors: ['flag-red','flag-red','flag-orange'],
    summary: `El SEM concentra <strong>+654M€</strong> adjudicats a FALCK SERVICIOS SANITARIOS en 4 contractes, tots amb l'import d'adjudicació igual o pràcticament igual al pressupost base. Dos contractes (278M€ i 231M€) van ser adjudicats exactament al <strong>100% del pressupost</strong>. El mercat de transport sanitari urgent és un oligopoli estructural on canviar de proveïdor és extremament difícil, el que pot justificar parcialment el procediment, però no elimina el risc de sobre-preus.`,
    companies: DATA.deep_dive.sem_falck.companies,
    note: "FALCK és l'empresa de serveis d'emergències sanitàries més gran d'Espanya i opera amb llicències exclusives per zones.",
    query: `contractes organ-top-companies --organ "Sistema d'Emergències Mèdiques (SEM)" --limit 10 --raw`,
  }},
  {{
    id: 'ctti', icon: '💻',
    title: 'Centre de Telecomunicacions i Tecnologies de la Informació (CTTI)',
    subtitle: 'Dependència tecnològica del Grup Seidor en la infraestructura digital de la Generalitat',
    flags: ['Guanyador repetit','Licitador únic','Concentració de grup empresarial'],
    flagColors: ['flag-orange','flag-orange','flag-yellow'],
    summary: `El CTTI ha adjudicat a diverses societats del <strong>Grup Seidor</strong> (Seidor Consulting, Seidor Solutions, Seidor Opentrends, SBS Seidor...) un total de <strong>+97M€</strong> en serveis IT. Seidor Consulting concentra 16 contractes per 79M€, molts amb un sol licitador. La fragmentació en filials permet mantenir el proveïdor de fet mentre es compleixen formalment els requisits de concurrència per lots.`,
    companies: DATA.deep_dive.ctti_seidor.companies,
    note: 'La fragmentació de contractes grans en lots assignats a filials del mateix grup és una pràctica que dilueix la concurrència real.',
    query: `contractes organ-top-companies --organ "Centre de Telecomunicacions i Tecnologies de la Informació de la Generalitat de Catalunya (CTTI)" --limit 10 --raw`,
  }},
];

document.getElementById('deep-dives').innerHTML = deepDives.map(dd => `
  <div class="card border-blue-900/40">
    <div class="deep-dive-header -mx-6 -mt-6 mb-4 rounded-t-xl">
      <div class="flex items-start gap-3">
        <span class="text-3xl">${{dd.icon}}</span>
        <div>
          <div class="font-bold text-white text-lg">${{dd.title}}</div>
          <div class="text-slate-400 text-sm mt-0.5">${{dd.subtitle}}</div>
          <div class="flex gap-2 flex-wrap mt-2">${{dd.flags.map((f,i)=>`<span class="flag-badge ${{dd.flagColors[i]}}">${{f}}</span>`).join(' ')}}</div>
        </div>
      </div>
    </div>
    <p class="text-slate-300 text-sm leading-relaxed mb-4">${{dd.summary}}</p>
    <div class="scroll-table mb-3">
      <table>
        <thead><tr><th>Empresa</th><th>NIF</th><th>Total acumulat</th><th>Nº contractes</th></tr></thead>
        <tbody>${{dd.companies.map(c=>`<tr>
          <td class="font-medium text-slate-200">${{c.name}}</td>
          <td class="muted">${{c.nif}}</td>
          <td class="amount">${{fmt(c.total_all_time)}}</td>
          <td class="ratio text-slate-400">${{c.contracts_all_time}}</td>
        </tr>`).join('')}}</tbody>
      </table>
    </div>
    <p class="text-xs text-slate-600 italic mb-3">${{dd.note}}</p>
    <details class="query-block">
      <summary class="cursor-pointer text-xs text-slate-500 hover:text-slate-300 select-none flex items-center gap-1.5">
        <span class="query-arrow">▶</span> Consulta CLI utilitzada
      </summary>
      <div class="query-body mt-2 relative">
        <pre class="query-pre"><code>${{dd.query}}</code></pre>
        <button class="copy-btn" onclick="copyCode(this)">Copia</button>
      </div>
    </details>
  </div>`).join('');
</script>
</body>
</html>"""

    with open(OUTPUT, "w") as f:
        f.write(html)
    print(f"Written {OUTPUT} ({len(html):,} bytes)")


if __name__ == "__main__":
    main()
