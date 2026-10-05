import { Flip, tween, ease } from "./turn.js";

/* ───────────────────────── 상태 ─────────────────────────
   책은 '마디(section)'를 차례로 이은 것이다: 첫 화면(오늘의 새) → 차례 → 목 → 과 → 종 … → 찾아보기 → 판권.
   마디마다 화면 크기에 맞춰 쪽을 엮되, 보러 갈 때 그 마디만 엮는다(600여 종을 한꺼번에 재지 않는다).
   종은 쪽 수가 화면마다 달라 도판 번호(Pl.)로 찾아간다. 위치는 쪽 key 로 기억한다. */
const S = {
  vid: "aves", book: null, nodes: new Map(), species: [], sections: [], secOf: new Map(),
  detail: new Map(), detailP: new Map(), layouts: new Map(),
  mode: null, W: 0, H: 0, pos: { s: 0, v: 0 }, busy: false, pending: null,
  cap: { list: 7, index: 40 }, today: null,
  reduced: matchMedia("(prefers-reduced-motion: reduce)"),
  edit: new URLSearchParams(location.search).has("edit"),
};
const $ = id => document.getElementById(id);
const bookEl = $("book"), slotL = $("slot-left"), slotR = $("slot-right");
const ESC = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ESC[c]);
const isTodo = v => v == null || v === "" || (typeof v === "string" && v.includes("TODO"));
const todo = `<span class="todo" title="출처로 확인하지 못해 비워 둔 값">조사 중</span>`;
const val = v => isTodo(v) ? todo : esc(v);
const href = key => `#/${S.vid}/${key}`;
const imgUrl = (id, kind) => `img/${S.vid}/${id}${kind === "plate" ? ".id" : ""}.webp`;
const RANK = { order: ["목", "Ordo"], family: ["과", "Familia"] };
const LABELS = { season: "관찰 시기", seen: "볼 수 있음", breed: "번식기", sexes: "암수 구별", young: "어린새", similar: "비슷한 종", points: "동정 포인트" };
const L = k => S.book?.labels?.[k] || LABELS[k];

/* ───────────────────────── 자료 ───────────────────────── */
async function getJSON(url) {
  const r = await fetch(url, { cache: "no-cache" });
  if (!r.ok) throw new Error(`${url} (${r.status})`);
  return r.json();
}

function indexBook(book) {
  S.book = book; S.nodes.clear(); S.species = [];
  const sec = [{ key: "", kind: "home" }, { key: "contents", kind: "contents" }];
  for (const o of book.tree) {
    S.nodes.set(o.id, o);
    sec.push({ key: o.id, kind: "group", node: o });
    for (const f of o.children) {
      f.parent = o; S.nodes.set(f.id, f);
      sec.push({ key: f.id, kind: "group", node: f });
      for (const s of f.children) {
        s.rank = "species"; s.parent = f; s.plateNo = S.species.length + 1;
        S.nodes.set(s.id, s); S.species.push(s);
        sec.push({ key: s.id, kind: "species", node: s });
      }
    }
  }
  sec.push({ key: "index", kind: "index" }, { key: "colophon", kind: "colophon" });
  sec.forEach((x, i) => { x.i = i; });
  S.sections = sec;
  S.secOf = new Map(sec.map(x => [x.key, x]));
  const range = n => {
    if (n.rank === "species") return [n.plateNo, n.plateNo];
    const r = n.children.map(range);
    return [Math.min(...r.map(x => x[0])), Math.max(...r.map(x => x[1]))];
  };
  for (const n of S.nodes.values()) n.plates = range(n);
}
const countSp = n => n.rank === "species" ? 1 : n.children.reduce((a, c) => a + countSp(c), 0);
const plateLabel = n => n?.plates ? (n.plates[0] === n.plates[1] ? `${n.plates[0]}` : `${n.plates[0]}–${n.plates[1]}`) : "";

function loadDetail(id) {
  if (!S.detailP.has(id)) {
    const p = getJSON(`data/${S.vid}/species/${id}.json`).then(d => { S.detail.set(id, d); return d; });
    p.catch(() => S.detailP.delete(id));
    S.detailP.set(id, p);
  }
  return S.detailP.get(id);
}

/* ───────────────────────── 판형 ─────────────────────────
   화면 전체가 책이다. 넓으면 양쪽 펼침, 좁거나 세로로 길면 한 쪽. */
function measure() {
  const vw = document.documentElement.clientWidth;
  const r = bookEl.getBoundingClientRect();
  const H = Math.max(300, Math.floor(r.height));
  const spread = vw >= 900 && vw / Math.max(1, H) >= 1.15;
  const W = Math.floor(spread ? vw / 2 : vw);
  return { mode: spread ? "spread" : "single", W, H };
}

function applySize() {
  const fs = Math.max(16, Math.min(19, S.W / 31, S.H / 40));
  document.documentElement.style.setProperty("--fs", `${fs.toFixed(2)}px`);
  document.documentElement.style.setProperty("--W", `${S.W}px`);
  document.documentElement.style.setProperty("--H", `${S.H}px`);
  document.body.dataset.mode = S.mode;
}

/* 보이지 않는 시험 쪽: 목록 줄 수와 해설이 들어가는지를 실제로 그려 보고 잰다 */
let probe = null;
function probeSlot() {
  if (!probe) { probe = document.createElement("div"); probe.className = "slot probe"; probe.setAttribute("aria-hidden", "true"); bookEl.appendChild(probe); }
  return probe;
}
function fitsPage(p, side) {
  const pr = probeSlot();
  pr.replaceChildren(makePage(p, side));
  const inn = pr.querySelector(".pg-in");
  return inn.scrollHeight <= inn.clientHeight + 1;
}
const sides = () => S.mode === "spread" ? ["left", "right"] : ["single"];

function measureCaps() {
  const pr = probeSlot();
  const fake = { id: "probe", ko: "가나다라마바사아", sci: "Abcdefg hijklmn", en: "Abcdefg", rank: "species", img: {}, focus: [0.5, 0.5], children: [], plates: [1, 9], status: "흔한 여름철새", length: "17cm" };
  const cap = (kind, n, sel) => Math.min(...sides().map(side => {
    pr.replaceChildren(makePage({ kind, key: "probe", items: Array.from({ length: n }, () => fake), part: 0, probe: true, node: { ko: "가나다목", rank: "order", children: [] } }, side));
    const list = pr.querySelector(sel);
    const st = getComputedStyle(list);
    const gap = parseFloat(st.rowGap) || 0;
    const h = list.firstElementChild.getBoundingClientRect().height;
    const rows = Math.max(3, Math.floor((list.clientHeight + gap - 3) / (h + gap)));
    const cols = Math.max(1, parseInt(st.columnCount) || 1);
    return kind === "index" ? rows * cols : rows;
  }));
  S.cap.list = Math.min(cap("list", 40, ".fill"), cap("contents", 40, ".fill"));
  S.cap.index = cap("index", 60, ".idx");
  pr.replaceChildren();
}

/* ───────────────────────── 마디 엮기 ───────────────────────── */
const chunk = (arr, n) => { const out = []; for (let i = 0; i < arr.length; i += n) out.push(arr.slice(i, i + n)); return out.length ? out : [[]]; };

/* 종: 도판 → 해설(필요한 만큼) → 동정 도해 · 동정 포인트(마주 봄) → 나머지.
   동정 도해와 동정 포인트가 늘 마주 보도록, 앞 해설이 왼쪽에서 끝나면 뒤쪽 글을 당겨 채운다. */
