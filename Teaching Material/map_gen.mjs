// map_gen.mjs — Underlisted master mind map generator
// Edit the MAP data below, then run:  node map_gen.mjs
// It writes IDEA-MAP.md (editable source) and IDEA-MAP.html (the picture).
// Render PDF/PNG from the HTML with Edge headless (see commands in the .md footer).
//
// Status legend used on leaves:
//   "done"   ✅ green  — built / live
//   "free"   🆓 green  — free data source, wired or pickable, no cost
//   "paid"   💲 amber  — costs money / paid tier
//   "next"   ⏳ amber  — planned, not yet
//   "off"    ⚪ muted  — not yet / parked / not subscribed
//   "warn"   ⚠️ red    — warning / rule / blocker

import { writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const __dirname = dirname(fileURLToPath(import.meta.url));

// ---- BRAND ----
const BRAND = {
  green: "#1D9E75",
  deep: "#0F6E56",
  fill: "#E1F5EE",
  ink: "#1F2933",
  amber: "#E08A00",
  red: "#C0392B",
  muted: "#8A97A3",
  paper: "#FBFEFD",
};

const CENTER = "UNDERLISTED — find under-priced U.S. homes";

// ---- THE MAP DATA (this is the source of truth — edit here) ----
const BRANCHES = [
  {
    name: "1 · LIVE SYSTEM",
    sub: "how the apps connect",
    icon: "🔌",
    color: BRAND.deep,
    groups: [
      {
        label: "🔑 Connected by API KEY",
        leaves: [
          { t: "RentCast → home listings / value / rent (RENTCAST_API_KEY)", s: "paid" },
          { t: "Resend → sends the alert emails (RESEND_API_KEY)", s: "done" },
          { t: "Supabase → the database (DATABASE_URL: address + password)", s: "done" },
          { t: "Google Street View → house photos (STREETVIEW_API_KEY)", s: "off", note: "PARKED / 403" },
        ],
      },
      {
        label: "👤 Connected by LOGIN",
        leaves: [
          { t: "GitHub stores the code", s: "done" },
          { t: "Streamlit Cloud runs the app (via GitHub login)", s: "done" },
          { t: "LIVE: underlisted-gidalbx5x5vlaeuvqncwpp.streamlit.app", s: "done" },
        ],
      },
      {
        label: "📍 Connected by ADDRESS / DNS",
        leaves: [
          { t: "Namecheap owns domain underlistedhomes.com", s: "done" },
          { t: "Netlify hosts public site + waitlist (DNS: A @→75.2.60.5, CNAME www)", s: "done" },
          { t: "Netlify Forms captures waitlist emails", s: "done" },
        ],
      },
      {
        label: "🗝️ Keys live in secret boxes",
        leaves: [
          { t: ".env (on your computer — local)", s: "done" },
          { t: "Streamlit Secrets (the live app)", s: "done" },
          { t: "GitHub Actions Secrets (the worker)", s: "next" },
        ],
      },
      {
        label: "⚙️ The Worker (keeps cost low)",
        leaves: [
          { t: "GitHub Actions cron fills the Supabase database", s: "next" },
          { t: "The app only READS the shared cache — never fetches on load", s: "done" },
        ],
      },
    ],
  },
  {
    name: "2 · DATA SOURCES",
    sub: "all over the USA",
    icon: "🗺️",
    color: BRAND.green,
    groups: [
      {
        label: "✅ Wired & FREE (government, no key)",
        leaves: [
          { t: "FEMA National Risk Index — fire / quake", s: "free" },
          { t: "FEMA National Flood Hazard Layer — flood", s: "free" },
          { t: "FHFA House Price Index — ZIP price trends", s: "free" },
        ],
      },
      {
        label: "✅ Wired & PAID",
        leaves: [
          { t: "RentCast — listings / value / rent (free 50/mo → $74/mo)", s: "paid" },
        ],
      },
      {
        label: "🏚️ Foreclosure / bank-owned (free gov to browse)",
        leaves: [
          { t: "HUD HomeStore · Fannie HomePath · Freddie HomeSteps", s: "free" },
          { t: "VA · USDA · Treasury · US Marshals · IRS · GSA auctions", s: "free" },
          { t: "County tax-sale: Bid4Assets · GovEase · RealAuction", s: "free" },
          { t: "Marketplaces: Auction.com · Hubzu · Xome", s: "free" },
        ],
      },
      {
        label: "🏚️ Foreclosure DATA APIs (paid, licensed)",
        leaves: [
          { t: "Foreclosure Data Hub — OUR PICK ($1 trial → $49/mo)", s: "off", note: "not subscribed yet" },
          { t: "ATTOM · CoreLogic · PropertyRadar · BatchData · Estated", s: "paid" },
        ],
      },
      {
        label: "📊 Free market data (download)",
        leaves: [
          { t: "Zillow Research · Redfin Data Center · Realtor.com Research", s: "free" },
          { t: "FRED · HUD USER · US Census ACS + TIGER · data.gov", s: "free" },
          { t: "HUD Fair Market Rents (free token)", s: "next" },
        ],
      },
      {
        label: "🏘️ MLS / IDX feeds (need broker approval)",
        leaves: [
          { t: "RESO Web API standard · Bridge Interactive · CoreLogic Trestle", s: "off" },
          { t: "SimplyRETS · MLS Grid · Spark API", s: "off" },
        ],
      },
      {
        label: "🧩 Modern property APIs (paid, some free tiers)",
        leaves: [
          { t: "Parcl Labs · HelloData.ai · Rentometer", s: "paid" },
          { t: "AirDNA · Datafiniti · Mashvisor", s: "paid" },
        ],
      },
      {
        label: "🔥 Free risk / climate",
        leaves: [
          { t: "FEMA NRI · FEMA NFHL · First Street / Risk Factor", s: "free" },
          { t: "USGS Earthquake · EPA EJScreen · AirNow", s: "free" },
          { t: "USFS Wildfire · CAL FIRE", s: "free" },
        ],
      },
      {
        label: "🚶 Livability",
        leaves: [
          { t: "Walk Score (free tier) · OpenStreetMap / Overpass", s: "free" },
          { t: "FCC Broadband Map", s: "free" },
          { t: "GreatSchools (paid)", s: "paid" },
        ],
      },
      {
        label: "⚠️ RULES (must follow)",
        leaves: [
          { t: "Crime / demographic data NEVER used in scoring (Fair Housing) — info only", s: "warn" },
          { t: "Never scrape portals — licensed APIs only", s: "warn" },
        ],
      },
    ],
  },
  {
    name: "3 · WHAT'S DONE",
    sub: "already built",
    icon: "✅",
    color: BRAND.green,
    groups: [
      {
        label: "Shipped",
        leaves: [
          { t: "Brand name Underlisted + owned domain underlistedhomes.com", s: "done" },
          { t: "Live public site + waitlist (Netlify)", s: "done" },
          { t: "HTTPS secured", s: "done" },
          { t: "Email alerts (Resend)", s: "done" },
          { t: "Brand applied across app / site / marketing", s: "done" },
          { t: "Marketing kit (ads, posts, launch email)", s: "done" },
          { t: "Promo video (map intro + app demo)", s: "done" },
          { t: "Code on GitHub (public)", s: "done" },
          { t: "App deployed LIVE on Streamlit", s: "done" },
          { t: "Supabase database created", s: "done" },
        ],
      },
    ],
  },
  {
    name: "4 · GAME PLAN / NEXT",
    sub: "in order",
    icon: "⏳",
    color: BRAND.amber,
    groups: [
      {
        label: "Do these in order",
        leaves: [
          { t: "1. Verify the Supabase database connection (tables auto-create)", s: "next" },
          { t: "2. Auto-refresh WORKER (GitHub Actions cron): listings + risk + market + alert emails, cost-guarded", s: "next" },
          { t: "3. Payment button $29.99/mo (provider TBD — don't wire selling without asking)", s: "next" },
          { t: "4. Wire more FREE data (HUD Fair Market Rents token; gov foreclosure browse links)", s: "next" },
          { t: "5. Later (when revenue justifies): subscribe Foreclosure Data Hub; verify domain in Resend; fix Street View 403", s: "off" },
          { t: "6. GROWTH: SEO city pages (done) · short promo videos · waitlist → launch", s: "next" },
        ],
      },
      {
        label: "💲 Pricing path",
        leaves: [
          { t: "$12.99/mo intro (12 months) → $29.99 now → $44.99 later", s: "paid" },
        ],
      },
    ],
  },
  {
    name: "5 · THE MOAT",
    sub: "why we win",
    icon: "🛡️",
    color: BRAND.deep,
    groups: [
      {
        label: "Our edge",
        leaves: [
          { t: "Beginner-simple plain-English Deal Score 0–100", s: "done" },
          { t: "Fire / flood INSURANCE-RISK warning (unique)", s: "done" },
          { t: "True monthly cost shown", s: "done" },
          { t: "Real cash needed shown", s: "done" },
          { t: "Nationwide USA", s: "done" },
          { t: "Cheap-to-run shared-cache architecture", s: "done" },
          { t: "$12.99 founding price", s: "paid" },
        ],
      },
    ],
  },
];

// ---- status meta ----
const STATUS = {
  done: { mark: "✅", color: BRAND.green, name: "Built / live" },
  free: { mark: "🆓", color: BRAND.green, name: "Free source" },
  paid: { mark: "💲", color: BRAND.amber, name: "Paid" },
  next: { mark: "⏳", color: BRAND.amber, name: "Planned next" },
  off: { mark: "⚪", color: BRAND.muted, name: "Not yet / parked" },
  warn: { mark: "⚠️", color: BRAND.red, name: "Rule / warning" },
};

// count "built" = done leaves, "total" = all leaves in a branch
function counts(branch) {
  let total = 0, built = 0;
  for (const g of branch.groups) for (const l of g.leaves) {
    total++;
    if (l.s === "done") built++;
  }
  return { built, total };
}

// =================== MARKDOWN (editable source) ===================
function buildMd() {
  let md = `# Underlisted — Master Mind Map\n\n`;
  md += `_Center → branches → leaves. Edit \`map_gen.mjs\` and re-run to update this file and the picture._\n\n`;
  md += `**Center:** ${CENTER}\n\n`;
  md += `**Legend:** `;
  md += Object.values(STATUS).map(s => `${s.mark} ${s.name}`).join(" · ") + "\n\n";

  for (const b of BRANCHES) {
    const c = counts(b);
    md += `## ${b.icon} ${b.name} — _${b.sub}_  (${c.built}/${c.total} built)\n\n`;
    for (const g of b.groups) {
      md += `- **${g.label}**\n`;
      for (const l of g.leaves) {
        const st = STATUS[l.s];
        const note = l.note ? `  _(${l.note})_` : "";
        md += `  - ${st.mark} ${l.t}${note}\n`;
      }
    }
    md += `\n`;
  }

  // Mermaid mindmap block (previews as a diagram on GitHub / VS Code)
  md += `## Diagram (Mermaid mindmap)\n\n`;
  md += "```mermaid\nmindmap\n";
  md += `  root((Underlisted<br/>under-priced US homes))\n`;
  for (const b of BRANCHES) {
    md += `    ${b.icon} ${b.name}\n`;
    for (const g of b.groups) {
      const label = g.label.replace(/[()]/g, "");
      md += `      ${label}\n`;
      for (const l of g.leaves) {
        const st = STATUS[l.s];
        const txt = l.t.replace(/[()]/g, "").slice(0, 60);
        md += `        ${st.mark} ${txt}\n`;
      }
    }
  }
  md += "```\n\n";

  md += `---\n\n### How to refresh the picture\n`;
  md += "```\nnode map_gen.mjs\n";
  md += `"C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe" --headless=new --disable-gpu --no-pdf-header-footer --print-to-pdf="<ABS>/IDEA-MAP.pdf" "file:///<ABS>/IDEA-MAP.html"\n`;
  md += `"C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe" --headless=new --disable-gpu --hide-scrollbars --window-size=1600,1130 --screenshot="<ABS>/IDEA-MAP.png" "file:///<ABS>/IDEA-MAP.html"\n`;
  md += "```\n";
  return md;
}

// =================== HTML (the drawn picture) ===================
function leafHtml(l) {
  const st = STATUS[l.s];
  const note = l.note ? `<span class="note">${l.note}</span>` : "";
  return `<li class="leaf s-${l.s}"><span class="mark">${st.mark}</span><span class="ltxt">${l.t}${note}</span></li>`;
}

function groupHtml(g) {
  return `<div class="group">
    <div class="glabel">${g.label}</div>
    <ul class="leaves">${g.leaves.map(leafHtml).join("")}</ul>
  </div>`;
}

function cardHtml(b) {
  const c = counts(b);
  return `<section class="card" style="--accent:${b.color}">
    <header class="chead">
      <div class="ctitle"><span class="cicon">${b.icon}</span>${b.name}</div>
      <div class="csub">${b.sub}</div>
      <div class="badge">${c.built}/${c.total} built</div>
    </header>
    <div class="groups">${b.groups.map(groupHtml).join("")}</div>
  </section>`;
}

function legendHtml() {
  return Object.values(STATUS).map(s =>
    `<span class="lg"><span class="lgmark">${s.mark}</span>${s.name}</span>`
  ).join("");
}

function buildHtml() {
  return `<!doctype html><html lang="en"><head><meta charset="utf-8">
<style>
  @page { size: A4 landscape; margin: 10mm; }
  * { box-sizing: border-box; }
  body {
    margin: 0; font-family: "Segoe UI", system-ui, Arial, sans-serif;
    color: ${BRAND.ink}; background: ${BRAND.paper};
    -webkit-print-color-adjust: exact; print-color-adjust: exact;
  }
  .sheet { padding: 16px 20px 20px; }

  /* center node */
  .center-wrap { text-align: center; margin: 2px 0 14px; }
  .center {
    display: inline-block; padding: 14px 34px; border-radius: 999px;
    background: linear-gradient(135deg, ${BRAND.green}, ${BRAND.deep});
    color: #fff; font-size: 21px; font-weight: 800; letter-spacing: .2px;
    box-shadow: 0 6px 18px rgba(15,110,86,.30);
  }
  .center .small { display:block; font-size: 12px; font-weight:600; opacity:.92; margin-top:2px; }

  /* legend */
  .legend {
    text-align:center; margin: 0 0 14px; font-size: 11.5px; color:${BRAND.ink};
  }
  .lg { display:inline-block; margin: 0 8px; padding: 3px 10px; border-radius: 999px;
        background: ${BRAND.fill}; border:1px solid #cfeadf; }
  .lgmark { margin-right: 5px; }

  /* grid of branch cards */
  .grid {
    display: grid; grid-template-columns: repeat(3, 1fr);
    gap: 14px; align-items: start;
  }
  .card {
    border: 1px solid #e3ebe8; border-top: 6px solid var(--accent);
    border-radius: 12px; background: #fff; overflow: hidden;
    box-shadow: 0 2px 8px rgba(31,41,51,.06);
    break-inside: avoid;
  }
  .card.span2 { grid-column: span 2; }
  .chead {
    padding: 10px 14px 8px; background:
      linear-gradient(180deg, color-mix(in srgb, var(--accent) 9%, #fff), #fff);
    position: relative;
  }
  .ctitle { font-size: 16px; font-weight: 800; color: var(--accent); display:flex; align-items:center; gap:7px; }
  .cicon { font-size: 17px; }
  .csub { font-size: 11px; color: ${BRAND.muted}; margin-top: 1px; }
  .badge {
    position: absolute; top: 10px; right: 12px;
    background: var(--accent); color:#fff; font-size: 11px; font-weight: 700;
    padding: 3px 10px; border-radius: 999px;
  }

  .groups { padding: 8px 12px 12px; }
  .group { margin-top: 8px; }
  .group:first-child { margin-top: 2px; }
  .glabel {
    font-size: 11.5px; font-weight: 700; color: ${BRAND.deep};
    margin-bottom: 3px; padding-bottom: 2px; border-bottom: 1px dashed #d4e7df;
  }
  ul.leaves { list-style: none; margin: 0; padding: 0; }
  .leaf { display: flex; gap: 6px; align-items: baseline; font-size: 11px;
          line-height: 1.32; padding: 1.5px 0; }
  .leaf .mark { flex: 0 0 auto; font-size: 11px; }
  .leaf .ltxt { color: ${BRAND.ink}; }
  .note { display:inline-block; margin-left:6px; font-size: 9.5px; font-weight:700;
          padding: 0 6px; border-radius: 999px; vertical-align: middle; }

  /* status accents on leaves */
  .s-done .ltxt { color: ${BRAND.ink}; }
  .s-free .mark, .s-done .mark { filter: none; }
  .s-paid .note { background:#fbeccd; color:${BRAND.amber}; }
  .s-off  .ltxt { color: ${BRAND.muted}; }
  .s-off  .note { background:#eceff1; color:${BRAND.muted}; }
  .s-warn .ltxt { color: ${BRAND.red}; font-weight: 600; }

  .foot { text-align:center; margin-top: 12px; font-size: 10px; color:${BRAND.muted}; }
</style></head>
<body>
  <div class="sheet">
    <div class="center-wrap">
      <div class="center">UNDERLISTED
        <span class="small">find under-priced U.S. homes — type a city, get a plain-English Deal Score</span>
      </div>
    </div>
    <div class="legend">${legendHtml()}</div>
    <div class="grid">
      ${cardHtml(BRANCHES[0])}
      ${cardHtml(BRANCHES[1].name ? { ...BRANCHES[1] } : BRANCHES[1])}
      <div style="display:flex; flex-direction:column; gap:14px;">
        ${cardHtml(BRANCHES[2])}
        ${cardHtml(BRANCHES[3])}
        ${cardHtml(BRANCHES[4])}
      </div>
    </div>
    <div class="foot">Underlisted master mind map · edit map_gen.mjs and re-run to update · brand green ${BRAND.green}</div>
  </div>
</body></html>`;
}

// ---- write files ----
const mdPath = join(__dirname, "IDEA-MAP.md");
const htmlPath = join(__dirname, "IDEA-MAP.html");
writeFileSync(mdPath, buildMd(), "utf8");
writeFileSync(htmlPath, buildHtml(), "utf8");

const totals = BRANCHES.reduce((a, b) => {
  const c = counts(b); a.built += c.built; a.total += c.total; return a;
}, { built: 0, total: 0 });

console.log(`Wrote:\n  ${mdPath}\n  ${htmlPath}`);
console.log(`Built ${totals.built} of ${totals.total} leaves across ${BRANCHES.length} branches.`);
