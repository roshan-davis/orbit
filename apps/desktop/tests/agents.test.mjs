// Dependency-free interaction checks: exercise the component's event handlers with
// a minimal hook/element host, plus the real HTTP client. No browser/layout claims.
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import ts from 'typescript';

function host() {
  const states = []; let cursor = 0; let App; const calls = []; const replies = [];
  const react = { createElement: (type, props, ...children) => ({ type, props: { ...props, children } }),
    useState(initial) { const i = cursor++; if (!(i in states)) states[i] = initial;
      return [states[i], value => { states[i] = typeof value === 'function' ? value(states[i]) : value; }]; } };
  const context = { Error, document: { getElementById: () => ({}) }, AbortSignal, fetch: async (url, options) => {
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
  load('../src/main.tsx', { react, './agents': agents, './styles.css': {},
    'react-dom/client': { createRoot: () => ({ render: node => { App = node.props.children[0].type; } }) } });
  function render() { cursor = 0; return App(); }
  function nodes(node) { return Array.isArray(node) ? node.flatMap(nodes) : node && typeof node === 'object' ? [node, ...nodes(node.props.children)] : []; }
  const all = () => nodes(render());
  const text = node => Array.isArray(node) ? node.map(text).join('') : node && typeof node === 'object' ? text(node.props.children) : node ?? '';
  const byId = id => all().find(n => n.props.id === id);
  const button = label => all().find(n => n.type === 'button' && text(n) === label);
  return { agents, calls, replies, all, text, byId, button,
    change(id, value) { byId(id).props.onChange({ target: { value } }); },
    async submit(editor = false) { await all().find(n => n.type === 'form' && !!n.props.className === editor).props.onSubmit({ preventDefault() {} }); },
  };
}

const profile = { name: 'Alex', role: 'engineer', seniority: 'principal', expertise: ['architecture'],
  skills: ['review@v2'], tools: ['read-files'], instructions: 'Keep this.\nAnd this.', provider: 'ollama', model: 'qwen' };
const saved = { ...profile, id: 'persistent-id' };
async function connected(h, agents = []) {
  h.change('token', 'in-memory-test-session');
  h.replies.push({ status: 200, body: agents }, { status: 200, body: [] });
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
    assert.equal(h.all().find(n => n.type === 'fieldset').props.disabled, false);
  }
  h.replies.push({ status: 200, body: { ...saved, name: 'Retained draft' } }); await h.submit(true);
  assert.ok(h.button('Edit Retained draft'));
});
test('failed load leaves creation disabled and reports connection error', async () => {
  const h = host(); h.change('token', 'wrong');
  h.replies.push({ status: 401 }, { status: 401 }); await h.submit();
  assert.equal(h.button('Create agent').props.disabled, true);
  assert.ok(h.all().some(n => n.props.role === 'status' && h.text(n).includes('Connection denied')));
});

test('save in progress disables the editor and connection until completion', async () => {
  const h = host(); await connected(h, [saved]); h.button('Edit Alex').props.onClick();
  let finish; h.replies.push(new Promise(resolve => { finish = resolve; }));
  const pending = h.submit(true);
  assert.equal(h.all().find(n => n.type === 'fieldset').props.disabled, true);
  assert.equal(h.button('Connect').props.disabled, true);
  assert.ok(h.button('Saving…'));
  for (const field of Object.keys(profile)) {
    assert.ok(h.all().some(n => n.type === 'label' && n.props.htmlFor === `agent-${field}`));
  }
  finish({ status: 200, body: saved }); await pending;
  assert.equal(h.button('Connect').props.disabled, false);
});