function blockList(d) {
  const brief = d.origin && isTodo(d.summary);
  const A = brief ? ["facts", "brief"] : ["facts", "season", "summary", "sexes"];
  const B = brief ? [] : ["young", ...(d.similar || []).map((_, i) => `sim${i}`)];
  if (!brief && isTodo(d.young)) B.shift();
  if (d.taxon_note) B.push("tnote");
  if ((d.sources || []).length) B.push("sources");
  return { A, B };
}

function flowSpecies(node) {
  const d = S.detail.get(node.id);
  const spread = S.mode === "spread";
  const { A, B } = blockList(d);
  const hasId = (d.points || []).length > 0;
  const out = [{ kind: "plate" }];
  const sideAt = i => spread ? (i % 2 === 0 ? "left" : "right") : "single";
  const fits = pg => fitsPage({ ...pg, key: "probe", node }, sideAt(out.length));
  let page = { kind: "text", head: true, blocks: [] };
  const place = b => {
    page.blocks.push(b);
    if (fits(page)) return;
    page.blocks.pop();
    if (page.blocks.length || page.head) { out.push(page); page = { kind: "text", blocks: [b] }; }
    else page.blocks.push(b); // 한 쪽보다 큰 덩어리: 그대로 둔다(쪽 안에서 스크롤)
  };
  A.forEach(place);
  if (hasId) {
    if (spread && out.length % 2 === 0) { // 해설이 왼쪽에서 끝남 → 오른쪽 한 쪽을 더 채운다
      out.push(page);
      page = { kind: "text", blocks: [] };
      while (B.length) { page.blocks.push(B[0]); if (!fits(page)) { page.blocks.pop(); break; } B.shift(); }
    }
    out.push(page);
    out.push({ kind: "idplate" });
    page = { kind: "text", blocks: [] };
    ["points", ...B].forEach(place);
  } else B.forEach(place);
  if (page.blocks.length || page.head) out.push(page);
  let t = 0;
  return out.map(p => ({
    ...p, node,
    key: p.kind === "plate" ? node.id : p.kind === "idplate" ? `${node.id}/id` : `${node.id}/t${++t}`,
  }));
}

function sectionPages(sec) {
  const lists = (kind, key, node, items) => chunk(items, S.cap.list).map((it, i) =>
    ({ kind, key: i ? `${key}/${i + 1}` : key, node, items: it, part: i }));
  switch (sec.kind) {
    case "home":
      return S.mode === "spread"
        ? [{ kind: "intro", key: "" }, { kind: "today", key: "today" }]
        : [{ kind: "today", key: "", top: true }, { kind: "intro", key: "about" }];
    case "contents":
      return lists("contents", "contents", null, [...S.book.tree, { plain: "찾아보기", key: "index" }, { plain: "출처와 판권", key: "colophon" }]);
    case "group":
      return [{ kind: "group", key: sec.key, node: sec.node }, ...lists("list", `${sec.key}/list`, sec.node, sec.node.children)];
    case "species":
      return flowSpecies(sec.node);
    case "index": {
      const sorted = [...S.species].sort((a, b) => a.ko.localeCompare(b.ko, "ko"));
      return chunk(sorted, S.cap.index).map((it, i) => ({ kind: "index", key: i ? `index/${i + 1}` : "index", items: it, part: i }));
    }
    case "colophon":
      return [{ kind: "colophon", key: "colophon" }];
  }
  return [];
}

/** 마디를 화면 판형에 맞게 엮는다. 종은 자료를 먼저 읽는다. */
async function layoutOf(i) {
  const sec = S.sections[i];
  if (!sec) return null;
  if (S.layouts.has(sec.key)) return S.layouts.get(sec.key);
  if (sec.kind === "species") await loadDetail(sec.key);
  if (sec.kind === "home") await ensureToday();
  if (S.layouts.has(sec.key)) return S.layouts.get(sec.key);
  const pages = sectionPages(sec);
  probe?.replaceChildren();
  const views = [];
  if (S.mode === "spread") for (let k = 0; k < pages.length; k += 2) views.push([pages[k], pages[k + 1] || { kind: "blank", key: `${sec.key}/blank` }]);
  else for (const p of pages) views.push([p]);
  const lay = { pages, views, viewOf: new Map() };
  views.forEach((v, n) => v.forEach(p => lay.viewOf.set(p.key, n)));
  S.layouts.set(sec.key, lay);
  return lay;
}
const layoutNow = i => S.layouts.get(S.sections[i]?.key);

function splitKey(key) {
  key = String(key || "");
  const head = key.split("/")[0];
  if (key === "today" || key === "about") return { sec: S.secOf.get(""), key };
  return { sec: S.secOf.get(head) || S.secOf.get(""), key };
}

async function posOfKey(key) {
  const { sec, key: k } = splitKey(key);
  const lay = await layoutOf(sec.i);
  let v = lay.viewOf.get(k);
  if (v == null && k.includes("/")) { // 다른 판형에서 엮인 쪽(t3 등) → 가까운 쪽
    const m = k.match(/\/(?:t|list|)(\d+)$/);
    v = m ? Math.min(lay.views.length - 1, Math.max(0, Math.floor((+m[1] - 1) / (S.mode === "spread" ? 2 : 1)))) : 0;
    if (k.endsWith("/id")) v = lay.views.findIndex(vw => vw.some(p => p.kind === "idplate"));
  }
  return { s: sec.i, v: Math.max(0, v ?? 0) };
}

async function stepPos(pos, d) {
  const lay = await layoutOf(pos.s);
  const v = pos.v + d;
  if (v >= 0 && v < lay.views.length) return { s: pos.s, v };
  const s = pos.s + Math.sign(d);
  if (s < 0 || s >= S.sections.length) return null;
  const nl = await layoutOf(s);
  return { s, v: d > 0 ? 0 : nl.views.length - 1 };
}

const keyOfPos = pos => {
  const v = layoutNow(pos.s)?.views[pos.v];
  const p = v?.find(p => p && p.kind !== "blank") || v?.[0];
  return p?.key ?? "";
};
const viewAt = pos => layoutNow(pos.s)?.views[pos.v] || [];

/* ───────────────────────── 오늘의 새 ─────────────────────────
   날짜(한국 시간)로 정한 한 종. 이번 달에 볼 수 없는 것으로 알려진 종은 고르지 않는다.
   그림이 있는 종을 더 자주 고른다. '다른 새'를 누르면 아무 종이나 새로 뽑는다. */
function todayParts() {
  const kst = new Date(Date.now() + 9 * 3600e3);
  return { y: kst.getUTCFullYear(), m: kst.getUTCMonth() + 1, d: kst.getUTCDate(), w: kst.getUTCDay() };
}
function todayPool() {
  const { m } = todayParts();
  const pool = S.species.filter(s => s.text && (!Array.isArray(s.seen) || s.seen.includes(m)));
  return pool.length ? pool : S.species;
}
function weighted(pool, rnd) {
  const w = pool.map(s => (s.img?.scene ? 6 : 1));
  let r = rnd * w.reduce((a, b) => a + b, 0);
  for (let i = 0; i < pool.length; i++) { r -= w[i]; if (r <= 0) return pool[i]; }
  return pool[pool.length - 1];
}
function seeded(n) { // 날짜 → 0..1
  let x = (n ^ 0x9e3779b9) >>> 0;
  x = Math.imul(x ^ (x >>> 16), 0x85ebca6b) >>> 0;
  x = Math.imul(x ^ (x >>> 13), 0xc2b2ae35) >>> 0;
  return ((x ^ (x >>> 16)) >>> 0) / 4294967296;
}
async function ensureToday(reroll = false) {
  if (S.today && !reroll) { await loadDetail(S.today.id); return; }
  const { y, m, d } = todayParts();
  const pool = todayPool();
  let pick = reroll ? weighted(pool, Math.random()) : weighted(pool, seeded(y * 10000 + m * 100 + d));
  if (reroll && pool.length > 1) while (pick === S.today) pick = weighted(pool, Math.random());
  S.today = pick;
  await loadDetail(pick.id);
}

