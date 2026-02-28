"""
Companion 演示前端 — 独立文件，用完删除即可，不影响任何项目代码。
启动: python _demo_companion.py
访问: http://localhost:8899
"""
import json
import uvicorn
from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

from agents.companion.node import socratic_companion_node
from memory.shared import shared_memory, _STORE

demo = FastAPI(title="Companion Demo")
demo.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_SEEDED = False

def _seed():
    global _SEEDED
    if _SEEDED:
        return
    shared_memory.write("teacher_authority_graph", "global", {
        "scope_level": "moderate",
        "curriculum_topics": [
            "Newton's Second Law", "force", "momentum",
            "牛顿第二定律", "力", "动量",
        ],
        "knowledge_nodes": [
            {"concept": "Newton's Second Law", "description": "F=ma"},
            {"concept": "momentum", "description": "p=mv"},
            {"concept": "force", "description": "force concept"},
        ],
        "latest_boundary": {
            "scope_level": "moderate",
            "curriculum_topics": [
                "Newton's Second Law", "force", "momentum",
                "牛顿第二定律", "力", "动量",
            ],
        },
    })
    _SEEDED = True


@demo.post("/chat")
async def chat(body: dict):
    _seed()
    student_id = body.get("student_id", "demo-student-001")
    state = {
        "event_type": "student_message",
        "event_payload": {
            "student_id": student_id,
            "content": body.get("content", ""),
            "target_concept": body.get("target_concept", ""),
            "is_correct": body.get("is_correct"),
            "error_analysis": {},
            "time_spent": 0.0,
            "help_requests": 0,
        },
        "current_agent": "",
        "agent_decision": "",
        "tools_to_call": [],
        "working_memory": body.get("_working_memory", {}),
        "response_to_student": None,
        "response_to_teacher": None,
        "notifications": [],
        "session_id": "demo-session",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "loop_count": 0,
    }

    result = socratic_companion_node(state)

    wm = result.get("working_memory", {})
    cog = wm.get("cognitive_model", {})
    tracker = wm.get("session_error_tracker", {})
    boundary = wm.get("knowledge_boundary", {})
    tools = result.get("tools_to_call", [])

    tool_details = []
    for t in tools:
        r = t.get("result", {})
        detail = {"tool": t["tool"]}
        if t["tool"] == "construct_hint":
            detail["strategy"] = r.get("strategy")
            detail["difficulty"] = r.get("difficulty_level")
        elif t["tool"] == "escalate_to_human":
            detail["reason"] = r.get("reason")
            detail["urgency"] = r.get("urgency")
        elif t["tool"] == "update_student_cognition_map":
            detail["confidence_delta"] = cog.get("confidence_delta")
            detail["new_confidence"] = cog.get("new_confidence")
            detail["misconceptions"] = r.get("new_misconceptions", [])
        tool_details.append(detail)

    return JSONResponse({
        "response": result.get("response_to_student", ""),
        "tools": tool_details,
        "reasoning": wm.get("llm_reasoning", "")[:600],
        "cognition": {
            "confidence": cog.get("new_confidence"),
            "uncertainty": cog.get("new_uncertainty"),
            "delta": cog.get("confidence_delta"),
        },
        "session_tracker": tracker,
        "scope_level": boundary.get("scope_level"),
        "_working_memory": {"session_error_tracker": tracker},
    })


@demo.get("/memory")
async def memory_dump():
    _seed()
    out = {}
    for ns, entries in _STORE.items():
        if entries:
            out[ns] = {}
            for k, entry in entries.items():
                val = entry.get("value", {})
                txt = json.dumps(val, ensure_ascii=False, default=str)
                out[ns][k] = txt[:400] + "…" if len(txt) > 400 else txt
    return JSONResponse(out)


@demo.post("/reset")
async def reset():
    global _SEEDED
    for ns in _STORE:
        _STORE[ns].clear()
    _SEEDED = False
    _seed()
    return JSONResponse({"ok": True})


