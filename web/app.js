/* 红源智导 · 前端交互（原生 JS，无构建步骤） */
const S = { token: null, user: null, sid: 'sid-' + Math.random().toString(36).slice(2, 8), busy: false };

const QUICK = [
  '帮我安排延安两天红色研学',
  '介绍延安革命纪念馆',
  '洛川苹果有哪些可核验的数据',
  '给洛川苹果写一段直播开场',
  '延安红色旅游2024年接待多少人',
];

/* ---------------- 基础 ---------------- */
async function api(path, opts = {}) {
  const headers = Object.assign({ 'Content-Type': 'application/json' }, opts.headers || {});
  if (S.token) headers['Authorization'] = 'Bearer ' + S.token;
  const res = await fetch(path, Object.assign({}, opts, { headers }));
  const data = await res.json().catch(() => ({}));
  if (res.status === 401) { logout(); throw new Error('登录已过期'); }
  if (!res.ok) throw new Error(data.error || ('请求失败 ' + res.status));
  return data;
}

function esc(s) {
  return String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

function md(text) {
  const lines = esc(text || '').split('\n');
  let out = '', inList = false;
  const inline = s => s
    .replace(/\*\*(.+?)\*\*/g, '<b>$1</b>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/(^|[\s(（])_([^_]+)_(?=[\s，。；)）]|$)/g, '$1<em class="muted">$2</em>');
  for (let raw of lines) {
    const line = raw.trim();
    if (!line) { if (inList) { out += '</ul>'; inList = false; } continue; }
    if (/^[-·]\s+/.test(line)) {
      if (!inList) { out += '<ul>'; inList = true; }
      out += '<li>' + inline(line.replace(/^[-·]\s+/, '')) + '</li>';
      continue;
    }
    if (inList) { out += '</ul>'; inList = false; }
    out += '<p>' + inline(line) + '</p>';
  }
  if (inList) out += '</ul>';
  return out;
}

/* ---------------- 登录 ---------------- */
async function doLogin() {
  const u = document.getElementById('username').value.trim();
  const p = document.getElementById('password').value;
  const err = document.getElementById('loginErr');
  err.textContent = '';
  if (!u || !p) { err.textContent = '请输入账号和密码'; return; }
  try {
    const data = await api('/api/login', { method: 'POST', body: JSON.stringify({ username: u, password: p }) });
    S.token = data.token; S.user = data.user;
    enterApp();
  } catch (e) { err.textContent = e.message; }
}

function enterApp() {
  document.getElementById('loginView').style.display = 'none';
  document.getElementById('appView').classList.add('on');
  document.getElementById('userName').textContent = S.user.display || S.user.username;
  document.getElementById('userRole').textContent = S.user.role;
  document.getElementById('userAva').textContent = (S.user.display || S.user.username).slice(0, 1);
  applyRole();
  renderQuick();
  bootstrap();
  if (!document.getElementById('messages').children.length) welcome();
}

/* 运营看板仅 demo 账号可见；judge 账号隐藏入口且不可访问 */
function applyRole() {
  const isDemo = S.user && S.user.role === 'demo';
  const nav = document.querySelector('.nav-item[data-page="admin"]');
  const page = document.getElementById('page-admin');
  if (nav) nav.style.display = isDemo ? 'flex' : 'none';
  if (!isDemo && page && !page.classList.contains('hidden')) go('chat');
}

function logout() {
  S.token = null;
  document.getElementById('appView').classList.remove('on');
  document.getElementById('loginView').style.display = 'grid';
}

/* ---------------- 导航 ---------------- */
const TITLES = { chat: ['智能导览', '延安 · 红色文旅与农产品 IP'], plan: ['行程规划', '点位取自知识库，按片区成团'], ip: ['农品 IP 工坊', '事实槽位生成 + 广告法合规检查'], kb: ['知识库溯源', '每条事实都有出处'], admin: ['运营看板', '真实会话日志统计'] };

function go(page) {
  if (page === 'admin' && (!S.user || S.user.role !== 'demo')) page = 'chat';
  document.querySelectorAll('.nav-item').forEach(n => n.classList.toggle('on', n.dataset.page === page));
  document.querySelectorAll('.page').forEach(p => p.classList.add('hidden'));
  document.getElementById('page-' + page).classList.remove('hidden');
  document.getElementById('composerWrap').style.display = page === 'chat' ? 'block' : 'none';
  document.getElementById('pageTitle').textContent = TITLES[page][0];
  document.getElementById('pageMeta').textContent = TITLES[page][1];
  if (page === 'admin') loadAdmin();
  if (page === 'kb' && !document.getElementById('kbOut').dataset.loaded) searchKb();
}

document.querySelectorAll('.nav-item').forEach(n => n.addEventListener('click', () => go(n.dataset.page)));

/* ---------------- 对话 ---------------- */
function welcome() {
  addBot({
    text: '我是**红源智导**，服务革命老区延安的 AI 导览智能体。\n' +
      '可以问我：红色景点讲解、1–4 天行程、洛川苹果等老区农品的产地事实与推广文案、革命老区振兴政策。\n' +
      '门票、开放时间、天气这类实时信息我不猜，会直接给你官方查询入口。',
    sources: [], cards: [], trace: { intent: 'greeting' },
    followups: ['帮我安排延安两天红色研学', '介绍枣园革命旧址', '洛川苹果品牌价值是多少']
  });
}

function renderQuick() {
  document.getElementById('quickRow').innerHTML = QUICK.map(q =>
    `<span class="followup" onclick="ask('${esc(q)}')">${esc(q)}</span>`).join('');
}

function addUser(text) {
  const box = document.getElementById('messages');
  const el = document.createElement('div');
  el.className = 'msg user';
  el.innerHTML = `<div class="ava">我</div><div class="bubble">${md(text)}</div>`;
  box.appendChild(el);
  scrollBottom();
}

function addBot(reply) {
  const box = document.getElementById('messages');
  const el = document.createElement('div');
  el.className = 'msg bot';
  let html = `<div class="ava">智</div><div class="bubble">${md(reply.text)}`;
  html += renderCards(reply.cards || []);
  if (reply.sources && reply.sources.length) {
    html += '<div class="sources">' + reply.sources.map(s => {
      const label = [s.name, s.doc, s.date].filter(Boolean).join(' · ');
      const href = s.url || '#';
      return `<a class="source-chip" href="${esc(href)}" target="_blank" rel="noopener" title="${esc(label)}">来源 ${esc(label)}</a>`;
    }).join('') + '</div>';
  }
  const tr = reply.trace || {};
  const hits = (tr.retrieved && tr.retrieved.length) ? tr.retrieved.length : 0;
  const mode = tr.mode === 'deepseek-api' ? ('DeepSeek API · ' + esc(tr.model || '')) : '本地规则';
  const rt = tr.realtime ? `<span>实时联网 <b>${tr.web_hits || 0}</b> 条</span>` : '<span>实时联网 <b>关</b></span>';
  html += `<div class="trace"><span>意图 <b>${esc(tr.intent || '-')}</b></span>` +
    `<span>检索命中 <b>${hits}</b> 条</span>` +
    `<span>时延 <b>${tr.latency_ms || '-'}</b> ms</span>` +
    `<span>生成 <b>${mode}</b></span>` + rt +
    (tr.api_error ? '<span style="color:#b4232b">接口异常，已回退本地</span>' : '') + `</div>`;
  if (reply.followups && reply.followups.length) {
    html += '<div class="followups">' + reply.followups.map(f =>
      `<span class="followup" onclick="ask('${esc(f)}')">${esc(f)}</span>`).join('') + '</div>';
  }
  html += '</div>';
  el.innerHTML = html;
  box.appendChild(el);
  scrollBottom();
  if (reply.intent === 'ip' || reply.intent === 'product') loadIpProducts();
}

function renderCards(cards) {
  let html = '';
  for (const c of cards) {
    if (c.type === 'plan') {
      html += `<div class="card"><div class="card-title">${esc(c.title)}<span class="pill">路线卡</span></div>`;
      c.days.forEach(d => {
        html += `<div class="day"><div class="day-head">D${d.day} · ${esc(d.theme)}</div>`;
        d.stops.forEach(s => {
          html += `<div class="stop"><div class="t">${esc(s.time)}</div><div><div class="n">${esc(s.name)}</div><div class="d">${esc(s.area)} · 建议 ${s.minutes} 分钟</div></div></div>`;
        });
        html += '</div>';
      });
      html += `<div class="card-foot">${c.notes.map(esc).join('<br>')}</div></div>`;
    }
    if (c.type === 'product') {
      const ok = c.compliance && c.compliance.pass;
      html += `<div class="card"><div class="card-title">${esc(c.product.name)}<span class="pill">农品卡</span></div>`;
      html += `<div class="prod"><div class="nm">${esc(c.product.region || '')}</div><div class="rg">${esc(c.product.gi || '')}</div></div>`;
      html += `<div style="margin-top:10px"><span class="compliance ${ok ? 'ok' : 'bad'}">${ok ? '✓ 广告法合规检查通过' : '! 命中风险词：' + esc((c.compliance.hits || []).join('、'))}</span></div></div>`;
    }
    if (c.type === 'product_list') {
      html += `<div class="prod-grid">` + c.items.map(p =>
        `<div class="prod" onclick="ask('给${esc(p.name)}写一段直播开场')"><div class="nm">${esc(p.name)}</div><div class="rg">${esc(p.region || '')}</div><span class="gi">${esc(p.gi || '产地信息待补')}</span></div>`
      ).join('') + `</div>`;
    }
    if (c.type === 'spot_list') {
      html += `<div class="prod-grid">` + c.items.map(p =>
        `<div class="prod" onclick="ask('介绍${esc(p.name)}')"><div class="nm">${esc(p.name)}</div><div class="rg">${esc(p.one_line || '')}</div><span class="gi">${esc(p.level || p.area || '')}</span></div>`
      ).join('') + `</div>`;
    }
  }
  return html;
}

function scrollBottom() {
  const p = document.getElementById('page-chat');
  p.scrollTop = p.scrollHeight;
}

function ask(text) {
  document.getElementById('input').value = text;
  send();
}

async function send() {
  if (S.busy) return;
  const input = document.getElementById('input');
  const text = input.value.trim();
  if (!text) return;
  input.value = '';
  autoGrow();
  addUser(text);
  S.busy = true;
  document.getElementById('sendBtn').disabled = true;
  try {
    const reply = await api('/api/chat', { method: 'POST', body: JSON.stringify({ message: text, session_id: S.sid }) });
    addBot(reply);
  } catch (e) {
    addBot({ text: '出错了：' + e.message, sources: [], cards: [], trace: {} });
  } finally {
    S.busy = false;
    document.getElementById('sendBtn').disabled = false;
  }
}

/* ---------------- 行程 ---------------- */
async function genPlan() {
  const days = document.getElementById('planDays').value;
  const theme = document.getElementById('planTheme').value;
  const pace = document.getElementById('planPace').value;
  const out = document.getElementById('planOut');
  out.innerHTML = '<div class="empty">生成中…</div>';
  const card = await api('/api/plan', { method: 'POST', body: JSON.stringify({ days: +days, theme, pace }) });
  out.innerHTML = renderCards([{ type: 'plan', ...card }]);
  out.dataset.loaded = '1';
}

/* ---------------- IP ---------------- */
async function loadIpProducts() {
  const sel = document.getElementById('ipProduct');
  if (sel.dataset.loaded) return;
  const data = await api('/api/products');
  sel.innerHTML = data.items.map(p => `<option>${esc(p.name)}</option>`).join('');
  sel.dataset.loaded = '1';
}

async function genCopy() {
  const product = document.getElementById('ipProduct').value;
  const channel = document.getElementById('ipChannel').value;
  const audience = document.getElementById('ipAudience').value;
  const out = document.getElementById('ipOut');
  out.innerHTML = '<div class="empty">生成中…</div>';
  const r = await api('/api/copy', { method: 'POST', body: JSON.stringify({ product, channel, audience }) });
  if (!r.ok) { out.innerHTML = `<div class="empty">${esc(r.reason)}</div>`; return; }
  let html = '<div class="card">';
  r.blocks.forEach(b => { html += `<div class="day-head">${esc(b.label)}</div><div style="font-size:13.5px;line-height:1.85;white-space:pre-wrap">${esc(b.content)}</div>`; });
  html += `<div style="margin-top:12px"><span class="compliance ${r.compliance.pass ? 'ok' : 'bad'}">${r.compliance.pass ? '✓ 广告法风险词检查通过' : '! 命中：' + esc(r.compliance.hits.join('、'))}</span></div>`;
  html += `<div class="card-foot">${esc(r.disclaimer)}</div></div>`;
  out.innerHTML = html;
}

/* ---------------- 知识库 ---------------- */
async function searchKb() {
  const q = document.getElementById('kbQ').value.trim() || '延安';
  const out = document.getElementById('kbOut');
  out.innerHTML = '<div class="empty">检索中…</div>';
  const data = await api('/api/kb/search?q=' + encodeURIComponent(q));
  if (!data.items.length) { out.innerHTML = '<div class="empty">没有命中，换一个关键词试试。</div>'; return; }
  out.innerHTML = data.items.map(it => `
    <div class="kb-item">
      <div class="h"><b>${esc(it.title)}</b><span class="cat">相关度 ${it.score}</span></div>
      <p>${esc(it.text)}</p>
      <div class="s">来源：${esc([it.source.name, it.source.doc, it.source.date].filter(Boolean).join(' · '))}</div>
    </div>`).join('');
  out.dataset.loaded = '1';
}

/* ---------------- 看板 ---------------- */
async function loadAdmin() {
  const d = await api('/api/admin/stats');
  document.getElementById('statGrid').innerHTML = [
    ['累计对话', d.total_chats, '轮'], ['平均时延', d.avg_latency_ms, 'ms'],
    ['知识库条目', d.kb_docs, '条'], ['风险词词表', d.banned_terms, '个'],
    ['反馈有用率', d.feedback.total ? Math.round(d.feedback.helpful / d.feedback.total * 100) : 0, '%'],
  ].map(([k, v, u]) => `<div class="stat"><div class="k">${k}</div><div class="v">${v}<span class="u">${u}</span></div></div>`).join('');
  const rows = (d.intent_dist || []).map(([k, v]) =>
    `<tr><td>${esc(k)}</td><td>${v}</td><td><div style="height:7px;border-radius:4px;background:linear-gradient(90deg,#b4232b,#d8b25e);width:${Math.min(100, v * 8)}%"></div></td></tr>`).join('');
  document.getElementById('adminBody').innerHTML =
    `<table><thead><tr><th>意图</th><th>次数</th><th>占比</th></tr></thead><tbody>${rows || '<tr><td colspan="3">暂无数据</td></tr>'}</tbody></table>` +
    `<div class="note">日志字段：时间、账号、会话、问句、意图、时延、命中来源、反馈。不记录密码与身份证等个人信息。</div>`;
}

/* ---------------- 初始化 ---------------- */
function autoGrow() {
  const t = document.getElementById('input');
  t.style.height = 'auto';
  t.style.height = Math.min(120, t.scrollHeight) + 'px';
}

async function bootstrap() {
  try {
    const health = await fetch('/health').then(r => r.json());
    document.getElementById('kbCount').textContent = health.kb_docs;
    const cfg = await fetch('/api/config').then(r => r.json());
    const tag = document.querySelector('.tagline');
    if (tag) tag.textContent = cfg.llm
      ? ('DeepSeek API 驱动 · 实时联网' + (cfg.search ? '已开' : '关'))
      : '本地规则引擎 · 零外部调用';
  } catch (e) { }
  loadIpProducts();
}

document.getElementById('input').addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); }
});
document.getElementById('input').addEventListener('input', autoGrow);