/* ───────────────────────── 그림 조각 ───────────────────────── */
const SKETCH = `<svg class="sketch" viewBox="0 0 120 90" aria-hidden="true" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
<path d="M99 33.5c-3-.6-5.6-1-7.4-1.4-1.5-4.6-5.4-7.6-10.4-7.6-6.6 0-10.8 4.6-14.4 9.4C61.6 41 54 46.4 42 52.4 32.6 57 21.4 61.4 9.6 66.6c9.8.4 19.8-1 28.6-3.2 6.4 3.6 14.6 4.8 22.8 3.2C75 64 85 55.4 88.6 43.6c4.2-3.2 7.6-6.6 10.4-10.1z" stroke-width="1.3"/>
<path d="M52.6 47.6c7.2 1.4 15.8.2 22.4-4.6M47 53.2c8.8 2.2 19.6 1 27.6-4.8" stroke-width=".9" opacity=".7"/>
<circle cx="84.6" cy="33" r="1.3" fill="currentColor" stroke="none"/>
<path d="M60.4 66.6l-1.6 8.6m8.4-9.4l.4 9M28 76.6c18-1.4 44-2.6 76-1.2" stroke-width="1.1"/></svg>`;

const ORN = `<svg class="orn" viewBox="0 0 120 14" aria-hidden="true"><path d="M2 7h44M74 7h44" stroke="currentColor" stroke-width=".8"/><path d="M60 1.5c3 2.6 3 8.4 0 11-3-2.6-3-8.4 0-11zM52 7c2.6-2.4 5-2.4 6.4 0-1.4 2.4-3.8 2.4-6.4 0zm16 0c-2.6-2.4-5-2.4-6.4 0 1.4 2.4 3.8 2.4 6.4 0z" fill="currentColor"/></svg>`;

function vignette(node, cls = "vig") {
  const sp = node && (node.rank === "species" ? node : S.nodes.get(node.rep));
  if (sp?.img?.scene) {
    const [fx, fy] = sp.focus || [0.5, 0.5];
    return `<span class="${cls}"><img src="${imgUrl(sp.id, "scene")}" alt="" decoding="async" style="object-position:${fx * 100}% ${fy * 100}%"></span>`;
  }
  return `<span class="${cls} ph">${SKETCH}</span>`;
}

function plateImg(n, alt) {
  return n.img?.scene
    ? `<img src="${imgUrl(n.id, "scene")}" alt="${esc(alt)}" decoding="async">`
    : `<div class="ph-plate">${SKETCH}<span>도판 준비 중</span></div>`;
}

/* 관찰 시기 달력 */
function monthRanges(ms) {
  const set = new Set(ms);
  if (set.size === 12) return "연중";
  const out = [];
  for (let m = 1; m <= 12; m++) {
    if (!set.has(m) || set.has(((m + 10) % 12) + 1)) continue;
    let e = m; while (set.has((e % 12) + 1) && ((e % 12) + 1) !== m) e = (e % 12) + 1;
    out.push(e === m ? `${m}월` : `${m}–${e}월`);
  }
  return out.join(", ");
}
function calendar(months, compact = false) {
  const seen = Array.isArray(months?.seen) ? new Set(months.seen) : null;
  const breed = Array.isArray(months?.breed) ? new Set(months.breed) : null;
  const noBreed = breed && breed.size === 0;
  if (!seen && !(breed && breed.size)) return `<p class="cal-todo">${L("seen")} ${todo}${noBreed ? " · 국내 번식 안 함" : ""}</p>`;
  const label = [seen ? `${L("seen")}: ${monthRanges([...seen])}` : "", breed?.size ? `${L("breed")}: ${monthRanges([...breed])}` : ""].filter(Boolean).join(", ");
  const now = todayParts().m;
  const cells = Array.from({ length: 12 }, (_, i) => {
    const m = i + 1;
    return `<span class="mo${seen?.has(m) ? " on" : ""}${breed?.has(m) ? " br" : ""}${m === now ? " now" : ""}"><i></i><b>${m}</b></span>`;
  }).join("");
  const key = compact ? "" : `<p class="cal-key">${seen ? `<span class="k on"></span>${L("seen")}` : `<span class="dim">${L("seen")} ${todo}</span>`}
    ${breed?.size ? `<span class="k br"></span>${L("breed")}` : noBreed ? `<span class="dim">국내 번식 안 함</span>` : `<span class="dim">${L("breed")} ${todo}</span>`}</p>`;
  return `<div class="cal${seen ? "" : " unseen"}" role="img" aria-label="${esc(label)}">${cells}</div>${key}`;
}

function facts(d, known = false) {
  return S.book.fields.map(f => {
    let v = d[f.key];
    if (Array.isArray(v)) {
      if (!v.length) return "";
      v = v.map(x => `<span class="stamp">${esc(x)}</span>`).join(" ");
    } else {
      if ((f.optional || known) && isTodo(v)) return "";
      v = val(v);
    }
    return `<dt>${esc(f.label)}</dt><dd>${v}</dd>`;
  }).join("");
}

/* 동정 도해 위 번호·지시선 */
function callouts(points) {
  const placed = points.map((p, i) => ({ ...p, n: i + 1 })).filter(p => Array.isArray(p.at));
  if (!placed.length) return "";
  const withLabel = placed.filter(p => Array.isArray(p.label));
  const lines = withLabel.map(p => `<line x1="${p.at[0] * 100}" y1="${p.at[1] * 100}" x2="${p.label[0] * 100}" y2="${p.label[1] * 100}"/>`).join("");
  const labels = withLabel.map(p =>
    `<span class="co-label ${p.label[0] < p.at[0] ? "to-left" : "to-right"}" style="left:${p.label[0] * 100}%;top:${p.label[1] * 100}%">${esc(p.ko)}</span>`).join("");
  const dots = placed.map(p => `<span class="co-dot" style="left:${p.at[0] * 100}%;top:${p.at[1] * 100}%"><b>${p.n}</b></span>`).join("");
  return `<svg class="co-lines" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">${lines}</svg>${labels}${dots}`;
}

const firstSentence = t => isTodo(t) ? "" : (String(t).match(/^.*?[다요]\./) || [t])[0];
function entry(n, extra = "", roomy = false) {
  let desc = "";
  if (roomy) {
    desc = n.rank === "species"
      ? [isTodo(n.en) ? "" : n.en, isTodo(n.status) ? "" : n.status, isTodo(n.length) ? "" : `몸길이 ${n.length}`].filter(Boolean).join(" · ")
      : firstSentence(n.desc) || n.children.slice(0, 4).map(c => c.ko).join(", ") + (n.children.length > 4 ? " …" : "");
  }
  return `<li><a class="entry${roomy ? " roomy" : ""}" href="${href(n.id)}">${vignette(n)}<span class="en-names"><span class="l1"><span class="ko">${esc(n.ko)}</span>${extra}</span><span class="sci"><i>${esc(n.sci)}</i></span>${desc ? `<span class="desc">${esc(desc)}</span>` : ""}</span><span class="lead"></span><span class="pg"><span class="pl">Pl.</span>${plateLabel(n)}</span></a></li>`;
}

