// ================================================================
// PDA Simulation -- Frontend Controller (ASCII-safe)
// ================================================================

const TOPICS = ['arithmetic', 'hanoi', 'html', 'nlp'];
const PLAY_INTERVAL_MS = 850;

// Per-topic runtime state
const sim = {};
TOPICS.forEach(t => { sim[t] = { steps: [], cursor: 0, timer: null }; });

// State machine node definitions per topic
const STATE_DEFS = {
  arithmetic: { nodes: ['q0', 'q_op', 'q_f'],         final: ['q_f'],  error: []        },
  hanoi:      { nodes: ['q0', 'q1', 'q_f'],            final: ['q_f'],  error: []        },
  html:       { nodes: ['q0', 'q_f', 'q_err'],         final: ['q_f'],  error: ['q_err'] },
  nlp:        { nodes: ['q0', 'q1', 'q_f'],            final: ['q_f'],  error: []        },
};

// ----------------------------------------------------------------
// Boot: attach all event listeners after DOM is ready
// ----------------------------------------------------------------
document.addEventListener('DOMContentLoaded', function () {

  // Tab buttons
  document.querySelectorAll('.tab-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var topic = btn.dataset.topic;
      document.querySelectorAll('.tab-btn').forEach(function (b) {
        b.classList.toggle('active', b === btn);
        b.setAttribute('aria-selected', b === btn ? 'true' : 'false');
      });
      document.querySelectorAll('.topic-panel').forEach(function (p) {
        p.classList.toggle('active', p.id === 'panel-' + topic);
      });
    });
  });

  // Run buttons
  TOPICS.forEach(function (topic) {
    var runBtn = document.getElementById(topic + '-run');
    if (runBtn) runBtn.addEventListener('click', function () { runTopic(topic); });

    var prevBtn = document.getElementById('prev-' + topic);
    if (prevBtn) prevBtn.addEventListener('click', function () { stepNav(topic, -1); });

    var nextBtn = document.getElementById('next-' + topic);
    if (nextBtn) nextBtn.addEventListener('click', function () { stepNav(topic, 1); });

    var playBtn = document.getElementById('play-' + topic);
    if (playBtn) playBtn.addEventListener('click', function () { togglePlay(topic); });

    var resetBtn = document.getElementById('reset-' + topic);
    if (resetBtn) resetBtn.addEventListener('click', function () { resetTopic(topic); });

    var firstBtn = document.getElementById('first-' + topic);
    if (firstBtn) firstBtn.addEventListener('click', function () { goTo(topic, 0); });

    var lastBtn = document.getElementById('last-' + topic);
    if (lastBtn) lastBtn.addEventListener('click', function () { goTo(topic, sim[topic].steps.length - 1); });
  });

  // Enter key on text inputs
  var arithInput = document.getElementById('arith-input');
  if (arithInput) arithInput.addEventListener('keydown', function (e) { if (e.key === 'Enter') runTopic('arithmetic'); });

  var nlpInput = document.getElementById('nlp-input');
  if (nlpInput) nlpInput.addEventListener('keydown', function (e) { if (e.key === 'Enter') runTopic('nlp'); });
});

