"use strict";

const $ = (name) => document.getElementById(name);
let selectedId = null;
let activeDate = null;
let currentData = null;
let chatHistory = [];
let busy = false;

function node(tag, text, cls) {
  const e = document.createElement(tag);
  if (text !== undefined && text !== null) e.textContent = String(text);
  if (cls) e.className = cls;
  return e;
}
function fmt(value, decimal = 1) {
  const n = Number(value);
  return value === null || value === undefined || value === "" || !Number.isFinite(n) ? "—" : n.toFixed(decimal);
}
function dateOnly(raw) {
  const m = String(raw || "").match(/^\d{4}-\d{2}-\d{2}/);
  return m ? m[0] : null;
}
function hhmm(raw) {
  const m = String(raw || "").match(/(\d{2}:\d{2})/);
  return m ? m[1] : String(raw || "").slice(-5);
}
function parseDate(raw) {
  const value = String(raw || "").replace(" ", "T");
  const d = new Date(value);
  return Number.isFinite(d.getTime()) ? d : null;
}
function dateLabel(raw) {
  const text = String(raw || "").replace("T", " ");
  if (/^\d{4}-\d{2}-\d{2}/.test(text)) {
    const [y,m,d] = text.slice(0,10).split("-");
    return `${d}/${m}/${y}${text.length>10 ? " " + text.slice(11,19) : ""}`;
  }
  return text || "—";
}
function svgChild(svg,tag,attrs={},text){
  const n=document.createElementNS("http://www.w3.org/2000/svg",tag);
  for(const [k,v] of Object.entries(attrs))n.setAttribute(k,String(v));
  if(text!==undefined)n.textContent=String(text);
  svg.append(n);return n;
}