function taxonLinks(n) {
  const f = n.parent, o = f?.parent;
  return o ? `<a href="${href(o.id)}">${esc(o.ko)}</a> › <a href="${href(f.id)}">${esc(f.ko)}</a>` : "";
}

/* 해설 덩어리 */
const BLOCK = {
  facts: d => {
    const brief = d.origin && isTodo(d.summary);
    const rows = facts(d, brief);
    return rows ? `<dl class="facts">${rows}</dl>` : "";
  },
  season: d => `<section class="season"><h3>${L("season")}</h3>${calendar(d.months)}${d.months?.note && !isTodo(d.months.note) ? `<p class="note">${esc(d.months.note)}</p>` : ""}</section>`,
  summary: d => `<p class="summary">${val(d.summary)}</p>`,
  brief: () => `<p class="brief">이 종은 아직 해설을 싣지 못했다. 국가생물종목록의 이름과 분류, 보호 표시만 먼저 싣는다.</p>`,
  sexes: d => {
    const sx = d.sexes || {};
    if (sx.alike == null && isTodo(sx.text)) return `<section><h3>${L("sexes")}</h3><p>${todo}</p></section>`;
    return `<section><h3>${L("sexes")}</h3>${sx.alike !== false ? `<p>${val(sx.text)}</p>`
      : `<dl class="sexes"><dt>수컷</dt><dd>${val(sx.male)}</dd><dt>암컷</dt><dd>${val(sx.female)}</dd></dl>`}</section>`;
  },
  points: d => `<section class="pts-sec"><h2 class="pg-title small">${L("points")}</h2><ol class="pts">${(d.points || []).map((x, i) => `<li><span class="num" aria-hidden="true"><b>${i + 1}</b></span><span>${val(x.ko)}</span></li>`).join("")}</ol></section>`,
  young: d => `<section><h3>${L("young")}</h3><p>${val(d.young)}</p></section>`,
  tnote: d => `<p class="tnote">${esc(d.taxon_note)}</p>`,
  sources: d => `<footer class="src"><h4>출처</h4>${d.origin === "nibr" && !isTodo(d.summary) ? `<p>해설은 국립생물자원관 종 설명을 바탕으로 다시 썼다. 원문에 없는 값은 비워 두었다.</p>` : ""}<ol>${(d.sources || []).map(s => `<li>${s.url ? `<a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.title)}</a>` : esc(s.title)}</li>`).join("")}</ol></footer>`,
};
function block(b, d, node) {
  if (b.startsWith("sim")) {
    const i = +b.slice(3), x = d.similar[i];
    const id = S.book.similar?.[node.id]?.[i];
    const name = id ? `<a href="${href(id)}">${esc(x.ko)}</a>` : esc(x.ko);
    return `<section class="sim">${i === 0 ? `<h3>${L("similar")}</h3>` : ""}<p><b>${name}</b> ${val(x.how)}</p></section>`;
  }
  return BLOCK[b](d);
}

