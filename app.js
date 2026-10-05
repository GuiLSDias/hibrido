'use strict';

const data = window.EXPERIMENT;
if (!data) throw new Error('Execute python analyze.py para gerar os dados da apresentação.');

const { metadata: m, summary: rows, conclusions: c, names, runs } = data;

const set = (id, text) => {
  const el = document.getElementById(id);
  if (el) el.textContent = text;
};

// 1. Fill Metadata & Slide Conclusions
set('sizes-count', m.sizes.length);
set('reps-count', m.reps);
set('budget', `${m.T} s`);
set('density', String(m.density).replace('.', ','));
set('sizes-list', m.sizes.join(', '));
set('solver-version', m.highs);
set('transition', c.transition);
set('answer1', c.transition);

set('fo-result', `O Fix-and-Optimize crítico produziu ${c.fo_improvements} reduções de cores nas execuções principais. A fase exata final continua necessária para buscar a prova global.`);

const proofSentence = `Na comparação das mesmas instâncias, o híbrido provou ${c.proof_gains.length} casos em que o exato não provou; o exato provou ${c.proof_losses.length} casos em que o híbrido não provou.`;
const allProof = method => rows.filter(r => r.metodo === method && r.provadas === r.replicas).map(r => r.N);
const e = allProof('exato'), h = allProof('hibrido');
const maxE = e.length ? Math.max(...e) : null, maxH = h.length ? Math.max(...h) : null;
set('answer2', `${proofSentence} Maior tamanho com todas as réplicas provadas: exato ${maxE ?? 'nenhum'}; híbrido ${maxH ?? 'nenhum'}.`);

set('answer3', c.quality_comparison.map(r => `N=${r.N}: mesma quantidade de cores em ${r.iguais}/${r.replicas}.`).join(' ') + ' Igualar a solução não equivale a obter uma prova.');

const easy = rows.filter(r => r.metodo === 'exato' && r.provadas === r.replicas).map(r => r.N);
const comparable = easy.filter(n => rows.some(r => r.N === n && r.metodo === 'hibrido' && r.provadas === r.replicas));
const faster = comparable.filter(n => {
  const hRow = rows.find(r => r.N === n && r.metodo === 'hibrido');
  const eRow = rows.find(r => r.N === n && r.metodo === 'exato');
  return hRow && eRow && hRow.tempo_medio_s < eRow.tempo_medio_s;
});
const fasterFO = c.fo_comparison.filter(r => r.hibrido_mais_rapido).map(r => r.N);

set('answer4', `Entre os tamanhos em que ambos provaram todas as réplicas (${comparable.join(', ') || 'nenhum'}), o híbrido teve menor tempo total médio em ${faster.length ? faster.join(', ') : 'nenhum'}. F&O reduziu cores ${c.fo_improvements} vezes. Frente ao warm start sozinho, a média do híbrido foi menor em ${fasterFO.length ? fasterFO.join(', ') : 'nenhum tamanho'}. Variações pequenas não provam aceleração causal do F&O.`);

set('results-caption', `${c.instances} grafos · ${m.reps} réplicas por tamanho · T=${m.T} s · ${c.runs} execuções incluindo a ablação.`);
set('timing-note', `Máximo excesso registrado sobre o limite nominal: ${c.max_overrun_s.toFixed(3)} s. O tempo inclui preparação e extração; o limite interno do solver recebe apenas o tempo restante.`);

// 2. Slide Navigation System
const slides = [...document.querySelectorAll('.slide')];
const dotsContainer = document.getElementById('dots-container');
let currentSlide = 0;

// Create slide indicator dots
if (dotsContainer) {
  dotsContainer.innerHTML = '';
  slides.forEach((_, idx) => {
    const dot = document.createElement('div');
    dot.className = `dot ${idx === 0 ? 'active' : ''}`;
    dot.title = `Ir para slide ${idx + 1}`;
    dot.onclick = () => showSlide(idx);
    dotsContainer.appendChild(dot);
  });
}