/* ---------------- 预览模式（仅本机截图用） ---------------- */
(async function preview() {
  const params = new URLSearchParams(location.search);
  const scenario = params.get('preview');
  if (!scenario) return;
  const r = await fetch('/api/preview_token').then(x => x.json());
  S.token = r.token;
  S.user = { display: '演示预览', username: 'demo', role: 'demo' };
  enterApp();
  document.getElementById('messages').innerHTML = '';
  if (scenario === 'chat') {
    addUser('帮我安排延安两天红色研学，节奏别太赶');
    const a = await api('/api/chat', { method: 'POST', body: JSON.stringify({ message: '帮我安排延安两天红色研学，节奏别太赶', session_id: S.sid }) });
    addBot(a);
    addUser('介绍枣园革命旧址');
    const b = await api('/api/chat', { method: 'POST', body: JSON.stringify({ message: '介绍枣园革命旧址', session_id: S.sid }) });
    addBot(b);
  } else if (scenario === 'plan') {
    go('plan');
    document.getElementById('planDays').value = '2';
    await genPlan();
  } else if (scenario === 'ip') {
    go('ip');
    await loadIpProducts();
    document.getElementById('ipChannel').value = '直播';
    await genCopy();
  } else if (scenario === 'kb') {
    go('kb');
    document.getElementById('kbQ').value = '洛川苹果';
    await searchKb();
  } else if (scenario === 'admin') {
    go('admin');
  }
  const flag = document.createElement('div');
  flag.className = 'preview-flag';
  flag.textContent = '预览模式 · 免密';
  document.body.appendChild(flag);
})();