/* ───────────────────────── 쪽 그리기 ───────────────────────── */
const WEEK = "일월화수목금토";
const R = {
  intro() {
    const b = S.book, c = b.counts;
    return `<div class="pg-in intro">
      <p class="kicker">${esc(b.kicker)}</p>
      <h1 class="title">${esc(b.title)}</h1>
      <p class="title-en"><i>${esc(b.en)}</i></p>
      ${ORN}
      <p class="lede">${esc(b.intro)}</p>
      <dl class="tally">
        <div><dt>목</dt><dd>${c.orders}</dd></div><div><dt>과</dt><dd>${c.families}</dd></div><div><dt>종</dt><dd>${c.species}</dd></div>
        <div><dt>해설</dt><dd>${c.text}</dd></div><div><dt>도판</dt><dd>${c.scenes}</dd></div>
      </dl>
      <nav class="ways">
        <a href="${href("contents")}"><b>차례</b><span>목 → 과 → 종 순서로</span></a>
        <a href="${href("index")}"><b>찾아보기</b><span>가나다순 국명</span></a>
        <a href="${href(S.species[0]?.id || "")}"><b>처음부터</b><span>Pl. 1 ${esc(S.species[0]?.ko || "")}부터 넘기기</span></a>
      </nav>
      <p class="howto">← → 키, 화면을 옆으로 밀기, 아래 단추로 넘긴다. <kbd>/</kbd> 를 누르면 새 이름을 찾는다.</p>
    </div>`;
  },
  today(p) {
    const n = S.today, d = n && S.detail.get(n.id);
    if (!d) return `<div class="pg-in"><p class="loading">…</p></div>`;
    const { m, d: day, w } = todayParts();
    const facts = [d.status, isTodo(d.length) ? "" : `몸길이 ${d.length}`].filter(x => !isTodo(x)).map(esc).join(" · ");
    const sum = isTodo(d.summary) ? "" : String(d.summary).split(/(?<=다\.)\s+/).slice(0, 2).join(" ");
    return `<div class="pg-in today">
      <header class="today-head"><h2>오늘의 새</h2><p class="date">${m}월 ${day}일 ${WEEK[w]}요일</p></header>
      <a class="today-plate" href="${href(n.id)}">${plateImg(n, `${n.ko} 도판`)}</a>
      <div class="today-name">
        <h3><a href="${href(n.id)}">${esc(n.ko)}</a></h3>
        <p class="sci"><i>${esc(n.sci)}</i>${isTodo(n.en) ? "" : ` <span class="en">${esc(n.en)}</span>`}</p>
        <p class="taxon">${taxonLinks(n)} · Pl. ${n.plateNo}</p>
      </div>
      ${facts ? `<p class="today-facts">${facts}${(d.protect || []).map(x => ` <span class="stamp">${esc(x)}</span>`).join("")}</p>` : ""}
      ${Array.isArray(d.months?.seen) || (Array.isArray(d.months?.breed) && d.months.breed.length) ? calendar(d.months, true) : ""}
      ${sum ? `<p class="today-sum">${esc(sum)}</p>` : ""}
      <p class="today-act"><a class="btn" href="${href(n.id)}">도판 펼치기 →</a> <button type="button" class="btn ghost" data-act="reroll">다른 새 ↻</button></p>
    </div>`;
  },
  contents(p) {
    const rows = p.items.map(it => it.plain
      ? `<li><a class="entry plain" href="${href(it.key)}"><span class="vig none"></span><span class="en-names"><span class="l1"><span class="ko">${esc(it.plain)}</span></span></span><span class="lead"></span><span class="pg"></span></a></li>`
      : entry(it, `<span class="meta">${it.children.length}과 ${countSp(it)}종</span>`)).join("");
    return `<div class="pg-in list-page">
      <h2 class="pg-title">차례${p.part ? `<span class="cont">이어서</span>` : ""}</h2>
      <ul class="entries fill">${rows}</ul></div>`;
  },
  group(p) {
    const n = p.node, [rk, la] = RANK[n.rank];
    const inBook = n.rank === "order" ? `${n.children.length}과 ${countSp(n)}종` : `${countSp(n)}종`;
    const desc = isTodo(n.desc) ? "" : `<p class="grp-desc">${esc(n.desc)}</p>`;
    const up = n.rank === "family" ? `<p class="grp-up"><a href="${href(n.parent.id)}">${esc(n.parent.ko)}</a></p>` : "";
    return `<div class="pg-in group-page">
      ${up}
      <p class="rank">${rk} <span class="la">${la}</span></p>
      <h2 class="grp-ko">${esc(n.ko)}</h2>
      <p class="grp-sci"><i>${esc(n.sci)}</i></p>
      ${vignette(n, "cartouche")}
      ${desc}
      ${ORN}
      <p class="grp-count">${inBook} · Pl. ${plateLabel(n)}</p>
    </div>`;
  },
  list(p) {
    const n = p.node;
    const sub = n.rank === "order" ? "과" : "종";
    const roomy = !p.probe && p.items.length <= Math.floor(S.cap.list / 2);
    const rows = p.items.map(c => c.rank === "species"
      ? entry(c, roomy || isTodo(c.en) ? "" : `<span class="meta">${esc(c.en)}</span>`, roomy)
      : entry(c, `<span class="meta">${countSp(c)}종</span>`, roomy)).join("");
    return `<div class="pg-in list-page">
      <h2 class="pg-title">${esc(n.ko)}의 ${sub}${p.part ? `<span class="cont">이어서</span>` : ""}</h2>
      <ul class="entries fill">${rows}</ul></div>`;
  },
  plate(p) {
    const n = p.node, d = S.detail.get(n.id);
    return `<div class="pg-in plate-page">
      <figure class="plate">
        <div class="pl-frame${S.edit ? " editable" : ""}" data-edit="focus" data-id="${n.id}">${plateImg(n, `${n.ko}가 사는 곳을 배경으로 그린 수채 도판`)}</div>
        <figcaption>
          <span class="pl-no">Pl. ${n.plateNo}</span>
          <span class="ko">${esc(n.ko)}</span>
          <span class="sci"><i>${esc(n.sci)}</i></span>
          ${isTodo(n.en) ? "" : `<span class="en">${esc(n.en)}</span>`}
          ${(d?.protect || []).length ? `<span class="stamps">${d.protect.map(x => `<span class="stamp">${esc(x)}</span>`).join(" ")}</span>` : ""}
        </figcaption>
      </figure></div>`;
  },
  text(p) {
    const n = p.node, d = S.detail.get(n.id);
    if (!d) return `<div class="pg-in"><p class="loading">…</p></div>`;
    const head = p.head ? `<header class="sp-head">
        <h2>${esc(d.ko)}</h2>
        <p class="sci"><i>${esc(d.sci)}</i> <span class="auth">${esc(d.author || "")}</span></p>
        ${isTodo(d.en) ? "" : `<p class="en">${esc(d.en)}</p>`}
        <p class="taxon">${taxonLinks(n)}</p>
      </header>` : "";
    return `<div class="pg-in text-page">${head}${(p.blocks || []).map(b => block(b, d, n)).join("")}</div>`;
  },
  idplate(p) {
    const n = p.node, d = S.detail.get(n.id);
    const body = n.img?.plate
      ? `<div class="idframe${S.edit ? " editable" : ""}" data-edit="points" data-id="${n.id}"><img src="${imgUrl(n.id, "plate")}" alt="${esc(n.ko)} 동정 도해" decoding="async">${callouts(d?.points || [])}</div>`
      : `<div class="ph-plate tall">${SKETCH}<span>동정 도해 준비 중</span></div>`;
    return `<div class="pg-in idplate-page">
      <figure class="idfig">${body}
        <figcaption><span class="ko">${esc(n.ko)}</span> 동정 도해${d?.art?.views?.length ? ` · ${d.art.views.length}가지 모습` : ""}</figcaption>
      </figure></div>`;
  },
  index(p) {
    let last = "";
    const rows = p.items.map(s => {
      const ini = initial(s.ko);
      const mark = ini !== last ? `<span class="ini">${ini}</span>` : `<span class="ini"></span>`;
      last = ini;
      return `<li><a href="${href(s.id)}">${mark}<span class="ko">${esc(s.ko)}</span><span class="lead"></span><span class="pg">${s.plates ? s.plates[0] : ""}</span></a></li>`;
    }).join("");
    return `<div class="pg-in index-page">
      <h2 class="pg-title">찾아보기${p.part ? `<span class="cont">이어서</span>` : ""}</h2>
      <ul class="idx">${rows}</ul></div>`;
  },
  colophon() {
    const b = S.book;
    return `<div class="pg-in colophon">
      <h2 class="pg-title">출처와 판권</h2>
      <p>분류와 국명, 학명, 보호 표시는 <a href="${esc(b.basis.url)}" target="_blank" rel="noopener">${esc(b.basis.name)}</a>(${esc(b.basis.edition)})을 따랐다.
        영문명은 IOC World Bird List(v15.2)에서 학명으로 찾아 붙였다.</p>
      <p>${b.counts.hand}종은 여러 문헌을 견주어 따로 조사했고, 나머지 종의 해설은 국립생물자원관 종 설명을 근거로 다시 썼다.
        근거에 없는 값은 지어내지 않고 <span class="todo">조사 중</span>으로 비워 두었다. 종마다 참고한 곳은 그 종의 해설 끝에 적었다.</p>
      <p>도판과 동정 도해는 생성형 이미지 모델로 그린 뒤 사람이 살펴 고른 그림이다. 동정 도해의 글자는 그림에 넣지 않고 해설 자료에서 얹었다.</p>
      ${ORN}
      <p class="colo">${esc(b.title)} · ${esc(b.kicker)}<br>${esc(b.edition)}년 엮음 · 자료 갱신 ${esc(b.built)}</p>
    </div>`;
  },
  blank() { return `<div class="pg-in blank-page">${ORN}</div>`; },
};

const CHO = "ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ";
const NORM = { "ㄲ": "ㄱ", "ㄸ": "ㄷ", "ㅃ": "ㅂ", "ㅆ": "ㅅ", "ㅉ": "ㅈ" };
function initial(s) {
  const c = s.charCodeAt(0) - 0xac00;
  if (c < 0 || c > 11171) return s[0];
  const j = CHO[Math.floor(c / 588)];
  return NORM[j] || j;
}
const choseong = s => [...s].map(ch => { const c = ch.charCodeAt(0) - 0xac00; return c >= 0 && c <= 11171 ? CHO[Math.floor(c / 588)] : ch; }).join("");

function imgFallback(img) {
  const ph = document.createElement(img.closest(".vig, .cartouche") ? "span" : "div");
  if (img.closest(".vig, .cartouche")) { img.parentElement.classList.add("ph"); img.replaceWith(Object.assign(ph, { innerHTML: SKETCH })); return; }
  ph.className = `ph-plate${img.closest(".idframe") ? " tall" : ""}`;
  ph.innerHTML = `${SKETCH}<span>그림 준비 중</span>`;
  (img.closest(".idframe") || img).replaceWith(ph);
}
function makePage(p, side) {
  const el = document.createElement("article");
  el.className = `page ${side} k-${p.kind}`;
  el.dataset.key = p.key;
  el.innerHTML = R[p.kind](p, side);
  for (const img of el.querySelectorAll("img")) img.addEventListener("error", () => imgFallback(img), { once: true });
  if (p.kind === "plate" || p.kind === "idplate") el.setAttribute("aria-label", `${p.node.ko} ${p.kind === "plate" ? "도판" : "동정 도해"}`);
  return el;
}
const blankPage = side => makePage({ kind: "blank", key: "blank" }, side);

/* ───────────────────────── 펼치기 ───────────────────────── */
function put(slot, el) { slot.replaceChildren(...(el ? [el] : [])); }
function take(slot) { const el = slot.firstElementChild; if (el) el.remove(); return el; }

