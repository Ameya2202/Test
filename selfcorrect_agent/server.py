"""FastAPI app: runs the self-correction cycle and serves the review website.

Endpoints
    GET  /                 -> the review UI (auto-runs the cycle for the target file)
    GET  /api/target       -> the file under review
    POST /api/run          -> run the full self-correction cycle, return the session
    POST /api/apply        -> apply the approved change to the real file (with backup)
    POST /api/reject       -> discard the session
"""
from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Dict, Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from .agent import SelfCorrectingAgent, Session
from .config import Config

SESSIONS: Dict[str, Session] = {}


def _session_json(s: Session) -> dict:
    return {
        "id": s.id,
        "file_path": s.file_path,
        "status": s.status,
        "changed": s.changed,
        "attempts_used": s.attempts_used,
        "final_summary": s.final_summary,
        "baseline_summary": s.baseline_summary,
        "verified_summary": s.verified_summary,
        "before_score": s.before_score,
        "after_score": s.after_score,
        "improvement_percent": s.improvement_percent,
        "rationale": s.rationale,
        "original_code": s.original_code,
        "improved_code": s.improved_code,
        "tests_code": s.tests_code,
        "diff": s.unified_diff,
        "applied": s.applied,
        "backup_path": s.backup_path,
        "test_path": s.test_path,
        "steps": [
            {"name": st.name, "status": st.status, "detail": st.detail, "attempt": st.attempt}
            for st in s.steps
        ],
    }


class RunReq(BaseModel):
    path: Optional[str] = None


class SessionReq(BaseModel):
    session_id: str
    write_tests: bool = True


def _validate_target(path: str) -> str:
    resolved = Path(path).expanduser().resolve()
    if not resolved.is_file():
        raise HTTPException(status_code=400, detail=f"File not found: {resolved}")
    if resolved.suffix != ".py":
        raise HTTPException(
            status_code=400,
            detail="Only Python files (.py) are supported by the pytest dreaming cycle.",
        )
    try:
        resolved.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="File must be UTF-8 text.") from exc
    return str(resolved)


def create_app(target_path: str, config: Optional[Config] = None, provider=None) -> FastAPI:
    config = config or Config()
    agent = SelfCorrectingAgent(config, provider=provider)
    app = FastAPI(title="Self-Correcting Agent")

    @app.get("/", response_class=HTMLResponse)
    def index():
        return HTML_PAGE

    @app.get("/api/target")
    def target():
        return {"path": _validate_target(target_path), "mock": config.use_mock or not config.has_api_key,
                "model": config.model}

    @app.post("/api/upload")
    async def upload(file: UploadFile = File(...)):
        if not file.filename or not file.filename.endswith(".py"):
            raise HTTPException(status_code=400, detail="Upload a Python .py file.")
        data = await file.read()
        try:
            data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise HTTPException(status_code=400, detail="File must be UTF-8 text.") from exc
        safe_name = Path(file.filename).name
        upload_dir = Path(tempfile.mkdtemp(prefix="selfcorrect_upload_"))
        uploaded = upload_dir / safe_name
        uploaded.write_bytes(data)
        return {"path": str(uploaded), "filename": safe_name, "bytes": len(data)}

    @app.post("/api/run")
    def run(req: RunReq):
        path = _validate_target(req.path or target_path)
        try:
            session = agent.run(path)
        except Exception as e:  # surface the error to the UI rather than 500-ing silently
            raise HTTPException(status_code=400, detail=f"{type(e).__name__}: {e}")
        SESSIONS[session.id] = session
        return JSONResponse(_session_json(session))

    @app.post("/api/apply")
    def apply(req: SessionReq):
        s = SESSIONS.get(req.session_id)
        if not s:
            raise HTTPException(status_code=404, detail="Unknown session.")
        if s.status != "ready":
            raise HTTPException(status_code=400,
                                detail="Session is not in a ready state; not applying.")
        s.apply(write_tests=req.write_tests)
        return JSONResponse(_session_json(s))

    @app.post("/api/reject")
    def reject(req: SessionReq):
        SESSIONS.pop(req.session_id, None)
        return {"ok": True}

    return app


