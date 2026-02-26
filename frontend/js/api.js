/**
 * Compass API Client
 * Handles all communication with the FastAPI backend.
 */

const API = (() => {
  const BASE_URL = window.location.origin;

  async function post(path, body) {
    const res = await fetch(`${BASE_URL}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return res.json();
  }

  async function get(path) {
    const res = await fetch(`${BASE_URL}${path}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  }

  /**
   * Send a chat message to the orchestrator (Nova 2 Lite).
   * @param {string} message - User's text message
   * @param {string} sessionId - Session ID
   * @returns {Promise<{session_id, response, tool_calls_made, session_data}>}
   */
  async function chat(message, sessionId) {
    return post('/api/chat', {
      message,
      session_id: sessionId,
      language: App.getLanguage(),
    });
  }

  /**
   * Upload a document for analysis via Nova Lite vision + Nova Embeddings.
   * @param {File} file - File object
   * @param {string} sessionId - Session ID
   * @param {string} message - Accompanying message
   * @returns {Promise<{session_id, response, document_analysis, embedding_matches}>}
   */
  async function uploadDocument(file, sessionId, message = "Please analyze this document I've uploaded.") {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('session_id', sessionId);
    formData.append('message', message);

    // Guess document type from filename
    const name = file.name.toLowerCase();
    let docType = 'unknown';
    if (name.includes('pay') || name.includes('stub') || name.includes('salary')) docType = 'pay_stub';
    else if (name.includes('tax') || name.includes('w2') || name.includes('1040')) docType = 'tax_return';
    else if (name.includes('bill') || name.includes('electric') || name.includes('gas')) docType = 'utility_bill';
    else if (name.includes('lease') || name.includes('rent')) docType = 'lease';
    else if (name.includes('medical') || name.includes('health')) docType = 'medical_record';
    formData.append('document_type', docType);

    const res = await fetch(`${BASE_URL}/api/document`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return res.json();
  }

  /**
   * Get full session data.
   * @param {string} sessionId
   */
  async function getSession(sessionId) {
    return get(`/api/session/${sessionId}`);
  }

  /**
   * Run a pre-seeded demo scenario via Nova 2 Lite agent loop.
   * @param {string} persona - 'single_parent' | 'senior' | 'veteran'
   * @returns {Promise<{session_id, persona, seed_message, response, tool_calls_made, session_data}>}
   */
  async function runDemo(persona) {
    return post(`/api/demo/${persona}`, {});
  }

  /**
   * Trigger Nova Act to navigate a benefit portal.
   * @param {string} sessionId
   * @param {string} programId - Program ID (e.g., 'snap', 'medicaid')
   * @param {object} userInfo - User info for pre-filling
   * @param {boolean} demoMode - Use local demo portal instead of live government site
   */
  async function navigatePortal(sessionId, programId, userInfo = {}, demoMode = true) {
    return post('/api/navigate', {
      session_id: sessionId,
      program_id: programId,
      user_info: userInfo,
      demo_mode: demoMode,
    });
  }

  /**
   * Semantic search for benefit programs using Nova Embeddings.
   * @param {string} text - Description of situation
   */
  async function semanticSearch(text) {
    return post('/api/embedding/search', { text });
  }

  return { chat, uploadDocument, getSession, runDemo, navigatePortal, semanticSearch };
})();
