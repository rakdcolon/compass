/**
 * Compass App Controller
 * Manages state, views, interactions, and all UI rendering.
 */

const App = (() => {
  let sessionId = generateSessionId();
  let language = 'en';
  let isLoading = false;
  let isDemoMode = false;
  let activeModel = null;

  function generateSessionId() {
    return 'sess_' + Math.random().toString(36).slice(2, 11);
  }

  // ===== View Management =====

  function showView(viewId) {
    ['view-welcome', 'view-chat'].forEach(id => {
      document.getElementById(id)?.classList.toggle('hidden', id !== viewId);
    });
    const isChat = viewId === 'view-chat';
    document.getElementById('bottom-bar')?.classList.toggle('hidden', !isChat);
    document.getElementById('model-strip')?.classList.toggle('hidden', !isChat);
  }

  function goHome() {
    Voice.disconnect();
    isDemoMode = false;
    document.getElementById('demo-badge')?.classList.add('hidden');
    showView('view-welcome');
    // Clear chat for fresh start
    const msgs = document.getElementById('chat-messages');
    if (msgs) msgs.innerHTML = '';
    sessionId = generateSessionId();
    setActiveModel(null);
  }

  // ===== Getters =====
  function getSessionId() { return sessionId; }
  function getLanguage() { return language; }
  function setLanguage(lang) {
    language = lang;
    showToast(`Language: ${lang === 'es' ? 'Español' : lang === 'fr' ? 'Français' : 'English'}`, 'info');
  }

  // ===== Nova Model Activity Indicator =====

  const MODEL_CONFIGS = {
    lite:  { id: 'pill-lite',  label: 'Nova 2 Lite',    loadingLabel: 'Amazon Nova 2 Lite' },
    sonic: { id: 'pill-sonic', label: 'Nova 2 Sonic',   loadingLabel: 'Amazon Nova 2 Sonic' },
    embed: { id: 'pill-embed', label: 'Nova Embeddings',loadingLabel: 'Amazon Nova Embeddings' },
    act:   { id: 'pill-act',   label: 'Nova Act',       loadingLabel: 'Amazon Nova Act' },
  };

  function setActiveModel(modelKey) {
    activeModel = modelKey;
    Object.entries(MODEL_CONFIGS).forEach(([key, config]) => {
      const pill = document.getElementById(config.id);
      if (!pill) return;
      pill.classList.toggle('active', key === modelKey);
    });
    // Update loading overlay model label
    const modelLabel = document.getElementById('loading-model');
    if (modelLabel && modelKey) {
      modelLabel.textContent = MODEL_CONFIGS[modelKey]?.loadingLabel || '';
    }
  }

  // ===== Demo Scenarios =====

  // Second-turn messages that provide enough detail to trigger tool calls
  const DEMO_FOLLOWUPS = {
    single_parent: "My annual income before losing my job was about $42,000, but right now it's $0. I live alone with my two kids — ages 3 and 7. My zip code is 94601. I have no savings and we really need food and healthcare help.",
    senior:        "I get about $1,200 a month from Social Security, so roughly $14,400 a year. I live alone. My zip code is 78201. I'm really struggling with my Medicare premiums and the electric bills.",
    veteran:       "I work part-time and earn about $18,000 a year. I live with my partner, so household of 2. My zip code is 33601. I have a 70% service-connected disability rating from the VA.",
  };

  async function runDemo(persona) {
    showView('view-chat');
    isDemoMode = true;
    document.getElementById('demo-badge')?.classList.remove('hidden');

    // Show voice panel but not active
    document.getElementById('voice-panel')?.classList.remove('hidden');

    const personaLabels = {
      single_parent: { emoji: '👩‍👧‍👦', label: 'Single Parent — Maria, Oakland CA' },
      senior:        { emoji: '👴', label: 'Senior Citizen — Robert, San Antonio TX' },
      veteran:       { emoji: '🎖️', label: 'Veteran — James, Tampa FL' },
    };

    const info = personaLabels[persona] || { emoji: '👤', label: persona };
    addMessage('system', `${info.emoji} Demo Scenario: ${info.label}`);
    showTypingIndicator();
    setActiveModel('lite');
    setLoading(true, 'Running full Nova 2 Lite agent loop...');

    try {
      // --- Turn 1: Seed message ---
      const result = await API.runDemo(persona);
      sessionId = result.session_id;
      removeTypingIndicator();
      addMessage('user', result.seed_message);
      addMessage('assistant', result.response, { toolCalls: result.tool_calls_made });

      if (result.session_data?.has_results) {
        updateResultsPanel(result.session_data);
      }

      // --- Turn 2: Auto follow-up with specific details ---
      const followup = DEMO_FOLLOWUPS[persona];
      if (followup && !result.session_data?.has_results) {
        // Small pause so the conversation reads naturally
        await new Promise(r => setTimeout(r, 600));

        showTypingIndicator();
        setLoading(true, 'Nova 2 Lite running eligibility analysis...');

        const result2 = await API.chat(followup, sessionId);
        sessionId = result2.session_id;
        removeTypingIndicator();

        addMessage('user', followup);
        addMessage('assistant', result2.response, { toolCalls: result2.tool_calls_made });

        if (result2.tool_calls_made?.length > 0) {
          const toolNames = result2.tool_calls_made.map(t => formatToolName(t.name)).join(' → ');
          addMessage('system', `Nova 2 Lite used tools: ${toolNames}`);
        }

        if (result2.session_data?.has_results) {
          updateResultsPanel(result2.session_data);
        }
      } else if (result.tool_calls_made?.length > 0) {
        const toolNames = result.tool_calls_made.map(t => formatToolName(t.name)).join(' → ');
        addMessage('system', `Nova 2 Lite used tools: ${toolNames}`);
      }

      // Invite continued conversation
      addMessage('system', '💬 Demo loaded — you can keep chatting to explore further');
      document.getElementById('chat-input')?.focus();

    } catch (err) {
      removeTypingIndicator();
      addMessage('system', `Demo error: ${err.message}`);
      showToast('Demo failed — check AWS credentials in .env', 'error');
    } finally {
      setLoading(false);
      setActiveModel(null);
    }
  }

  // ===== Voice Start =====

  async function startVoice() {
    showView('view-chat');
    document.getElementById('voice-panel')?.classList.remove('hidden');
    setActiveModel('sonic');

    addMessage('assistant',
      "Hello! I'm Compass, your AI benefits navigator. I'm powered by Amazon Nova 2 Sonic for voice. " +
      "Tell me about your situation — what kind of help are you looking for today?",
      { noAnimate: true }
    );

    try {
      await Voice.connect(sessionId, language);
      await Voice.startRecording();
    } catch (err) {
      showToast('Voice unavailable — using text mode.', 'warning');
      setActiveModel(null);
    }
  }

  // ===== Text Chat Start =====

  function startChat() {
    showView('view-chat');
    addMessage('assistant',
      "Hello! I'm Compass, your AI benefits navigator. " +
      "Tell me about your situation — are you having trouble with food, healthcare, rent, or something else? " +
      "I'll help you find programs you may qualify for.",
      { noAnimate: true }
    );
    document.getElementById('chat-input')?.focus();
  }

  // ===== Send Text Message =====

  async function sendMessage() {
    const input = document.getElementById('chat-input');
    const message = input?.value.trim();
    if (!message || isLoading) return;

    input.value = '';
    addMessage('user', message);
    showTypingIndicator();
    setActiveModel('lite');
    setLoading(true, 'Nova 2 Lite is analyzing your situation...');

    try {
      const result = await API.chat(message, sessionId);
      sessionId = result.session_id;

      removeTypingIndicator();
      addMessage('assistant', result.response, { toolCalls: result.tool_calls_made });

      if (result.tool_calls_made?.length > 0) {
        const names = result.tool_calls_made.map(t => formatToolName(t.name)).join(' → ');
        addMessage('system', `Nova 2 Lite used: ${names}`);
      }

      if (result.session_data?.has_results) {
        updateResultsPanel(result.session_data);
      }

    } catch (err) {
      removeTypingIndicator();
      addMessage('system', `Error: ${err.message}`);
      showToast(err.message, 'error');
    } finally {
      setLoading(false);
      setActiveModel(null);
    }
  }

  // ===== Document Upload =====

  async function uploadDocument(input) {
    const file = input?.files?.[0];
    if (!file) return;

    // Show preview
    const reader = new FileReader();
    reader.onload = e => {
      const img = document.getElementById('doc-preview-img');
      const card = document.getElementById('doc-preview-card');
      if (img && card) { img.src = e.target.result; card.classList.remove('hidden'); }
    };
    reader.readAsDataURL(file);

    addMessage('user', `📎 Uploaded: ${file.name}`);
    showTypingIndicator();

    // Embeddings first, then vision
    setActiveModel('embed');
    setLoading(true, 'Nova Embeddings matching document to programs...');

    // Brief pause to show embeddings model active
    await new Promise(r => setTimeout(r, 800));
    setActiveModel('lite');
    document.getElementById('loading-text').textContent = 'Nova 2 Lite analyzing document...';
    document.getElementById('loading-model').textContent = 'Amazon Nova 2 Lite Vision';

    try {
      const result = await API.uploadDocument(file, sessionId);
      sessionId = result.session_id;

      removeTypingIndicator();
      addMessage('assistant', result.response);

      if (result.document_analysis) {
        renderDocumentAnalysis(result.document_analysis);
      }

      if (result.embedding_matches?.length > 0) {
        addMessage('system', `Nova Embeddings matched ${result.embedding_matches.length} programs via semantic similarity`);
      }

      if (result.session_data?.has_results) {
        updateResultsPanel(result.session_data);
      }

    } catch (err) {
      removeTypingIndicator();
      addMessage('system', `Document analysis failed: ${err.message}`);
      showToast('Could not analyze document', 'error');
    } finally {
      setLoading(false);
      setActiveModel(null);
      if (input) input.value = '';
    }
  }

  /**
   * Upload one of the pre-generated sample documents.
   * Fetches the image from /static/samples/ and submits it as if the user uploaded it.
   */
  async function uploadSample(filename) {
    try {
      showToast(`Loading sample: ${filename}`, 'info');
      const res = await fetch(`/static/samples/${filename}`);
      if (!res.ok) throw new Error('Sample not found. Run the server first to generate samples.');
      const blob = await res.blob();
      const file = new File([blob], filename, { type: 'image/png' });

      // Show preview
      const reader = new FileReader();
      reader.onload = e => {
        const img = document.getElementById('doc-preview-img');
        const card = document.getElementById('doc-preview-card');
        if (img && card) { img.src = e.target.result; card.classList.remove('hidden'); }
      };
      reader.readAsDataURL(file);

      addMessage('user', `📎 Sample document: ${filename.replace(/_/g, ' ').replace('.png', '')}`);
      showTypingIndicator();
      setActiveModel('embed');
      setLoading(true, 'Nova Embeddings matching document to programs...');

      await new Promise(r => setTimeout(r, 600));
      setActiveModel('lite');
      document.getElementById('loading-text').textContent = 'Nova 2 Lite analyzing document with vision...';
      document.getElementById('loading-model').textContent = 'Amazon Nova 2 Lite Vision';

      const result = await API.uploadDocument(file, sessionId, `I've uploaded a sample ${filename.includes('pay') ? 'pay stub' : 'utility bill'} for analysis.`);
      sessionId = result.session_id;
      removeTypingIndicator();
      addMessage('assistant', result.response);

      if (result.document_analysis) renderDocumentAnalysis(result.document_analysis);
      if (result.embedding_matches?.length > 0) {
        addMessage('system', `Nova Embeddings: ${result.embedding_matches.length} programs matched by semantic similarity`);
      }
      if (result.session_data?.has_results) updateResultsPanel(result.session_data);

    } catch (err) {
      removeTypingIndicator();
      showToast(err.message, 'error');
    } finally {
      setLoading(false);
      setActiveModel(null);
    }
  }

  // ===== Nova Act Portal Navigation =====

  async function navigatePortal(programId, programName) {
    setActiveModel('act');
    showToast(`Nova Act is navigating the ${programName} portal...`, 'info');
    setLoading(true, `Nova Act navigating ${programName} portal...`);
    document.getElementById('loading-model').textContent = 'Amazon Nova Act';

    try {
      const result = await API.navigatePortal(sessionId, programId, {}, true);
      setLoading(false);
      setActiveModel(null);

      if (result.status === 'success') {
        const stepsText = (result.steps_completed || []).map((s, i) => `${i+1}. ${s}`).join('\n');
        addMessage('assistant',
          `Nova Act successfully navigated the ${programName} portal and completed these steps:\n\n${stepsText}\n\n` +
          `**Confirmation:** ${result.confirmation || 'Application submitted'}`
        );
        showToast(`Nova Act: ${result.steps_completed?.length || 0} steps completed`, 'success');
      } else {
        const steps = (result.instructions || []).join('\n');
        addMessage('assistant', `To apply for ${programName}:\n\n${steps}`);
        if (result.apply_url) window.open(result.apply_url, '_blank');
      }
    } catch (err) {
      setLoading(false);
      setActiveModel(null);
      showToast('Nova Act error', 'error');
    }
  }

  // ===== Results Panel =====

  function updateResultsPanel(sessionData) {
    document.getElementById('results-placeholder')?.classList.add('hidden');

    if (sessionData.eligible_programs?.length > 0) {
      renderPrograms(sessionData.eligible_programs);
    }
    if (sessionData.local_resources?.length > 0) {
      renderResources(sessionData.local_resources);
    }
    if (sessionData.action_plan) {
      renderActionPlan(sessionData.action_plan);
    }
  }

  // ===== Benefits Value Calculator =====

  function calculateTotalValue(programs) {
    let monthlyTotal = 0;
    programs.forEach(p => {
      const val = p.estimated_value || '';
      // Match patterns like "$600/month", "~$346/month", "$2,000-$5,000/year"
      const monthMatch = val.match(/\$?([\d,]+)(?:–|-[\d,]+)?\/month/i);
      const yearMatch  = val.match(/\$?([\d,]+)(?:–|-[\d,]+)?\/year/i);
      const upToMatch  = val.match(/up to \$?([\d,]+)/i);

      if (monthMatch) {
        monthlyTotal += parseInt(monthMatch[1].replace(/,/g, ''), 10);
      } else if (yearMatch) {
        monthlyTotal += parseInt(yearMatch[1].replace(/,/g, ''), 10) / 12;
      } else if (upToMatch) {
        monthlyTotal += parseInt(upToMatch[1].replace(/,/g, ''), 10) / 12;
      }
    });
    return Math.round(monthlyTotal * 12);
  }

  function renderPrograms(programs) {
    const card = document.getElementById('programs-card');
    const list = document.getElementById('programs-list');
    if (!card || !list) return;

    card.classList.remove('hidden');
    list.innerHTML = '';

    // Value banner
    const totalAnnual = calculateTotalValue(programs);
    const banner = document.getElementById('value-banner');
    const totalEl = document.getElementById('value-total');
    const subline = document.getElementById('value-subline');
    if (banner && totalEl && totalAnnual > 0) {
      banner.classList.remove('hidden');
      // Animate count-up
      animateCountUp(totalEl, 0, totalAnnual, 1200);
      if (subline) subline.textContent = `Across ${programs.length} program${programs.length !== 1 ? 's' : ''} you likely qualify for`;
    }

    const categoryEmojis = {
      food: '🥗', healthcare: '🏥', cash_assistance: '💰',
      utilities: '💡', disability_income: '♿', housing: '🏠', tax_credit: '📋',
    };

    programs.slice(0, 7).forEach(program => {
      const likelihood = (program.likelihood || 'medium').toLowerCase();
      const emoji = categoryEmojis[program.category] || '✓';
      const div = document.createElement('div');
      div.className = `program-card ${likelihood}`;
      div.innerHTML = `
        <div class="flex items-start justify-between gap-2 mb-1">
          <div class="flex items-center gap-1.5 min-w-0">
            <span>${emoji}</span>
            <span class="text-sm font-medium text-white truncate">${escapeHtml(program.short_name || program.name)}</span>
          </div>
          <span class="text-xs px-1.5 py-0.5 rounded likelihood-${likelihood} font-medium flex-shrink-0">${likelihood.charAt(0).toUpperCase()+likelihood.slice(1)}</span>
        </div>
        <div class="text-xs text-slate-400 mb-2 line-clamp-1">${escapeHtml(program.estimated_value || '')}</div>
        <div class="flex gap-2 flex-wrap">
          <a href="${escapeHtml(program.apply_url || '#')}" target="_blank" rel="noopener"
             class="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1 transition-colors">
            Apply Now ↗
          </a>
          <button onclick="App.navigatePortal('${program.id}','${escapeHtml(program.short_name||program.name)}')"
                  class="text-xs text-orange-400 hover:text-orange-300 flex items-center gap-1 ml-auto transition-colors">
            <span class="nova-act-badge">Nova Act</span>
          </button>
        </div>`;
      list.appendChild(div);
    });
  }

  function renderResources(resources) {
    const card = document.getElementById('resources-card');
    const list = document.getElementById('resources-list');
    if (!card || !list) return;

    card.classList.remove('hidden');
    list.innerHTML = '';

    const typeEmojis = {
      food_bank:'🥫', pantry:'🧺', clinic:'🏥', free_clinic:'💊',
      shelter:'🏠', energy_assistance:'💡', benefits_navigator:'🧭',
      legal_aid:'⚖️', employment:'💼', crisis_support:'🆘',
    };

    resources.slice(0, 5).forEach(r => {
      const emoji = typeEmojis[r.type] || '📍';
      const div = document.createElement('div');
      div.className = 'resource-card';
      div.innerHTML = `
        <div class="flex items-start gap-2">
          <span>${emoji}</span>
          <div class="flex-1 min-w-0">
            <div class="text-xs font-medium text-white truncate">${escapeHtml(r.name)}</div>
            <div class="text-xs text-slate-400">${escapeHtml(r.phone || '')}</div>
            ${r.website ? `<a href="${escapeHtml(r.website)}" target="_blank" class="text-xs text-blue-400 hover:text-blue-300">Visit →</a>` : ''}
          </div>
        </div>`;
      list.appendChild(div);
    });
  }

  function renderActionPlan(plan) {
    const card = document.getElementById('action-plan-card');
    const steps = document.getElementById('action-plan-steps');
    if (!card || !steps) return;

    card.classList.remove('hidden');
    steps.innerHTML = '';

    (plan.all_steps || []).forEach(step => {
      const div = document.createElement('div');
      div.className = `action-step ${step.urgency || 'short_term'}`;
      div.innerHTML = `
        <div class="action-step-number">${step.step}</div>
        <div class="flex-1 min-w-0">
          <div class="text-xs font-semibold text-white">${escapeHtml(step.title)}</div>
          ${step.action ? `<div class="text-xs text-blue-400 mt-0.5">${escapeHtml(step.action)}</div>` : ''}
        </div>`;
      steps.appendChild(div);
    });
  }

  function renderDocumentAnalysis(analysis) {
    const div = document.getElementById('doc-analysis-result');
    if (!div) return;
    const fields = analysis.key_fields || {};
    const items = [];
    if (analysis.document_type_detected) items.push(`Type: ${analysis.document_type_detected.replace(/_/g,' ')}`);
    if (analysis.annual_income_estimate) items.push(`Est. income: $${Number(analysis.annual_income_estimate).toLocaleString()}/yr`);
    if (fields.employer_name) items.push(`Employer: ${fields.employer_name}`);
    if (analysis.confidence) items.push(`Confidence: ${analysis.confidence}`);
    div.innerHTML = items.map(i => `<div class="flex items-center gap-1"><span class="text-green-400">✓</span>${escapeHtml(i)}</div>`).join('');
  }

  // ===== Agent Reasoning Trace =====

  function renderReasoningTrace(toolCalls) {
    if (!toolCalls?.length) return null;

    const wrapper = document.createElement('div');
    wrapper.className = 'reasoning-trace-wrapper';

    const toggle = document.createElement('button');
    toggle.className = 'reasoning-toggle';
    toggle.innerHTML = `
      <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="toggle-chevron">
        <polyline points="6 9 12 15 18 9"/>
      </svg>
      See Nova 2 Lite's reasoning (${toolCalls.length} tool${toolCalls.length !== 1 ? 's' : ''})`;

    const trace = document.createElement('div');
    trace.className = 'reasoning-trace hidden';

    toolCalls.forEach((call, i) => {
      const step = document.createElement('div');
      step.className = 'trace-step';

      const inputSummary = summarizeToolInput(call.name, call.input || {});

      step.innerHTML = `
        <div class="trace-dot"></div>
        <div class="trace-content">
          <div class="trace-tool">Nova 2 Lite → <strong>${formatToolName(call.name)}</strong></div>
          <div class="trace-input">${escapeHtml(inputSummary)}</div>
        </div>`;
      trace.appendChild(step);
    });

    toggle.onclick = () => {
      const open = !trace.classList.contains('hidden');
      trace.classList.toggle('hidden', open);
      toggle.querySelector('.toggle-chevron').style.transform = open ? '' : 'rotate(180deg)';
    };

    wrapper.appendChild(toggle);
    wrapper.appendChild(trace);
    return wrapper;
  }

  function summarizeToolInput(toolName, input) {
    if (toolName === 'check_benefit_eligibility') {
      return `Income $${(input.annual_income||0).toLocaleString()}/yr, ${input.household_size||'?'} people, ${input.state||'?'}, age ${input.age||'?'}`;
    }
    if (toolName === 'find_local_resources') {
      return `Location: ${input.zip_code||'?'}, needs: ${(input.needs_list||[]).join(', ')}`;
    }
    if (toolName === 'analyze_document') {
      return `Document type: ${input.document_type||'unknown'}`;
    }
    if (toolName === 'create_action_plan') {
      return `Compiling plan for ${(input.eligible_programs||[]).length} programs`;
    }
    return JSON.stringify(input).slice(0, 80);
  }

  // ===== Chat Message Rendering =====

  function addMessage(role, text, options = {}) {
    const container = document.getElementById('chat-messages');
    if (!container) return;

    const div = document.createElement('div');
    div.className = 'message-animate';

    if (role === 'user') {
      div.innerHTML = `<div class="flex justify-end"><div class="bubble-user text-sm leading-relaxed">${escapeHtml(text)}</div></div>`;
    } else if (role === 'assistant') {
      const msgEl = document.createElement('div');
      msgEl.className = 'flex gap-2 items-start';
      msgEl.innerHTML = `
        <div class="w-7 h-7 rounded-full bg-gradient-to-br from-blue-500 to-cyan-400 flex-shrink-0 flex items-center justify-center mt-0.5">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <circle cx="12" cy="12" r="10"/><polygon points="16.24,7.76 14.12,14.12 7.76,16.24 9.88,9.88"/>
          </svg>
        </div>
        <div class="flex-1 min-w-0">
          <div class="bubble-assistant text-sm leading-relaxed">${formatAssistantText(text)}</div>
        </div>`;

      div.appendChild(msgEl);

      // Append reasoning trace if tool calls were made
      if (options.toolCalls?.length > 0) {
        const trace = renderReasoningTrace(options.toolCalls);
        if (trace) {
          const traceWrapper = document.createElement('div');
          traceWrapper.className = 'ml-9 mt-1';
          traceWrapper.appendChild(trace);
          div.appendChild(traceWrapper);
        }
      }
    } else if (role === 'system') {
      div.innerHTML = `<div class="bubble-system">${escapeHtml(text)}</div>`;
    }

    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
  }

  function showTypingIndicator() {
    const container = document.getElementById('chat-messages');
    if (!container) return;
    const div = document.createElement('div');
    div.id = 'typing-indicator';
    div.innerHTML = `
      <div class="flex gap-2 items-start">
        <div class="w-7 h-7 rounded-full bg-gradient-to-br from-blue-500 to-cyan-400 flex-shrink-0 flex items-center justify-center">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <circle cx="12" cy="12" r="10"/><polygon points="16.24,7.76 14.12,14.12 7.76,16.24 9.88,9.88"/>
          </svg>
        </div>
        <div class="bubble-assistant flex items-center gap-1.5 py-3">
          <span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span>
        </div>
      </div>`;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
  }

  function removeTypingIndicator() {
    document.getElementById('typing-indicator')?.remove();
  }

  function setLoading(loading, text = 'Processing...') {
    isLoading = loading;
    const overlay = document.getElementById('loading-overlay');
    if (!overlay) return;
    document.getElementById('loading-text').textContent = text;
    overlay.classList.toggle('hidden', !loading);
  }

  function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;
    const colors = {
      info:'text-blue-300 border-blue-700/50', success:'text-green-300 border-green-700/50',
      error:'text-red-300 border-red-700/50', warning:'text-yellow-300 border-yellow-700/50',
    };
    const toast = document.createElement('div');
    toast.className = `toast ${colors[type] || colors.info}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => {
      toast.style.cssText = 'opacity:0;transform:translateX(20px);transition:all .3s ease-out';
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  }

  // ===== Utilities =====

  function animateCountUp(el, from, to, duration) {
    const start = performance.now();
    function update(now) {
      const progress = Math.min((now - start) / duration, 1);
      const value = Math.round(from + (to - from) * easeOut(progress));
      el.textContent = '$' + value.toLocaleString();
      if (progress < 1) requestAnimationFrame(update);
    }
    requestAnimationFrame(update);
  }

  function easeOut(t) { return 1 - Math.pow(1 - t, 3); }

  function escapeHtml(text) {
    const div = document.createElement('div');
    div.appendChild(document.createTextNode(String(text || '')));
    return div.innerHTML;
  }

  function formatAssistantText(text) {
    return escapeHtml(text)
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\n\n/g, '</p><p class="mt-2">')
      .replace(/\n/g, '<br/>');
  }

  function formatToolName(name) {
    return {
      check_benefit_eligibility: 'Eligibility Check',
      find_local_resources: 'Resource Finder',
      analyze_document: 'Document Analysis',
      create_action_plan: 'Action Plan',
    }[name] || name;
  }

  return {
    startVoice, startChat, sendMessage, uploadDocument, uploadSample,
    navigatePortal, runDemo, goHome, getSessionId, getLanguage,
    setLanguage, setActiveModel, addMessage, showToast,
  };
})();
