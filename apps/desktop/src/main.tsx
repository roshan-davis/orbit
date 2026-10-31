import React, { useState } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';
import { Agent, Profile, emptyProfile, profileOf, request } from './agents';

type Provider = { id: string; execution_enabled: boolean; energy: { kind: string; status: string } };

function App() {
  const [token, setToken] = useState('');
  const [agents, setAgents] = useState<Agent[]>([]);
  const [providers, setProviders] = useState<Provider[]>([]);
  const [status, setStatus] = useState('Start the local engine, then connect.');
  const [busy, setBusy] = useState(false);
  const [session, setSession] = useState('');
  const [editor, setEditor] = useState<Profile | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [saveError, setSaveError] = useState('');
  const [saving, setSaving] = useState(false);
  function openEditor(agent?: Agent) {
    setEditingId(agent?.id ?? null); setEditor(agent ? profileOf(agent) : emptyProfile()); setSaveError('');
  }
  async function save(event: React.FormEvent) {
    event.preventDefault();
    if (!editor) return;
    setSaving(true); setSaveError('');
    try {
      const profile = { ...editor,
        expertise: editor.expertise.filter(value => value.trim()),
        skills: editor.skills.filter(value => value.trim()),
        tools: editor.tools.filter(value => value.trim()),
      };
      const path = editingId ? `/agents/${encodeURIComponent(editingId)}` : '/agents';
      const saved = await request<Agent>(session, path, profile);
      setAgents(current => editingId ? current.map(a => a.id === saved.id ? saved : a) : [...current, saved]);
      setEditor(null); setStatus(`Saved ${saved.name}.`);
    } catch (error) { setSaveError(error instanceof Error ? error.message : 'Unable to save profile.'); }
    finally { setSaving(false); }
  }
  async function connect(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setAgents([]); setProviders([]); setSession(''); setEditor(null);
    try {
      const [nextAgents, nextProviders] = await Promise.all([
        request<Agent[]>(token, '/agents'), request<Provider[]>(token, '/providers')]);
      setAgents(nextAgents); setProviders(nextProviders); setSession(token);
      setStatus('Connected to the local engine. Provider execution is not enabled in this foundation.');
    } catch (error) {
      setStatus(error instanceof Error ? error.message : 'Engine unavailable.');
    } finally { setBusy(false); }
  }
  return <main>
    <header><span className="eyebrow">LOCAL MISSION CONTROL · FOUNDATION</span><h1>Orbit<span>✳</span></h1>
      <p>Many minds. One mission.</p></header>
    <section aria-labelledby="connection"><h2 id="connection">Your workspace</h2>
      <form onSubmit={connect}><label htmlFor="token">Engine session token</label>
        <div className="connect"><input id="token" type="password" value={token} onChange={e => setToken(e.target.value)} disabled={busy || saving} autoComplete="off" required />
        <button disabled={busy || saving || editor !== null}>{busy ? 'Connecting…' : 'Connect'}</button></div></form>
      <p role="status">{status}</p></section>
    <section aria-labelledby="energy"><h2 id="energy">Team energy</h2>
      <p>Shared provider pools appear once. Local compute is tracked separately.</p>
      {providers.length === 0 ? <p className="empty">Connect to view provider declarations. No live quota data is available.</p> :
        <div className="grid">{providers.map(p => <article key={p.id}><h3>{p.id}</h3>
          <strong>Unknown</strong><p>{p.energy.kind === 'compute' ? 'Local compute' : 'Shared subscription pool'}</p>
          <small>Telemetry not connected · execution disabled</small></article>)}</div>}
    </section>
    <section aria-labelledby="agents"><h2 id="agents">Persistent agents <span className="count">{agents.length}</span></h2>
      <button type="button" disabled={!session || busy || saving || editor !== null} onClick={() => openEditor()}>Create agent</button>
      {editor && <form className="editor" onSubmit={save} aria-labelledby="editor-title">
        <h3 id="editor-title">{editingId ? 'Edit agent' : 'Create agent'}</h3>
        <fieldset disabled={saving}>
          {(['name', 'role', 'seniority', 'model'] as const).map(field => <label key={field} htmlFor={`agent-${field}`}>
            {field[0].toUpperCase() + field.slice(1)}
            <input id={`agent-${field}`} value={editor[field]} required pattern=".*\S.*" maxLength={field === 'name' || field === 'role' ? 120 : undefined}
              onChange={e => setEditor({ ...editor, [field]: e.target.value })} />
          </label>)}
          <label htmlFor="agent-provider">Provider<select id="agent-provider" value={editor.provider} onChange={e => setEditor({ ...editor, provider: e.target.value })}>
            {['ollama', 'claude-code', 'codex-cli', 'gemini-cli'].map(p => <option key={p}>{p}</option>)}
          </select></label>
          {(['expertise', 'skills', 'tools'] as const).map(field => <label key={field} htmlFor={`agent-${field}`}>
            {field === 'skills' ? 'Skill references (include versions when available)' : field === 'tools' ? 'Configured tools' : 'Expertise'} — one per line
            <textarea id={`agent-${field}`} rows={3} value={editor[field].join('\n')}
              onChange={e => setEditor({ ...editor, [field]: e.target.value.split('\n') })} />
          </label>)}
          <label htmlFor="agent-instructions">Instructions<textarea id="agent-instructions" rows={6} value={editor.instructions}
            onChange={e => setEditor({ ...editor, instructions: e.target.value })} /></label>
          <p>Tools are configuration only. Saving does not grant execution permissions. Provider execution remains disabled.</p>
          <div className="actions"><button type="submit">{saving ? 'Saving…' : 'Save agent'}</button>
            <button type="button" onClick={() => { setEditor(null); setSaveError(''); }}>Cancel</button></div>
        </fieldset>
        {saveError && <p role="alert">{saveError} Your unsaved profile remains here.</p>}
      </form>}
      {agents.length === 0 ? <p className="empty">No agents loaded. Connect, then create your first agent.</p> :
        <div className="grid">{agents.map(a => <article key={a.id}><h3>{a.name}</h3><p>{a.seniority} · {a.role}</p><small>{a.provider} / {a.model}</small><p><button type="button" disabled={busy || saving || editor !== null} onClick={() => openEditor(a)}>Edit {a.name}</button></p></article>)}</div>}
    </section>
    <footer>Any agent. Any role. Any model. Any project.</footer>
  </main>;
}
createRoot(document.getElementById('root')!).render(<React.StrictMode><App /></React.StrictMode>);
