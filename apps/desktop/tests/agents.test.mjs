// Dependency-free interaction checks: exercise the component's event handlers with
// a minimal hook/element host, plus the real HTTP client. No browser/layout claims.
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import ts from 'typescript';

function host() {
  const states = []; let cursor = 0; let App; const calls = []; const replies = [];
  const react = { createElement: (type, props, ...children) => ({ type, props: { ...props, children: children.length ? children : (props?.children ?? []) } }),
    useState(initial) { const i = cursor++; if (!(i in states)) states[i] = initial;
      return [states[i], value => { states[i] = typeof value === 'function' ? value(states[i]) : value; }]; } };
  const context = { Error, window: { scrollTo() {} }, document: { getElementById: () => ({}) }, AbortSignal, fetch: async (url, options) => {
    calls.push({ url, ...options }); const reply = await replies.shift();
    if (reply instanceof Error) throw reply;
    assert.ok(reply, 'unexpected request');
    return { ok: reply.status < 400, status: reply.status, json: async () => reply.body };
  } };
  function load(file, dependencies) {
    const module = { exports: {} };
    vm.runInNewContext(ts.transpileModule(fs.readFileSync(new URL(file, import.meta.url), 'utf8'), {
      compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.React, esModuleInterop: true },
    }).outputText, { ...context, module, exports: module.exports, require: name => dependencies[name] });
    return module.exports;
  }
  const agents = load('../src/agents.ts', {});
  const design = load('../src/design-system.tsx', { react });
  load('../src/main.tsx', { react, './agents': agents, './design-system': design, './styles.css': {},
    'react-dom/client': { createRoot: () => ({ render: node => { App = node.props.children[0].type; } }) } });
  function render() { cursor = 0; return App(); }
  function nodes(node) { if (node && typeof node === 'object' && typeof node.type === 'function') return nodes(node.type(node.props)); return Array.isArray(node) ? node.flatMap(nodes) : node && typeof node === 'object' ? [node, ...nodes(node.props.children)] : []; }
  const all = () => nodes(render());
  const text = node => Array.isArray(node) ? node.map(text).join('') : node && typeof node === 'object' ? text(node.props.children) : typeof node === 'boolean' ? '' : node ?? '';
  const byId = id => all().find(n => n.props.id === id);
  const button = label => all().find(n => n.type === 'button' && (text(n) === label || n.props['aria-label'] === label));
  return { agents, calls, replies, all, text, byId, button,
    change(id, value) { byId(id).props.onChange({ target: { value } }); },
    async submit(editor = false) { await all().find(n => n.type === 'form' && (editor ? n.props.className === 'editor' : !n.props.className)).props.onSubmit({ preventDefault() {} }); },
  };
}

const profile = { name: 'Alex', role: 'engineer', seniority: 'principal', expertise: ['architecture'],
  skills: ['review@v2'], tools: ['read-files'], instructions: 'Keep this.\nAnd this.', provider: 'ollama', model: 'qwen' };
const saved = { ...profile, id: 'persistent-id' };
async function connected(h, agents = []) {
  h.change('token', 'in-memory-test-session');
  h.replies.push({ status: 200, body: agents }, { status: 200, body: [] }, { status: 200, body: [] });
  await h.submit();
}
test('connect, create, save, edit provider/model without field loss, cancel', async () => {
  const h = host(); assert.equal(h.button('Create agent').props.disabled, true);
  await connected(h); h.button('Create agent').props.onClick();
  assert.deepEqual(Array.from(h.agents.emptyProfile().tools), []);
  for (const [key, value] of Object.entries(profile)) h.change(`agent-${key}`, Array.isArray(value) ? value.join('\n') : value);
  h.replies.push({ status: 201, body: saved }); await h.submit(true);
  assert.deepEqual(JSON.parse(h.calls.at(-1).body), profile);
  assert.equal(h.calls.at(-1).method, 'POST');
  h.button('Edit Alex').props.onClick();
  for (const id of Object.keys(profile)) assert.ok(h.byId(`agent-${id}`), `labeled ${id}`);
  h.change('agent-provider', 'codex-cli'); h.change('agent-model', 'chosen-model');
  h.replies.push({ status: 200, body: { ...saved, provider: 'codex-cli', model: 'chosen-model' } });
  await h.submit(true);
  assert.equal(h.calls.at(-1).method, 'PUT'); assert.ok(h.calls.at(-1).url.endsWith('/agents/persistent-id'));
  assert.deepEqual(JSON.parse(h.calls.at(-1).body), { ...profile, provider: 'codex-cli', model: 'chosen-model' });
  h.button('Edit Alex').props.onClick(); h.change('agent-name', 'Unsaved');
  const count = h.calls.length; h.button('Cancel').props.onClick();
  assert.equal(h.calls.length, count); h.button('Edit Alex').props.onClick();
  assert.equal(h.byId('agent-name').props.value, 'Alex');
});
test('failed saves retain draft, report auth/validation/missing/network errors and allow retry', async () => {
  const h = host(); await connected(h, [saved]); h.button('Edit Alex').props.onClick();
  h.change('agent-name', 'Retained draft');
  for (const reply of [{ status: 401 }, { status: 422 }, { status: 404 }, new Error('offline')]) {
    h.replies.push(reply); await h.submit(true);
    assert.equal(h.byId('agent-name').props.value, 'Retained draft');
    assert.ok(h.all().some(n => n.props.role === 'alert' && h.text(n).includes('Your unsaved profile')));
    assert.equal(h.all().find(n => n.props.className === 'editor').props.children.flat(Infinity).find(n => n?.type === 'fieldset').props.disabled, false);
  }
  h.replies.push({ status: 200, body: { ...saved, name: 'Retained draft' } }); await h.submit(true);
  assert.ok(h.button('Edit Retained draft'));
});
test('failed load leaves creation disabled and reports connection error', async () => {
  const h = host(); h.change('token', 'wrong');
  h.replies.push({ status: 401 }, { status: 401 }, { status: 401 }); await h.submit();
  assert.equal(h.button('Create agent').props.disabled, true);
  assert.ok(h.all().some(n => n.props.role === 'status' && h.text(n).includes('Connection denied')));
});

