/**
 * ContentRenderer — standalone interactive renderer for published content.
 * Supports Quiz, QuestGame, BranchedNarrative, and WebSimulation formats.
 * Pure vanilla JS, no dependencies. Import via <script src="/content-renderer.js">.
 */
const ContentRenderer = (() => {
  let _stylesInjected = false;

  // ---------------------------------------------------------------------------
  // CSS (injected once)
  // ---------------------------------------------------------------------------
  function injectStyles() {
    if (_stylesInjected) return;
    _stylesInjected = true;
    const s = document.createElement('style');
    s.textContent = `
      .cr-root { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #1a1a2e; }
      .cr-title { margin: 0 0 4px; font-size: 1.35rem; color: #667eea; }
      .cr-subtitle { margin: 0 0 14px; font-size: 0.92rem; color: #555; }
      .cr-text { margin: 0 0 10px; line-height: 1.6; white-space: pre-line; }
      .cr-emph { font-style: italic; color: #444; margin: 0 0 12px; padding: 8px 12px; border-left: 3px solid #667eea; background: #f4f5ff; border-radius: 0 6px 6px 0; }
      .cr-badge { display: inline-block; padding: 2px 9px; border-radius: 10px; font-size: 0.72rem; font-weight: 700; margin-right: 5px; letter-spacing: 0.3px; vertical-align: middle; }
      .cr-badge-default { background: #e8e8e8; color: #555; }
      .cr-badge-success { background: #d4edda; color: #155724; }
      .cr-badge-warning { background: #fff3cd; color: #856404; }
      .cr-badge-danger { background: #f8d7da; color: #721c24; }
      .cr-badge-info { background: #d4f4fa; color: #1a7a8a; }
      .cr-badge-purple { background: #e8dff5; color: #5a3d8a; }

      .cr-progress { display: flex; align-items: center; gap: 10px; margin-bottom: 14px; }
      .cr-progress-label { font-size: 0.85rem; font-weight: 600; color: #555; white-space: nowrap; }
      .cr-progress-track { flex: 1; height: 8px; background: #e0e0e0; border-radius: 4px; overflow: hidden; }
      .cr-progress-fill { height: 100%; background: #667eea; border-radius: 4px; transition: width 0.3s; }
      .cr-score { font-size: 0.85rem; font-weight: 600; color: #333; white-space: nowrap; }

      .cr-topbar { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; padding: 10px 14px; background: #f4f5ff; border-radius: 8px; margin-bottom: 16px; }

      .cr-options { list-style: none; margin: 0 0 6px; padding: 0; display: flex; flex-direction: column; gap: 6px; }
      .cr-option { padding: 10px 14px; border: 2px solid #ddd; border-radius: 8px; cursor: pointer; font-size: 0.92rem; transition: all 0.15s; background: white; }
      .cr-option:hover:not(.cr-opt-locked) { border-color: #667eea; background: #f4f5ff; }
      .cr-opt-selected { border-color: #667eea; background: #eef1ff; }
      .cr-opt-correct { border-color: #28a745 !important; background: #d4edda !important; }
      .cr-opt-incorrect { border-color: #dc3545 !important; background: #f8d7da !important; }
      .cr-opt-locked { cursor: default; opacity: 0.85; }
      .cr-opt-letter { display: inline-block; width: 22px; height: 22px; line-height: 22px; text-align: center; border-radius: 50%; background: #e0e0e0; color: #555; font-size: 0.78rem; font-weight: 700; margin-right: 10px; }
      .cr-opt-correct .cr-opt-letter { background: #28a745; color: white; }
      .cr-opt-incorrect .cr-opt-letter { background: #dc3545; color: white; }

      .cr-feedback { padding: 10px 14px; border-radius: 8px; margin: 6px 0 16px; font-size: 0.88rem; line-height: 1.5; }
      .cr-feedback-correct { background: #d4edda; color: #155724; border-left: 4px solid #28a745; }
      .cr-feedback-incorrect { background: #f8d7da; color: #721c24; border-left: 4px solid #dc3545; }

      .cr-card { background: white; border: 1px solid #e0e0e0; border-radius: 10px; padding: 16px; margin-bottom: 14px; box-shadow: 0 2px 8px rgba(0,0,0,0.04); }
      .cr-card-active { border-color: #667eea; box-shadow: 0 2px 12px rgba(102,126,234,0.15); }

      .cr-choice-btn { display: block; width: 100%; text-align: left; padding: 10px 14px; margin-bottom: 6px; border: 2px solid #667eea; border-radius: 8px; background: white; color: #667eea; cursor: pointer; font-size: 0.92rem; font-weight: 500; transition: all 0.15s; }
      .cr-choice-btn:hover { background: #667eea; color: white; }

      .cr-summary { padding: 18px; border-radius: 10px; text-align: center; margin-top: 16px; }
      .cr-summary-pass { background: #d4edda; border: 2px solid #28a745; }
      .cr-summary-fail { background: #f8d7da; border: 2px solid #dc3545; }
      .cr-summary h3 { margin: 0 0 8px; font-size: 1.2rem; }
      .cr-summary p { margin: 4px 0; font-size: 0.95rem; }
      .cr-restart-btn { margin-top: 12px; padding: 8px 20px; border: none; border-radius: 8px; background: #667eea; color: white; cursor: pointer; font-size: 0.9rem; font-weight: 600; }
      .cr-restart-btn:hover { opacity: 0.9; }

      .cr-slider-row { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
      .cr-slider-label { min-width: 140px; font-size: 0.88rem; font-weight: 600; color: #333; word-wrap: break-word; }
      .cr-slider { flex: 1; accent-color: #667eea; }
      .cr-slider-val { min-width: 70px; text-align: right; font-size: 0.88rem; font-family: 'Consolas', monospace; color: #1565c0; }

      .cr-output-row { display: flex; align-items: baseline; gap: 8px; padding: 8px 12px; margin-bottom: 6px; background: #f4f5ff; border-radius: 8px; border-left: 3px solid #667eea; }
      .cr-output-label { font-size: 0.88rem; font-weight: 600; color: #333; flex: 1; }
      .cr-output-val { font-size: 1.1rem; font-weight: 700; font-family: 'Consolas', monospace; color: #667eea; }
      .cr-output-unit { font-size: 0.78rem; color: #888; }

      .cr-rules { margin: 0; padding: 0; list-style: none; }
      .cr-rule { padding: 8px 12px; margin-bottom: 6px; background: #f8f9fa; border-left: 3px solid #667eea; border-radius: 0 6px 6px 0; font-size: 0.88rem; color: #333; font-family: 'Consolas', monospace; }

      .cr-formula-card { padding: 10px 14px; margin-bottom: 8px; background: #f8f9fa; border: 1px solid #e0e0e0; border-radius: 8px; font-family: 'Consolas', monospace; font-size: 0.88rem; display: flex; align-items: baseline; gap: 8px; flex-wrap: wrap; }
      .cr-formula-lhs { font-weight: 700; color: #667eea; white-space: nowrap; }
      .cr-formula-eq { color: #999; }
      .cr-formula-rhs { color: #333; flex: 1; word-break: break-word; }
      .cr-formula-text { font-style: italic; color: #666; font-size: 0.85rem; margin-bottom: 6px; padding: 4px 0; }
      .cr-calc-btn { display: block; margin: 12px auto; padding: 10px 28px; border: none; border-radius: 8px; background: #667eea; color: white; cursor: pointer; font-size: 0.95rem; font-weight: 600; transition: all 0.15s; }
      .cr-calc-btn:hover { opacity: 0.9; transform: translateY(-1px); box-shadow: 0 4px 12px rgba(102,126,234,0.3); }

      .cr-section-title { font-size: 1rem; font-weight: 700; color: #667eea; margin: 16px 0 8px; }

      .cr-node-history { display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 12px; }
      .cr-node-crumb { padding: 2px 8px; border-radius: 10px; font-size: 0.72rem; background: #e8e8e8; color: #555; cursor: pointer; }
      .cr-node-crumb-active { background: #667eea; color: white; }

      .cr-toggle-btn { padding: 6px 14px; border: 1px solid #667eea; border-radius: 6px; background: white; color: #667eea; cursor: pointer; font-size: 0.82rem; font-weight: 600; }
      .cr-toggle-btn:hover { background: #667eea; color: white; }
      .cr-toggle-btn.cr-active { background: #667eea; color: white; }

      .cr-rewards { display: flex; flex-wrap: wrap; gap: 4px; margin: 8px 0; }

      .cr-divider { border: none; border-top: 1px solid #e0e0e0; margin: 12px 0; }

      .cr-ending { text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea22, #764ba222); border-radius: 10px; margin-top: 12px; }
      .cr-ending h3 { color: #667eea; margin: 0 0 8px; }

      .cr-controls-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 12px; }

      .cr-q-num { font-size: 0.78rem; color: #999; margin-bottom: 4px; }
    `;
    document.head.appendChild(s);
  }

  // ---------------------------------------------------------------------------
  // Shared UI block factories
  // ---------------------------------------------------------------------------

  function el(tag, cls, html) {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (html !== undefined) e.innerHTML = html;
    return e;
  }

  function titleBlock(title, subtitle) {
    const f = document.createDocumentFragment();
    f.appendChild(el('h2', 'cr-title', esc(title)));
    if (subtitle) f.appendChild(el('p', 'cr-subtitle', esc(subtitle)));
    return f;
  }

  function textBlock(text) { return el('p', 'cr-text', esc(text)); }
  function emphBlock(text) { return el('div', 'cr-emph', esc(text)); }

  function badgeBlock(label, variant = 'default') {
    return el('span', `cr-badge cr-badge-${variant}`, esc(label));
  }

  function progressBar(current, total, label) {
    const wrap = el('div', 'cr-progress');
    wrap.appendChild(el('span', 'cr-progress-label', esc(label || `${current} / ${total}`)));
    const track = el('div', 'cr-progress-track');
    const fill = el('div', 'cr-progress-fill');
    fill.style.width = `${Math.round((current / Math.max(total, 1)) * 100)}%`;
    track.appendChild(fill);
    wrap.appendChild(track);
    return wrap;
  }

  function scoreDisplay(score, total, passingScore) {
    let html = `<strong>${score}</strong> / ${total} pts`;
    if (passingScore != null && total > 0) {
      const needed = quizPassPoints(total, passingScore);
      if (needed != null) html += ` &nbsp;(need ${needed} to pass)`;
    }
    return el('span', 'cr-score', html);
  }

  function optionList(options, onSelect) {
    const ul = el('ul', 'cr-options');
    const letters = 'ABCDEFGHIJKLMNOP';
    options.forEach((text, i) => {
      const li = el('li', 'cr-option');
      li.innerHTML = `<span class="cr-opt-letter">${letters[i] || i}</span>${esc(text)}`;
      li.dataset.idx = i;
      li.onclick = () => onSelect(i, li, ul);
      ul.appendChild(li);
    });
    return ul;
  }

  function feedbackBlock(isCorrect, explanation) {
    const cls = isCorrect ? 'cr-feedback cr-feedback-correct' : 'cr-feedback cr-feedback-incorrect';
    const prefix = isCorrect ? 'Correct!' : 'Incorrect.';
    return el('div', cls, `<strong>${prefix}</strong>${explanation ? ' ' + esc(explanation) : ''}`);
  }

  function sliderControl(label, value, min, max, unit, onChange) {
    const row = el('div', 'cr-slider-row');
    row.appendChild(el('span', 'cr-slider-label', esc(label)));
    const input = document.createElement('input');
    input.type = 'range';
    input.className = 'cr-slider';
    input.min = min ?? 0;
    input.max = max ?? 100;
    input.step = (max - min) <= 10 ? 0.1 : 1;
    input.value = value;
    const valSpan = el('span', 'cr-slider-val', `${parseFloat(value).toFixed(input.step < 1 ? 1 : 0)}${unit ? ' ' + unit : ''}`);
    input.oninput = () => {
      const v = parseFloat(input.value);
      valSpan.textContent = `${v.toFixed(input.step < 1 ? 1 : 0)}${unit ? ' ' + unit : ''}`;
      if (onChange) onChange(v);
    };
    row.appendChild(input);
    row.appendChild(valSpan);
    return row;
  }

  function ruleBlock(rules) {
    const ul = el('ul', 'cr-rules');
    rules.forEach(r => ul.appendChild(el('li', 'cr-rule', esc(r))));
    return ul;
  }

  function choiceButton(text, onClick) {
    const btn = el('button', 'cr-choice-btn', esc(text));
    btn.onclick = onClick;
    return btn;
  }

  function esc(s) {
    if (typeof s !== 'string') return String(s ?? '');
    return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  // ---------------------------------------------------------------------------
  // Format detection
  // ---------------------------------------------------------------------------

  const FORMAT_KEYS = new Set(['quiz', 'story', 'game', 'simulation']);

  function unwrapContent(data) {
    if (!data || typeof data !== 'object' || Array.isArray(data)) return data;
    const keys = Object.keys(data);
    if (keys.length === 1 && FORMAT_KEYS.has(keys[0].toLowerCase())) {
      const inner = data[keys[0]];
      if (inner && typeof inner === 'object' && !Array.isArray(inner)) return inner;
    }
    return data;
  }

  function detectFormat(data) {
    if (!data || typeof data !== 'object') return null;
    const d = unwrapContent(data);
    if (Array.isArray(d.questions)) return 'quiz';
    if (d.variables && (d.controls || d.rules)) return 'simulation';
    if (d.parameters && (d.rules || d.metrics || d.initial_state)) return 'simulation';
    if ((d.variables || d.parameters) && d.variables && d.variables.some && d.variables.some(v => v.rule)) return 'simulation';
    if (d.nodes && d.victory_conditions) return 'game';
    if (d.nodes) {
      const arr = Array.isArray(d.nodes) ? d.nodes : Object.values(d.nodes);
      if (arr.some(n => n && (n.rewards || n.penalties || n.requirements))) return 'game';
    }
    if (d.nodes && (d.synopsis || d.genre)) return 'story';
    if (d.nodes) return 'story';
    return null;
  }

  // ---------------------------------------------------------------------------
  // Quiz renderer
  // ---------------------------------------------------------------------------

  /**
   * Quiz passing_score in JSON is usually minimum POINTS (per format schema:
   * "60-80% of total" expressed as the integer point threshold, e.g. 6 of 9).
   * If value > max points and <= 100, treat as percentage (e.g. 70 = 70%).
   */
  function quizPassPoints(total, passingScore) {
    if (passingScore == null || total <= 0) return null;
    const ps = Number(passingScore);
    if (!isFinite(ps) || ps < 0) return null;
    if (ps <= total) return Math.min(total, Math.max(1, Math.round(ps)));
    if (ps <= 100) return Math.max(1, Math.ceil((total * ps) / 100));
    return Math.min(total, Math.max(1, Math.round(ps)));
  }

  function quizScoreLineHtml(score, total, passNeeded) {
    let html = `<strong>${score}</strong> / ${total} pts`;
    if (passNeeded != null) html += ` &nbsp;(need ${passNeeded} to pass)`;
    return html;
  }

  function renderQuiz(root, data) {
    const totalScore = data.questions.reduce((s, q) => s + (q.score || 1), 0);
    const passNeeded = quizPassPoints(totalScore, data.passing_score ?? Math.ceil(totalScore * 0.7));
    const state = { current: 0, score: 0, answered: new Array(data.questions.length).fill(false) };

    root.appendChild(titleBlock(data.title, data.description));

    const topbar = el('div', 'cr-topbar');
    const progressEl = el('div', 'cr-progress');
    const progressLabel = el('span', 'cr-progress-label', `Question 1 / ${data.questions.length}`);
    const progressTrack = el('div', 'cr-progress-track');
    const progressFill = el('div', 'cr-progress-fill');
    progressFill.style.width = `${Math.round(100 / data.questions.length)}%`;
    progressTrack.appendChild(progressFill);
    progressEl.appendChild(progressLabel);
    progressEl.appendChild(progressTrack);
    topbar.appendChild(progressEl);
    topbar.appendChild(el('span', 'cr-score', quizScoreLineHtml(0, totalScore, passNeeded)));
    root.appendChild(topbar);

    const questionsContainer = el('div', '');

    function updateTopbar() {
      const answeredCount = state.answered.filter(Boolean).length;
      progressLabel.textContent = `Question ${Math.min(answeredCount + 1, data.questions.length)} / ${data.questions.length}`;
      progressFill.style.width = `${Math.round((answeredCount / data.questions.length) * 100)}%`;
      topbar.querySelector('.cr-score').innerHTML = quizScoreLineHtml(state.score, totalScore, passNeeded);
    }

    function renderQuestion(idx) {
      const q = data.questions[idx];
      const card = el('div', 'cr-card cr-card-active');
      card.id = `cr-q-${idx}`;

      card.appendChild(el('div', 'cr-q-num', `Question ${idx + 1}`));

      const tierMap = { low: 'info', mid: 'warning', high: 'danger' };
      const headerRow = el('div', '', '');
      headerRow.style.marginBottom = '8px';
      headerRow.appendChild(badgeBlock(q.tier || 'mid', tierMap[q.tier] || 'default'));
      headerRow.appendChild(badgeBlock(`${q.score || 1} pt${(q.score || 1) > 1 ? 's' : ''}`, 'purple'));
      card.appendChild(headerRow);

      card.appendChild(el('p', 'cr-text', `<strong>${esc(q.question || q.question_text)}</strong>`));

      const rawOpts = q.options || [];
      const isObjOpts = rawOpts.length > 0 && typeof rawOpts[0] === 'object';
      const optTexts = isObjOpts
        ? rawOpts.map(o => o.text || o.option_text || o.label || o.content || o.value || o.answer || (typeof o === 'object' ? JSON.stringify(o) : String(o)))
        : rawOpts;
      let correctIdx = q.correct_answer;
      if (typeof correctIdx === 'string') correctIdx = parseInt(correctIdx, 10);
      if (correctIdx == null || isNaN(correctIdx) || correctIdx < 0) correctIdx = -1;

      const opts = optionList(optTexts, (chosenIdx, li, ul) => {
        if (state.answered[idx]) return;
        state.answered[idx] = true;
        const correct = chosenIdx === correctIdx;
        if (correct) state.score += (q.score || 1);

        ul.querySelectorAll('.cr-option').forEach((o, oi) => {
          o.classList.add('cr-opt-locked');
          if (oi === correctIdx) o.classList.add('cr-opt-correct');
          if (oi === chosenIdx && !correct) o.classList.add('cr-opt-incorrect');
        });

        card.appendChild(feedbackBlock(correct, q.explanation));
        card.classList.remove('cr-card-active');
        updateTopbar();

        if (idx + 1 < data.questions.length) {
          renderQuestion(idx + 1);
        } else {
          showSummary();
        }
      });
      card.appendChild(opts);
      questionsContainer.appendChild(card);
      card.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    function showSummary() {
      const passed = passNeeded != null ? state.score >= passNeeded : true;
      const summary = el('div', `cr-summary ${passed ? 'cr-summary-pass' : 'cr-summary-fail'}`);
      summary.innerHTML = `
        <h3>${passed ? 'Passed!' : 'Not Passed'}</h3>
        <p>Score: <strong>${state.score}</strong> / ${totalScore} pts</p>
        ${passNeeded != null ? `<p>Passing threshold: <strong>${passNeeded}</strong> pts</p>` : ''}
      `;
      const restart = el('button', 'cr-restart-btn', 'Restart Quiz');
      restart.onclick = () => {
        state.current = 0;
        state.score = 0;
        state.answered.fill(false);
        questionsContainer.innerHTML = '';
        updateTopbar();
        renderQuestion(0);
      };
      summary.appendChild(restart);
      questionsContainer.appendChild(summary);
      summary.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    root.appendChild(questionsContainer);
    renderQuestion(0);
  }

  // ---------------------------------------------------------------------------
  // Quest Game renderer
  // ---------------------------------------------------------------------------

  function normalizeNodes(raw) {
    if (!raw) return {};
    if (Array.isArray(raw)) {
      const map = {};
      raw.forEach(n => {
        const key = n && (n.id || n.node_id);
        if (key) { n.id = key; map[key] = n; }
      });
      return map;
    }
    return raw;
  }

  function renderGame(root, data) {
    data.nodes = normalizeNodes(data.nodes);
    Object.values(data.nodes).forEach(n => {
      if (!n.description && n.text) n.description = n.text;
      if (!n.title && n.id) n.title = n.id;
      if (n.choices) {
        n.choices = n.choices.map(c => ({
          ...c,
          next_node_id: c.next_node_id || c.next_node || c.target_node || c.next,
        }));
      }
      if (n.rewards && !Array.isArray(n.rewards)) {
        const flat = [];
        if (n.rewards.gold) flat.push(`${n.rewards.gold} Gold`);
        if (n.rewards.status) flat.push(n.rewards.status);
        if (Array.isArray(n.rewards.items)) n.rewards.items.forEach(i => flat.push(typeof i === 'object' ? (i.item || i.name || String(i)) : i));
        n.rewards = flat;
      } else if (n.rewards && n.rewards.length && typeof n.rewards[0] === 'object') {
        n.rewards = n.rewards.map(r => r.item || r.name || String(r));
      }
    });
    const nodeKeys = Object.keys(data.nodes || {});
    const state = { currentNode: data.start_node || nodeKeys[0], rewards: [], visited: new Set() };

    root.appendChild(titleBlock(data.title, data.description));

    const topbar = el('div', 'cr-topbar');
    const progressEl = progressBar(0, nodeKeys.length, `Scene 0 / ${nodeKeys.length}`);
    topbar.appendChild(progressEl);
    const rewardsEl = el('div', 'cr-rewards');
    topbar.appendChild(rewardsEl);
    root.appendChild(topbar);

    const sceneContainer = el('div', '');
    root.appendChild(sceneContainer);

    function updateTopbar() {
      const pLabel = progressEl.querySelector('.cr-progress-label');
      const pFill = progressEl.querySelector('.cr-progress-fill');
      pLabel.textContent = `Scene ${state.visited.size} / ${nodeKeys.length}`;
      pFill.style.width = `${Math.round((state.visited.size / nodeKeys.length) * 100)}%`;
      rewardsEl.innerHTML = '';
      state.rewards.forEach(r => rewardsEl.appendChild(badgeBlock(r, 'success')));
    }

    function renderNode(nodeId) {
      sceneContainer.innerHTML = '';
      const node = data.nodes[nodeId];
      if (!node) {
        sceneContainer.appendChild(el('div', 'cr-ending', '<h3>End of journey</h3><p>No further path available.</p>'));
        addRestart();
        return;
      }

      state.currentNode = nodeId;
      state.visited.add(nodeId);
      if (node.rewards) node.rewards.forEach(r => { if (!state.rewards.includes(r)) state.rewards.push(r); });
      updateTopbar();

      const card = el('div', 'cr-card cr-card-active');
      card.appendChild(el('h3', 'cr-section-title', esc(node.title)));
      card.appendChild(textBlock(node.description));

      if (node.requirements && node.requirements.length) {
        const reqDiv = el('div', '', '');
        reqDiv.appendChild(el('span', 'cr-badge cr-badge-warning', 'Requires'));
        node.requirements.forEach(r => reqDiv.appendChild(badgeBlock(r, state.rewards.includes(r) ? 'success' : 'danger')));
        card.appendChild(reqDiv);
        const unmet = node.requirements.filter(r => !state.rewards.includes(r));
        if (unmet.length) {
          card.appendChild(el('div', 'cr-feedback cr-feedback-incorrect', `Missing: ${unmet.join(', ')}`));
        }
      }

      if (node.rewards && node.rewards.length) {
        const rwDiv = el('div', 'cr-rewards');
        rwDiv.appendChild(el('span', 'cr-badge cr-badge-info', 'Rewards'));
        node.rewards.forEach(r => rwDiv.appendChild(badgeBlock(r, 'success')));
        card.appendChild(rwDiv);
      }

      card.appendChild(el('hr', 'cr-divider'));

      if (node.choices && node.choices.length) {
        node.choices.forEach(c => {
          card.appendChild(choiceButton(c.text, () => renderNode(c.next_node_id)));
        });
      } else {
        const victory = data.victory_conditions && data.victory_conditions.length > 0;
        card.appendChild(el('div', 'cr-ending',
          `<h3>${victory ? 'Victory!' : 'Journey Complete'}</h3>` +
          (victory ? `<p>${data.victory_conditions.map(esc).join(', ')}</p>` : '')));
        addRestart();
      }

      sceneContainer.appendChild(card);
    }

    function addRestart() {
      const btn = el('button', 'cr-restart-btn', 'Restart Game');
      btn.style.display = 'block';
      btn.style.margin = '12px auto';
      btn.onclick = () => {
        state.currentNode = data.start_node || nodeKeys[0];
        state.rewards = [];
        state.visited.clear();
        updateTopbar();
        renderNode(state.currentNode);
      };
      sceneContainer.appendChild(btn);
    }

    renderNode(state.currentNode);
  }

  // ---------------------------------------------------------------------------
  // Branched Narrative renderer
  // ---------------------------------------------------------------------------

  function renderStory(root, data) {
    data.nodes = normalizeNodes(data.nodes);
    Object.values(data.nodes).forEach(n => {
      if (!n.content && n.text) n.content = n.text;
      if (!n.branches && n.choices) {
        n.branches = n.choices.map(c => ({
          text: c.text,
          next_node_id: c.next_node_id || c.next_node || c.next,
        }));
      }
      if (n.type === 'ending' || ((!n.branches || !n.branches.length) && !n.choices)) n.is_ending = true;
    });
    const nodeKeys = Object.keys(data.nodes || {});
    const state = { currentNode: data.start_node || nodeKeys[0], history: [], showAll: false };

    root.appendChild(titleBlock(data.title, data.synopsis));

    if (data.characters && data.characters.length) {
      const charRow = el('div', '', '');
      charRow.style.marginBottom = '10px';
      charRow.appendChild(el('span', 'cr-badge cr-badge-default', 'Characters'));
      data.characters.forEach(c => charRow.appendChild(badgeBlock(c, 'purple')));
      root.appendChild(charRow);
    }
    if (data.genre) {
      root.appendChild(badgeBlock(data.genre, 'info'));
    }

    const controls = el('div', '');
    controls.style.cssText = 'display:flex;gap:8px;align-items:center;margin:12px 0';
    const toggleBtn = el('button', 'cr-toggle-btn', 'Show All Nodes');
    controls.appendChild(toggleBtn);
    const historyEl = el('div', 'cr-node-history');
    controls.appendChild(historyEl);
    root.appendChild(controls);

    const storyContainer = el('div', '');
    root.appendChild(storyContainer);

    function updateHistory() {
      historyEl.innerHTML = '';
      state.history.forEach((nid, i) => {
        const crumb = el('span', `cr-node-crumb${nid === state.currentNode ? ' cr-node-crumb-active' : ''}`, esc(nid));
        crumb.onclick = () => { state.currentNode = nid; state.history = state.history.slice(0, i + 1); render(); };
        historyEl.appendChild(crumb);
      });
    }

    function renderCurrentNode() {
      storyContainer.innerHTML = '';
      const node = data.nodes[state.currentNode];
      if (!node) { storyContainer.appendChild(el('div', 'cr-ending', '<h3>The End</h3>')); return; }

      if (!state.history.includes(state.currentNode)) state.history.push(state.currentNode);
      updateHistory();

      const card = el('div', 'cr-card cr-card-active');
      if (node.tags && node.tags.length) {
        const tagRow = el('div', '');
        tagRow.style.marginBottom = '6px';
        node.tags.forEach(t => tagRow.appendChild(badgeBlock(t, 'default')));
        card.appendChild(tagRow);
      }
      card.appendChild(textBlock(node.content));

      if (node.is_ending) {
        card.appendChild(el('div', 'cr-ending', '<h3>The End</h3>'));
        const restart = el('button', 'cr-restart-btn', 'Read Again');
        restart.onclick = () => {
          state.currentNode = data.start_node || nodeKeys[0];
          state.history = [];
          render();
        };
        card.appendChild(restart);
      } else if (node.branches && node.branches.length) {
        card.appendChild(el('hr', 'cr-divider'));
        node.branches.forEach(b => {
          card.appendChild(choiceButton(b.text, () => {
            state.currentNode = b.next_node_id;
            render();
          }));
        });
      }

      storyContainer.appendChild(card);
    }

    function renderAllNodes() {
      storyContainer.innerHTML = '';
      updateHistory();
      nodeKeys.forEach(nid => {
        const node = data.nodes[nid];
        const isActive = nid === state.currentNode;
        const card = el('div', `cr-card${isActive ? ' cr-card-active' : ''}`);
        card.id = `cr-story-node-${nid}`;

        const header = el('div', '');
        header.style.cssText = 'display:flex;align-items:center;gap:6px;margin-bottom:6px';
        header.appendChild(badgeBlock(nid, isActive ? 'info' : 'default'));
        if (node.is_ending) header.appendChild(badgeBlock('ending', 'warning'));
        if (node.tags) node.tags.forEach(t => header.appendChild(badgeBlock(t, 'default')));
        card.appendChild(header);

        card.appendChild(textBlock(node.content));

        if (node.branches && node.branches.length) {
          const branchList = el('div', '');
          node.branches.forEach(b => {
            const link = el('span', 'cr-badge cr-badge-info', `→ ${b.text} [${b.next_node_id}]`);
            link.style.cursor = 'pointer';
            link.onclick = () => {
              state.currentNode = b.next_node_id;
              if (!state.history.includes(b.next_node_id)) state.history.push(b.next_node_id);
              render();
              const target = document.getElementById(`cr-story-node-${b.next_node_id}`);
              if (target) target.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            };
            branchList.appendChild(link);
          });
          card.appendChild(branchList);
        }
        storyContainer.appendChild(card);
      });
    }

    function render() {
      if (state.showAll) renderAllNodes(); else renderCurrentNode();
    }

    toggleBtn.onclick = () => {
      state.showAll = !state.showAll;
      toggleBtn.textContent = state.showAll ? 'Show Current Only' : 'Show All Nodes';
      toggleBtn.classList.toggle('cr-active', state.showAll);
      render();
    };

    render();
  }

  // ---------------------------------------------------------------------------
  // Web Simulation renderer
  // ---------------------------------------------------------------------------

  function humanLabel(name) {
    return name.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
  }

  function escRe(s) { return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); }

  function buildEvaluators(rules, varNames) {
    const sorted = [...varNames].sort((a, b) => b.length - a.length);
    return (rules || []).map(rawInput => {
      const raw = (typeof rawInput === 'object' && rawInput !== null)
        ? (rawInput.formula || rawInput.expression || rawInput.rule || JSON.stringify(rawInput))
        : String(rawInput);
      let clean = raw.replace(/\/\/.*$/gm, '').replace(/\/\*[\s\S]*?\*\//g, '').trim();
      if (!clean) return { text: raw };
      const eqIdx = clean.indexOf('=');
      if (eqIdx < 1) return { text: raw };
      const lhs = clean.slice(0, eqIdx).trim();
      const rhs = clean.slice(eqIdx + 1).trim();
      if (!lhs || !rhs) return { text: raw };
      let expr = rhs;
      sorted.forEach(n => {
        expr = expr.replace(new RegExp('\\b' + escRe(n) + '\\b', 'g'), `s["${n}"]`);
      });
      try {
        const fn = new Function('s', `"use strict"; const Math=globalThis.Math; function CLAMP(v,lo,hi){return Math.max(lo,Math.min(hi,v));} return (${expr});`);
        fn({});
        return { output: lhs, evaluate: fn, raw, formula: clean };
      } catch { return { text: raw }; }
    });
  }

  function normalizeSimData(data) {
    if (data.parameters && !data.variables) {
      data.variables = data.parameters.map(p => ({
        name: p.name,
        initial_value: p.default_value ?? p.initial_value ?? 0,
        min_value: p.min_value ?? 0,
        max_value: p.max_value ?? 100,
        unit: p.unit || '',
      }));
    }
    if (data.parameters && !data.controls) {
      const ruleOutputs = new Set();
      (data.rules || []).forEach(r => {
        if (typeof r === 'object' && r.operations) {
          r.operations.forEach(op => ruleOutputs.add(op.variable));
        } else if (typeof r === 'string') {
          const eq = r.indexOf('=');
          if (eq > 0) ruleOutputs.add(r.slice(0, eq).trim());
        }
      });
      const inputParams = (data.parameters || data.variables || []).filter(
        p => !ruleOutputs.has(p.name)
      );
      data.controls = inputParams.map((p, i) => ({
        control_id: `c${i + 1}`,
        label: p.label || p.display_name || humanLabel(p.name),
        type: 'slider',
        affects: [p.name],
        parameters: { min: p.min_value, max: p.max_value },
      }));
    }
    if (Array.isArray(data.rules) && data.rules.length > 0 && typeof data.rules[0] === 'object') {
      const flat = [];
      data.rules.forEach(r => {
        if (r.operations) {
          r.operations.forEach(op => {
            if (op.variable && op.operation) flat.push(`${op.variable} = ${op.operation}`);
          });
        } else if (r.formula || r.expression || r.rule) {
          flat.push(r.formula || r.expression || r.rule);
        }
      });
      data.rules = flat;
    }
  }

  function renderSimulation(root, data) {
    if (!data.title && data.simulation_name) data.title = data.simulation_name;
    normalizeSimData(data);
    if (!data.rules && data.variables) {
      data.rules = data.variables.filter(v => v.rule).map(v => v.rule);
    }
    const vars = data.variables || [];
    const controls = data.controls || [];
    const rules = data.rules || [];
    const varNames = vars.map(v => v.name);

    const inputNames = new Set();
    controls.forEach(c => (c.affects || []).forEach(n => inputNames.add(n)));

    const state = {};
    vars.forEach(v => { state[v.name] = v.initial_value; });

    const allEvs = buildEvaluators(rules, varNames);
    const formulaEvs = allEvs.filter(e => e.output);
    const textEvs = allEvs.filter(e => e.text);
    const outputDisplays = {};

    if (controls.length === 0 && vars.length > 0) {
      const ruleOutputs = new Set(allEvs.filter(e => e.output).map(e => e.output));
      vars.forEach(v => { if (!ruleOutputs.has(v.name)) inputNames.add(v.name); });
    }

    const inputVars = vars.filter(v => inputNames.has(v.name));
    const outputVars = vars.filter(v => !inputNames.has(v.name));

    root.appendChild(titleBlock(data.title || data.name, data.description));

    // --- Inputs card ---
    if (inputVars.length) {
      root.appendChild(el('h4', 'cr-section-title', 'Inputs'));
      const card = el('div', 'cr-card');
      const ctrlMap = {};
      controls.forEach(c => (c.affects || []).forEach(n => { ctrlMap[n] = c; }));

      inputVars.forEach(v => {
        const ctrl = ctrlMap[v.name];
        const label = ctrl ? ctrl.label : humanLabel(v.name);
        const min = v.min_value ?? 0;
        const max = v.max_value ?? 100;
        const slider = sliderControl(label, v.initial_value, min, max, v.unit || '', (val) => {
          state[v.name] = val;
          applyRules();
        });
        slider.dataset.varName = v.name;
        card.appendChild(slider);
      });
      root.appendChild(card);
    }

    // --- Calculate button ---
    const calcBtn = el('button', 'cr-calc-btn', 'Calculate');
    calcBtn.onclick = () => applyRules();
    root.appendChild(calcBtn);

    // --- Outputs card ---
    if (outputVars.length) {
      root.appendChild(el('h4', 'cr-section-title', 'Computed Results'));
      const card = el('div', 'cr-card');
      outputVars.forEach(v => {
        const row = el('div', 'cr-output-row');
        row.appendChild(el('span', 'cr-output-label', esc(humanLabel(v.name))));
        const valEl = el('span', 'cr-output-val', '0');
        row.appendChild(valEl);
        if (v.unit) row.appendChild(el('span', 'cr-output-unit', esc(v.unit)));
        card.appendChild(row);
        outputDisplays[v.name] = valEl;
      });
      root.appendChild(card);
    }

    // --- Formulas section ---
    if (formulaEvs.length || textEvs.length) {
      root.appendChild(el('h4', 'cr-section-title', 'Formulas'));
      formulaEvs.forEach(ev => {
        const card = el('div', 'cr-formula-card');
        const parts = ev.formula.split('=');
        card.appendChild(el('span', 'cr-formula-lhs', esc(humanLabel(parts[0].trim()))));
        card.appendChild(el('span', 'cr-formula-eq', '='));
        card.appendChild(el('span', 'cr-formula-rhs', esc(parts.slice(1).join('=').trim())));
        root.appendChild(card);
      });
      textEvs.forEach(ev => {
        root.appendChild(el('p', 'cr-formula-text', esc(ev.text)));
      });
    }

    // --- Buttons row ---
    const btnRow = el('div', '');
    btnRow.style.cssText = 'display:flex;justify-content:center;gap:10px;margin:14px 0';
    const resetBtn = el('button', 'cr-restart-btn', 'Reset');
    resetBtn.onclick = () => {
      vars.forEach(v => { state[v.name] = v.initial_value; });
      root.querySelectorAll('.cr-slider').forEach(slider => {
        const row = slider.closest('.cr-slider-row');
        const name = row && row.dataset.varName;
        if (name && state[name] !== undefined) {
          slider.value = state[name];
          const valSpan = row.querySelector('.cr-slider-val');
          if (valSpan) {
            const v = vars.find(x => x.name === name);
            const prec = (v.max_value - v.min_value) <= 10 ? 1 : 0;
            valSpan.textContent = `${parseFloat(state[name]).toFixed(prec)}${v.unit ? ' ' + v.unit : ''}`;
          }
        }
      });
      applyRules();
    };
    btnRow.appendChild(resetBtn);
    root.appendChild(btnRow);

    function applyRules() {
      formulaEvs.forEach(ev => {
        try {
          let val = ev.evaluate(state);
          const vDef = vars.find(x => x.name === ev.output);
          if (vDef) {
            if (vDef.min_value != null && val < vDef.min_value) val = vDef.min_value;
            if (vDef.max_value != null && val > vDef.max_value) val = vDef.max_value;
          }
          if (!isFinite(val)) val = 0;
          state[ev.output] = val;
        } catch { /* skip broken rule */ }
      });
      Object.entries(outputDisplays).forEach(([name, span]) => {
        const prec = Math.abs(state[name]) < 10 ? 2 : (Math.abs(state[name]) < 100 ? 1 : 0);
        span.textContent = parseFloat(state[name] || 0).toFixed(prec);
      });
    }

    applyRules();
  }

  // ---------------------------------------------------------------------------
  // Public API
  // ---------------------------------------------------------------------------

  return {
    render(container, data) {
      injectStyles();
      if (typeof container === 'string') container = document.getElementById(container);
      if (!container) { console.error('ContentRenderer: container not found'); return; }
      container.innerHTML = '';

      const d = unwrapContent(data);
      const root = el('div', 'cr-root');
      const fmt = detectFormat(d);
      if (!fmt) {
        root.appendChild(el('p', 'cr-text', 'Unknown content format — cannot render.'));
        container.appendChild(root);
        return;
      }

      switch (fmt) {
        case 'quiz': renderQuiz(root, d); break;
        case 'game': renderGame(root, d); break;
        case 'story': renderStory(root, d); break;
        case 'simulation': renderSimulation(root, d); break;
      }

      container.appendChild(root);
    },

    detectFormat,
  };
})();