function render(pos) {
  S.pos = pos;
  const v = viewAt(pos);
  if (S.mode === "spread") {
    put(slotL, v[0] ? makePage(v[0], "left") : null);
    put(slotR, v[1] ? makePage(v[1], "right") : null);
  } else {
    put(slotL, null);
    put(slotR, makePage(v[0], "single"));
  }
  chrome();
}

function nameOf(p) {
  if (!p) return "";
  if (p.node?.rank === "species") return p.node.ko;
  if (p.node) return p.node.ko;
  return { contents: "차례", index: "찾아보기", colophon: "출처와 판권", today: "오늘의 새", intro: S.book.title }[p.kind] || "";
}

function chrome() {
  const v = viewAt(S.pos), sec = S.sections[S.pos.s];
  const lay = layoutNow(S.pos.s);
  const main = v.find(p => p && p.kind !== "blank") || v[0];
  const node = sec.node;
  // 머리말: 왼쪽은 갈래(차례 › 목 › 과), 오른쪽은 지금 보는 이름
  const chain = [];
  for (let n = node?.rank === "species" ? node.parent : node; n; n = n.parent) chain.unshift(n);
  if (node && node.rank !== "species") chain.pop();
  const crumbs = sec.kind === "home" ? "" : [`<a href="${href("contents")}">차례</a>`, ...chain.map(n => `<a href="${href(n.id)}">${esc(n.ko)}</a>`)].join(`<span class="sep">›</span>`);
  $("crumbs").innerHTML = crumbs;
  const nm = ["home", "contents", "index"].includes(sec.kind) ? "" : node?.rank === "species" ? `${esc(node.ko)} <i>${esc(node.sci)}</i>` : esc(nameOf(main));
  $("here").innerHTML = nm;
  // 꼬리말
  const part = lay.views.length > 1 ? ` <span class="part">${S.pos.v + 1}/${lay.views.length}</span>` : "";
  $("folio").innerHTML = node?.rank === "species" ? `Pl. ${node.plateNo} <span class="of">/ ${S.species.length}</span>${part}` : `${esc(nameOf(main) || S.book.title)}${part}`;
  $("prev").disabled = S.pos.s === 0 && S.pos.v === 0;
  $("next").disabled = S.pos.s === S.sections.length - 1 && S.pos.v === lay.views.length - 1;
  $("progress").style.transform = `scaleX(${(S.pos.s / Math.max(1, S.sections.length - 1)).toFixed(4)})`;
  const name = nameOf(main);
  document.title = sec.kind !== "home" && name ? `${name} — ${S.book.title}` : `${S.book.title} — ${S.book.kicker}`;
  $("live").textContent = sec.kind === "home" ? `${S.book.title}, 오늘의 새 ${S.today?.ko || ""}` : name;
  if (S.edit) editPanel();
}

