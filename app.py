import base64
import json
from pathlib import Path

import networkx as nx
import streamlit as st
import streamlit.components.v1 as components

ICON_FILES = {
    "temperature": "temperature.jpeg",
    "moisture": "moisture.jpeg",
    "ph": "ph.jpeg",
    "gas": "gas.jpeg",
    "traffic": "traffic.jpeg",
    "base_station": "server.jpeg",
}

TOPOLOGY_THEMES = {
    "Mountain": {
        "topology_key": "mountain",
        "canvas_base": "#e7efe6",
        "grid_line": "rgba(99, 131, 99, 0.16)",
        "panel_bg": "#f8fbf7",
        "panel_border": "#c9d8c6",
        "accent": "#4f7651",
        "pdr_bias": -3.0,
        "delay_bias": 0.10,
        "throughput_mult": 0.92,
        "energy_mult": 1.10,
    },
    "Farmlands": {
        "topology_key": "farmlands",
        "canvas_base": "#f0e8dc",
        "grid_line": "rgba(150, 120, 83, 0.14)",
        "panel_bg": "#fbf8f3",
        "panel_border": "#dcccb5",
        "accent": "#8b6846",
        "pdr_bias": 1.5,
        "delay_bias": -0.02,
        "throughput_mult": 1.05,
        "energy_mult": 0.96,
    },
    "Seas": {
        "topology_key": "seas",
        "canvas_base": "#e4edf3",
        "grid_line": "rgba(88, 119, 144, 0.15)",
        "panel_bg": "#f6fafd",
        "panel_border": "#c8d8e4",
        "accent": "#456e8f",
        "pdr_bias": -1.5,
        "delay_bias": 0.05,
        "throughput_mult": 0.97,
        "energy_mult": 1.03,
    },
}


def resolve_icons_dir() -> Path | None:
    candidates = [
        Path("D:/Prince/icons"),
        Path(__file__).resolve().parents[1] / "icons",
        Path.cwd() / "icons",
    ]
    for path in candidates:
        if path.exists() and path.is_dir():
            return path
    return None


def load_icon_data() -> tuple[dict[str, str], list[str]]:
    icons_dir = resolve_icons_dir()
    if icons_dir is None:
        return {}, list(ICON_FILES.values())

    icon_data: dict[str, str] = {}
    missing: list[str] = []
    for sensor_type, filename in ICON_FILES.items():
        icon_path = icons_dir / filename
        if not icon_path.exists():
            missing.append(filename)
            continue
        suffix = icon_path.suffix.lower()
        mime = "image/png" if suffix == ".png" else "image/jpeg"
        encoded = base64.b64encode(icon_path.read_bytes()).decode("ascii")
        icon_data[sensor_type] = f"data:{mime};base64,{encoded}"
    return icon_data, missing


class MockSim:
    def __init__(self):
        self.nodes = {}
        self.graph = nx.Graph()
        self.base_station = (90, 10)
        self.area = 100