test('save in progress disables the editor and connection until completion', async () => {
  const h = host(); await connected(h, [saved]); h.button('Edit Alex').props.onClick();
  let finish; h.replies.push(new Promise(resolve => { finish = resolve; }));
  const pending = h.submit(true);
  assert.equal(h.all().find(n => n.props.className === 'editor').props.children.flat(Infinity).find(n => n?.type === 'fieldset').props.disabled, true);
  assert.equal(h.button('Connect').props.disabled, true);
  assert.ok(h.button('Saving…'));
  for (const field of Object.keys(profile)) {
    assert.ok(h.all().some(n => n.type === 'label' && n.props.htmlFor === `agent-${field}`));
  }
  finish({ status: 200, body: saved }); await pending;
  assert.equal(h.button('Connect').props.disabled, false);
});

test('project registration, fresh selection, failure recovery and reconnect', async () => {
  const h = host(); await connected(h);
  assert.equal(h.byId('project-name').props.pattern, '.*\\S.*');
  h.change('project-name', 'Local repo'); h.change('project-root', '/canonical/repo');
  const project = { id: 'project-id', name: 'Local repo', root: '/canonical/repo' };
  const submit = () => h.all().find(n => n.props.className === 'project-editor').props.onSubmit({ preventDefault() {} });
  h.replies.push({ status: 422 }); await submit();
  assert.equal(h.byId('project-root').props.value, '/canonical/repo');
  h.replies.push({ status: 201, body: project }); await submit();
  assert.equal(h.calls.at(-1).method, 'POST');
  assert.deepEqual(JSON.parse(h.calls.at(-1).body), { name: 'Local repo', root: '/canonical/repo' });
  assert.equal(h.byId('project-selection').props.value, 'project-id');
  h.replies.push({ status: 409 });
  await h.byId('project-selection').props.onChange({ target: { value: 'project-id' } });
  // onChange deliberately does not return the promise; drain the async fetch.
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(h.byId('project-selection').props.value, '');
  h.replies.push({ status: 200, body: project });
  h.change('project-selection', 'project-id'); await new Promise(resolve => setImmediate(resolve));
  assert.equal(h.byId('project-selection').props.value, 'project-id');
  assert.ok(h.calls.at(-1).url.endsWith('/projects/project-id'));
  await connected(h);
  assert.equal(h.byId('project-selection').props.value, '');
});

const task = { id: 'task-1', title: 'Check parser', acceptance: 'Reject invalid input', state: 'queued', version: 0,
  dependencies: [], assignments: [], events: [{ sequence: 1, kind: 'created', data: {}, created_at: '2026-10-31T12:00:00Z' }] };