// ----------------------------------------------------------------
// Run a topic -- fetch steps from Flask API
// ----------------------------------------------------------------
function runTopic(topic) {
  stopPlay(topic);

  var payload = getPayload(topic);
  if (!payload) return;

  var errBox  = document.getElementById('err-' + topic);
  var simArea = document.getElementById('sim-' + topic);
  errBox.style.display  = 'none';
  simArea.style.display = 'none';

  var runBtn = document.getElementById(topic + '-run');
  runBtn.textContent = 'Running...';
  runBtn.disabled = true;

  var endpoints = { arithmetic: '/api/arithmetic', hanoi: '/api/hanoi', html: '/api/html', nlp: '/api/nlp' };

  fetch(endpoints[topic], {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
  .then(function (res) { return res.json().then(function (data) { return { ok: res.ok, data: data }; }); })
  .then(function (r) {
    if (!r.ok || r.data.error) throw new Error(r.data.error || 'Server error');

    sim[topic].steps  = r.data.steps;
    sim[topic].cursor = 0;

    buildStateDiagram(topic);

    // Init Hanoi peg visualization on first load
    if (topic === 'hanoi' && r.data.steps.length) {
      initHanoiViz(r.data.steps[0]);
    }

    buildLogTable(topic, r.data.steps);
    simArea.style.display = 'block';
    renderStep(topic, 0);
  })
  .catch(function (err) {
    errBox.textContent = 'Error: ' + err.message;
    errBox.style.display = 'block';
  })
  .finally(function () {
    runBtn.textContent = 'Run Simulation';
    runBtn.disabled = false;
  });
}

// ----------------------------------------------------------------
// Build request payload from UI inputs
// ----------------------------------------------------------------
function getPayload(topic) {
  if (topic === 'arithmetic') {
    var expr = document.getElementById('arith-input').value.trim();
    if (!expr) { showErr(topic, 'Please enter a postfix expression.'); return null; }
    return { expression: expr };
  }
  if (topic === 'hanoi') {
    var n    = parseInt(document.getElementById('hanoi-n').value, 10);
    var src  = document.getElementById('hanoi-src').value;
    var dest = document.getElementById('hanoi-dest').value;
    var aux  = document.getElementById('hanoi-aux').value;
    if (src === dest || src === aux || dest === aux) {
      showErr(topic, 'Source, destination, and auxiliary pegs must all be different.');
      return null;
    }
    return { n: n, source: src, dest: dest, aux: aux };
  }
  if (topic === 'html') {
    var html = document.getElementById('html-input').value.trim();
    if (!html) { showErr(topic, 'Please enter an HTML/XML snippet.'); return null; }
    return { html: html };
  }
  if (topic === 'nlp') {
    var sent = document.getElementById('nlp-input').value.trim();
    if (!sent) { showErr(topic, 'Please enter a sentence.'); return null; }
    return { sentence: sent };
  }
  return null;
}

function showErr(topic, msg) {
  var errBox = document.getElementById('err-' + topic);
  errBox.textContent = 'Error: ' + msg;
  errBox.style.display = 'block';
}

// ----------------------------------------------------------------
// State Diagram Strip
// ----------------------------------------------------------------
function buildStateDiagram(topic) {
  var container = document.getElementById('states-' + topic);
  container.innerHTML = '';
  var def = STATE_DEFS[topic];

  def.nodes.forEach(function (name, i) {
    var node = document.createElement('div');
    node.className = 'state-node';
    if (def.final.indexOf(name) >= 0) node.classList.add('accept-state');
    if (def.error.indexOf(name) >= 0)  node.classList.add('error-state');
    node.textContent = name;
    node.id = 'state-node-' + topic + '-' + sanitiseId(name);
    container.appendChild(node);

    if (i < def.nodes.length - 1) {
      var wrap = document.createElement('div');
      wrap.className = 'state-arrow';
      var line = document.createElement('div');
      line.className = 'arrow-line';
      line.id = 'state-arrow-' + topic + '-' + i;
      var head = document.createElement('div');
      head.className = 'arrow-head';
      wrap.appendChild(line);
      wrap.appendChild(head);
      container.appendChild(wrap);
    }
  });
}

function sanitiseId(name) {
  return name.replace(/[^a-zA-Z0-9]/g, '_');
}

function highlightState(topic, stateName) {
  var def = STATE_DEFS[topic];

  def.nodes.forEach(function (name) {
    var node = document.getElementById('state-node-' + topic + '-' + sanitiseId(name));
    if (!node) return;
    node.classList.remove('active-state');
    if (name === stateName) node.classList.add('active-state');
  });

  def.nodes.forEach(function (_, i) {
    var line = document.getElementById('state-arrow-' + topic + '-' + i);
    if (!line) return;
    line.classList.remove('active-arrow', 'error-arrow');
  });

  var idx = def.nodes.indexOf(stateName);
  if (idx > 0) {
    var prevArrow = document.getElementById('state-arrow-' + topic + '-' + (idx - 1));
    if (prevArrow) {
      prevArrow.classList.add(def.error.indexOf(stateName) >= 0 ? 'error-arrow' : 'active-arrow');
    }
  }
}

// ----------------------------------------------------------------
// Transition Log Table
// ----------------------------------------------------------------
function buildLogTable(topic, steps) {
  var tbody = document.querySelector('#log-' + topic + ' tbody');
  tbody.innerHTML = '';

  steps.forEach(function (s, i) {
    var tr = document.createElement('tr');
    tr.id = 'log-row-' + topic + '-' + i;

    if (s.state === 'q_f')   tr.classList.add('accept-row');
    if (s.state === 'q_err') tr.classList.add('error-row');

    var stackTop  = (s.stack && s.stack.length) ? s.stack[0] : '-';
    var remaining = s.input_remaining || s.note || '';

    if (topic === 'hanoi') {
      tr.innerHTML =
        '<td>' + s.step + '</td>' +
        '<td>' + s.state + '</td>' +
        '<td class="td-wrap">' + esc(s.action) + '</td>' +
        '<td>' + esc(stackTop) + '</td>';
    } else {
      tr.innerHTML =
        '<td>' + s.step + '</td>' +
        '<td>' + s.state + '</td>' +
        '<td class="td-wrap">' + esc(s.action) + '</td>' +
        '<td>' + esc(stackTop) + '</td>' +
        '<td class="td-wrap">' + esc(remaining) + '</td>';
    }
    tbody.appendChild(tr);
  });
}

function esc(str) {
  return String(str == null ? '' : str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

// ----------------------------------------------------------------
// Step Renderer
// ----------------------------------------------------------------
// ----------------------------------------------------------------
// Hanoi Peg Visualization
// ----------------------------------------------------------------

// Store total disks and last-moved disk between renders
var hanoiMeta = { n: 0, lastMovedDisk: 0 };

var DISK_COLORS = ['disk-c1','disk-c2','disk-c3','disk-c4','disk-c5','disk-c6','disk-c7'];

function initHanoiViz(firstStep) {
  var n = firstStep.total_disks || 3;
  hanoiMeta.n = n;
  hanoiMeta.lastMovedDisk = 0;

  var stage = document.getElementById('hanoi-stage');
  if (!stage) return;
  stage.innerHTML = '';

  var SVG_NS = 'http://www.w3.org/2000/svg';
  var W = 340, H = 200;
  var svg = document.createElementNS(SVG_NS, 'svg');
  svg.setAttribute('viewBox', '0 0 ' + W + ' ' + H);
  svg.setAttribute('preserveAspectRatio', 'xMidYMid meet');
  svg.setAttribute('id', 'hanoi-svg');

  var PEG_X = { A: 57, B: 170, C: 283 };
  var BASE_Y = 170;
  var ROD_H  = 130;
  var ROD_W  = 7;

  // Base bar
  var base = document.createElementNS(SVG_NS, 'rect');
  base.setAttribute('x', '14'); base.setAttribute('y', BASE_Y);
  base.setAttribute('width', W - 28); base.setAttribute('height', '7');
  base.setAttribute('rx', '3.5'); base.setAttribute('fill', '#C5C0B8');
  svg.appendChild(base);

  // Pegs and labels
  ['A','B','C'].forEach(function(p) {
    var rod = document.createElementNS(SVG_NS, 'rect');
    rod.setAttribute('x', PEG_X[p] - ROD_W/2);
    rod.setAttribute('y', BASE_Y - ROD_H);
    rod.setAttribute('width', ROD_W); rod.setAttribute('height', ROD_H);
    rod.setAttribute('rx', '3'); rod.setAttribute('fill', '#D2CEC7');
    svg.appendChild(rod);

    var lbl = document.createElementNS(SVG_NS, 'text');
    lbl.setAttribute('x', PEG_X[p]); lbl.setAttribute('y', H - 4);
    lbl.setAttribute('text-anchor', 'middle'); lbl.setAttribute('font-size', '12');
    lbl.setAttribute('font-family', 'DM Mono, monospace');
    lbl.setAttribute('fill', '#7A756C'); lbl.setAttribute('font-weight', '600');
    lbl.textContent = p;
    svg.appendChild(lbl);
  });

  // Create one rect + label per disk (they persist across renders, only transform changes)
  var MAX_W = 90, MIN_W = n > 1 ? 26 : 58;
  var DISK_H = Math.min(18, Math.max(12, Math.floor(ROD_H / (n + 1))));

  for (var d = 1; d <= n; d++) {
    var dw = n === 1 ? 58 : MIN_W + (d - 1) * (MAX_W - MIN_W) / (n - 1);
    var colorClass = DISK_COLORS[(d - 1) % DISK_COLORS.length];

    var rect = document.createElementNS(SVG_NS, 'rect');
    rect.setAttribute('id', 'hdisk-' + d);
    rect.setAttribute('width', Math.round(dw));
    rect.setAttribute('height', DISK_H);
    rect.setAttribute('rx', '4');
    rect.setAttribute('class', 'hanoi-disk-rect ' + colorClass);
    rect.setAttribute('stroke', 'rgba(0,0,0,0.10)');
    rect.setAttribute('stroke-width', '1');
    // Start at position 0,0; updateHanoiViz will move it
    rect.style.transform = 'translate(0px,0px)';
    svg.appendChild(rect);

    var dlbl = document.createElementNS(SVG_NS, 'text');
    dlbl.setAttribute('id', 'hdisk-lbl-' + d);
    dlbl.setAttribute('class', 'hanoi-disk-label');
    dlbl.setAttribute('text-anchor', 'middle');
    dlbl.setAttribute('font-size', '9');
    dlbl.setAttribute('font-family', 'DM Mono, monospace');
    dlbl.setAttribute('fill', 'rgba(0,0,0,0.45)');
    dlbl.setAttribute('font-weight', '500');
    dlbl.textContent = d;
    dlbl.style.transform = 'translate(0px,0px)';
    svg.appendChild(dlbl);
  }

  stage.appendChild(svg);

  // Position disks immediately (no transition on first render)
  disableHanoiTransition();
  updateHanoiViz(firstStep);
  // Re-enable transition on next frame
  requestAnimationFrame(function() { enableHanoiTransition(); });
}

function disableHanoiTransition() {
  for (var d = 1; d <= hanoiMeta.n; d++) {
    var el = document.getElementById('hdisk-' + d);
    var lb = document.getElementById('hdisk-lbl-' + d);
    if (el) el.style.transition = 'none';
    if (lb) lb.style.transition = 'none';
  }
}

function enableHanoiTransition() {
  for (var d = 1; d <= hanoiMeta.n; d++) {
    var el = document.getElementById('hdisk-' + d);
    var lb = document.getElementById('hdisk-lbl-' + d);
    if (el) el.style.transition = '';
    if (lb) lb.style.transition = '';
  }
}

function updateHanoiViz(step) {
  if (!step || !step.peg_state) return;
  var n = hanoiMeta.n;
  var pegState = step.peg_state;
  var lastMove = step.last_move;

  var PEG_X = { A: 57, B: 170, C: 283 };
  var BASE_Y = 170;
  var MAX_W = 90, MIN_W = n > 1 ? 26 : 58;
  var DISK_H = Math.min(18, Math.max(12, Math.floor(130 / (n + 1))));
  var DISK_GAP = 1;

  var movedDisk = lastMove ? lastMove.disk : 0;
  hanoiMeta.lastMovedDisk = movedDisk;

  ['A','B','C'].forEach(function(p) {
    var disksOnPeg = pegState[p] || [];
    disksOnPeg.forEach(function(diskNum, idx) {
      var dw = n === 1 ? 58 : MIN_W + (diskNum - 1) * (MAX_W - MIN_W) / (n - 1);
      var px = PEG_X[p];
      var diskTop = BASE_Y - (idx + 1) * (DISK_H + DISK_GAP);
      var diskLeft = px - dw / 2;

      var rect = document.getElementById('hdisk-' + diskNum);
      var lbl  = document.getElementById('hdisk-lbl-' + diskNum);
      if (!rect) return;

      rect.style.transform = 'translate(' + Math.round(diskLeft) + 'px,' + Math.round(diskTop) + 'px)';
      if (lbl) {
        lbl.style.transform = 'translate(' + Math.round(px) + 'px,' + Math.round(diskTop + DISK_H/2 + 3.5) + 'px)';
      }

      // Highlight the just-moved disk
      rect.classList.toggle('just-moved', diskNum === movedDisk);
    });
  });
}

// ----------------------------------------------------------------
// NLP Syntax Tree Rendering
// ----------------------------------------------------------------

function renderSyntaxTree(treeRoots) {
  var wrap = document.getElementById('tree-svg-wrap');
  if (!wrap) return;
  wrap.innerHTML = '';

  var SVG_NS = 'http://www.w3.org/2000/svg';

  if (!treeRoots || !treeRoots.length) {
    var ph = document.createElement('div');
    ph.style.cssText = 'padding:18px;font-size:12px;color:var(--text-dim);text-align:center;width:100%;';
    ph.textContent = 'Parse tree will build here as steps progress...';
    wrap.appendChild(ph);
    return;
  }

  var LEVEL_H = 46;   // vertical gap between levels
  var LEAF_W  = 58;   // horizontal space per leaf node
  var PAD     = 14;   // left/right padding

  // ---- Layout ----
  function countLeaves(node) {
    if (!node.children || !node.children.length) return 1;
    var total = 0;
    node.children.forEach(function(c) { total += countLeaves(c); });
    return total;
  }

  function assignPositions(node, startX, depth) {
    node._depth = depth;
    if (!node.children || !node.children.length) {
      node._x = startX + LEAF_W / 2;
      return LEAF_W;
    }
    var x = startX;
    node.children.forEach(function(c) {
      x += assignPositions(c, x, depth + 1);
    });
    var firstX = node.children[0]._x;
    var lastX  = node.children[node.children.length - 1]._x;
    node._x = (firstX + lastX) / 2;
    return x - startX;
  }

  function maxDepth(node) {
    if (!node.children || !node.children.length) return 0;
    return 1 + Math.max.apply(null, node.children.map(maxDepth));
  }

  // Layout all roots side by side
  var xCursor = PAD;
  treeRoots.forEach(function(root) {
    assignPositions(root, xCursor, 0);
    xCursor += countLeaves(root) * LEAF_W + 16;
  });

  var totalDepth = Math.max.apply(null, treeRoots.map(maxDepth));
  var svgH = (totalDepth + 1) * LEVEL_H + 36;
  var svgW = Math.max(xCursor, 180);

  var svg = document.createElementNS(SVG_NS, 'svg');
  svg.setAttribute('width', svgW);
  svg.setAttribute('height', svgH);
  svg.setAttribute('viewBox', '0 0 ' + svgW + ' ' + svgH);

  var NODE_COLORS = {
    'S':   { bg: '#E3EEE4', stroke: '#6A9B6E', text: '#3A6B3E' },
    'NP':  { bg: '#E8EDF5', stroke: '#7A90B8', text: '#3A5088' },
    'VP':  { bg: '#F0E8F5', stroke: '#9A7AB8', text: '#5A3A88' },
    'Det': { bg: '#F5F0E8', stroke: '#B8A070', text: '#7A6030' },
    'N':   { bg: '#EBF5E8', stroke: '#78A870', text: '#385830' },
    'V':   { bg: '#F5EBE8', stroke: '#B87870', text: '#883830' },
    'Adj': { bg: '#E8F5F5', stroke: '#70A8A8', text: '#306868' },
    'Adv': { bg: '#F5F5E8', stroke: '#A8A870', text: '#686830' },
  };
  var LEAF_COLOR = { bg: '#F5F3EF', stroke: '#C8C3BB', text: '#6B6460' };
  var DEFAULT    = { bg: '#EFEDEA', stroke: '#C0BBB5', text: '#5A5550' };

  function getColors(label) {
    if (NODE_COLORS[label]) return NODE_COLORS[label];
    if (!label) return DEFAULT;
    // leaf word — no POS match
    return LEAF_COLOR;
  }

  // ---- Draw edges first (so nodes render on top) ----
  function drawEdges(node) {
    (node.children || []).forEach(function(child) {
      var nodeY  = node._depth  * LEVEL_H + 24;
      var childY = child._depth * LEVEL_H + 24;
      var line = document.createElementNS(SVG_NS, 'line');
      line.setAttribute('x1', node._x); line.setAttribute('y1', nodeY + 13);
      line.setAttribute('x2', child._x); line.setAttribute('y2', childY - 13);
      line.setAttribute('stroke', '#D5D0C8'); line.setAttribute('stroke-width', '1.5');
      line.setAttribute('stroke-linecap', 'round');
      svg.appendChild(line);
      drawEdges(child);
    });
  }

  // ---- Draw nodes ----
  function drawNodes(node) {
    var y = node._depth * LEVEL_H + 24;
    var isLeaf = !node.children || !node.children.length;
    var r = isLeaf ? 13 : 16;
    var col = getColors(node.label);

    var circle = document.createElementNS(SVG_NS, 'circle');
    circle.setAttribute('cx', node._x); circle.setAttribute('cy', y);
    circle.setAttribute('r', r);
    circle.setAttribute('fill', col.bg);
    circle.setAttribute('stroke', col.stroke);
    circle.setAttribute('stroke-width', '1.5');
    circle.setAttribute('class', 'tree-node-circle');
    svg.appendChild(circle);

    var text = document.createElementNS(SVG_NS, 'text');
    text.setAttribute('x', node._x); text.setAttribute('y', y + 4);
    text.setAttribute('text-anchor', 'middle');
    text.setAttribute('font-size', isLeaf ? '8.5' : '9.5');
    text.setAttribute('font-family', 'DM Mono, monospace');
    text.setAttribute('fill', col.text);
    text.setAttribute('font-weight', isLeaf ? '400' : '600');
    text.textContent = node.label;
    svg.appendChild(text);

    (node.children || []).forEach(drawNodes);
  }

  treeRoots.forEach(drawEdges);
  treeRoots.forEach(drawNodes);
  wrap.appendChild(svg);
}

// ----------------------------------------------------------------
// Step Renderer (updated to call viz functions)
// ----------------------------------------------------------------

function renderStep(topic, index) {
  var steps = sim[topic].steps;
  if (!steps || !steps.length) return;
  if (index < 0) index = 0;
  if (index >= steps.length) index = steps.length - 1;

  var s     = steps[index];
  var total = steps.length;
  sim[topic].cursor = index;

  // Info panel
  document.getElementById('stepctr-' + topic).textContent = 'Step ' + s.step + ' of ' + total;
  document.getElementById('stepaction-' + topic).textContent = s.action;
  document.getElementById('steparrow-' + topic).textContent = s.arrow || '';

  if (topic !== 'hanoi') {
    var remEl = document.getElementById('steprem-' + topic);
    if (remEl) remEl.textContent = s.input_remaining || '';
  }

  if (topic === 'hanoi' && s.moves_so_far !== undefined) {
    var ol = document.getElementById('moves-list-hanoi');
    if (ol) {
      ol.innerHTML = '';
      s.moves_so_far.forEach(function (m) {
        var li = document.createElement('li');
        li.textContent = m;
        ol.appendChild(li);
      });
    }
  }

  renderStack(topic, s.stack || []);
  highlightState(topic, s.state);

  // Visualization hooks
  if (topic === 'hanoi') {
    updateHanoiViz(s);
  }
  if (topic === 'nlp') {
    renderSyntaxTree(s.tree || []);
  }

  // Log table highlight
  document.querySelectorAll('#log-' + topic + ' tbody tr').forEach(function (tr) {
    tr.classList.remove('active-row');
  });
  var activeRow = document.getElementById('log-row-' + topic + '-' + index);
  if (activeRow) {
    activeRow.classList.add('active-row');
    activeRow.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
  }

  // Button states
  updateControls(topic, index, total);
}

function updateControls(topic, index, total) {
  var prevBtn  = document.getElementById('prev-'  + topic);
  var nextBtn  = document.getElementById('next-'  + topic);
  var firstBtn = document.getElementById('first-' + topic);
  var lastBtn  = document.getElementById('last-'  + topic);

  if (prevBtn)  prevBtn.disabled  = index === 0;
  if (firstBtn) firstBtn.disabled = index === 0;
  if (nextBtn)  nextBtn.disabled  = index === total - 1;
  if (lastBtn)  lastBtn.disabled  = index === total - 1;
}

function renderStack(topic, stackArr) {
  var container = document.getElementById('stack-' + topic);
  container.innerHTML = '';

  var displayItems = stackArr.filter(function (s) { return s !== 'Z0'; });

  if (displayItems.length === 0) {
    var empty = document.createElement('div');
    empty.className = 'stack-empty-msg';
    empty.textContent = '(empty)';
    container.appendChild(empty);
    return;
  }

  displayItems.forEach(function (item, i) {
    var cell = document.createElement('div');
    cell.className = 'stack-cell' + (i === 0 ? ' top-cell' : '');
    cell.textContent = item;
    container.appendChild(cell);
  });
}

// ----------------------------------------------------------------
// Navigation
// ----------------------------------------------------------------
function stepNav(topic, delta) {
  var next  = sim[topic].cursor + delta;
  var total = sim[topic].steps.length;
  if (next < 0 || next >= total) return;
  stopPlay(topic);
  renderStep(topic, next);
}

function goTo(topic, index) {
  stopPlay(topic);
  renderStep(topic, index);
}

function resetTopic(topic) {
  stopPlay(topic);
  sim[topic].steps  = [];
  sim[topic].cursor = 0;

  // Hide sim area and error
  var simArea = document.getElementById('sim-' + topic);
  var errBox  = document.getElementById('err-' + topic);
  if (simArea) simArea.style.display = 'none';
  if (errBox)  errBox.style.display  = 'none';

  // Clear inputs back to defaults
  if (topic === 'arithmetic') {
    document.getElementById('arith-input').value = '4 5 3 * +';
  }
  if (topic === 'hanoi') {
    document.getElementById('hanoi-n').value    = '3';
    document.getElementById('hanoi-src').value  = 'A';
    document.getElementById('hanoi-dest').value = 'C';
    document.getElementById('hanoi-aux').value  = 'B';
  }
  if (topic === 'html') {
    document.getElementById('html-input').value = '<div> <p> <b> text </b> </p> </div>';
  }
  if (topic === 'nlp') {
    document.getElementById('nlp-input').value = 'the dog chased the cat';
  }
}

// ----------------------------------------------------------------
// Auto-play
// ----------------------------------------------------------------
function togglePlay(topic) {
  var btn = document.getElementById('play-' + topic);
  if (sim[topic].timer) {
    stopPlay(topic);
  } else {
    btn.textContent = 'Pause';
    btn.classList.add('playing');
    sim[topic].timer = setInterval(function () {
      var next  = sim[topic].cursor + 1;
      var total = sim[topic].steps.length;
      if (next >= total) { stopPlay(topic); return; }
      renderStep(topic, next);
    }, PLAY_INTERVAL_MS);
  }
}

function stopPlay(topic) {
  if (sim[topic] && sim[topic].timer) {
    clearInterval(sim[topic].timer);
    sim[topic].timer = null;
  }
  var btn = document.getElementById('play-' + topic);
  if (btn) {
    btn.textContent = 'Play';
    btn.classList.remove('playing');
  }
}