function plot(series, selected) {
  const root = $("chart"); root.replaceChildren();
  if (!Array.isArray(series) || series.length < 2) {
    root.append(node("div", "No hay mediciones de potencia para el día seleccionado.", "chart-empty"));
    return;
  }
  const pointsRaw = series.map((p,i) => ({t:parseDate(p.x)?.getTime() ?? i*60000, v:Number(p.y), raw:p.x})).filter(p=>Number.isFinite(p.v));
  if(pointsRaw.length<2){root.append(node("div","No hay datos válidos para graficar.","chart-empty"));return;}
  const W=750,H=285,L=51,T=20,R=16,B=39, PW=W-L-R,PH=H-T-B;
  const minT=Math.min(...pointsRaw.map(p=>p.t)),maxT=Math.max(...pointsRaw.map(p=>p.t));
  const spanT=Math.max(1,maxT-minT);
  const maxV=Math.max(10,Math.ceil(Math.max(...pointsRaw.map(p=>p.v))*1.1/10)*10);
  const x=p=>L+(p.t-minT)/spanT*PW, y=p=>T+PH-Math.max(0,p.v)/maxV*PH;
  const svg=document.createElementNS("http://www.w3.org/2000/svg","svg");
  svg.setAttribute("viewBox",`0 0 ${W} ${H}`);svg.setAttribute("preserveAspectRatio","none");
  const defs=svgChild(svg,"defs");const g=document.createElementNS("http://www.w3.org/2000/svg","linearGradient");g.id="powerFill";g.setAttribute("x1","0");g.setAttribute("y1","0");g.setAttribute("x2","0");g.setAttribute("y2","1");
  [["0%","#68bb75",".33"],["100%","#cce6c5",".08"]].forEach(([offset,color,opacity])=>{const s=document.createElementNS("http://www.w3.org/2000/svg","stop");s.setAttribute("offset",offset);s.setAttribute("stop-color",color);s.setAttribute("stop-opacity",opacity);g.append(s);});defs.append(g);
  for(let i=0;i<=5;i++){
    const yy=T+PH*i/5;
    svgChild(svg,"line",{x1:L,x2:W-R,y1:yy,y2:yy,stroke:"#e4e7df","stroke-width":1});
    svgChild(svg,"text",{x:L-12,y:yy+4,"text-anchor":"end",fill:"#708077","font-size":11},Math.round(maxV*(5-i)/5));
  }
  const d=pointsRaw.map((p,i)=>`${i===0?"M":"L"} ${x(p).toFixed(2)} ${y(p).toFixed(2)}`).join(" ");
  svgChild(svg,"path",{d:`${d} L ${x(pointsRaw.at(-1))} ${T+PH} L ${x(pointsRaw[0])} ${T+PH} Z`,fill:"url(#powerFill)"});
  svgChild(svg,"path",{d,fill:"none",stroke:"#287e38","stroke-width":2.8,"stroke-linecap":"round","stroke-linejoin":"round"});
  svgChild(svg,"line",{x1:L,x2:W-R,y1:T+PH,y2:T+PH,stroke:"#96a098","stroke-width":1});
  for(let i=0;i<=5;i++){
    const t=minT+(maxT-minT)*i/5;
    const tick=new Date(t);
    const label=Number.isFinite(tick.getTime()) ? `${String(tick.getHours()).padStart(2,"0")}:${String(tick.getMinutes()).padStart(2,"0")}` : hhmm(pointsRaw[Math.round(i*(pointsRaw.length-1)/5)].raw);
    svgChild(svg,"text",{x:L+i*PW/5,y:H-13,"text-anchor":"middle",fill:"#556559","font-size":11},label);
  }
  svgChild(svg,"text",{x:11,y:11,fill:"#748373","font-size":11},"kW");
  // Highlight only if the selected anomaly actually lies within the plotted time interval.
  const eventTime=selected?parseDate(selected.fecha)?.getTime():null;
  if(eventTime && eventTime>=minT-180000 && eventTime<=maxT+180000){
    const nearest=pointsRaw.reduce((best,p)=>Math.abs(p.t-eventTime)<Math.abs(best.t-eventTime)?p:best,pointsRaw[0]);
    if(Math.abs(nearest.t-eventTime)<=15*60*1000){
      const xx=x(nearest), yy=y(nearest);
      svgChild(svg,"rect",{x:Math.max(L,xx-10),y:T,width:20,height:PH,fill:"#f2a43c","fill-opacity":.13});
      svgChild(svg,"line",{x1:xx,x2:xx,y1:T,y2:T+PH,stroke:"#edac43","stroke-width":1.3,"stroke-dasharray":"4 4"});
      svgChild(svg,"circle",{cx:xx,cy:yy,r:5.7,fill:"#eb9f29",stroke:"#fff","stroke-width":2});
    }
  }
  root.append(svg);
}
function selectedEvent(){return (currentData?.eventos||[]).find(e=>e.id===selectedId) || null;}
function showDetails(event) {
  if (!event) {
    selectedId=null;
    $("selected-alert").textContent="No hay anomalías para esta fecha";
    ["selected-date","selected-inverter","selected-duration","tev-score","ai-explanation","ai-recommendation"].forEach(k=>$(k).textContent="—");
    $("ai-causes").replaceChildren();
  } else {
    selectedId=event.id;
    $("selected-alert").textContent="⚠  "+event.titulo;
    $("selected-date").textContent=dateLabel(event.fecha);
    $("selected-inverter").textContent=event.inversor ?? "—";
    $("selected-duration").textContent=event.duracion==null ? "No determinada" : `${fmt(event.duracion,2)} min${event.duracion_tipo==="cota_superior"?" (cota superior)":""}`;
    $("tev-score").textContent=fmt(event.puntuacion,4);
    $("ai-explanation").textContent=event.explicacion || "Análisis no disponible.";
    const list=$("ai-causes");list.replaceChildren();
    if(Array.isArray(event.causas)&&event.causas.length){event.causas.forEach(c=>list.append(node("li",typeof c==="string"?c:JSON.stringify(c))))}
    else list.append(node("li","No se registraron hipótesis."));
    $("ai-recommendation").textContent=event.recomendacion || "No hay una recomendación registrada.";
  }
  document.querySelectorAll("#alerts-body tr").forEach(tr=>tr.classList.toggle("selected",tr.dataset.id===selectedId));
  plot(currentData?.serie||[],event);
}
function showAlerts(events){
  const body=$("alerts-body");body.replaceChildren();
  if(!events.length){const tr=node("tr"),td=node("td","No se encontraron anomalías para esta fecha.");td.colSpan=4;tr.append(td);body.append(tr);showDetails(null);return;}
  events.slice(0,30).forEach(e=>{
    const tr=node("tr",undefined,"clickable");tr.dataset.id=e.id;tr.tabIndex=0;
    const desc=e.explicacion && e.estado_ia==="completo" ? e.explicacion.slice(0,77)+(e.explicacion.length>77?"…":"") : "Sin interpretación disponible";
    tr.append(node("td",dateLabel(e.fecha)),node("td",e.titulo),node("td",desc));
    const status=node("td");status.append(node("span",e.estado_ia==="completo"?"Analizada":"Pendiente",`pill ${e.estado_ia==="completo"?"ok":"wait"}`));tr.append(status);
    tr.addEventListener("click",()=>chooseEvent(e));tr.addEventListener("keydown",ev=>{if(ev.key==="Enter"||ev.key===" "){ev.preventDefault();chooseEvent(e);}});
    body.append(tr);
  });
  showDetails(events.find(e=>e.id===selectedId)||events[0]);
}
function chooseEvent(event){
  const changed=selectedId!==event.id;showDetails(event);
  if(changed){chatHistory=[];appendMessage("Ahora estoy consultando: "+event.titulo+" ("+dateLabel(event.fecha)+"). Podés preguntarme sobre este evento.","assistant");}
}
function showReadings(data){
  const body=$("readings-body");body.replaceChildren();
  if(!Array.isArray(data.corrientes)||!data.corrientes.length){const tr=node("tr"),td=node("td","Sin mediciones disponibles");td.colSpan=3;tr.append(td);body.append(tr);return;}
  data.corrientes.slice(0,4).forEach((amp,i)=>{
    const tr=node("tr");tr.append(node("td",`CC${i+1}`),node("td",fmt(amp,2)),node("td",fmt(data.tensiones?.[i],1)));body.append(tr);
  });
}
async function update(){
  const url="/api/estado"+(activeDate?"?fecha="+encodeURIComponent(activeDate):"");
  try{
    const response=await fetch(url);
    const data=await response.json();currentData=data;
    const demo=data.modo==="demo";
    $("header-status").textContent=demo?"Modo de demostración":"Archivos locales";
    $("header-clock").textContent="Inversor 2 · "+(data.fecha_activa||"sin fecha");
    $("notice").textContent=(data.nota||"")+(data.aviso_csv?" "+data.aviso_csv:"");
    $("power").replaceChildren(document.createTextNode(fmt(data.potencia_kw,1)+" "),node("small","kW"));
    $("avg-voltage").replaceChildren(document.createTextNode(fmt(data.tension_promedio,1)+" "),node("small","V"));
    $("avg-current").replaceChildren(document.createTextNode(fmt(data.corriente_promedio,2)+" "),node("small","A"));
    $("energy").replaceChildren(document.createTextNode(fmt(data.energia_estimada_kwh,1)+" "),node("small","kWh"));
    $("energy-note").textContent=data.energia_estimada_kwh==null?"Sin energía calculada":data.energia_parcial?"Estimación parcial (hay intervalos sin datos)":"Estimación por integración de muestras";
    $("data-state").textContent=data.estado_datos||"—";
    $("last-measurement").textContent="Última medición: "+dateLabel(data.ultima_medicion||"");
    if(data.fecha_activa&&!activeDate)$("day-picker").value=data.fecha_activa;
    $("chart-note").textContent=demo?"DEMO: curva ilustrativa, no datos reales.":"Serie del archivo CSV configurado. La fecha del gráfico y las alertas corresponde al día seleccionado.";
    showReadings(data);showAlerts(data.eventos||[]);
  }catch(e){$("header-status").textContent="Error de conexión";$("notice").textContent="No fue posible consultar el servidor de SolarCare AI.";console.error(e);}
}
function changeDate(days){
  const input=$("day-picker");if(!input.value)return;
  const d=new Date(input.value+"T12:00:00");if(!Number.isFinite(d.getTime()))return;
  d.setDate(d.getDate()+days);activeDate=`${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,"0")}-${String(d.getDate()).padStart(2,"0")}`;
  input.value=activeDate;selectedId=null;chatHistory=[];update();
}
function appendMessage(text, role, isError=false){
  const wrap=node("div",undefined,`message ${role==="user"?"user-message":isError?"error-message":"assistant-message"}`);
  if(role!=="user")wrap.append(node("span","✦","message-avatar"));
  const burbuja=node("div",undefined,"bubble");
  String(text).split(/(\*\*[^*]+\*\*)/g).forEach(p=>{
    if(p.startsWith("**") && p.endsWith("**"))
      burbuja.append(node("strong",p.slice(2,-2)));
    else
      burbuja.append(document.createTextNode(p));
  });
  wrap.append(burbuja);$("chat-messages").append(wrap);
  $("chat-messages").scrollTop=$("chat-messages").scrollHeight;
}
async function sendQuestion(ev){
  ev.preventDefault();if(busy)return;
  const input=$("chat-question"),question=input.value.trim();if(!question)return;
  appendMessage(question,"user");input.value="";busy=true;$("send-chat").disabled=true;
  const loading=node("div","Consultando Qwen3...","bubble");const box=node("div",undefined,"message assistant-message");box.append(node("span","✦","message-avatar"),loading);$("chat-messages").append(box);$("chat-messages").scrollTop=$("chat-messages").scrollHeight;
  try{
    const response=await fetch("/api/chat",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({pregunta:question,fecha:activeDate||currentData?.fecha_activa||null,id_evento:selectedId,historial:chatHistory})});
    const data=await response.json();box.remove();
    if(!response.ok)throw new Error(data.error||"No se pudo consultar Qwen3.");
    appendMessage(data.respuesta||"No se recibió ninguna respuesta.","assistant");
    chatHistory.push({role:"user",content:question},{role:"assistant",content:data.respuesta});
    chatHistory=chatHistory.slice(-8);$("chat-status").textContent="QWEN3 · RESPONDIÓ";
  }catch(error){box.remove();appendMessage(error.message||"El modelo no respondió.","assistant",true);$("chat-status").textContent="QWEN3 · SIN CONEXIÓN";}
  finally{busy=false;$("send-chat").disabled=false;input.focus();}
}

$("day-picker").addEventListener("change",ev=>{activeDate=ev.target.value||null;selectedId=null;chatHistory=[];update();});
$("prev-day").addEventListener("click",()=>changeDate(-1));
$("next-day").addEventListener("click",()=>changeDate(1));
$("chat-form").addEventListener("submit",sendQuestion);
document.querySelectorAll(".nav-item").forEach(link=>link.addEventListener("click",()=>{document.querySelectorAll(".nav-item").forEach(x=>x.classList.remove("active"));link.classList.add("active");}));
update();setInterval(update,25000);
