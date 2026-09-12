const $ = (sel) => document.querySelector(sel);
const form = $("#ask-form"), input = $("#q"), btn = $("#ask-btn"),
      thread = $("#thread"), bars = $("#bars"), hint = $("#hint");
let episodes = [];

/* ---------- the archive bars: one per episode, height by length ---------- */
async function drawArchive() {
  try {
    episodes = await (await fetch("/api/episodes")).json();
  } catch { return; }                       // the bars are decoration; never block asking
  const longest = Math.max(...episodes.map(e => e.minutes), 1);
  bars.replaceChildren(...episodes.map(ep => {
    const b = document.createElement("span");
    b.style.height = `${Math.max(12, (ep.minutes / longest) * 100)}%`;
    b.dataset.videoId = ep.video_id;
    b.title = `${ep.title} · ${ep.minutes} min`;
    return b;
  }));
  $("#ep-count").textContent = episodes.length;
  $("#hour-count").textContent = Math.round(episodes.reduce((s, e) => s + e.minutes, 0) / 60);
}

function litArchive(videoIds) {
  const cited = new Set(videoIds);
  bars.querySelectorAll("span").forEach(b =>
    b.classList.toggle("lit", cited.has(b.dataset.videoId)));
}

/* ---------- rendering an answer ---------- */
const escape = (s) => s.replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

// The model writes markdown-ish text; render the little it uses, and nothing else.
function renderAnswer(markdown, sources) {
  const inline = (line) => escape(line)
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\[(\d+)\]/g, (whole, n) => {           // [2] -> a chip linking to that timecode
      const s = sources[Number(n) - 1];
      return s ? `<a class="cite" href="${s.url}" target="_blank" rel="noopener"
                    title="${escape(s.title)} at ${s.timecode}">${s.timecode}</a>` : whole;
    });

  const html = [];
  let list = null;        // "ol" | "ul" | null - the list we're currently inside
  let nested = false;     // true when a <ul> is open inside the current <li>

  const closeNested = () => { if (nested) { html.push("</ul>"); nested = false; } };
  const closeList = () => {
    if (!list) return;
    closeNested();
    if (list === "ol") html.push("</li>");          // the last item is still open
    html.push(`</${list}>`);
    list = null;
  };

  for (const raw of markdown.split("\n")) {
    const line = raw.trim();
    if (!line) continue;                            // blank lines never break a list

    const ordered = line.match(/^\d+[.)]\s+(.*)$/);
    const bullet = line.match(/^[-*]\s+(.*)$/);

    if (ordered) {
      if (list === "ol") { closeNested(); html.push("</li>"); }
      else { closeList(); html.push("<ol>"); list = "ol"; }
      html.push(`<li>${inline(ordered[1])}`);       // left open: a nested list may follow
    } else if (bullet) {
      if (list === "ol") {                          // bullets under a numbered point nest inside it
        if (!nested) { html.push("<ul>"); nested = true; }
        html.push(`<li>${inline(bullet[1])}</li>`);
      } else {
        if (list !== "ul") { closeList(); html.push("<ul>"); list = "ul"; }
        html.push(`<li>${inline(bullet[1])}</li>`);
      }
    } else if (/^#+\s/.test(line)) {
      closeList();
      html.push(`<h3>${inline(line.replace(/^#+\s*/, ""))}</h3>`);
    } else {
      closeList();
      html.push(`<p>${inline(line)}</p>`);
    }
  }
  closeList();
  return html.join("");
}

function renderSources(sources) {
  return sources.map(s => `
    <details class="source">
      <summary><span class="tc">${s.timecode}</span><span class="ttl">${escape(s.title)}</span></summary>
      <div class="player">
        <iframe loading="lazy" allowfullscreen title="${escape(s.title)} at ${s.timecode}"
          src="https://www.youtube-nocookie.com/embed/${s.video_id}?start=${s.start}"></iframe>
      </div>
      <p class="excerpt">${escape(s.text)}</p>
    </details>`).join("");
}

/* ---------- asking ---------- */
async function ask(question) {
  const turn = document.importNode($("#turn-template").content, true).firstElementChild;
  turn.querySelector(".asked").textContent = question;
  turn.querySelector(".answer").innerHTML =
    `<p class="status"><span class="pulse"></span>Searching 5,938 moments…</p>`;
  thread.prepend(turn);
  turn.scrollIntoView({ behavior: "smooth", block: "start" });

  btn.disabled = true;
  try {
    const res = await fetch("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "The answer service failed.");
    turn.querySelector(".answer").innerHTML = renderAnswer(data.answer, data.sources);
    turn.querySelector(".sources").innerHTML = renderSources(data.sources);
    litArchive(data.sources.map(s => s.video_id));
  } catch (err) {
    turn.querySelector(".answer").innerHTML =
      `<p class="status error">${escape(err.message)} Try again in a moment.</p>`;
  } finally {
    btn.disabled = false;
  }
}

form.addEventListener("submit", (e) => {
  e.preventDefault();
  const question = input.value.trim();
  if (question) { ask(question); input.value = ""; }
});
input.addEventListener("keydown", (e) => {          // Enter sends, Shift+Enter makes a new line
  if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); form.requestSubmit(); }
});
$("#starters").addEventListener("click", (e) => {
  if (e.target.tagName === "BUTTON") ask(e.target.textContent.trim());
});

drawArchive();