async function withProject(h) {
  await connected(h, [saved]);
  h.change('project-name', 'Repo'); h.change('project-root', '/canonical/repo');
  h.replies.push({ status: 201, body: { id: 'p', name: 'Repo', root: '/canonical/repo' } });
  await h.all().find(n => n.props.className === 'project-editor').props.onSubmit({ preventDefault() {} });
  h.replies.push({ status: 200, body: [] });
  h.button('Refresh tasks').props.onClick(); await new Promise(resolve => setImmediate(resolve));
}
test('task create, readiness, assignment snapshot and audit detail', async () => {
  const h = host(); await withProject(h);
  assert.equal(h.byId('task-title').props.pattern, '.*\\S.*');
  h.change('task-title', task.title); h.change('task-acceptance', task.acceptance);
  h.replies.push({ status: 201, body: task });
  await h.all().find(n => n.props.className === 'task-editor').props.onSubmit({ preventDefault() {} });
  assert.equal(h.calls.at(-1).method, 'POST');
  assert.deepEqual(JSON.parse(h.calls.at(-1).body), { project_id: 'p', title: task.title, acceptance: task.acceptance, dependencies: [] });
  h.replies.push({ status: 200, body: { ...task, state: 'ready', version: 1 } });
  h.button('Mark Check parser ready').props.onClick(); await new Promise(resolve => setImmediate(resolve));
  assert.equal(JSON.parse(h.calls.at(-1).body).expected_version, 0);
  assert.equal(h.button('Assign Check parser').props.disabled, true);
  h.change('task-agent', saved.id);
  const assigned = { ...task, state: 'assigned', version: 2, assignments: [{ id: 'assignment-1', agent_id: saved.id, snapshot: saved }] };
  h.replies.push({ status: 200, body: assigned });
  h.button('Assign Check parser').props.onClick(); await new Promise(resolve => setImmediate(resolve));
  assert.deepEqual(JSON.parse(h.calls.at(-1).body), { expected_version: 1, agent_id: saved.id });
  assert.ok(h.all().some(n => n.type === 'p' && h.text(n).includes('saved configuration')));
  assert.ok(h.all().some(n => n.type === 'li' && h.text(n).includes('created')));
  assert.equal(h.button('Assign Check parser'), undefined);
  assert.ok(h.all().some(n => n.type === 'summary' && h.text(n).includes('File access')));
});
test('task errors retain draft, refresh clears stale data, project change clears tasks', async () => {
  const h = host(); await withProject(h);
  h.change('task-title', 'Retain me'); h.change('task-acceptance', 'Pass');
  h.replies.push({ status: 422 });
  await h.all().find(n => n.props.className === 'task-editor').props.onSubmit({ preventDefault() {} });
  assert.equal(h.byId('task-title').props.value, 'Retain me');
  h.replies.push({ status: 200, body: [task] });
  h.button('Refresh tasks').props.onClick(); await new Promise(resolve => setImmediate(resolve));
  h.replies.push({ status: 409 });
  h.button('Mark Check parser ready').props.onClick(); await new Promise(resolve => setImmediate(resolve));
  assert.ok(h.all().some(n => n.props.role === 'alert' && h.text(n).includes('state changed')));
  assert.ok(h.button('Mark Check parser ready'));
  let finish; h.replies.push(new Promise(resolve => { finish = resolve; }));
  h.button('Refresh tasks').props.onClick();
  assert.equal(h.byId('project-selection').props.disabled, true);
  assert.equal(h.button('Connect').props.disabled, true);
  finish({ status: 200, body: [task] }); await new Promise(resolve => setImmediate(resolve));
  assert.equal(h.byId('task-title').props.value, 'Retain me');
  h.change('project-selection', '');
  assert.equal(h.button('View Check parser'), undefined);
  assert.equal(h.byId('task-title'), undefined);
});

test('explicit file run grant, refresh diff, cancellation and failure recovery', async () => {
  const h = host(); await withProject(h);
  const assigned = { ...task, state: 'assigned', version: 2, assignments: [{ id: 'a', agent_id: saved.id, snapshot: saved }] };
  h.replies.push({ status: 200, body: [assigned] });
  h.button('Refresh tasks').props.onClick(); await new Promise(resolve => setImmediate(resolve));
  assert.equal(h.button('Start Check parser locally').props.disabled, true);
  h.change('run-parent', '/canonical/worktrees'); h.change('run-files', 'src/parser.py');
  h.byId('run-grant').props.onChange({ target: { checked: true } });
  assert.equal(h.button('Start Check parser locally').props.disabled, false);
  h.replies.push({ status: 409 });
  h.button('Start Check parser locally').props.onClick(); await new Promise(resolve => setImmediate(resolve));
  assert.equal(h.byId('run-files').props.value, 'src/parser.py');
  assert.equal(h.byId('run-grant').props.checked, true);
  const run = { id: 'r', status: 'running', path: '/canonical/worktrees/run-r', branch: 'orbit/run-r',
    base_sha: 'a'.repeat(40), model: 'local', files: ['src/parser.py'], logs: ['Run claimed.'], diff: '' };
  const running = { ...assigned, state: 'running', version: 3 };
  h.replies.push({ status: 202, body: [run] }, { status: 200, body: running });
  h.button('Start Check parser locally').props.onClick(); await new Promise(resolve => setImmediate(resolve));
  const start = h.calls.at(-2);
  assert.deepEqual(JSON.parse(start.body), { expected_version: 2, approved_parent: '/canonical/worktrees', files: ['src/parser.py'], grant_file_access: true });
  assert.equal(h.byId('run-grant').props.checked, false);
  assert.ok(h.button('Cancel Check parser run'));
  h.replies.push({ status: 200, body: [{ ...run, logs: ['Cancellation requested.'] }] }, { status: 200, body: running });
  h.button('Cancel Check parser run').props.onClick(); await new Promise(resolve => setImmediate(resolve));
  assert.ok(h.calls.at(-2).url.endsWith('/runs/cancel'));
  assert.equal(h.calls.at(-2).method, 'POST');
  h.replies.push({ status: 200, body: [{ ...run, status: 'cancelled' }] }, { status: 200, body: { ...running, state: 'cancelled', version: 4 } });
  h.button('Refresh Check parser run and diff').props.onClick(); await new Promise(resolve => setImmediate(resolve));
  assert.equal(h.button('Cancel Check parser run'), undefined);
  // Stored diff is rendered as plain text, including markup supplied in a file.
  h.replies.push({ status: 200, body: [{ ...run, status: 'awaiting_review', diff: '+<script>literal file content</script>' }] },
    { status: 200, body: { ...running, state: 'awaiting_review', version: 4 } });
  h.button('Refresh Check parser run and diff').props.onClick(); await new Promise(resolve => setImmediate(resolve));
  assert.ok(h.all().some(n => n.type === 'pre' && h.text(n).includes('<script>literal')));
  assert.equal(h.button('Record completed independent review for Check parser').props.disabled, true);
  h.change('project-selection', '');
  assert.equal(h.button('Refresh Check parser run and diff'), undefined);
});

