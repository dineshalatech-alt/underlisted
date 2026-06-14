// =============================================================
//  Underlisted — Project MAP generator (the strategy brain)
// -------------------------------------------------------------
//  HOW TO USE (plain English):
//   * Each "branch" below is one part of the business.
//   * Each "leaf" is one idea/piece. Set status to:
//        "done"    -> shows green check
//        "waiting" -> shows amber hourglass
//        "idea"    -> shows a lightbulb (new / being researched)
//   * To add an idea: copy a leaf line, change the text, save.
//   * Then run:  node map_gen.mjs
//     ...and re-render the picture (see render commands in IDEA-MAP.md).
//  This file is the SINGLE source of truth -> it writes IDEA-MAP.md
//  and IDEA-MAP.html. Never hand-edit those two; edit HERE.
// =============================================================

import { writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const __dirname = dirname(fileURLToPath(import.meta.url));

// ---- THE MAP DATA -------------------------------------------
const project = {
  center: "UNDERLISTED",
  tagline: "We tell you which U.S. homes are actually good deals — and why.",
  // the big flow arrows across the bottom
  flow: ["FUEL  (homes in)", "MAGIC  (we score them)", "FRONT DOOR  (customer sees)", "MONEY  (they subscribe)"],
  branches: [
    {
      name: "A.  Where the homes come from",
      sub: "the FUEL — no homes, nothing to show",
      color: "#E07A3F",      // warm coral
      tint: "#FCEDE3",
      icon: "⛽",         // fuel pump
      leaves: [
        { text: "RentCast — the PAID source of real listings (price + value + rent). The ONE paid thing.", status: "waiting" },
        { text: "RentCast is EMPTY now (quota maxed) — refills FREE on July 7, or pay to unlock sooner.", status: "waiting" },
        { text: "FEMA fire / flood risk — FREE (powers the insurance warning)", status: "done" },
        { text: "Census Building Permits — FREE (will the price hold?)", status: "done" },
        { text: "FHFA price trend — FREE (is the area going up or down?)", status: "done" },
        { text: "Freddie Mac live mortgage rate — FREE (today's real rate)", status: "done" },
        { text: "HUD Fair Market Rents — FREE (backup rent estimate)", status: "done" },
      ],
    },
    {
      name: "B.  What we DO with the homes",
      sub: "the MAGIC / our moat — all FREE math on top",
      color: "#D4A017",      // warm gold
      tint: "#FBF3D9",
      icon: "✨",         // sparkles
      leaves: [
        { text: "Deal Score 0–100 (green = good deal)", status: "done" },
        { text: "Insurance-risk warning (fire / flood) — never blank now", status: "done" },
        { text: "\"Can I afford it?\" badge (income/cash/debts → green/amber/red + money left each month)", status: "done" },
        { text: "Surprise-cost panel (tax, insurance, PMI, HOA) as honest ranges", status: "done" },
        { text: "Plain \"why this score\" sentence", status: "done" },
      ],
    },
    {
      name: "C.  What the customer sees & does",
      sub: "the FRONT DOOR",
      color: "#3FA796",      // warm teal-green
      tint: "#E2F3EF",
      icon: "\u{1F6AA}",      // door
      leaves: [
        { text: "The app (Streamlit) — LIVE", status: "done" },
        { text: "The public website (SEO site) — LIVE", status: "done" },
        { text: "Waitlist email capture — LIVE", status: "done" },
        { text: "How a buyer contacts the seller/bank & finds the address to go see the home", status: "idea" },
        { text: "Free \"What does this mean?\" learn-in-plain-English section", status: "idea" },
      ],
    },
    {
      name: "D.  How they pay",
      sub: "the MONEY",
      color: "#9B6BB0",      // warm purple
      tint: "#F1E7F5",
      icon: "\u{1F4B3}",      // card
      leaves: [
        { text: "Payhip subscribe button — BUILT, dormant until a link is pasted in", status: "waiting" },
        { text: "Founding price $18.99 / month", status: "done" },
      ],
    },
    {
      name: "E.  Status / what blocks go-live",
      sub: "where we are right now",
      color: "#C0653C",      // warm brick
      tint: "#F8E8DF",
      icon: "\u{1F6A6}",      // traffic light
      leaves: [
        { text: "DONE: affordability moat + 2 free data sources", status: "done" },
        { text: "DONE: live app, live website, live email alerts", status: "done" },
        { text: "BLOCKED until July 7: fill database with real nationwide homes (needs RentCast)", status: "waiting" },
        { text: "THEN: switch payment on and go live", status: "waiting" },
      ],
    },
  ],
};

// ---- status helpers -----------------------------------------
const MARK = { done: "✅", waiting: "⏳", idea: "\u{1F4A1}" };
const DOT  = { done: "✅", waiting: "⏳", idea: "\u{1F4A1}" };

function counts(leaves) {
  const done = leaves.filter((l) => l.status === "done").length;
  return { done, total: leaves.length };
}

// =============================================================
//  1) WRITE THE MARKDOWN SOURCE OF TRUTH (IDEA-MAP.md)
// =============================================================
function buildMarkdown() {
  let m = `# ${project.center} — Project Map\n\n`;
  m += `> ${project.tagline}\n\n`;
  m += `**The flow:**  ${project.flow.join("  →  ")}\n\n`;
  m += `**Key:**  ✅ done   ⏳ waiting   \u{1F4A1} new idea (being researched)\n\n`;
  m += `---\n\n`;

  // nested outline
  for (const b of project.branches) {
    const c = counts(b.leaves);
    m += `## ${b.icon} ${b.name}  —  *${b.sub}*  \`(${c.done}/${c.total} built)\`\n\n`;
    for (const l of b.leaves) {
      m += `- ${MARK[l.status]} ${l.text}\n`;
    }
    m += `\n`;
  }

  // mermaid mindmap block (previews as a diagram on GitHub / VS Code)
  m += `---\n\n## Diagram (auto-preview)\n\n`;
  m += "```mermaid\nmindmap\n";
  m += `  root((${project.center}))\n`;
  for (const b of project.branches) {
    const safe = b.name.replace(/[()]/g, "");
    m += `    ${safe}\n`;
    for (const l of b.leaves) {
      const txt = `${DOT[l.status]} ${l.text}`.replace(/[()]/g, "").slice(0, 70);
      m += `      ${txt}\n`;
    }
  }
  m += "```\n\n";
  m += `*This file is auto-generated by \`map_gen.mjs\`. To change the map, edit the data in that file and run \`node map_gen.mjs\`.*\n`;
  return m;
}

// =============================================================
//  2) WRITE THE PRETTY HTML (renders to PNG + PDF)
// =============================================================
function buildHtml() {
  const cards = project.branches
    .map((b) => {
      const c = counts(b.leaves);
      const leaves = b.leaves
        .map((l) => {
          const cls =
            l.status === "done" ? "done" : l.status === "waiting" ? "wait" : "idea";
          return `<li class="${cls}"><span class="mk">${MARK[l.status]}</span><span class="tx">${l.text}</span></li>`;
        })
        .join("");
      return `
      <section class="card" style="--accent:${b.color}; --tint:${b.tint};">
        <header>
          <div class="ttl"><span class="ic">${b.icon}</span> ${b.name}</div>
          <div class="badge">${c.done}/${c.total} built</div>
        </header>
        <div class="sub">${b.sub}</div>
        <ul>${leaves}</ul>
      </section>`;
    })
    .join("");

  const flowPills = project.flow
    .map((f, i) => {
      const arrow = i < project.flow.length - 1 ? '<span class="arr">→</span>' : "";
      return `<span class="pill">${f}</span>${arrow}`;
    })
    .join("");

  return `<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<style>
  @page { size: A4 landscape; margin: 10mm; }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: "Segoe UI", "DM Sans", system-ui, sans-serif;
    background: #FBF7F2; color: #2B211B; padding: 22px 26px;
  }
  .top { text-align: center; margin-bottom: 14px; }
  .center-pill {
    display: inline-block; padding: 12px 34px; border-radius: 999px;
    background: linear-gradient(135deg, #E07A3F 0%, #D4A017 100%);
    color: #fff; font-size: 30px; font-weight: 800; letter-spacing: 1px;
    box-shadow: 0 6px 18px rgba(224,122,63,.35);
  }
  .tag { margin-top: 8px; font-size: 14px; color: #6B5B4F; font-style: italic; }
  .flow {
    display: flex; justify-content: center; align-items: center;
    gap: 8px; margin: 14px 0 18px; flex-wrap: wrap;
  }
  .flow .pill {
    background: #fff; border: 2px solid #E7D9C9; border-radius: 10px;
    padding: 7px 14px; font-weight: 700; font-size: 13px; color: #4A3A2E;
    box-shadow: 0 2px 5px rgba(0,0,0,.05);
  }
  .flow .arr { color: #C08A4A; font-size: 20px; font-weight: 800; }

  .grid {
    display: grid; grid-template-columns: repeat(3, 1fr);
    gap: 14px; align-items: start;
  }
  .card {
    background: var(--tint); border-radius: 14px; overflow: hidden;
    border: 1px solid rgba(0,0,0,.06);
    border-top: 6px solid var(--accent);
    box-shadow: 0 4px 12px rgba(0,0,0,.06);
  }
  .card header {
    display: flex; justify-content: space-between; align-items: center;
    padding: 12px 14px 4px;
  }
  .ttl { font-size: 15px; font-weight: 800; color: #2B211B; }
  .ic { font-size: 17px; }
  .badge {
    background: var(--accent); color: #fff; font-size: 11px; font-weight: 800;
    padding: 3px 9px; border-radius: 999px; white-space: nowrap;
  }
  .sub {
    padding: 0 14px 8px; font-size: 12px; color: #7A6A5C;
    font-style: italic; font-weight: 600;
  }
  ul { list-style: none; padding: 0 14px 14px; }
  li {
    display: flex; gap: 8px; align-items: flex-start;
    background: #fff; border-radius: 8px; padding: 8px 10px;
    margin-top: 6px; font-size: 12.5px; line-height: 1.35;
    border-left: 3px solid #ccc;
  }
  li.done { border-left-color: #2E9E6B; }
  li.wait { border-left-color: #E08A00; }
  li.idea { border-left-color: #9B6BB0; background: #FBF6FF; }
  .mk { font-size: 13px; }
  .tx { color: #3A2E25; }

  .legend {
    margin-top: 16px; display: flex; justify-content: center; gap: 22px;
    font-size: 12.5px; color: #5A4A3E; font-weight: 600;
  }
  .legend span b { font-weight: 800; }
</style></head>
<body>
  <div class="top">
    <div class="center-pill">\u{1F3E1} ${project.center}</div>
    <div class="tag">${project.tagline}</div>
  </div>
  <div class="flow">${flowPills}</div>
  <div class="grid">${cards}</div>
  <div class="legend">
    <span><b>✅ Done</b> — built &amp; working</span>
    <span><b>⏳ Waiting</b> — blocked / not switched on yet</span>
    <span><b>\u{1F4A1} New idea</b> — being researched</span>
  </div>
</body></html>`;
}

// ---- write the files ----------------------------------------
const mdPath = join(__dirname, "IDEA-MAP.md");
const htmlPath = join(__dirname, "IDEA-MAP.html");
writeFileSync(mdPath, buildMarkdown(), "utf8");
writeFileSync(htmlPath, buildHtml(), "utf8");

// ---- console summary ----------------------------------------
let totalDone = 0,
  total = 0;
for (const b of project.branches) {
  const c = counts(b.leaves);
  totalDone += c.done;
  total += c.total;
}
console.log(`Map written:`);
console.log(`  ${mdPath}`);
console.log(`  ${htmlPath}`);
console.log(`Overall: ${totalDone} of ${total} pieces built.`);