HTML = r"""<!DOCTYPE html>
<html lang="zh-CN"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Companion Demo — 5-Phase ReAct</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:system-ui,sans-serif;background:#0f172a;color:#e2e8f0;display:flex;height:100vh}
#side{width:270px;background:#1e293b;padding:14px;overflow-y:auto;border-right:1px solid #334155;flex-shrink:0;font-size:13px}
#side h3{color:#38bdf8;margin:10px 0 6px;font-size:13px}
#side label{display:block;color:#94a3b8;margin:6px 0 2px;font-size:12px}
#side input,#side select{width:100%;padding:5px 7px;border:1px solid #475569;border-radius:5px;background:#0f172a;color:#e2e8f0;font-size:12px}
.pb{display:block;width:100%;margin:3px 0;padding:7px;border:1px solid #334155;border-radius:5px;background:#1e293b;color:#cbd5e1;cursor:pointer;font-size:11px;text-align:left}
.pb:hover{background:#334155;border-color:#38bdf8}
.rst{background:#7f1d1d;border-color:#991b1b;color:#fca5a5;margin-top:10px}
.rst:hover{background:#991b1b}
#main{flex:1;display:flex;flex-direction:column}
#hdr{padding:10px 18px;background:#1e293b;border-bottom:1px solid #334155;display:flex;align-items:center;gap:10px}
#hdr h1{font-size:15px}
.tag{font-size:10px;background:#0ea5e9;color:#fff;padding:2px 7px;border-radius:8px}
#chat{flex:1;overflow-y:auto;padding:16px;display:flex;flex-direction:column;gap:10px}
.m{max-width:78%;padding:9px 13px;border-radius:10px;font-size:13px;line-height:1.55;white-space:pre-wrap;word-break:break-word}
.m.u{align-self:flex-end;background:#0ea5e9;color:#fff;border-bottom-right-radius:3px}
.m.b{align-self:flex-start;background:#1e293b;border:1px solid #334155;border-bottom-left-radius:3px}
.meta{font-size:10px;color:#64748b;margin-top:5px;line-height:1.6}
.meta b{color:#94a3b8}
.meta .st{display:inline-block;padding:1px 5px;border-radius:3px;margin-right:4px;font-size:9px}
.st-socratic{background:#164e63;color:#67e8f9}
.st-decompose{background:#3b0764;color:#c084fc}
.st-analogy{background:#14532d;color:#86efac}
.st-confront{background:#7c2d12;color:#fdba74}
.st-escalate{background:#7f1d1d;color:#fca5a5}
.st-boundary{background:#78350f;color:#fde68a}
#bar{padding:10px 18px;background:#1e293b;border-top:1px solid #334155;display:flex;gap:7px}
#bar input{flex:1;padding:9px 12px;border:1px solid #475569;border-radius:7px;background:#0f172a;color:#e2e8f0;font-size:13px;outline:none}
#bar input:focus{border-color:#0ea5e9}
#bar button{padding:9px 18px;border:none;border-radius:7px;background:#0ea5e9;color:#fff;font-size:13px;cursor:pointer;font-weight:600}
#bar button:disabled{opacity:.4;cursor:not-allowed}
.ld{display:inline-block;width:5px;height:5px;border-radius:50%;background:#94a3b8;animation:bl 1.4s infinite both}
.ld:nth-child(2){animation-delay:.2s}.ld:nth-child(3){animation-delay:.4s}
@keyframes bl{0%,80%,100%{opacity:0}40%{opacity:1}}
#mp{display:none;position:fixed;top:0;right:0;width:400px;height:100vh;background:#1e293b;border-left:1px solid #334155;overflow-y:auto;padding:14px;z-index:99}
#mp pre{font-size:10px;color:#94a3b8;white-space:pre-wrap;word-break:break-all}
#mt{position:fixed;top:10px;right:10px;background:#334155;color:#e2e8f0;border:none;padding:5px 10px;border-radius:5px;cursor:pointer;font-size:11px;z-index:100}
</style></head><body>

<div id="side">
  <h3>🎓 Companion Demo</h3>
  <label>Student ID</label>
  <input id="sid" value="demo-student-001">
  <label>Target Concept</label>
  <input id="concept" value="牛顿第二定律">
  <label>is_correct</label>
  <select id="cor">
    <option value="">未知(null)</option>
    <option value="false" selected>错误(false)</option>
    <option value="true">正确(true)</option>
  </select>

  <h3>⚡ 快捷测试</h3>
  <button class="pb" data-m="力不就是质量乘速度吗？" data-c="牛顿第二定律" data-r="false">
    ❌ 误解: "力=质量×速度"
  </button>
  <button class="pb" data-m="力不就是质量乘速度吗？" data-c="牛顿第二定律" data-r="false">
    ❌ 再错一次 (测试策略切换)
  </button>
  <button class="pb" data-m="F=ma 对吧？" data-c="牛顿第二定律" data-r="true">
    ✅ 正确: "F=ma"
  </button>
  <button class="pb" data-m="我放弃了，太难了" data-c="牛顿第二定律" data-r="false">
    😞 挫败: "我放弃了"
  </button>
  <button class="pb" data-m="量子力学和这个有什么关系？" data-c="" data-r="">
    🚧 超范围: 量子力学
  </button>
  <button class="pb" data-m="动量p=mv，那力F又是什么？" data-c="force" data-r="false">
    🔗 追问: 力与动量区别
  </button>
  <button class="pb rst" onclick="doReset()">🗑 重置内存 (清空认知模型)</button>
</div>

<div id="main">
  <div id="hdr">
    <h1>Socratic Companion</h1>
    <span class="tag">5-Phase ReAct</span>
    <span class="tag">Demo</span>
  </div>
  <div id="chat"></div>
  <div id="bar">
    <input id="msg" placeholder="输入学生消息…" autofocus>
    <button id="btn" onclick="send()">发送</button>
  </div>
</div>

<button id="mt" onclick="togMem()">📦 Memory</button>
<div id="mp"><h3 style="margin-bottom:6px">Shared Memory Dump</h3><pre id="mj">点击按钮刷新</pre></div>

<script>
const C=document.getElementById('chat'),I=document.getElementById('msg'),B=document.getElementById('btn');
let wm={};

document.querySelectorAll('.pb:not(.rst)').forEach(b=>b.addEventListener('click',()=>{
  I.value=b.dataset.m;
  document.getElementById('concept').value=b.dataset.c||'';
  document.getElementById('cor').value=b.dataset.r||'';
  send();
}));
I.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();send()}});

async function send(){
  const txt=I.value.trim();if(!txt)return;
  addM(txt,'u');I.value='';B.disabled=true;
  const dots=addLD();
  const cv=document.getElementById('cor').value;
  try{
    const r=await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({
        student_id:document.getElementById('sid').value,
        content:txt,
        target_concept:document.getElementById('concept').value,
        is_correct:cv===''?null:cv==='true',
        _working_memory:wm,
      })});
    const d=await r.json();
    wm=d._working_memory||{};
    dots.remove();
    addM(d.response||'(无回复)','b',d);
  }catch(e){dots.remove();addM('请求失败: '+e.message,'b')}
  B.disabled=false;I.focus();
}

function addM(text,who,d){
  const div=document.createElement('div');div.className='m '+who;
  div.textContent=text;
  if(d){
    const mt=document.createElement('div');mt.className='meta';
    let h='';
    // tools & strategy
    (d.tools||[]).forEach(t=>{
      if(t.tool==='construct_hint'){
        h+=`<span class="st st-${t.strategy||'socratic'}">${t.strategy||'?'}</span>`;
        if(t.difficulty!=null) h+=`难度:${t.difficulty.toFixed(1)} `;
      }else if(t.tool==='escalate_to_human'){
        h+=`<span class="st st-escalate">ESCALATE:${t.reason}</span>`;
      }else if(t.tool==='update_student_cognition_map'){
        if(t.new_confidence!=null) h+=`<b>置信度:</b>${t.new_confidence.toFixed(2)} `;
        if(t.confidence_delta!=null) h+=`(Δ${t.confidence_delta>0?'+':''}${t.confidence_delta.toFixed(2)}) `;
      }
    });
    // cognition
    if(d.cognition?.confidence!=null) h+=`| <b>conf:</b>${d.cognition.confidence.toFixed(2)} `;
    // scope
    if(d.scope_level) h+=`| <b>scope:</b>${d.scope_level} `;
    // session tracker
    const tr=d.session_tracker||{};
    const keys=Object.keys(tr);
    if(keys.length){
      h+='<br>';
      keys.forEach(k=>{
        const v=tr[k];
        h+=`<b>${k}:</b> errors=${v.consecutive_errors}, tried=[${(v.strategies_tried||[]).join(',')}] `;
      });
    }
    mt.innerHTML=h;div.appendChild(mt);
  }
  C.appendChild(div);C.scrollTop=C.scrollHeight;return div;
}

function addLD(){
  const d=document.createElement('div');d.className='m b';
  d.innerHTML='<span class="ld"></span><span class="ld"></span><span class="ld"></span>';
  C.appendChild(d);C.scrollTop=C.scrollHeight;return d;
}

async function doReset(){
  await fetch('/reset',{method:'POST'});wm={};
  C.innerHTML='<div class="m b" style="color:#94a3b8">内存已重置，可重新测试</div>';
}

let mo=false;
async function togMem(){
  const p=document.getElementById('mp');mo=!mo;p.style.display=mo?'block':'none';
  if(mo){try{const r=await fetch('/memory');const d=await r.json();
    document.getElementById('mj').textContent=JSON.stringify(d,null,2);
  }catch(e){document.getElementById('mj').textContent='Error: '+e.message}}
}
</script></body></html>"""


@demo.get("/", response_class=HTMLResponse)
async def index():
    return HTML


if __name__ == "__main__":
    print("\n  Companion Demo 启动中…")
    print("  访问: http://localhost:8899\n")
    uvicorn.run(demo, host="0.0.0.0", port=8899, log_level="info")