def render_interactive_network(sim: MockSim, icons: dict[str, str], themes: dict[str, dict]) -> None:
    payload = {
        "nodes": [
            {
                "id": int(node_id),
                "x": float(data["pos"][0]),
                "y": float(data["pos"][1]),
                "alive": bool(data["alive"]),
                "sensor_type": data.get("sensor_type", "temperature"),
            }
            for node_id, data in sim.nodes.items()
        ],
        "area": float(sim.area),
        "base_station": {"x": float(sim.base_station[0]), "y": float(sim.base_station[1])},
        "icons": icons,
        "themes": themes,
        "default_environment": next(iter(themes.keys())),
        "defaults": {
            "radius": 26,
            "energy": 100,
            "packets": 800,
            "rounds": 100,
            "auto_base": True,
        },
    }
    payload_json = json.dumps(payload)

    html = """
<style>
*{box-sizing:border-box}body{margin:0;font-family:Segoe UI,Tahoma,sans-serif;background:#f4f7fb;color:#1e2b3a}
.wsn{padding:10px;max-width:100vw}
.title{font-size:14px;font-weight:600;margin-bottom:8px}
.layout{display:grid;grid-template-columns:300px minmax(0,1fr);gap:10px;align-items:start}
.panel{background:var(--panel-bg);border:1px solid var(--panel-border);border-radius:12px;padding:10px}
.h{font-size:12px;font-weight:700;margin:0 0 7px;color:#2a3d57}
.row{margin-bottom:8px}.row label{display:block;font-size:11px;color:#4e6179;margin-bottom:3px}
.row select,.row input[type=number]{width:100%;border:1px solid var(--panel-border);background:#fff;border-radius:8px;padding:6px;font-size:12px}
.row input[type=range]{width:100%}.note{font-size:11px;color:#3c5570}
.palette{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}
.item{border:1px solid var(--panel-border);border-radius:10px;background:rgba(255,255,255,.74);padding:7px;text-align:center;cursor:grab}
.item.active{border-color:var(--accent)}
.item img{width:42px;height:42px;border-radius:9px;object-fit:cover}
.item div{font-size:11px;margin-top:5px;text-transform:capitalize}
.btns{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin:8px 0}
button{border:1px solid var(--panel-border);border-radius:8px;padding:7px;font-size:12px;background:rgba(255,255,255,.86);cursor:pointer;color:#23374f}
button.primary{background:var(--accent);color:#f7fbff;border-color:transparent}
.stats{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.card{border:1px solid var(--panel-border);border-radius:10px;background:rgba(255,255,255,.78);padding:7px}
.k{font-size:11px;color:#5b6f89}.v{font-size:15px;font-weight:700;color:#203347}
#wrap{height:72vh;min-height:520px;overflow:auto;border:1px solid var(--panel-border);border-radius:12px;background:rgba(255,255,255,.45);cursor:grab}
#stage{position:relative;width:1200px;height:1200px;transform-origin:top left;border:2px dashed rgba(109,133,160,.45);border-radius:12px;
background:linear-gradient(0deg,var(--grid-line) 1px,transparent 1px),linear-gradient(90deg,var(--grid-line) 1px,transparent 1px),var(--canvas-base);background-size:38px 38px}
#edges{position:absolute;inset:0;pointer-events:none}
.node{position:absolute;width:56px;transform:translate(-50%,-50%);text-align:center;user-select:none;cursor:grab}
.node img{width:52px;height:52px;border-radius:12px;border:2px solid #2f638f;background:#fff;object-fit:cover;box-shadow:0 3px 12px rgba(51,83,113,.25)}
.node.dead img{border-color:#b24a4a;filter:grayscale(.7)}
.node .l{margin-top:4px;font-size:10px;background:rgba(255,255,255,.9);border:1px solid var(--panel-border);border-radius:6px;padding:2px 4px}
.base{position:absolute;width:62px;transform:translate(-50%,-50%);pointer-events:none;text-align:center}
.base img{width:58px;height:58px;border-radius:14px;border:2px solid #c89c2c}
.base .l{margin-top:4px;font-size:10px;background:rgba(255,255,255,.9);border:1px solid #ead9ad;border-radius:7px;padding:2px 4px}
.status{font-size:11px;color:#4f6581}
.history{margin-top:8px;display:grid;gap:8px}.hist{border:1px solid var(--panel-border);border-radius:9px;background:rgba(255,255,255,.78);padding:7px;font-size:11px}
.hist .t{display:flex;justify-content:space-between;font-weight:700;margin-bottom:3px}
@media (max-width:1080px){.layout{grid-template-columns:1fr}#wrap{height:68vh;min-height:420px}}
</style>
<div class="wsn" id="root">
  <div class="title">Wireless Sensor Network Simulator</div>
  <div class="layout">
    <div class="panel">
      <div class="h">Simulation Controls</div>
      <div class="row"><label for="env">Environment</label><select id="env"></select></div>
      <div class="row"><label for="radius">Transmission Range</label><input id="radius" type="range" min="8" max="80" step="1"><div class="note" id="radius-note"></div></div>
      <div class="row"><label for="energy">Initial Energy Per Node</label><input id="energy" type="range" min="20" max="200" step="1"><div class="note" id="energy-note"></div></div>
      <div class="row"><label for="packets">Packets Sent (per run)</label><input id="packets" type="range" min="50" max="5000" step="50"><div class="note" id="packets-note"></div></div>
      <div class="row"><label for="rounds">Rounds</label><input id="rounds" type="number" min="1" max="5000" step="1"></div>
      <div class="row"><label><input id="auto-base" type="checkbox"> Auto-connect sensors to base station by distance</label></div>
      <div class="btns">
        <button id="fit">Fit Grid</button>
        <button id="run" class="primary">Run Deployment</button>
        <button id="connect-base">Connect All to Base</button>
        <button id="clear-base">Clear Base Links</button>
      </div>
      <div class="status" id="status">Deploy sensors from the palette, then run deployment.</div>
      <div class="h" style="margin-top:10px">Sensor Palette</div>
      <div class="palette" id="palette"></div>
      <div class="note" style="margin-top:7px">Click icon to select. Drag to grid or double-click grid to place selected icon.</div>
    </div>
    <div class="panel"><div id="wrap"><div id="stage"><svg id="edges" width="1200" height="1200"></svg></div></div></div>
  </div>
  <div class="panel" style="margin-top:10px">
    <div class="h">Layout Statistics</div>
    <div class="stats" style="margin-bottom:8px">
      <div class="card"><div class="k">Total Nodes</div><div class="v" id="s-total">0</div></div>
      <div class="card"><div class="k">Sensor Links</div><div class="v" id="s-links">0</div></div>
      <div class="card"><div class="k">Base Links</div><div class="v" id="s-base">0</div></div>
      <div class="card"><div class="k">Avg Dist to Base</div><div class="v" id="s-dist">0</div></div>
    </div>
    <div class="h">Deployment Output</div>
    <div class="stats">
      <div class="card"><div class="k">PDR</div><div class="v" id="o-pdr">-</div></div>
      <div class="card"><div class="k">Avg Delay</div><div class="v" id="o-delay">-</div></div>
      <div class="card"><div class="k">Throughput</div><div class="v" id="o-thr">-</div></div>
      <div class="card"><div class="k">Residual Energy</div><div class="v" id="o-energy">-</div></div>
      <div class="card"><div class="k">Packets Sent</div><div class="v" id="o-packets">-</div></div>
    </div>
    <div class="btns" style="margin-top:8px">
      <button id="clear-history">Clear History</button>
      <button id="refresh-history">Refresh Summary</button>
    </div>
    <div class="history" id="history"></div>
  </div>
</div>
<script>
const cfg=__PAYLOAD__;
const STORAGE_KEY="wsn_sim_deployment_history_v1";
const root=document.getElementById("root"),stage=document.getElementById("stage"),wrap=document.getElementById("wrap"),edgesSvg=document.getElementById("edges");
const envSel=document.getElementById("env"),radius=document.getElementById("radius"),energy=document.getElementById("energy"),rounds=document.getElementById("rounds"),autoBase=document.getElementById("auto-base");
const radiusNote=document.getElementById("radius-note"),energyNote=document.getElementById("energy-note"),status=document.getElementById("status");
const palette=document.getElementById("palette"),historyHost=document.getElementById("history");
const area=cfg.area,stageSize=1300,nodeRadius=28,sensorTypes=["temperature","moisture","ph","gas","traffic"];
const icons=cfg.icons||{},themes=cfg.themes||{},fallbackIcon="data:image/svg+xml;base64,PHN2ZyB4bWxucz0naHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmcnIHdpZHRoPSc2NCcgaGVpZ2h0PSc2NCc+PHJlY3Qgd2lkdGg9JzY0JyBoZWlnaHQ9JzY0JyByeD0nMTInIGZpbGw9JyNlMWVkZmInIHN0cm9rZT0nIzZiOTFjNycgc3Ryb2tlLXdpZHRoPScyJy8+PGNpcmNsZSBjeD0nMzInIGN5PSczMicgcj0nMTAnIGZpbGw9JyM0NDZjYjEnLz48L3N2Zz4=";
let zoom=1,nodes=cfg.nodes.map(n=>({...n})),nextId=nodes.length?Math.max(...nodes.map(n=>n.id))+1:1,selectedType=sensorTypes[0],sensorEdges=[],history=[],manualBaseLinks=new Set();
let radiusVal=Number(cfg.defaults.radius||26),energyVal=Number(cfg.defaults.energy||100),roundsVal=Number(cfg.defaults.rounds||100),autoBaseVal=Boolean(cfg.defaults.auto_base),envName=cfg.default_environment in themes?cfg.default_environment:Object.keys(themes)[0];
const nodeEls=new Map();
const clamp=(v,min,max)=>Math.min(max,Math.max(min,v));
const toStage=v=>(v/area)*stageSize;
const fromStage=px=>(px/stageSize)*area;
const iconFor=t=>icons[t]||fallbackIcon;
const getTheme=()=>themes[envName]||themes[Object.keys(themes)[0]];
const dist=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y);
const clientToStage=(cx,cy)=>{const r=stage.getBoundingClientRect();return{x:(cx-r.left)/zoom,y:(cy-r.top)/zoom};};

function applyTheme(){const t=getTheme();root.style.setProperty("--canvas-base",t.canvas_base);root.style.setProperty("--grid-line",t.grid_line);root.style.setProperty("--panel-bg",t.panel_bg);root.style.setProperty("--panel-border",t.panel_border);root.style.setProperty("--accent",t.accent);}
function setZoom(z){zoom=clamp(z,0.35,1.6);stage.style.transform=`scale(${zoom})`;}
function fitGrid(){const xf=wrap.clientWidth/stageSize,yf=wrap.clientHeight/stageSize;setZoom(Math.min(xf,yf));wrap.scrollTop=0;wrap.scrollLeft=0;}
function getBaseLinks(){const links=new Set(),b=cfg.base_station;manualBaseLinks.forEach(id=>{if(nodes.find(n=>n.id===id))links.add(id);});if(autoBaseVal){nodes.forEach(n=>{if(dist(n,b)<=radiusVal*1.1)links.add(n.id);});}return [...links];}
function recomputeEdges(){const e=[];for(let i=0;i<nodes.length;i++){for(let j=i+1;j<nodes.length;j++){if(dist(nodes[i],nodes[j])<=radiusVal)e.push([nodes[i].id,nodes[j].id]);}}sensorEdges=e;}
function drawEdges(){edgesSvg.innerHTML="";const byId=Object.fromEntries(nodes.map(n=>[n.id,n]));sensorEdges.forEach(([a,b])=>{const na=byId[a],nb=byId[b];if(!na||!nb)return;const l=document.createElementNS("http://www.w3.org/2000/svg","line");l.setAttribute("x1",toStage(na.x));l.setAttribute("y1",toStage(na.y));l.setAttribute("x2",toStage(nb.x));l.setAttribute("y2",toStage(nb.y));l.setAttribute("stroke","#6f91b4");l.setAttribute("stroke-width","1.7");l.setAttribute("stroke-opacity","0.7");edgesSvg.appendChild(l);});const b=cfg.base_station;getBaseLinks().forEach(id=>{const n=byId[id];if(!n)return;const l=document.createElementNS("http://www.w3.org/2000/svg","line");l.setAttribute("x1",toStage(n.x));l.setAttribute("y1",toStage(n.y));l.setAttribute("x2",toStage(b.x));l.setAttribute("y2",toStage(b.y));l.setAttribute("stroke","#be9c42");l.setAttribute("stroke-width","2");l.setAttribute("stroke-dasharray","5 4");l.setAttribute("stroke-opacity","0.85");edgesSvg.appendChild(l);});}
function placeNode(n){const el=nodeEls.get(n.id);if(!el)return;el.style.left=`${toStage(n.x)}px`;el.style.top=`${toStage(n.y)}px`;}
function stats(){const total=nodes.length,b=cfg.base_station,avg=total?nodes.reduce((a,n)=>a+dist(n,b),0)/total:0;document.getElementById("s-total").textContent=String(total);document.getElementById("s-links").textContent=String(sensorEdges.length);document.getElementById("s-base").textContent=String(getBaseLinks().length);document.getElementById("s-dist").textContent=avg.toFixed(1);}
function updateNotes(){radiusNote.textContent=`${radiusVal.toFixed(0)} units`;energyNote.textContent=`${energyVal.toFixed(0)} J`;}
function loadHistory(){try{const raw=localStorage.getItem(STORAGE_KEY);const arr=JSON.parse(raw||"[]");return Array.isArray(arr)?arr:[];}catch{return[];}}
function saveHistory(){try{localStorage.setItem(STORAGE_KEY,JSON.stringify(history.slice(0,30)));}catch{}}
function renderHistory(){historyHost.innerHTML="";if(!history.length){const d=document.createElement("div");d.className="hist";d.textContent="No deployment runs yet.";historyHost.appendChild(d);return;}history.forEach(h=>{const d=document.createElement("div");d.className="hist";d.innerHTML=`<div class="t"><span>${h.environment}</span><span>${new Date(h.timestamp).toLocaleString()}</span></div><div>Nodes ${h.nodes} | Radius ${h.radius} | Rounds ${h.rounds} | PDR ${h.pdr}% | Delay ${h.delay}s | Thrpt ${h.throughput} | Energy ${h.energy_left}% | BaseLinks ${h.base_links}</div>`;historyHost.appendChild(d);});}
function runDeployment(){if(!nodes.length){status.textContent="Add at least one node before running deployment.";return;}const alive=nodes.filter(n=>n.alive).length/nodes.length,baseRatio=getBaseLinks().length/nodes.length,maxLinks=(nodes.length*(nodes.length-1))/2,density=maxLinks?sensorEdges.length/maxLinks:0,b=cfg.base_station,avgDist=nodes.reduce((a,n)=>a+dist(n,b),0)/nodes.length,t=getTheme();const pdr=clamp(58+density*28+baseRatio*15+alive*8+radiusVal*0.15-avgDist*0.16+Number(t.pdr_bias||0)-Math.log10(Math.max(2,roundsVal))*1.8,22,99.8);const delay=clamp(0.12+(100-pdr)/120+roundsVal/1600+Number(t.delay_bias||0),0.08,3.5);const thr=Math.max(1,Math.round(nodes.length*(pdr/100)*(radiusVal/6.5)*Number(t.throughput_mult||1)));const drain=(0.35+radiusVal/70+roundsVal/900)*Number(t.energy_mult||1);const remain=clamp(((energyVal-drain)/energyVal)*100,0,100);document.getElementById("o-pdr").textContent=`${pdr.toFixed(1)}%`;document.getElementById("o-delay").textContent=`${delay.toFixed(2)} s`;document.getElementById("o-thr").textContent=`${thr} pkts`;document.getElementById("o-energy").textContent=`${remain.toFixed(1)}%`;history.unshift({timestamp:new Date().toISOString(),environment:envName,nodes:nodes.length,radius:radiusVal.toFixed(0),rounds:roundsVal,pdr:pdr.toFixed(1),delay:delay.toFixed(2),throughput:thr,energy_left:remain.toFixed(1),base_links:getBaseLinks().length});history=history.slice(0,30);saveHistory();renderHistory();status.textContent=`Deployment run saved for ${envName.toLowerCase()} environment.`;}
function addDrag(node,el){let drag=null;el.addEventListener("pointerdown",e=>{e.preventDefault();e.stopPropagation();drag={id:e.pointerId};el.setPointerCapture(e.pointerId);el.style.cursor="grabbing";});el.addEventListener("pointermove",e=>{if(!drag||drag.id!==e.pointerId)return;const p=clientToStage(e.clientX,e.clientY),x=clamp(p.x,nodeRadius,stageSize-nodeRadius),y=clamp(p.y,nodeRadius,stageSize-nodeRadius);node.x=fromStage(x);node.y=fromStage(y);placeNode(node);recomputeEdges();drawEdges();stats();});const end=e=>{if(!drag||drag.id!==e.pointerId)return;drag=null;el.style.cursor="grab";};el.addEventListener("pointerup",end);el.addEventListener("pointercancel",end);}
function renderNode(n){const el=document.createElement("div");el.className=`node${n.alive?"":" dead"}`;el.innerHTML=`<img src="${iconFor(n.sensor_type)}" alt="${n.sensor_type}"><div class="l">#${n.id} - ${n.sensor_type}</div>`;stage.appendChild(el);nodeEls.set(n.id,el);placeNode(n);addDrag(n,el);}
function addNode(type,cx,cy){const p=clientToStage(cx,cy),x=clamp(p.x,nodeRadius,stageSize-nodeRadius),y=clamp(p.y,nodeRadius,stageSize-nodeRadius),n={id:nextId++,x:fromStage(x),y:fromStage(y),alive:true,sensor_type:type};nodes.push(n);renderNode(n);recomputeEdges();drawEdges();stats();}
function addPalette(){sensorTypes.forEach(t=>{const d=document.createElement("div");d.className="item"+(t===selectedType?" active":"");d.draggable=true;d.innerHTML=`<img src="${iconFor(t)}" alt="${t}"><div>${t}</div>`;d.addEventListener("click",()=>{selectedType=t;[...palette.querySelectorAll(".item")].forEach(x=>x.classList.remove("active"));d.classList.add("active");});d.addEventListener("dragstart",e=>e.dataTransfer.setData("sensor/type",t));palette.appendChild(d);});}
function addBase(){const b=document.createElement("div");b.className="base";b.innerHTML=`<img src="${iconFor("base_station")}" alt="base"><div class="l">Base Station</div>`;stage.appendChild(b);b.style.left=`${toStage(cfg.base_station.x)}px`;b.style.top=`${toStage(cfg.base_station.y)}px`;}
function bindPan(){let pan=null;wrap.addEventListener("pointerdown",e=>{if(e.target.closest(".node"))return;pan={id:e.pointerId,x:e.clientX,y:e.clientY,l:wrap.scrollLeft,t:wrap.scrollTop};wrap.setPointerCapture(e.pointerId);wrap.style.cursor="grabbing";});wrap.addEventListener("pointermove",e=>{if(!pan||pan.id!==e.pointerId)return;wrap.scrollLeft=pan.l-(e.clientX-pan.x);wrap.scrollTop=pan.t-(e.clientY-pan.y);});const end=e=>{if(!pan||pan.id!==e.pointerId)return;pan=null;wrap.style.cursor="grab";};wrap.addEventListener("pointerup",end);wrap.addEventListener("pointercancel",end);}
function bindControls(){Object.keys(themes).forEach(name=>{const op=document.createElement("option");op.value=name;op.textContent=name;envSel.appendChild(op);});envSel.value=envName;envSel.addEventListener("change",()=>{envName=envSel.value;applyTheme();drawEdges();stats();status.textContent=`Environment switched to ${envName}.`;});radius.value=String(radiusVal);radius.addEventListener("input",()=>{radiusVal=Number(radius.value);updateNotes();recomputeEdges();drawEdges();stats();});energy.value=String(energyVal);energy.addEventListener("input",()=>{energyVal=Number(energy.value);updateNotes();});rounds.value=String(roundsVal);rounds.addEventListener("change",()=>{const p=Number(rounds.value);roundsVal=Number.isFinite(p)?clamp(p,1,5000):100;rounds.value=String(roundsVal);});autoBase.checked=autoBaseVal;autoBase.addEventListener("change",()=>{autoBaseVal=autoBase.checked;drawEdges();stats();});document.getElementById("fit").addEventListener("click",fitGrid);document.getElementById("run").addEventListener("click",runDeployment);document.getElementById("connect-base").addEventListener("click",()=>{nodes.forEach(n=>manualBaseLinks.add(n.id));drawEdges();stats();status.textContent="All sensors explicitly connected to base station.";});document.getElementById("clear-base").addEventListener("click",()=>{manualBaseLinks.clear();drawEdges();stats();status.textContent="Manual base links cleared.";});document.getElementById("clear-history").addEventListener("click",()=>{history=[];saveHistory();renderHistory();status.textContent="Deployment history cleared.";});document.getElementById("refresh-history").addEventListener("click",()=>{renderHistory();status.textContent="Deployment summary refreshed.";});window.addEventListener("resize",fitGrid);}
function bindDeploy(){wrap.addEventListener("dragover",e=>e.preventDefault());wrap.addEventListener("drop",e=>{e.preventDefault();addNode(e.dataTransfer.getData("sensor/type")||selectedType,e.clientX,e.clientY);});wrap.addEventListener("dblclick",e=>addNode(selectedType,e.clientX,e.clientY));}
function init(){applyTheme();addPalette();addBase();nodes.forEach(renderNode);recomputeEdges();drawEdges();stats();updateNotes();history=loadHistory();renderHistory();bindPan();bindControls();bindDeploy();fitGrid();}
init();
</script>
"""
    components.html(html.replace("__PAYLOAD__", payload_json), height=1320)


st.title("Wireless Sensor Network Visualizer")
st.caption("Interactive WSN simulator with persistent deployment runs.")

icons, missing_icons = load_icon_data()
if missing_icons:
    st.warning(
        "Some sensor icons were not found. Missing files: "
        + ", ".join(sorted(missing_icons))
    )

sim = MockSim()
render_interactive_network(sim, icons, TOPOLOGY_THEMES)