function setHash(push) {
  const url = `#/${S.vid}/${keyOfPos(S.pos)}`;
  if (location.hash === url) return;
  history[push ? "pushState" : "replaceState"](null, "", url);
}
function routeKey() {
  const m = location.hash.match(/^#\/?([^/]*)\/?(.*)$/);
  return m && m[1] === S.vid ? decodeURIComponent(m[2]) : "";
}

async function prefetch(pos) {
  for (const d of [1, -1]) {
    const s = pos.s + d;
    const sec = S.sections[s];
    if (sec?.kind === "species") loadDetail(sec.key).catch(() => {});
  }
  for (const d of [1, -1]) {
    try {
      const q = await stepPos(pos, d);
      for (const p of q ? viewAt(q) : []) {
        if (p?.kind === "plate" && p.node.img?.scene) new Image().src = imgUrl(p.node.id, "scene");
        if (p?.kind === "idplate" && p.node.img?.plate) new Image().src = imgUrl(p.node.id, "plate");
      }
    } catch {}
  }
}

function imagesReady(els, ms = 400) {
  const imgs = els.filter(Boolean).flatMap(el => [...el.querySelectorAll("img")]);
  const all = Promise.all(imgs.map(i => i.decode ? i.decode().catch(() => {}) : Promise.resolve()));
  return Promise.race([all, new Promise(r => setTimeout(r, ms))]);
}

/* ───────────────────────── 넘기기 ───────────────────────── */
const DUR = 620;
const cmp = (a, b) => a.s - b.s || a.v - b.v;

/** from → to 로 넘길 장을 준비한다(아직 움직이지 않음) */
function setupTurn(to) {
  const fwd = cmp(to, S.pos) > 0, spread = S.mode === "spread";
  const tv = viewAt(to);
  let flip, commit, restore;
  if (spread) {
    if (fwd) {
      const front = take(slotR) || blankPage("right");
      const back = tv[0] ? makePage(tv[0], "left") : blankPage("left");
      put(slotR, tv[1] ? makePage(tv[1], "right") : null);
      flip = new Flip(bookEl, { left: S.W, width: S.W, hinge: "left", front, back });
      commit = () => put(slotL, back);
      restore = () => put(slotR, front);
    } else {
      const front = take(slotL) || blankPage("left");
      const back = tv[1] ? makePage(tv[1], "right") : blankPage("right");
      put(slotL, tv[0] ? makePage(tv[0], "left") : null);
      flip = new Flip(bookEl, { left: 0, width: S.W, hinge: "right", front, back });
      commit = () => put(slotR, back);
      restore = () => put(slotL, front);
    }
  } else if (fwd) {
    const front = take(slotR);
    put(slotR, makePage(tv[0], "single"));
    flip = new Flip(bookEl, { left: 0, width: S.W, hinge: "left", sweep: 100, front, back: blankPage("single") });
    commit = () => {};
    restore = () => put(slotR, front);
  } else {
    const front = makePage(tv[0], "single");
    flip = new Flip(bookEl, { left: 0, width: S.W, hinge: "left", sweep: 100, front, back: blankPage("single") });
    commit = () => put(slotR, front);
    restore = () => {};
  }
  // 한 쪽 화면에서 뒤로 갈 때는 넘어가 있던 장이 돌아오는 것이므로 t 를 거꾸로 쓴다
  const rev = !spread && !fwd;
  const set = t => flip.set(rev ? 1 - t : t);
  set(0);
  return { to, fwd, flip, set, commit, restore };
}

function finishTurn(t) {
  t.commit();
  t.flip.destroy();
  S.pos = t.to;
  chrome();
  prefetch(t.to);
  keepFocus();
}

/** 누른 링크가 쪽과 함께 사라졌으면 새 쪽으로 초점을 옮긴다 */
function keepFocus() {
  const a = document.activeElement;
  if (a && a !== document.body && document.contains(a)) return;
  const pg = (S.mode === "spread" ? slotL.querySelector(".pg-in") || slotR.querySelector(".pg-in") : slotR.querySelector(".pg-in"));
  if (pg) { pg.tabIndex = -1; pg.focus({ preventScroll: true }); }
}

/** spec: { key } 또는 { delta } */
async function turnTo(spec, { push = false, fast = false } = {}) {
  if (S.busy) { S.pending = { spec, push }; return; }
  S.busy = true;
  try {
    const to = spec.key != null ? await posOfKey(spec.key) : await stepPos(S.pos, spec.delta);
    if (!to || !cmp(to, S.pos)) { setHash(false); return; }
    await layoutOf(S.pos.s);
    if (S.reduced.matches) {
      render(to);
      bookEl.animate?.([{ opacity: 0.55 }, { opacity: 1 }], { duration: 160 });
      prefetch(to);
      keepFocus();
    } else {
      const t = setupTurn(to);
      await imagesReady([t.flip.root, slotL, slotR]);
      await tween(fast ? DUR * 0.6 : DUR, ease.inOut, t.set);
      finishTurn(t);
    }
    setHash(push);
  } catch (err) {
    console.error(err);
  } finally {
    idle();
  }
}

function idle() {
  S.busy = false;
  if (S.pending) { const { spec, push } = S.pending; S.pending = null; turnTo(spec, { push, fast: true }); }
}

const go = d => turnTo({ delta: d });

/* ───────────── 손으로 밀어 넘기기 ───────────── */
const drag = { st: null };
function onPointerDown(e) {
  if (e.button !== 0 || S.busy || (S.edit && e.target.closest(".editable"))) return;
  if (e.target.closest("input,button,textarea,select")) return;
  drag.st = { id: e.pointerId, x0: e.clientX, y0: e.clientY, vx: 0, lastX: e.clientX, lastT: performance.now(), type: e.pointerType };
}
async function onPointerMove(e) {
  const d = drag.st;
  if (!d || e.pointerId !== d.id) return;
  const dx = e.clientX - d.x0, dy = e.clientY - d.y0;
  const now = performance.now();
  d.vx = (e.clientX - d.lastX) / Math.max(1, now - d.lastT); d.lastX = e.clientX; d.lastT = now;
  if (!d.session) {
    if (d.starting || Math.abs(dx) < 10 || Math.abs(dx) < Math.abs(dy) * 1.2) return;
    if (d.type === "mouse" && !e.buttons) { drag.st = null; return; }
    const dir = dx < 0 ? 1 : -1;
    d.starting = true;
    S.busy = true;
    const to = await stepPos(S.pos, dir).catch(() => null);
    if (drag.st !== d) { S.busy = false; idle(); return; }
    if (!to) { drag.st = null; S.busy = false; idle(); return; }
    d.session = { t: setupTurn(to), dir, span: S.W * (S.mode === "spread" ? 1.15 : 0.9) };
    try { bookEl.setPointerCapture(e.pointerId); } catch {}
    bookEl.classList.add("dragging");
  }
  const s = d.session;
  s.p = Math.max(0, Math.min(1, (-s.dir * (e.clientX - d.x0)) / s.span));
  s.t.set(s.p);
  e.preventDefault();
}
async function onPointerUp(e) {
  const d = drag.st;
  if (!d || e.pointerId !== d.id) return;
  drag.st = null;
  const s = d.session;
  if (!s) { if (d.starting) { /* 준비 중 손을 뗌: 아래에서 정리 */ } return; }
  bookEl.classList.remove("dragging");
  bookEl.dataset.dragged = "1";
  setTimeout(() => delete bookEl.dataset.dragged, 0);
  const p = s.p || 0;
  const complete = p > 0.38 || -s.dir * d.vx > 0.45;
  const end = complete ? 1 : 0;
  const ms = S.reduced.matches ? 0 : Math.max(120, Math.abs(end - p) * DUR);
  await tween(ms, ease.out, e2 => s.t.set(p + (end - p) * e2));
  if (complete) { finishTurn(s.t); setHash(false); }
  else { s.t.restore(); s.t.flip.destroy(); }
  idle();
}

/* ───────────────────────── 찾기 ───────────────────────── */
function searchHits(q) {
  q = q.trim().toLowerCase();
  if (!q) return [];
  const onlyCho = /^[ㄱ-ㅎ]+$/.test(q);
  const score = s => {
    const ko = s.ko, sci = s.sci.toLowerCase(), en = String(s.en || "").toLowerCase();
    if (onlyCho) { const c = choseong(ko); return c.startsWith(q) ? 0 : c.includes(q) ? 2 : -1; }
    if (ko === q) return -1 + 0.5;
    if (ko.startsWith(q)) return 0;
    if (ko.includes(q)) return 1;
    if (sci.startsWith(q) || en.startsWith(q)) return 2;
    if (sci.includes(q) || en.includes(q)) return 3;
    return -1;
  };
  return S.species.map(s => [score(s), s]).filter(x => x[0] >= -0.5).sort((a, b) => a[0] - b[0] || a[1].ko.length - b[1].ko.length || a[1].ko.localeCompare(b[1].ko, "ko")).slice(0, 8).map(x => x[1]);
}
function setupSearch() {
  const form = $("find"), q = $("q"), hits = $("hits");
  let sel = 0, list = [];
  const draw = () => {
    list = searchHits(q.value);
    sel = Math.min(sel, Math.max(0, list.length - 1));
    hits.innerHTML = list.map((s, i) => `<li role="option" aria-selected="${i === sel}"><a href="${href(s.id)}" data-i="${i}"><span class="ko">${esc(s.ko)}</span> <i>${esc(s.sci)}</i><span class="pl">Pl. ${s.plateNo}</span></a></li>`).join("")
      || (q.value.trim() ? `<li class="none">찾는 새가 없다</li>` : "");
    form.classList.toggle("has-hits", !!q.value.trim());
  };
  const close = () => { q.value = ""; draw(); document.body.classList.remove("finding"); q.blur(); };
  q.addEventListener("input", () => { sel = 0; draw(); });
  q.addEventListener("keydown", e => {
    if (e.key === "ArrowDown") { sel = Math.min(list.length - 1, sel + 1); draw(); e.preventDefault(); }
    else if (e.key === "ArrowUp") { sel = Math.max(0, sel - 1); draw(); e.preventDefault(); }
    else if (e.key === "Escape") close();
  });
  form.addEventListener("submit", e => {
    e.preventDefault();
    const s = list[sel];
    if (s) { location.hash = href(s.id); close(); }
  });
  hits.addEventListener("click", e => { if (e.target.closest("a")) setTimeout(close, 0); });
  $("find-btn").addEventListener("click", () => {
    const on = document.body.classList.toggle("finding");
    if (on) q.focus(); else close();
  });
  document.addEventListener("pointerdown", e => { if (!e.target.closest("#find,#find-btn")) { if (q.value) { q.value = ""; draw(); } document.body.classList.remove("finding"); } });
}

/* ───────────────────────── 검수 모드 ─────────────────────────
   ?edit 로 열면 동정 도해를 눌러 번호 위치(at)·글자 위치(label)를, 도판을 눌러 둥근 그림의 초점(focus)을 정한다.
   tools/serve.py 로 띄웠으면 '저장'이 종 파일을 바로 고쳐 쓴다. */
const ED = { point: 0, target: "at" };
function editPanel() {
  let pn = $("edit-panel");
  if (!pn) {
    pn = document.createElement("aside");
    pn.id = "edit-panel";
    document.body.appendChild(pn);
    pn.addEventListener("click", e => {
      const b = e.target.closest("button");
      if (!b) return;
      if (b.dataset.pt) { ED.point = +b.dataset.pt; ED.target = b.dataset.t; }
      if (b.dataset.act === "save") saveEdits(b.dataset.id);
      editPanel();
    });
  }
  const sec = S.sections[S.pos.s];
  const d = sec.kind === "species" && S.detail.get(sec.key);
  if (!d) { pn.innerHTML = `<p><b>검수 모드</b> 종 쪽으로 가면 위치를 정할 수 있다.</p>`; return; }
  const rows = (d.points || []).map((p, i) => `<li class="${ED.point === i ? "on" : ""}"><span>${i + 1}. ${esc(p.ko)}</span>
    <button data-pt="${i}" data-t="at" class="${ED.point === i && ED.target === "at" ? "sel" : ""}">번호 ${p.at ? "✓" : ""}</button>
    <button data-pt="${i}" data-t="label" class="${ED.point === i && ED.target === "label" ? "sel" : ""}">글자 ${p.label ? "✓" : ""}</button></li>`).join("");
  pn.innerHTML = `<p><b>검수 모드</b> ${esc(d.ko)}</p>
    <p class="hint">동정 도해: 항목을 고르고 그림을 누른다. 도판: 그림을 누르면 둥근 그림의 초점.</p>
    <ol>${rows}</ol>
    <p>초점 ${d.art?.focus ? d.art.focus.map(x => x.toFixed(2)).join(", ") : "가운데"}</p>
    <button data-act="save" data-id="${d.id}">저장</button> <span id="edit-msg"></span>`;
}
function onEditClick(e) {
  const fr = e.target.closest(".editable");
  if (!fr) return;
  e.preventDefault();
  const img = fr.querySelector("img");
  if (!img) return;
  const r = img.getBoundingClientRect();
  const x = +((e.clientX - r.left) / r.width).toFixed(3), y = +((e.clientY - r.top) / r.height).toFixed(3);
  const d = S.detail.get(fr.dataset.id);
  if (fr.dataset.edit === "focus") {
    d.art.focus = [x, y];
    S.nodes.get(d.id).focus = [x, y];
  } else {
    const p = d.points[ED.point];
    p[ED.target] = [x, y];
    if (ED.target === "at" && !p.label) ED.target = "label";
    else { ED.point = Math.min(d.points.length - 1, ED.point + 1); ED.target = "at"; }
  }
  render(S.pos);
}
async function saveEdits(id) {
  const d = S.detail.get(id);
  const body = JSON.stringify(d, null, 2) + "\n";
  const msg = t => { const m = $("edit-msg"); if (m) m.textContent = t; };
  try {
    const r = await fetch(`/__save/data/${S.vid}/species/${id}.json`, { method: "PUT", body, headers: { "Content-Type": "application/json" } });
    if (!r.ok) throw new Error(r.status);
    msg("저장했다. uv run tools/build.py 로 다시 엮을 것");
  } catch {
    await navigator.clipboard?.writeText(body).catch(() => {});
    msg("저장 서버가 아니어서 JSON을 클립보드에 복사했다");
  }
}

/* ───────────────────────── 시작 ───────────────────────── */
/* 글꼴이 늦게 들어오면(한글 글꼴은 글자 묶음별로 나눠 받는다) 같은 자리를 붙든 채 쪽을 다시 엮는다 */
async function relayout() {
  if (S.busy) return;
  S.busy = true;
  try {
    const keep = keyOfPos(S.pos);
    const sig = pos => viewAt(pos).map(p => p && `${p.key}:${(p.blocks || []).join(",")}:${(p.items || []).length}`).join("|");
    const before = sig(S.pos);
    measureCaps();
    S.layouts.clear();
    S.pos = await posOfKey(keep);
    // 쪽 나눔이 그대로면 다시 그리지 않는다(그림이 깜빡이지 않게)
    if (sig(S.pos) !== before) render(S.pos); else chrome();
  } finally { idle(); }
}

async function layout() {
  const m = measure();
  if (m.mode === S.mode && m.W === S.W && m.H === S.H && S.layouts.size) return false;
  const keep = S.layouts.size ? keyOfPos(S.pos) : null;
  Object.assign(S, m);
  applySize();
  measureCaps();
  S.layouts.clear();
  S.pos = await posOfKey(keep ?? routeKey());
  return true;
}

async function start() {
  try {
    const lib = await getJSON("data/library.json");
    const want = (location.hash.match(/^#\/?([^/]+)/) || [])[1];
    const vol = lib.volumes.find(v => v.id === want) || lib.volumes[0];
    S.vid = vol.id;
    indexBook(await getJSON(vol.book));
    $("toc").href = href("contents");
    $("idx").href = href("index");
    $("home").href = href("");
    await Promise.race([document.fonts?.ready, new Promise(r => setTimeout(r, 2500))]);
    document.body.classList.add("ready");
    await layout();
    render(S.pos);
    prefetch(S.pos);
    $("boot").remove();
  } catch (err) {
    console.error(err);
    $("boot").innerHTML = `도감 자료를 읽지 못했습니다.<br><small>폴더에서 <code>uv run tools/serve.py</code>(또는 <code>python -m http.server</code>)를 실행한 뒤 http://localhost:8000 으로 여세요. 파일을 바로 열면 브라우저가 자료 읽기를 막습니다.</small>`;
    return;
  }

  // 확인용: ?freeze=0.4 → 다음 쪽으로 넘기는 중간 모습에서 멈춘다(음수는 뒤로)
  const fz = parseFloat(new URLSearchParams(location.search).get("freeze"));
  if (!Number.isNaN(fz)) {
    const to = await stepPos(S.pos, fz < 0 ? -1 : 1);
    if (to) { S.busy = true; setupTurn(to).set(Math.abs(fz)); }
  }

  $("prev").addEventListener("click", () => go(-1));
  $("next").addEventListener("click", () => go(1));
  addEventListener("hashchange", () => turnTo({ key: routeKey() }));
  document.addEventListener("keydown", e => {
    if (e.altKey || e.ctrlKey || e.metaKey || e.target.closest("input,textarea")) return;
    if (e.key === "ArrowRight" || e.key === "PageDown") { e.preventDefault(); go(1); }
    else if (e.key === "ArrowLeft" || e.key === "PageUp") { e.preventDefault(); go(-1); }
    else if (e.key === "Home") turnTo({ key: "" }, { push: true });
    else if (e.key === "End") turnTo({ key: "colophon" }, { push: true });
    else if (e.key === "/") { e.preventDefault(); document.body.classList.add("finding"); $("q").focus(); }
  });
  bookEl.addEventListener("pointerdown", onPointerDown);
  addEventListener("pointermove", onPointerMove, { passive: false });
  addEventListener("pointerup", onPointerUp);
  addEventListener("pointercancel", onPointerUp);
  bookEl.addEventListener("click", async e => {
    if (bookEl.dataset.dragged) { e.preventDefault(); e.stopPropagation(); return; }
    const rr = e.target.closest("[data-act=reroll]");
    if (rr && !S.busy) {
      S.busy = true;
      try {
        await ensureToday(true);
        S.layouts.delete("");
        await layoutOf(0);
        if (S.pos.s === 0) {
          render(S.pos);
          const slot = slotR; // 오늘의 새는 펼침에서는 오른쪽, 한 쪽 화면에서는 그 쪽
          slot.querySelector(".today")?.animate?.([{ opacity: 0 }, { opacity: 1 }], { duration: S.reduced.matches ? 0 : 260 });
          slot.querySelector("[data-act=reroll]")?.focus({ preventScroll: true });
        }
      } finally { idle(); }
      return;
    }
    if (S.edit) onEditClick(e);
  }, true);
  setupSearch();
  let ft;
  const later = () => { clearTimeout(ft); ft = setTimeout(() => (S.busy || drag.st ? later() : relayout()), 250); };
  document.fonts?.addEventListener?.("loadingdone", () => { if (!S.noAutoRelayout) later(); });
  let rt;
  addEventListener("resize", () => {
    clearTimeout(rt);
    rt = setTimeout(async () => { if (!S.busy && await layout()) render(S.pos); }, 160);
  });
}

if (new URLSearchParams(location.search).has("test")) window.__book = { S, render, turnTo, layoutOf, stepPos, posOfKey, keyOfPos, viewAt, loadDetail, relayout };
start();