function showSlide(i) {
  currentSlide = Math.max(0, Math.min(slides.length - 1, i));
  slides.forEach((el, k) => el.classList.toggle('active', k === currentSlide));
  set('pos', `${currentSlide + 1} / ${slides.length}`);
  
  const prevBtn = document.getElementById('prev');
  const nextBtn = document.getElementById('next');
  if (prevBtn) prevBtn.disabled = currentSlide === 0;
  if (nextBtn) nextBtn.disabled = currentSlide === slides.length - 1;

  if (dotsContainer) {
    const dots = dotsContainer.querySelectorAll('.dot');
    dots.forEach((dot, k) => dot.classList.toggle('active', k === currentSlide));
  }
}

document.getElementById('prev').onclick = () => showSlide(currentSlide - 1);
document.getElementById('next').onclick = () => showSlide(currentSlide + 1);

// Views Navigation (Header Tabs)
document.querySelectorAll('nav button').forEach(button => {
  button.onclick = () => {
    document.querySelectorAll('nav button').forEach(b => b.classList.toggle('active', b === button));
    document.querySelectorAll('.view').forEach(v => v.classList.toggle('active', v.id === button.dataset.view));
  };
});

// Keyboard Navigation
document.addEventListener('keydown', event => {
  if (!document.getElementById('slides').classList.contains('active')) return;
  if (event.key === 'ArrowRight' || event.key === ' ') {
    event.preventDefault();
    showSlide(currentSlide + 1);
  }
  if (event.key === 'ArrowLeft') {
    event.preventDefault();
    showSlide(currentSlide - 1);
  }
});

// Fullscreen Toggle
document.getElementById('full').onclick = () => {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen().catch(() => {});
  } else {
    document.exitFullscreen().catch(() => {});
  }
};

// 3. Render Summary & Detailed Tables with Filters
let summarySortCol = 'N';
let summarySortAsc = true;

