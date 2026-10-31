import React, { useState } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';
import { Agent, Profile, emptyProfile, profileOf, request } from './agents';

type Project = { id: string; name: string; root: string };

type Provider = { id: string; execution_enabled: boolean; energy: { kind: string; status: string } };

type Task = { id: string; title: string; acceptance: string; state: string; version: number;
  dependencies: string[]; assignments: { id: string; agent_id: string; snapshot: Agent }[];
  events: { sequence: number; kind: string; data: { note?: string; to?: string }; created_at: string }[] };

function App() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [taskTitle, setTaskTitle] = useState('');
  const [acceptance, setAcceptance] = useState('');
  const [dependencies, setDependencies] = useState<string[]>([]);
  const [taskAgent, setTaskAgent] = useState('');
  const [taskBusy, setTaskBusy] = useState(false);
  const [taskError, setTaskError] = useState('');
  const [taskLoaded, setTaskLoaded] = useState(false);
  const [detail, setDetail] = useState<string | null>(null);
  async function refreshTasks() {
    if (!selected) return;
    setTaskBusy(true); setTaskError(''); setTaskLoaded(false);
    try {
      setTasks(await request<Task[]>(session, `/tasks?project_id=${encodeURIComponent(selected.id)}`));
      setTaskLoaded(true);
    } catch (error) { setTaskError(error instanceof Error ? error.message : 'Unable to load tasks.'); }
    finally { setTaskBusy(false); }
  }
  function clearTasks() {
    setTasks([]); setTaskLoaded(false); setDetail(null); setDependencies([]); setTaskError('');
    setTaskTitle(''); setAcceptance(''); setTaskAgent('');
  }
  async function createTask(event: React.FormEvent) {
    event.preventDefault(); if (!selected) return;
    setTaskBusy(true); setTaskError('');
    try {
      const saved = await request<Task>(session, '/tasks', { project_id: selected.id, title: taskTitle, acceptance, dependencies });
      setTasks(current => [...current, saved]); setDetail(saved.id);
      setTaskTitle(''); setAcceptance(''); setDependencies([]);
    } catch (error) { setTaskError(error instanceof Error ? error.message : 'Unable to create task.'); }
    finally { setTaskBusy(false); }
  }
  async function taskAction(task: Task, assign = false) {
    setTaskBusy(true); setTaskError('');
    try {
      const saved = await request<Task>(session, `/tasks/${encodeURIComponent(task.id)}/${assign ? 'assignments' : 'transitions'}`,
        assign ? { expected_version: task.version, agent_id: taskAgent } :
          { expected_version: task.version, state: 'ready', note: 'Marked ready by human in desktop.' });
      setTasks(current => current.map(t => t.id === saved.id ? saved : t)); setDetail(saved.id);
    } catch (error) { setTaskError(error instanceof Error ? error.message : 'Unable to update task.'); }
    finally { setTaskBusy(false); }
  }

  const [projects, setProjects] = useState<Project[]>([]);
  const [selected, setSelected] = useState<Project | null>(null);
  const [projectName, setProjectName] = useState('');
  const [projectRoot, setProjectRoot] = useState('');
  const [projectBusy, setProjectBusy] = useState(false);
  const [projectError, setProjectError] = useState('');
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
  async function registerProject(event: React.FormEvent) {
    event.preventDefault(); clearTasks(); setProjectBusy(true); setProjectError('');
    try {
      const saved = await request<Project>(session, '/projects', { name: projectName, root: projectRoot });
      setProjects(current => [...current, saved]); setSelected(saved);
      setProjectName(''); setProjectRoot('');
    } catch (error) { setProjectError(error instanceof Error ? error.message : 'Unable to register project.'); }
    finally { setProjectBusy(false); }
  }
  async function selectProject(id: string) {
    clearTasks(); setSelected(null); setProjectError('');
    if (!id) return;
    setProjectBusy(true);
    try { setSelected(await request<Project>(session, `/projects/${encodeURIComponent(id)}`)); }
    catch (error) { setProjectError(error instanceof Error ? error.message : 'Project unavailable.'); }
    finally { setProjectBusy(false); }
  }
  async function connect(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true); clearTasks();
    setAgents([]); setProviders([]); setProjects([]); setSelected(null); setProjectError(''); setSession(''); setEditor(null);
    try {
      const [nextAgents, nextProviders, nextProjects] = await Promise.all([
        request<Agent[]>(token, '/agents'), request<Provider[]>(token, '/providers'), request<Project[]>(token, '/projects')]);
      setProjects(nextProjects); setAgents(nextAgents); setProviders(nextProviders); setSession(token);
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
        <div className="connect"><input id="token" type="password" value={token} onChange={e => setToken(e.target.value)} disabled={busy || saving || projectBusy || taskBusy} autoComplete="off" required />
        <button disabled={busy || saving || projectBusy || taskBusy || editor !== null}>{busy ? 'Connecting…' : 'Connect'}</button></div></form>
      <p role="status">{status}</p></section>
    <section aria-labelledby="projects"><h2 id="projects">Projects</h2>
      <label htmlFor="project-selection">Selected project</label>
      <select id="project-selection" value={selected?.id ?? ''} disabled={!session || busy || projectBusy || taskBusy}
        onChange={e => { void selectProject(e.target.value); }}>
        <option value="">Choose a registered project</option>
        {projects.map(p => <option key={p.id} value={p.id}>{p.name} — {p.root}</option>)}
      </select>
      {selected && <p role="status">Selected {selected.name}: {selected.root}</p>}
      <form className="project-editor" onSubmit={registerProject}>
        <fieldset disabled={!session || busy || projectBusy || taskBusy}>
          <legend>Register a Git checkout</legend>
          <label htmlFor="project-name">Project name<input id="project-name" required maxLength={120} pattern=".*\S.*"
            value={projectName} onChange={e => setProjectName(e.target.value)} /></label>
          <label htmlFor="project-root">Absolute canonical checkout root<input id="project-root" required maxLength={4096}
            placeholder="/Users/you/Projects/repository" value={projectRoot} onChange={e => setProjectRoot(e.target.value)} /></label>
          <button>{projectBusy ? 'Checking project…' : 'Register project'}</button>
        </fieldset>
      </form>
      {projectError && <p role="alert">{projectError} Registration entries are retained for retry.</p>}
      <p>Selection lasts for this connection. Registration persists across restarts. Load tasks below after selecting a project. Execution is not enabled yet.</p>
    </section>
    <section aria-labelledby="tasks"><h2 id="tasks">Tasks and assignments</h2>
      <p>Choose a project, then load its tasks. Assignments preserve the agent configuration at assignment time.</p>
      <button type="button" disabled={!selected || taskBusy || projectBusy || busy} onClick={() => { void refreshTasks(); }}>Refresh tasks</button>
      {taskError && <p role="alert">{taskError} Your draft is retained; refresh before retrying a stale action.</p>}
      {selected && taskLoaded && <>
        <form className="task-editor" onSubmit={createTask}><fieldset disabled={taskBusy}>
          <legend>Create task in {selected.name}</legend>
          <label htmlFor="task-title">Task title<input id="task-title" required maxLength={240} pattern=".*\S.*" value={taskTitle} onChange={e => setTaskTitle(e.target.value)} /></label>
          <label htmlFor="task-acceptance">Acceptance criteria<textarea id="task-acceptance" required maxLength={16000} value={acceptance} onChange={e => setAcceptance(e.target.value)} /></label>
          <fieldset><legend>Dependencies — must complete before this task is ready</legend>
            {tasks.length === 0 && <p>No existing tasks in this project.</p>}
            {tasks.map(task => <label key={task.id}><input type="checkbox" checked={dependencies.includes(task.id)}
              onChange={e => setDependencies(current => e.target.checked ? [...current, task.id] : current.filter(id => id !== task.id))} />{task.title} ({task.state})</label>)}
          </fieldset>
          <button>Create task</button>
        </fieldset></form>
        <label htmlFor="task-agent">Agent for next assignment<select id="task-agent" value={taskAgent} disabled={taskBusy} onChange={e => setTaskAgent(e.target.value)}>
          <option value="">Choose a configured agent</option>{agents.map(a => <option key={a.id} value={a.id}>{a.name} — {a.role}</option>)}
        </select></label>
        {tasks.length === 0 && <p>No tasks yet.</p>}
        {tasks.map(task => <article key={task.id}><h3>{task.title}</h3><p>State: {task.state} · revision {task.version}</p>
          <button type="button" disabled={taskBusy} onClick={() => setDetail(task.id)}>View {task.title}</button>
          {task.state === 'queued' && <button type="button" disabled={taskBusy} onClick={() => { void taskAction(task); }}>Mark {task.title} ready</button>}
          {task.state === 'ready' && <button type="button" disabled={taskBusy || !taskAgent} onClick={() => { void taskAction(task, true); }}>Assign {task.title}</button>}
          {detail === task.id && <div><h4>Acceptance criteria</h4><p style={{ whiteSpace: 'pre-wrap' }}>{task.acceptance}</p>
            <p>Dependencies: {task.dependencies.length ? task.dependencies.map(id => tasks.find(t => t.id === id)?.title ?? id).join(', ') : 'None'}</p>
            <h4>Assignment history</h4>{task.assignments.length === 0 && <p>Unassigned.</p>}
            {task.assignments.map(a => <p key={a.id}>{a.snapshot.name} · {a.snapshot.role} · {a.snapshot.provider}/{a.snapshot.model} (saved configuration)</p>)}
            <h4>Audit history</h4><ol>{task.events.map(event => <li key={event.sequence}>{event.kind}{event.data.to ? ` → ${event.data.to}` : ''} · {event.created_at}{event.data.note ? ` · ${event.data.note}` : ''}</li>)}</ol>
          </div>}
        </article>)}
      </>}
      <p>Execution, live cancellation, diff review and merge controls are planned. Assigning a task does not run a model or grant tools.</p>
    </section>
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
        <div className="grid">{agents.map(a => <article key={a.id}><h3>{a.name}</h3><p>{a.seniority} · {a.role}</p><small>{a.provider} / {a.model}</small><p><button type="button" disabled={busy || saving || projectBusy || taskBusy || editor !== null} onClick={() => openEditor(a)}>Edit {a.name}</button></p></article>)}</div>}
    </section>
    <footer>Any agent. Any role. Any model. Any project.</footer>
  </main>;
}
createRoot(document.getElementById('root')!).render(<React.StrictMode><App /></React.StrictMode>);
