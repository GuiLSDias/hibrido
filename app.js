// Navegação de abas + slides + tabela de resultados (dados embutidos de results_summary.csv para funcionar via file://)
const ROWS = [[25, "exato", 3, 3, 0.02, 0.0, 0.0], [25, "exato+warm", 3, 3, 2.02, 0.0, 0.0], [25, "heuristica", 0, 3, 20.0, 0.0, 0.0], [25, "hibrido", 3, 3, 2.02, 0.0, 0.0], [50, "exato", 3, 3, 0.09, 0.0, 0.0], [50, "exato+warm", 3, 3, 2.08, 0.0, 0.0], [50, "heuristica", 0, 3, 20.0, 0.0, 0.0], [50, "hibrido", 3, 3, 2.17, 0.0, 0.0], [100, "exato", 3, 3, 0.34, 0.0, 0.0], [100, "exato+warm", 3, 3, 2.25, 0.0, 0.0], [100, "heuristica", 0, 3, 20.0, 5e-05, 0.51], [100, "hibrido", 3, 3, 2.47, 0.0, 0.0], [200, "exato", 3, 3, 2.31, 0.0, 0.0], [200, "exato+warm", 3, 3, 2.42, 0.0, 0.0], [200, "heuristica", 0, 3, 20.0, 1e-05, 0.05], [200, "hibrido", 3, 3, 2.72, 0.0, 0.0], [400, "exato", 1, 3, 16.94, 0.0346, 0.0], [400, "exato+warm", 0, 3, 20.01, 0.0346, 0.0], [400, "heuristica", 0, 3, 20.0, 0.03462, 0.18], [400, "hibrido", 0, 3, 20.0, 0.0346, 0.0], [800, "exato", 0, 3, 20.01, 0.02902, 0.0], [800, "exato+warm", 0, 3, 20.01, 0.02902, 0.0], [800, "heuristica", 0, 3, 20.0, 0.02902, 0.0], [800, "hibrido", 0, 3, 20.01, 0.02902, 0.0]];
const NAMES = {heuristica:"Heurística (Tabu)", exato:"Exato (HiGHS)", "exato+warm":"Exato + warm start", hibrido:"Híbrido"};
document.querySelectorAll("nav button").forEach(b=>b.onclick=()=>{
  document.querySelectorAll("nav button").forEach(x=>x.classList.remove("active")); b.classList.add("active");
  document.querySelectorAll(".view").forEach(v=>v.classList.toggle("active",v.id===b.dataset.t));
});
const slides=[...document.querySelectorAll(".slide")]; let cur=0;
function show(i){cur=Math.max(0,Math.min(slides.length-1,i));slides.forEach((s,k)=>s.classList.toggle("active",k===cur));
  document.getElementById("pos").textContent=`${cur+1} / ${slides.length}`;}
document.getElementById("prev").onclick=()=>show(cur-1);document.getElementById("next").onclick=()=>show(cur+1);
document.addEventListener("keydown",e=>{if(e.key==="ArrowRight"||e.key===" ")show(cur+1);if(e.key==="ArrowLeft")show(cur-1);});
show(0);
const tb=document.querySelector("#tbl tbody");
ROWS.forEach(([n,m,prov,reps,t,gap,pp])=>{const tr=document.createElement("tr");
  tr.innerHTML=`<td>${n}</td><td>${NAMES[m]}</td><td class="${prov===reps?'ok':prov?'warn':'bad'}">${prov}/${reps}</td><td>${t.toFixed(2)}</td><td>${gap.toFixed(5)}</td><td>${pp.toFixed(2)}</td>`;tb.appendChild(tr);});