# --------------------------------------------------------------------------- #
# Single-file UI (polished productivity dashboard, no external assets)
# --------------------------------------------------------------------------- #
HTML_PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Self-Correcting Agent</title>
<style>
  :root{
    --bg:#f6f3ee; --paper:#fffdf9; --ink:#171717; --muted:#6f6b66;
    --line:#e6ded3; --soft:#f0e8de; --brand:#6d5dfc; --brand2:#ff8a65;
    --green:#10a37f; --yellow:#b7791f; --red:#d64545; --blue:#2563eb;
    --add:#e7f7ed; --del:#ffebeb; --shadow:0 20px 60px rgba(45,37,30,.12);
  }
  *{box-sizing:border-box}
  html{scroll-behavior:smooth}
  body{margin:0;min-height:100vh;color:var(--ink);
    background:
      radial-gradient(circle at 8% 10%, rgba(109,93,252,.18), transparent 32%),
      radial-gradient(circle at 85% 5%, rgba(255,138,101,.18), transparent 30%),
      linear-gradient(180deg,#fbf7f0 0%,var(--bg) 48%,#f2eee7 100%);
    font:14px/1.5 Inter,ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Arial}
  button,input{font:inherit}
  code,pre,.mono{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
  .shell{max-width:1240px;margin:0 auto;padding:28px}
  .hero{display:grid;grid-template-columns:minmax(0,1fr) 380px;gap:22px;align-items:stretch}
  @media(max-width:960px){.shell{padding:16px}.hero{grid-template-columns:1fr}}
  .glass,.card{background:rgba(255,253,249,.86);border:1px solid rgba(230,222,211,.92);
    box-shadow:var(--shadow);backdrop-filter:blur(16px);border-radius:28px}
  .intro{padding:30px;position:relative;overflow:hidden}
  .intro:after{content:"";position:absolute;right:-80px;top:-90px;width:260px;height:260px;
    border-radius:50%;background:linear-gradient(135deg,var(--brand),var(--brand2));opacity:.16}
  .eyebrow{display:inline-flex;gap:8px;align-items:center;color:#554dff;background:#eeebff;
    border:1px solid #ded9ff;border-radius:99px;padding:6px 10px;font-weight:700;font-size:12px}
  h1{font-size:clamp(34px,6vw,64px);line-height:.95;margin:18px 0 16px;letter-spacing:-2.5px}
  .lead{max-width:740px;color:var(--muted);font-size:16px;margin:0}
  .chips{display:flex;gap:8px;flex-wrap:wrap;margin-top:22px}
  .chip{background:var(--paper);border:1px solid var(--line);border-radius:12px;
    padding:8px 10px;color:#3d3935;font-weight:650;font-size:12px}
  .control{padding:20px;display:flex;flex-direction:column;gap:14px}
  .label{font-size:11px;letter-spacing:.9px;text-transform:uppercase;color:var(--muted);font-weight:800}
  .pathbox{display:flex;gap:8px;background:#fff;border:1px solid var(--line);border-radius:16px;padding:8px}
  .pathbox input{width:100%;border:0;outline:0;background:transparent;color:var(--ink)}
  button{border:0;border-radius:14px;padding:10px 14px;cursor:pointer;font-weight:800;
    color:var(--ink);background:#fff;border:1px solid var(--line);transition:.18s ease}
  button:hover{transform:translateY(-1px);box-shadow:0 10px 24px rgba(45,37,30,.08)}
  button:disabled{opacity:.55;cursor:not-allowed;transform:none;box-shadow:none}
  .primary{background:linear-gradient(135deg,var(--brand),#8b7dff);border-color:transparent;color:#fff}
  .danger{color:var(--red)}
  .drop{border:1.5px dashed #d8ccbd;border-radius:20px;padding:22px;text-align:center;background:#fffaf4;
    color:var(--muted);transition:.18s ease}
  .drop.hot{border-color:var(--brand);background:#f0edff;color:#3e34a3}
  .drop strong{display:block;color:var(--ink);font-size:15px;margin-bottom:4px}
  .mode{display:flex;justify-content:space-between;gap:12px;align-items:center;background:#111827;
    color:#e5e7eb;border-radius:18px;padding:12px 14px}
  .mode span{color:#a7f3d0;font-weight:800}
  .grid{display:grid;grid-template-columns:360px minmax(0,1fr);gap:22px;margin-top:22px}
  @media(max-width:960px){.grid{grid-template-columns:1fr}}
  .card{overflow:hidden}
  .card h2{display:flex;align-items:center;justify-content:space-between;margin:0;padding:16px 18px;
    border-bottom:1px solid var(--line);font-size:13px;letter-spacing:.7px;text-transform:uppercase;color:#514b45}
  .body{padding:18px}
  .score{display:grid;grid-template-columns:150px 1fr;gap:18px;align-items:center}
  @media(max-width:520px){.score{grid-template-columns:1fr}}
  .ring{--p:0; width:148px;height:148px;border-radius:50%;display:grid;place-items:center;margin:auto;
    background:conic-gradient(var(--green) calc(var(--p)*1%),#ece4da 0);position:relative}
  .ring:before{content:"";position:absolute;inset:12px;background:var(--paper);border-radius:50%}
  .ring b{position:relative;font-size:34px;letter-spacing:-1px}
  .metrics{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
  @media(max-width:560px){.metrics{grid-template-columns:1fr}}
  .metric{background:#fff;border:1px solid var(--line);border-radius:18px;padding:14px}
  .metric .k{color:var(--muted);font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:.7px}
  .metric .v{font-size:24px;font-weight:900;margin-top:4px;letter-spacing:-.8px}
  .metric small{display:block;color:var(--muted);margin-top:4px}
  .step{display:grid;grid-template-columns:30px 1fr auto;gap:10px;align-items:start;padding:11px 0;
    border-bottom:1px solid var(--line)}
  .step:last-child{border-bottom:0}
  .badge{width:30px;height:30px;border-radius:10px;display:grid;place-items:center;font-weight:900;color:#fff}
  .b-ok{background:var(--green)} .b-fail{background:var(--red)}
  .b-warn{background:var(--yellow)} .b-info{background:var(--blue)}
  .step .n{font-weight:850}.step .d{color:var(--muted);font-size:12.5px}.step .a{color:var(--muted);font-size:11px}
  .tabs{display:flex;gap:8px;flex-wrap:wrap;padding:14px 14px 0}
  .tab{padding:9px 12px;border-radius:13px;cursor:pointer;color:var(--muted);font-weight:800;font-size:12px}
  .tab.active{background:#111827;color:#fff}
  pre{margin:14px;padding:16px;overflow:auto;max-height:520px;font-size:12.5px;background:#111827;color:#e5e7eb;border-radius:18px}
  .diff .ln{display:block;white-space:pre}
  .diff .add{background:rgba(16,163,127,.2);color:#bbf7d0}.diff .del{background:rgba(214,69,69,.22);color:#fecaca}
  .diff .hdr{color:#93c5fd}.diff .meta{color:#a8a29e}
  .bar{display:none;gap:10px;align-items:center;padding:14px 18px;margin-top:16px;
    background:#111827;border-radius:22px;color:#e5e7eb;box-shadow:var(--shadow)}
  .bar label{display:flex;gap:8px;align-items:center;color:#d1d5db;font-size:13px}
  .bar .spacer{flex:1}
  .banner{padding:13px 15px;border-radius:16px;margin-top:14px;font-size:13px;border:1px solid var(--line);background:#fff}
  .banner.ok{background:#ecfdf5;border-color:#a7f3d0;color:#064e3b}
  .banner.warn{background:#fffbeb;border-color:#fde68a;color:#78350f}
  .banner.err{background:#fef2f2;border-color:#fecaca;color:#7f1d1d}
  .note{color:var(--muted)}
  .spin{width:16px;height:16px;border:2px solid #ddd2c4;border-top-color:var(--brand);
    border-radius:50%;display:inline-block;animation:s .8s linear infinite;vertical-align:-3px}
  @keyframes s{to{transform:rotate(360deg)}}
</style>
</head>
<body>
<div class="shell">
  <section class="hero">
    <div class="glass intro">
      <span class="eyebrow">Dreaming cycle workspace</span>
      <h1>Self-correct code with a reviewable website.</h1>
      <p class="lead">Drop in this package, point it at a Python file, and watch the agent generate tests, run them, diagnose failures, correct itself, and quantify the before/after improvement before you apply anything.</p>
      <div class="chips">
        <span class="chip">One-page review</span>
        <span class="chip">Human-in-the-loop apply</span>
        <span class="chip">Sandboxed pytest</span>
        <span class="chip">Before/after score</span>
      </div>
    </div>
    <aside class="glass control">
      <div>
        <div class="label">Target file path</div>
        <div class="pathbox">
          <input id="pathInput" class="mono" placeholder="/path/to/module.py"/>
          <button id="runPath" class="primary">Run</button>
        </div>
      </div>
      <div id="drop" class="drop">
        <strong>Upload or drag a .py file</strong>
        <span>Great for trying the agent without wiring it into a repo.</span><br/>
        <input id="fileInput" type="file" accept=".py" style="margin-top:12px"/>
      </div>
      <div class="mode"><div>Provider</div><span id="modeTag">loading...</span></div>
    </aside>
  </section>

  <div id="status"></div>
  <section class="grid">
    <div class="card">
      <h2>Dreaming cycle <span id="cycleState" class="note">idle</span></h2>
      <div class="body" id="steps"><span class="note">Choose a file to start.</span></div>
    </div>
    <div>
      <div class="card">
        <h2>Improvement score <span id="changedTag" class="note">no session</span></h2>
        <div class="body">
          <div class="score">
            <div class="ring" id="ring"><b id="ringText">0%</b></div>
            <div>
              <div class="metrics" id="metrics">
                <div class="metric"><div class="k">Before</div><div class="v">--</div></div>
                <div class="metric"><div class="k">After</div><div class="v">--</div></div>
                <div class="metric"><div class="k">Lift</div><div class="v">--</div></div>
              </div>
              <p id="rationale" class="note" style="margin:14px 0 0">Run the cycle to see the agent's rationale and scoring.</p>
            </div>
          </div>
        </div>
      </div>
      <div class="card" style="margin-top:22px">
        <div class="tabs">
          <div class="tab active" data-t="diff">Proposed diff</div>
          <div class="tab" data-t="tests">Generated tests</div>
          <div class="tab" data-t="improved">Improved file</div>
          <div class="tab" data-t="original">Original file</div>
        </div>
        <div id="pane"><pre class="note">No run yet.</pre></div>
      </div>
    </div>
  </section>

  <div class="bar" id="bar">
    <label><input type="checkbox" id="wt" checked/> also save the generated test file</label>
    <span class="spacer"></span>
    <button id="reject" class="danger">Reject</button>
    <button id="apply" class="primary">Apply to file</button>
  </div>
  <div id="ack"></div>
</div>

<script>
let SESSION=null, CURRENT_PATH="";
const $=s=>document.querySelector(s);
const esc=t=>String(t||"").replace(/[&<>]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;"}[c]));

function badge(s){const m={ok:["b-ok","✓"],fail:["b-fail","✕"],warn:["b-warn","!"],info:["b-info","i"]};
  const [c,ch]=m[s]||m.info;return `<span class="badge ${c}">${ch}</span>`;}
function setBusy(on){
  $("#runPath").disabled=on;$("#fileInput").disabled=on;
  $("#cycleState").innerHTML=on?'<span class="spin"></span> running':'idle';
}
function pct(n){return `${Number(n||0).toFixed(Number(n||0)%1===0?0:1)}%`;}
function renderSteps(steps){
  $("#steps").innerHTML = steps.map(s=>`
    <div class="step">${badge(s.status)}
      <div><div class="n">${esc(s.name)}</div><div class="d">${esc(s.detail)}</div></div>
      <div class="a">${s.attempt?("try "+s.attempt):""}</div>
    </div>`).join("");
}
function renderMetrics(d){
  const lift=Number(d.improvement_percent||0);
  $("#ring").style.setProperty("--p", Math.max(0, Math.min(100, Number(d.after_score||0))));
  $("#ringText").textContent=pct(d.after_score);
  $("#changedTag").textContent=d.changed?"change proposed":"no code change";
  $("#metrics").innerHTML=`
    <div class="metric"><div class="k">Before</div><div class="v">${pct(d.before_score)}</div><small>${esc(d.baseline_summary)}</small></div>
    <div class="metric"><div class="k">After</div><div class="v">${pct(d.after_score)}</div><small>${esc(d.verified_summary)}</small></div>
    <div class="metric"><div class="k">Lift</div><div class="v" style="color:${lift>=0?"var(--green)":"var(--red)"}">${lift>=0?"+":""}${pct(lift)}</div><small>${esc(d.attempts_used)} attempt(s)</small></div>`;
  $("#rationale").textContent=d.rationale||"No rationale returned.";
}
function diffHtml(diff){
  if(!String(diff||"").trim()) return '<pre class="note">No change proposed.</pre>';
  const lines=diff.split("\n").map(l=>{
    let cls=""; if(l.startsWith("+++")||l.startsWith("---")) cls="meta";
    else if(l.startsWith("@@")) cls="hdr"; else if(l.startsWith("+")) cls="add"; else if(l.startsWith("-")) cls="del";
    return `<span class="ln ${cls}">${esc(l)||"&nbsp;"}</span>`;
  }).join("");
  return `<pre class="diff">${lines}</pre>`;
}
function showPane(which){
  document.querySelectorAll(".tab").forEach(t=>t.classList.toggle("active",t.dataset.t===which));
  if(!SESSION){$("#pane").innerHTML='<pre class="note">No run yet.</pre>';return;}
  if(which==="diff") $("#pane").innerHTML=diffHtml(SESSION.diff);
  else if(which==="tests") $("#pane").innerHTML=`<pre>${esc(SESSION.tests_code)}</pre>`;
  else if(which==="original") $("#pane").innerHTML=`<pre>${esc(SESSION.original_code)}</pre>`;
  else $("#pane").innerHTML=`<pre>${esc(SESSION.improved_code)}</pre>`;
}
document.querySelectorAll(".tab").forEach(t=>t.onclick=()=>showPane(t.dataset.t));

async function run(path){
  CURRENT_PATH=path||CURRENT_PATH; SESSION=null;
  $("#status").innerHTML="";$("#ack").innerHTML="";$("#bar").style.display="none";
  $("#steps").innerHTML='<span class="spin"></span> running the dreaming cycle...'; setBusy(true);
  try{
    const r=await fetch("/api/run",{method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({path:CURRENT_PATH})});
    if(!r.ok){const e=await r.json().catch(()=>({}));throw new Error(e.detail||r.statusText);}
    const d=await r.json(); SESSION=d; CURRENT_PATH=d.file_path; $("#pathInput").value=CURRENT_PATH;
    renderSteps(d.steps); renderMetrics(d); showPane("diff");
    $("#cycleState").textContent=d.status==="ready"?"ready":d.status;
    if(d.status==="ready" && d.changed) $("#bar").style.display="flex";
    else if(d.status==="ready") $("#status").innerHTML='<div class="banner warn">The generated tests are already green for this file; no code change is needed.</div>';
    else $("#status").innerHTML='<div class="banner warn">The cycle exhausted its correction budget. Review the diagnosis and generated tests before applying anything manually.</div>';
  }catch(err){
    $("#steps").innerHTML='<span class="note">Run did not complete.</span>';
    $("#status").innerHTML=`<div class="banner err">Run failed: ${esc(err.message)}</div>`;
  }finally{setBusy(false);}
}
async function upload(file){
  if(!file) return;
  $("#ack").innerHTML=""; setBusy(true);
  const form=new FormData(); form.append("file",file);
  try{
    const r=await fetch("/api/upload",{method:"POST",body:form});
    if(!r.ok){const e=await r.json().catch(()=>({}));throw new Error(e.detail||r.statusText);}
    const d=await r.json(); $("#pathInput").value=d.path;
    $("#status").innerHTML=`<div class="banner ok">Uploaded ${esc(d.filename)} (${d.bytes} bytes). Running the dreaming cycle now.</div>`;
    await run(d.path);
  }catch(err){$("#status").innerHTML=`<div class="banner err">Upload failed: ${esc(err.message)}</div>`;}
  finally{setBusy(false);}
}
async function apply(){
  $("#apply").disabled=true;$("#reject").disabled=true;
  const r=await fetch("/api/apply",{method:"POST",headers:{"Content-Type":"application/json"},
    body:JSON.stringify({session_id:SESSION.id,write_tests:$("#wt").checked})});
  if(!r.ok){const e=await r.json().catch(()=>({}));
    $("#ack").innerHTML=`<div class="banner err">${esc(e.detail||"apply failed")}</div>`;
    $("#apply").disabled=false;$("#reject").disabled=false;return;}
  const d=await r.json(); SESSION=d; $("#bar").style.display="none";
  let msg=`<div class="banner ok"><strong>Applied to ${esc(d.file_path)}.</strong><br/>Backup: <span class="mono">${esc(d.backup_path)}</span>.`;
  if(d.test_path) msg+=`<br/>Tests written: <span class="mono">${esc(d.test_path)}</span>.`;
  $("#ack").innerHTML=msg+"</div>";
}
async function reject(){
  await fetch("/api/reject",{method:"POST",headers:{"Content-Type":"application/json"},
    body:JSON.stringify({session_id:SESSION.id})});
  $("#bar").style.display="none";
  $("#ack").innerHTML='<div class="banner warn">Rejected. The target file was not modified.</div>';
}
$("#runPath").onclick=()=>run($("#pathInput").value.trim());
$("#apply").onclick=apply; $("#reject").onclick=reject;
$("#fileInput").onchange=e=>upload(e.target.files[0]);
["dragenter","dragover"].forEach(ev=>$("#drop").addEventListener(ev,e=>{e.preventDefault();$("#drop").classList.add("hot");}));
["dragleave","drop"].forEach(ev=>$("#drop").addEventListener(ev,e=>{e.preventDefault();$("#drop").classList.remove("hot");}));
$("#drop").addEventListener("drop",e=>upload(e.dataTransfer.files[0]));

(async()=>{
  try{
    const t=await (await fetch("/api/target")).json();
    CURRENT_PATH=t.path; $("#pathInput").value=t.path;
    $("#modeTag").textContent=t.mock?"offline mock":"model: "+t.model;
    run(t.path);
  }catch(err){$("#status").innerHTML=`<div class="banner err">${esc(err.message)}</div>`;}
})();
</script>
</body>
</html>"""