function renderSummaryTable() {
  const tbody = document.getElementById('table-body');
  if (!tbody) return;
  tbody.innerHTML = '';

  const sizeFilter = document.getElementById('filter-size').value;
  const methodFilter = document.getElementById('filter-method').value;
  const search = document.getElementById('search-input').value.toLowerCase().trim();

  let filtered = rows.filter(r => {
    if (sizeFilter !== 'all' && String(r.N) !== sizeFilter) return false;
    if (methodFilter !== 'all' && r.metodo !== methodFilter) return false;
    if (search) {
      const text = `${r.N} ${names[r.metodo]} ${r.provadas}`.toLowerCase();
      if (!text.includes(search)) return false;
    }
    return true;
  });

  // Sort
  filtered.sort((a, b) => {
    let valA = a[summarySortCol];
    let valB = b[summarySortCol];
    if (typeof valA === 'string') {
      return summarySortAsc ? valA.localeCompare(valB) : valB.localeCompare(valA);
    }
    return summarySortAsc ? valA - valB : valB - valA;
  });

  for (const r of filtered) {
    const tr = document.createElement('tr');
    const cells = [
      r.N,
      names[r.metodo] || r.metodo,
      `${r.provadas}/${r.replicas}`,
      r.cores_media.toFixed(2),
      r.tempo_medio_s.toFixed(3),
      r.gap_certificado_pct.toFixed(2),
      r.gap_primal_pct.toFixed(2)
    ];

    cells.forEach((val, i) => {
      const td = document.createElement('td');
      td.textContent = val;
      if (i === 2) td.className = r.provadas === r.replicas ? 'proof' : 'none';
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  }
}

function renderDetailedTable() {
  const tbody = document.getElementById('detailed-table-body');
  if (!tbody || !runs) return;
  tbody.innerHTML = '';

  const sizeFilter = document.getElementById('filter-size').value;
  const methodFilter = document.getElementById('filter-method').value;
  const search = document.getElementById('search-input').value.toLowerCase().trim();

  const runKeys = Object.keys(runs);
  for (const key of runKeys) {
    const r = runs[key].row;
    if (sizeFilter !== 'all' && String(r.N) !== sizeFilter) continue;
    if (methodFilter !== 'all' && r.metodo !== methodFilter) continue;
    if (search) {
      const text = `${r.N} rep${r.rep} ${names[r.metodo]} ${r.status}`.toLowerCase();
      if (!text.includes(search)) continue;
    }

    const tr = document.createElement('tr');
    tr.className = 'clickable-row';
    tr.onclick = () => openRunInspector(key);

    const isProven = r.optimal;
    const badgeClass = r.metodo.startsWith('hibrido') ? 'badge-hybrid' :
                       r.metodo === 'exato+warm' ? 'badge-warm' :
                       r.metodo === 'exato' ? 'badge-exact' : 'badge-tabu';

    tr.innerHTML = `
      <td><strong>${r.N}</strong></td>
      <td>Rep ${r.rep}</td>
      <td><span class="badge ${badgeClass}">${names[r.metodo] || r.metodo}</span></td>
      <td><strong>${r.obj}</strong> cores</td>
      <td>${r.bound.toFixed(2)}</td>
      <td class="${isProven ? 'proof' : 'none'}">${isProven ? '✓ Sim' : '✗ Não'}</td>
      <td>${r.tempo_s.toFixed(3)}s</td>
      <td><small>${r.status}</small></td>
      <td><button class="btn-ctrl" style="padding:4px 8px; font-size:0.75rem;">Inspecionar</button></td>
    `;
    tbody.appendChild(tr);
  }
}

// Handle View Mode & Filters
const viewModeSelect = document.getElementById('view-mode-select');
if (viewModeSelect) {
  viewModeSelect.onchange = () => {
    const isSummary = viewModeSelect.value === 'summary';
    document.getElementById('summary-table-container').style.display = isSummary ? 'block' : 'none';
    document.getElementById('detailed-table-container').style.display = isSummary ? 'none' : 'block';
    if (isSummary) renderSummaryTable(); else renderDetailedTable();
  };
}

['filter-size', 'filter-method'].forEach(id => {
  const el = document.getElementById(id);
  if (el) el.onchange = () => { renderSummaryTable(); renderDetailedTable(); };
});

const searchInput = document.getElementById('search-input');
if (searchInput) {
  searchInput.oninput = () => { renderSummaryTable(); renderDetailedTable(); };
}

// Table Sort Headers
document.querySelectorAll('th[data-sort]').forEach(th => {
  th.onclick = () => {
    const col = th.dataset.sort;
    if (summarySortCol === col) {
      summarySortAsc = !summarySortAsc;
    } else {
      summarySortCol = col;
      summarySortAsc = true;
    }
    renderSummaryTable();
  };
});

// 4. Modal Inspectors & Lightbox
function openRunInspector(key) {
  const item = runs[key];
  if (!item) return;
  const { row: r, colors, trace, fo_log } = item;

  const modal = document.getElementById('inspector-modal');
  set('modal-run-title', `Execução N=${r.N}, Réplica ${r.rep} — ${names[r.metodo] || r.metodo}`);

  const detailsDiv = document.getElementById('modal-run-details');
  if (detailsDiv) {
    let traceRows = trace.map(t => `<tr><td>${t.t.toFixed(3)}s</td><td><strong>${t.cores}</strong> cores</td><td>${t.fase}</td></tr>`).join('');
    let foRows = (fo_log || []).map((f, i) => `<tr><td>Iter ${i+1}</td><td>K=${f.K}</td><td>${f.before} → ${f.after}</td><td>${f.time.toFixed(3)}s</td><td>${f.status}</td></tr>`).join('');

    // Color distribution count
    const colorCounts = {};
    colors.forEach(c => { colorCounts[c] = (colorCounts[c] || 0) + 1; });
    const colorPills = Object.entries(colorCounts).map(([c, count]) => 
      `<span style="display:inline-block; padding:4px 10px; margin:3px; background:#1e2c46; border-radius:12px; border:1px solid #38bdf8; font-size:0.85rem;">Cor ${c}: <strong>${count}</strong> vértices</span>`
    ).join('');

    detailsDiv.innerHTML = `
      <div class="grid two" style="margin-bottom:20px;">
        <div class="card compact">
          <h3>Métricas Principais</h3>
          <p><strong>Cores (Objetivo):</strong> ${r.obj}</p>
          <p><strong>Lower Bound:</strong> ${r.bound.toFixed(2)}</p>
          <p><strong>Ótimo Provado:</strong> ${r.optimal ? 'Sim (Status Optimal)' : 'Não'}</p>
          <p><strong>Tempo Total:</strong> ${r.tempo_s.toFixed(3)} s</p>
          <p><strong>Status:</strong> ${r.status}</p>
        </div>
        <div class="card compact">
          <h3>Fases e Warm Start</h3>
          <p><strong>Warm Start Aceito:</strong> ${r.warm_accepted ? 'Sim' : 'Não'}</p>
          <p><strong>Tempo Warm Start:</strong> ${r.warm_s.toFixed(3)} s</p>
          <p><strong>Tempo F&O:</strong> ${r.fo_s.toFixed(3)} s (${r.fo_sub} subproblemas, ${r.fo_imp} melhorias)</p>
          <p><strong>Tempo Solver MIP:</strong> ${r.solver_s.toFixed(3)} s</p>
        </div>
      </div>

      <div class="card compact" style="margin-bottom:20px;">
        <h3>Distribuição da Coloração (${colors.length} vértices)</h3>
        <div>${colorPills}</div>
      </div>

      ${trace.length ? `
      <div class="card compact" style="margin-bottom:20px;">
        <h3>Histórico de Incumbentes (Convergência)</h3>
        <div class="table-wrap" style="max-height:200px;">
          <table>
            <thead><tr><th>Tempo (s)</th><th>Cores</th><th>Fase</th></tr></thead>
            <tbody>${traceRows}</tbody>
          </table>
        </div>
      </div>` : ''}

      ${fo_log && fo_log.length ? `
      <div class="card compact">
        <h3>Log do Fix-and-Optimize (${fo_log.length} passos)</h3>
        <div class="table-wrap" style="max-height:200px;">
          <table>
            <thead><tr><th>Passo</th><th>Janela K</th><th>Cores (Antes → Depois)</th><th>Tempo</th><th>Status</th></tr></thead>
            <tbody>${foRows}</tbody>
          </table>
        </div>
      </div>` : ''}
    `;
  }

  modal.classList.add('active');
}

window.closeInspector = function(e) {
  if (e.target.id === 'inspector-modal') {
    document.getElementById('inspector-modal').classList.remove('active');
  }
};
window.closeInspectorDirect = function() {
  document.getElementById('inspector-modal').classList.remove('active');
};

// Lightbox for Charts
document.querySelectorAll('.fig').forEach(img => {
  img.onclick = () => {
    const modal = document.getElementById('lightbox-modal');
    const lightboxImg = document.getElementById('lightbox-img');
    const caption = document.getElementById('lightbox-caption');
    if (lightboxImg) lightboxImg.src = img.src;
    if (caption) caption.textContent = img.alt || img.title || '';
    if (modal) modal.classList.add('active');
  };
});

window.closeLightbox = function(e) {
  if (e.target.id === 'lightbox-modal') {
    document.getElementById('lightbox-modal').classList.remove('active');
  }
};
window.closeLightboxDirect = function() {
  document.getElementById('lightbox-modal').classList.remove('active');
};

// Copy Code Button
window.copyCode = function(button) {
  const pre = button.parentElement;
  const code = pre.querySelector('code');
  if (code) {
    navigator.clipboard.writeText(code.textContent.trim()).then(() => {
      const orig = button.textContent;
      button.textContent = 'Copiado!';
      setTimeout(() => { button.textContent = orig; }, 2000);
    });
  }
};

// SVG Hero Graph Interactive Hover Tooltips
document.querySelectorAll('.graph circle').forEach(circle => {
  circle.addEventListener('mouseenter', () => {
    const node = circle.dataset.node;
    const color = circle.dataset.color;
    circle.setAttribute('r', '30');
  });
  circle.addEventListener('mouseleave', () => {
    circle.setAttribute('r', '26');
  });
});

// Initial Setup
showSlide(0);
renderSummaryTable();