test('workspace navigation and theme keep one product view visible', async () => {
  const h = host();
  const views = () => h.all().filter(n => n.type === 'section' && n.props.className?.includes('page-view'));
  assert.equal(views().filter(n => !n.props.hidden).length, 1);
  assert.ok(views().find(n => !n.props.hidden).props.className.includes('missions-view'));
  h.button('Connect your workspace').props.onClick();
  assert.equal(views().find(n => !n.props.hidden).props['aria-label'], 'Workspace setup');
  h.button('Agents').props.onClick();
  assert.equal(views().find(n => !n.props.hidden).props['aria-label'], 'Persistent agents');
  h.button('Models & capacity').props.onClick();
  assert.equal(views().find(n => !n.props.hidden).props['aria-label'], 'Models and capacity');
  assert.equal(h.all().find(n => n.type === 'main').props['data-theme'], 'dark');
  h.button('Switch to light theme').props.onClick();
  assert.equal(h.all().find(n => n.type === 'main').props['data-theme'], 'light');
  h.button('Switch to dark theme').props.onClick();
  assert.equal(h.all().find(n => n.type === 'main').props['data-theme'], 'dark');
});

test('mission composer, focused selection and keyboard detail tabs preserve drafts', async () => {
  const h = host(); await withProject(h);
  const composer = () => h.all().find(n => n.props.className === 'task-editor');
  assert.equal(composer().props.hidden, true);
  h.button('New mission').props.onClick(); assert.equal(composer().props.hidden, false);
  h.change('task-title', 'A draft');
  h.button('Close draft').props.onClick(); assert.equal(composer().props.hidden, true);
  h.button('New mission').props.onClick(); assert.equal(h.byId('task-title').props.value, 'A draft');
  const second = { ...task, id: 'second', title: 'Another mission' };
  h.replies.push({ status: 200, body: [task, second] });
  h.button('Refresh tasks').props.onClick(); await new Promise(resolve => setImmediate(resolve));
  assert.ok(h.button('Mark Check parser ready'));
  assert.equal(h.button('Mark Another mission ready'), undefined);
  h.button('View Another mission').props.onClick();
  assert.ok(h.button('Mark Another mission ready'));
  assert.equal(h.button('Mark Check parser ready'), undefined);
  const tab = h.all().find(n => n.props.role === 'tab' && h.text(n) === 'Overview');
  let focused = -1; let prevented = false;
  tab.props.onKeyDown({ key: 'ArrowRight', preventDefault() { prevented = true; },
    currentTarget: { parentElement: { querySelectorAll: () => [0, 1, 2].map(i => ({ focus() { focused = i; } })) } } });
  assert.equal(prevented, true); assert.equal(focused, 1);
  const visible = h.all().filter(n => n.props.role === 'tabpanel' && !n.props.hidden);
  assert.equal(visible.length, 1); assert.ok(visible[0].props.id.endsWith('panel-changes'));
  h.all().find(n => n.props.role === 'tab' && h.text(n) === 'Activity').props.onClick();
  assert.ok(h.all().find(n => n.props.role === 'tabpanel' && !n.props.hidden).props.id.endsWith('panel-activity'));
});
