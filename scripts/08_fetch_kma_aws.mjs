// Step 1f: hourly weather (temperature, precipitation, wind speed) for the 29 Seoul AWS stations, 2025.
//
// Source: KMA 기상자료개방포털, 방재기상관측(AWS) 시간 자료 (https://data.kma.go.kr, login required).
// The portal times out on a one-year request, so this asks for one month at a time through a logged-in
// browser session and saves each month as UTF-8 CSV in raw/weather/aws_2025MM.csv.
//
// How to run (Windows, Node 22+):
//   1. Start Edge with remote debugging and log in to data.kma.go.kr in that window:
//        msedge --remote-debugging-port=9333 --user-data-dir=<any empty folder> https://data.kma.go.kr/data/grnd/selectAwsRltmList.do?pgmNo=56
//   2. node scripts/08_fetch_kma_aws.mjs eval "<js expression>"   (inspect the page, e.g. to read codes)
//      node scripts/08_fetch_kma_aws.mjs fetch <stnIds> <elementCds> <elementGroupSns> [months, default 1-12]
//   Used for this project (29 Seoul stations; 기온, 풍속, 강수량):
//      stnIds (group_station) 181_400,181_402,181_424,181_404,181_509,181_413,181_423,181_417,181_410,181_425,181_407,181_406,181_408,181_411,
//        181_422,181_420,181_412,181_401,181_421,181_414,181_403,181_405,181_510,181_415,181_416,181_419,181_409,181_418,181_889
//   The portal also asks once per session for the purpose of use (학술/연구): run one CSV download from the page
//   by hand first, then this script reuses that session.
//      elementCds SFC02008001,SFC02009002,SFC02010001   elementGroupSns 120,121,122
// The script only runs requests inside the logged-in page; it never reads or stores cookies.
import { writeFileSync, mkdirSync } from "node:fs";

const PORT = 9333;
const OUT = "raw/weather";

async function page() {
  const list = await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json();
  const t = list.find((x) => x.type === "page" && x.url.startsWith("https://data.kma.go.kr/"));
  if (!t) throw new Error("open data.kma.go.kr in the debugging Edge window first");
  const ws = new WebSocket(t.webSocketDebuggerUrl);
  await new Promise((ok, bad) => { ws.onopen = ok; ws.onerror = bad; });
  let id = 0;
  const pending = new Map();
  ws.onmessage = (m) => {
    const d = JSON.parse(m.data);
    if (pending.has(d.id)) { pending.get(d.id)(d); pending.delete(d.id); }
  };
  const evaluate = (expression) => new Promise((ok, bad) => {
    const n = ++id;
    pending.set(n, (d) => {
      if (d.error) return bad(new Error(JSON.stringify(d.error)));
      const r = d.result;
      if (r.exceptionDetails) return bad(new Error(r.exceptionDetails.exception?.description || r.exceptionDetails.text));
      ok(r.result.value);
    });
    ws.send(JSON.stringify({ id: n, method: "Runtime.evaluate",
      params: { expression, awaitPromise: true, returnByValue: true, timeout: 600000 } }));
  });
  return { evaluate, close: () => ws.close() };
}

// one month: ask the portal to build the CSV, then download it; decode from EUC-KR inside the page
// starts from the page's own search form (so every hidden field the portal expects is there) and overrides
// the data form (hourly), period, stations and elements
const monthJs = (stnIds, elementCds, groupSns, y, m) => {
  const last = new Date(y, m, 0).getDate();
  const mm = String(m).padStart(2, "0");
  return `(async () => {
    const p = new URLSearchParams($("form[name=schForm]").serialize());
    const set = { fileType: "csv", dataFormCd: "F00502", startDt: "${y}${mm}01", startHh: "00",
      endDt: "${y}${mm}${last}", endHh: "23", stnIds: "${stnIds}", elementCds: "${elementCds}",
      elementGroupSns: "${groupSns}" };
    for (const k in set) p.set(k, set[k]);
    const r = await fetch("/data/common/downloadDataCVS.do", { method: "POST", body: p,
      headers: { "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8", "X-Requested-With": "XMLHttpRequest" } });
    const tok = (await r.text()).trim();
    if (!/\\.csv$/.test(tok)) return "ERROR " + tok.slice(0, 300);
    const f = await fetch("/download/fileDownload.do", { method: "POST", body: new URLSearchParams({ file: tok, delYn: "Y" }) });
    return new TextDecoder("euc-kr").decode(await f.arrayBuffer());
  })()`;
};

const [cmd, ...args] = process.argv.slice(2);
const pg = await page();
try {
  if (cmd === "eval") {
    console.log(JSON.stringify(await pg.evaluate(args[0]), null, 1));
  } else if (cmd === "fetch") {
    const [stnIds, elementCds, groupSns, months = "1-12"] = args;
    const [a, b] = months.split("-").map(Number);
    mkdirSync(OUT, { recursive: true });
    for (let m = a; m <= (b || a); m++) {
      const t0 = Date.now();
      const txt = await pg.evaluate(monthJs(stnIds, elementCds, groupSns, 2025, m));
      if (txt.startsWith("ERROR")) { console.log(`2025-${m}: ${txt}`); continue; }
      const file = `${OUT}/aws_2025${String(m).padStart(2, "0")}.csv`;
      writeFileSync(file, txt, "utf8");
      console.log(`2025-${m}: ${txt.split("\n").length - 1} lines, ${(txt.length / 1e6).toFixed(2)} M chars, ${((Date.now() - t0) / 1000).toFixed(0)} s -> ${file}`);
    }
  } else if (cmd === "stations") {
    // station coordinates from the portal's station detail popup -> data/aws_stations.csv
    const ids = args[0].split(",");
    const rows = await pg.evaluate(`(async () => {
      const out = [];
      for (const id of ${JSON.stringify(ids)}) {
        const t = await (await fetch("/cmmn/stnDetailPopup.do", { method: "POST", body: new URLSearchParams({ stnId: id }) })).text();
        const txt = new DOMParser().parseFromString(t, "text/html").body.innerText.replace(/\\s+/g, " ");
        const g = (re) => (txt.match(re) || [])[1] || "";
        out.push([id, g(/지점명\\(한글\\) (\\S+)/), g(/위도 : ([0-9.]+)/), g(/경도 : ([0-9.]+)/), g(/해발고도\\(m\\) ([0-9.]+)/), g(/새주소 (.+?) 표준지점번호/)]);
      }
      return out;
    })()`);
    const esc = (v) => (/[,"]/.test(v) ? `"${v.replace(/"/g, '""')}"` : v);
    const csv = ["aws_id,name,lat,lon,alt_m,address", ...rows.map((r) => r.map(esc).join(","))].join("\n") + "\n";
    writeFileSync("data/aws_stations.csv", csv, "utf8");
    console.log(csv);
  } else {
    console.log("usage: eval <expr> | fetch <stnIds> <elementCds> <elementGroupSns> [months] | stations <ids>");
  }
} finally {
  pg.close();
}
