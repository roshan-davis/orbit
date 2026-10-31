import React, { useState } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';
import { Badge, Button, EmptyState, Icon, PageHeading, Panel, Tabs } from './design-system';
import { Agent, Profile, emptyProfile, profileOf, request } from './agents';

type Project = { id: string; name: string; root: string };

type Provider = { id: string; execution_enabled: boolean; energy: { kind: string; status: string } };

type Task = { id: string; title: string; acceptance: string; state: string; version: number;
  dependencies: string[]; assignments: { id: string; agent_id: string; snapshot: Agent }[];
  events: { sequence: number; kind: string; data: { note?: string; to?: string }; created_at: string }[] };

type Run = { id: string; status: string; path: string; branch: string; base_sha: string;
  files: string[]; logs: string[]; diff: string; model: string };

function App() {
  const [view, setView] = useState<'missions' | 'agents' | 'providers' | 'workspace'>('missions');
  const [evidenceTab, setEvidenceTab] = useState('overview');
  const [theme, setTheme] = useState<'dark' | 'light'>('dark');
  const [composing, setComposing] = useState(false);
  function navigate(next: typeof view) {
    setView(next); window.scrollTo({ top: 0, behavior: 'auto' });
  }
  const [runs, setRuns] = useState<Record<string, Run[]>>({});
  const [runParent, setRunParent] = useState('');
  const [runFiles, setRunFiles] = useState('');
  const [runGrant, setRunGrant] = useState(false);
  const [reviewNote, setReviewNote] = useState('');
  const [approveCompletion, setApproveCompletion] = useState(false);
  async function runAction(task: Task, action: 'start' | 'refresh' | 'cancel') {
    setTaskBusy(true); setTaskError('');
    try {
      const path = `/tasks/${encodeURIComponent(task.id)}/runs`;
      const result = await request<Run[]>(session, path + (action === 'cancel' ? '/cancel' : ''),
        action === 'start' ? { expected_version: task.version, approved_parent: runParent,
          files: runFiles.split('\n').map(v => v.trim()).filter(Boolean), grant_file_access: runGrant } :
          action === 'cancel' ? { run_id: runs[task.id]?.slice(-1)[0]?.id ?? '' } : undefined);
      setRuns(current => ({ ...current, [task.id]: result }));
      const updated = await request<Task>(session, `/tasks/${encodeURIComponent(task.id)}`);
      setTasks(current => current.map(t => t.id === updated.id ? updated : t)); setDetail(task.id);
      setEvidenceTab(action === 'refresh' ? 'changes' : 'overview');
      if (action === 'start') setRunGrant(false);
    } catch (error) { setTaskError(error instanceof Error ? error.message : 'Run action failed. Refresh to check the recorded outcome.'); }
    finally { setTaskBusy(false); }
  }
  async function recordReview(task: Task, approval = false) {
    setTaskBusy(true); setTaskError('');
    try {
      const updated = await request<Task>(session, `/tasks/${encodeURIComponent(task.id)}/transitions`, {
        expected_version: task.version, state: approval ? 'completed' : 'awaiting_approval', note: reviewNote,
        ...(approval ? { human_approval: approveCompletion } : { reviewer_id: taskAgent }),
      });
      setTasks(current => current.map(t => t.id === updated.id ? updated : t));
      setReviewNote(''); setApproveCompletion(false);
    } catch (error) { setTaskError(error instanceof Error ? error.message : 'Review action failed.'); }
    finally { setTaskBusy(false); }
  }

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
    setRuns({}); setEvidenceTab('overview'); setRunGrant(false); setApproveCompletion(false); setReviewNote('');
    setTasks([]); setTaskLoaded(false); setDetail(null); setDependencies([]); setTaskError('');
    setTaskTitle(''); setAcceptance(''); setTaskAgent(''); setComposing(false);
  }
  async function createTask(event: React.FormEvent) {
    event.preventDefault(); if (!selected) return;
    setTaskBusy(true); setTaskError('');
    try {
      const saved = await request<Task>(session, '/tasks', { project_id: selected.id, title: taskTitle, acceptance, dependencies });
      setTasks(current => [...current, saved]); setDetail(saved.id);
      setTaskTitle(''); setAcceptance(''); setDependencies([]); setComposing(false);
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
      setProjectName(''); setProjectRoot(''); navigate('missions');
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
      setStatus('Connected to the local engine. Local file runs are available for explicitly granted files and verified installed Ollama models.');
    } catch (error) {
      setStatus(error instanceof Error ? error.message : 'Engine unavailable.');
    } finally { setBusy(false); }
  }
  const focusedTask = tasks.find(task => task.id === detail) ?? tasks[0];
  const changingWorkspace = busy || projectBusy || taskBusy || saving;
  return <main className="app-shell" data-theme={theme}>
    <aside className="sidebar" aria-label="Orbit navigation">
      <a className="brand" href="#missions" onClick={() => navigate('missions')} aria-label="Orbit home"><span className="brand-symbol"><Icon name="orbit" /></span><span>Orbit<span className="brand-caption">Many minds. One mission.</span></span></a>
      <span className="nav-label">WORKSPACE</span>
      <nav>{([['missions', 'Missions', 'missions'], ['agents', 'Agents', 'agents'], ['providers', 'Models & capacity', 'providers'], ['workspace', 'Workspace setup', 'workspace']] as const).map(([id, label, icon]) =>
        <Button key={id} type="button" variant="quiet" className={`nav-item ${view === id ? 'is-active' : ''}`} aria-current={view === id ? 'page' : undefined} aria-label={label} title={label}
          disabled={changingWorkspace} onClick={() => navigate(id)}><Icon name={icon} />{label}{id === 'missions' && taskLoaded && <span className="nav-count">{tasks.length}</span>}</Button>)}</nav>
      <div className="sidebar-bottom"><div className="engine-status"><span className={`status-light ${session ? 'is-connected' : ''}`} /><div><strong>{session ? 'Engine connected' : 'Engine offline'}</strong><small>Local on this device</small></div></div>
        <Button type="button" variant="quiet" className="theme-switch" onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}><Icon name={theme === 'dark' ? 'sun' : 'moon'} />Switch to {theme === 'dark' ? 'light' : 'dark'} theme</Button>
        <small className="privacy-note">Private by design · Local preview</small></div>
    </aside>
    <div className="workspace-shell">
      <header className="topbar"><div className="breadcrumb">Workspace <span>/</span> <strong>{view === 'missions' ? 'Missions' : view === 'agents' ? 'Agents' : view === 'providers' ? 'Models & capacity' : 'Setup'}</strong></div>
        <div className="project-switcher">      <label htmlFor="project-selection">Selected project</label>
      <select id="project-selection" value={selected?.id ?? ''} disabled={!session || busy || projectBusy || taskBusy}
        onChange={e => { void selectProject(e.target.value); }}>
        <option value="">Choose a registered project</option>
        {projects.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
      </select>
</div></header>
      <div className="page-content">
        <section aria-labelledby="missions-title" hidden={view !== 'missions'} className="page-view missions-view">
          <PageHeading eyebrow="MISSION CONTROL" title={selected ? selected.name : 'A little focus. A lot of possibility.'}
            description={selected ? 'Give your team a clear goal. Follow the work from assignment to review.' : 'Bring your project, assemble your team, and turn an idea into a mission.'}
            action={selected && taskLoaded ? <Button type="button" variant="primary" disabled={taskBusy} onClick={() => setComposing(!composing)}><Icon name="plus" />New mission</Button> : undefined} />
          <h2 id="missions-title" className="sr-only">Tasks and assignments</h2>
          {!selected && <div className="welcome-layout"><Panel className="welcome-card"><span className="eyebrow">YOUR NEXT CHAPTER</span><div className="orbital-art" aria-hidden="true"><i /><i /><i /><span>✳</span></div>
            <h2>Make room for your next big idea.</h2><p>A calm space to coordinate your agents, follow their progress, and review every change.</p>
            <Button type="button" variant="primary" onClick={() => navigate('workspace')}>{session ? 'Add a project' : 'Connect your workspace'}<Icon name="arrow" /></Button>
          </Panel><Panel className="journey-card"><span className="eyebrow">A SIMPLE WAY TO WORK</span><ol className="journey"><li><span>01</span><div><h3>Bring a project</h3><p>Choose a local repository. Your existing work stays yours.</p></div></li><li><span>02</span><div><h3>Build your team</h3><p>Give your agents roles, expertise and a clear assignment.</p></div></li><li><span>03</span><div><h3>Run. Review. Decide.</h3><p>Follow a local run, inspect its changes and keep the final say.</p></div></li></ol><div className="subtle-note"><Icon name="workspace" />Everything starts on your device.</div></Panel></div>}
          {selected && <>
            <div className="mission-overview"><div><span>PROJECT</span><strong>{selected.name}</strong></div><div><span>MISSIONS</span><strong>{taskLoaded ? tasks.length : '—'}</strong></div><div><span>IN PROGRESS</span><strong>{taskLoaded ? tasks.filter(t => t.state === 'running').length : '—'}</strong></div><div><span>NEED REVIEW</span><strong>{taskLoaded ? tasks.filter(t => ['awaiting_review', 'awaiting_approval'].includes(t.state)).length : '—'}</strong></div><Button type="button" disabled={!selected || taskBusy || projectBusy || busy} onClick={() => { void refreshTasks(); }}><Icon name="refresh" />Refresh tasks</Button></div>
            {taskError && <p role="alert">{taskError} Your draft is retained; refresh before retrying a stale action.</p>}
            {!taskLoaded && <Panel><EmptyState icon="missions" title="Ready when you are">Refresh tasks to load this project's missions and saved assignments.</EmptyState></Panel>}
            {taskLoaded && <>
        <form hidden={!composing} className="task-editor" onSubmit={createTask}><fieldset disabled={taskBusy}>
          <legend>Create task in {selected.name}</legend>
          <label htmlFor="task-title">Task title<input id="task-title" required maxLength={240} pattern=".*\S.*" value={taskTitle} onChange={e => setTaskTitle(e.target.value)} /></label>
          <label htmlFor="task-acceptance">Acceptance criteria<textarea id="task-acceptance" required maxLength={16000} value={acceptance} onChange={e => setAcceptance(e.target.value)} /></label>
          <fieldset><legend>Dependencies — must complete before this task is ready</legend>
            {tasks.length === 0 && <p>No existing tasks in this project.</p>}
            {tasks.map(task => <label key={task.id}><input type="checkbox" checked={dependencies.includes(task.id)}
              onChange={e => setDependencies(current => e.target.checked ? [...current, task.id] : current.filter(id => id !== task.id))} />{task.title} ({task.state})</label>)}
          </fieldset>
          <div className="actions"><Button variant="primary">Create task</Button><Button type="button" onClick={() => setComposing(false)}>Close draft</Button></div>
        </fieldset></form>

              <div className="mission-workspace"><Panel className="mission-list"><div className="panel-title"><h2>Missions</h2><span className="count">{tasks.length}</span></div>
                {tasks.length === 0 && <EmptyState icon="missions" title="Your first mission awaits">Create a mission with a clear outcome and acceptance criteria.</EmptyState>}
                {tasks.map(task => <Button type="button" key={task.id} variant="quiet" className={`task-row ${focusedTask?.id === task.id ? 'is-selected' : ''}`} disabled={taskBusy} onClick={() => { setDetail(task.id); setEvidenceTab('overview'); setRunGrant(false); setReviewNote(''); setApproveCompletion(false); }} aria-label={`View ${task.title}`} aria-pressed={focusedTask?.id === task.id}><span className="task-row-title">{task.title}</span><Badge state={task.state} /><span className="task-row-meta">{task.assignments.slice(-1)[0]?.snapshot.name ?? 'No agent assigned'}</span></Button>)}
              </Panel><Panel className="mission-detail-panel">
                {focusedTask ? <>
        {tasks.filter(task => task.id === focusedTask?.id).map(task => <article key={task.id} className="task-detail"><div className="task-detail-heading"><div><span className="eyebrow">MISSION DETAIL</span><h2>{task.title}</h2></div><Badge state={task.state} /></div>        {['ready', 'awaiting_review'].includes(focusedTask.state) && <div className="assignment-control"><label htmlFor="task-agent">{focusedTask.state === 'awaiting_review' ? 'Independent reviewer' : 'Agent for next assignment'}<select id="task-agent" value={taskAgent} disabled={taskBusy} onChange={e => setTaskAgent(e.target.value)}>
          <option value="">Choose a configured agent</option>{agents.map(a => <option key={a.id} value={a.id}>{a.name} — {a.role}</option>)}
        </select></label></div>}
        <details className="run-permissions" hidden={focusedTask.state !== 'assigned'}><summary>File access for your next run<span>Choose exactly what the model can read and change</span></summary><fieldset disabled={taskBusy}><legend className="sr-only">Local file run permissions — for the next Start action</legend>
          <label htmlFor="run-parent">Existing canonical worktree parent outside your project<input id="run-parent" value={runParent}
            placeholder="/Users/you/OrbitWorktrees" onChange={e => { setRunParent(e.target.value); setRunGrant(false); }} /></label>
          <label htmlFor="run-files">Granted relative text files — one per line<textarea id="run-files" value={runFiles}
            placeholder="src/example.py" onChange={e => { setRunFiles(e.target.value); setRunGrant(false); }} /></label>
          <label htmlFor="run-grant"><input id="run-grant" type="checkbox" checked={runGrant}
            onChange={e => setRunGrant(e.target.checked)} />I approve sending these files from the recorded commit to the local model and editing them in a new isolated worktree.</label>
          <p>At most 16 UTF-8 files, 64 KiB combined context. Existing parent directories only. Hidden files, sensitive filenames, symlinks and commands are blocked. Do not grant files containing secrets.
            Uncommitted project changes are preserved and are not included. Inference can take up to two minutes; refresh to see progress.</p>
        </fieldset></details>
<div className="task-actions">
          {task.state === 'queued' && <Button type="button" disabled={taskBusy} onClick={() => { void taskAction(task); }} aria-label={`Mark ${task.title} ready`}> Mark ready</Button>}
          {task.state === 'ready' && <Button type="button" disabled={taskBusy || !taskAgent} onClick={() => { void taskAction(task, true); }} aria-label={`Assign ${task.title}`}> Assign agent</Button>}
          {task.state === 'assigned' && <Button type="button" disabled={taskBusy || !runGrant || !runParent || !runFiles.trim()}
            variant="primary" onClick={() => { void runAction(task, 'start'); }} aria-label={`Start ${task.title} locally`}> Start locally</Button>}
          {task.assignments.length > 0 && <Button type="button" disabled={taskBusy}
            onClick={() => { void runAction(task, 'refresh'); }} aria-label={`Refresh ${task.title} run and diff`}> Refresh run</Button>}
          {task.state === 'running' && <Button type="button" disabled={taskBusy || !runs[task.id]?.length}
            variant="danger" onClick={() => { void runAction(task, 'cancel'); }} aria-label={`Cancel ${task.title} run`}> Cancel run</Button>}
          </div><div className="task-evidence">
            <Tabs id={`mission-${task.id}`} items={[{id: 'overview', label: 'Overview'}, {id: 'changes', label: 'Changes & logs'}, {id: 'activity', label: 'Activity'}]} value={evidenceTab} onChange={setEvidenceTab} />
            <div role="tabpanel" id={`mission-${task.id}-panel-overview`} aria-labelledby={`mission-${task.id}-tab-overview`} hidden={evidenceTab !== 'overview'}>
<h4>Acceptance criteria</h4><p style={{ whiteSpace: 'pre-wrap' }}>{task.acceptance}</p>
            <p>Dependencies: {task.dependencies.length ? task.dependencies.map(id => tasks.find(t => t.id === id)?.title ?? id).join(', ') : 'None'}</p>
            <h4>Assignment history</h4>{task.assignments.length === 0 && <p>Unassigned.</p>}
            {task.assignments.map(a => <p key={a.id}>{a.snapshot.name} · {a.snapshot.role} · {a.snapshot.provider}/{a.snapshot.model} (saved configuration)</p>)}
            {['awaiting_review', 'awaiting_approval'].includes(task.state) && <fieldset disabled={taskBusy}>
              <legend>Record review evidence — never merges Git</legend>
              <label htmlFor={`review-note-${task.id}`}>Review or approval evidence<textarea id={`review-note-${task.id}`} value={reviewNote}
                onChange={e => setReviewNote(e.target.value)} maxLength={4000} /></label>
              {task.state === 'awaiting_review' && <Button type="button" disabled={!reviewNote.trim() || !taskAgent || task.assignments.some(a => a.agent_id === taskAgent)}
                onClick={() => { void recordReview(task); }}>Record completed independent review for {task.title}</Button>}
              {task.state === 'awaiting_approval' && <><label><input type="checkbox" checked={approveCompletion}
                onChange={e => setApproveCompletion(e.target.checked)} />I explicitly approve task completion after reviewing its evidence. This does not merge its branch.</label>
                <Button type="button" disabled={!approveCompletion || !reviewNote.trim()} onClick={() => { void recordReview(task, true); }}>Approve completion of {task.title}</Button></>}
              <p>Use the agent selector for the distinct reviewer who actually performed the review. Recording an assertion does not run a reviewer.</p>
            </fieldset>}
            </div>
            <div role="tabpanel" id={`mission-${task.id}-panel-changes`} aria-labelledby={`mission-${task.id}-tab-changes`} hidden={evidenceTab !== 'changes'}>
            {(runs[task.id] ?? []).map(run => <section key={run.id} aria-label="Local run evidence" className="run-evidence">
              <div className="run-heading"><h3>Run outcome</h3><Badge state={run.status} /></div><details className="run-metadata"><summary>Execution log & worktree details</summary><p>{run.model} · {run.branch}</p><p>Retained worktree: {run.path}</p>
              <p>Base commit: {run.base_sha}</p><ol>{run.logs.map((line, i) => <li key={i}>{line}</li>)}</ol>
</details>              <h3>Changes for review</h3><pre style={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere' }}>{run.diff || 'No successful diff recorded. Inspect retained worktree after failure or cancellation.'}</pre>
              <p>This is the recorded run output. Tests and independent review are manual. Later worktree edits are not included in this snapshot.</p>
            </section>)}
            {!(runs[task.id]?.length) && <EmptyState icon="missions" title="No run evidence loaded">Use Refresh run to load saved logs and changes for this mission.</EmptyState>}
            </div>
            <div role="tabpanel" id={`mission-${task.id}-panel-activity`} aria-labelledby={`mission-${task.id}-tab-activity`} hidden={evidenceTab !== 'activity'}>
            <div className="audit"><h3>Activity history <span className="count">{task.events.length} events</span></h3><ol>{task.events.map(event => <li key={event.sequence}>{event.kind}{event.data.to ? ` → ${event.data.to}` : ''} · {event.created_at}{event.data.note ? ` · ${event.data.note}` : ''}</li>)}</ol></div>
            </div>
          </div>
        </article>)}

                </> : <EmptyState title="A clear goal changes everything">Choose a mission to see its assignment, progress and reviewable changes.</EmptyState>}
              </Panel></div>
            </>}
          </>}
        </section>
    <section aria-label="Persistent agents" hidden={view !== 'agents'} className="page-view"><PageHeading eyebrow="YOUR TEAM" title="Persistent agents" description="Give each agent a lasting identity. Bring the right expertise to every mission." />
      <Button type="button" disabled={!session || busy || saving || editor !== null} onClick={() => openEditor()} variant="primary">Create agent</Button>
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
          <p>Tool names describe the profile. File access is approved separately when you start a local run.</p>
          <div className="actions"><Button type="submit">{saving ? 'Saving…' : 'Save agent'}</Button>
            <Button type="button" onClick={() => { setEditor(null); setSaveError(''); }}>Cancel</Button></div>
        </fieldset>
        {saveError && <p role="alert">{saveError} Your unsaved profile remains here.</p>}
      </form>}
      {agents.length === 0 ? <EmptyState icon="agents" title={session ? "Build your first mission team" : "Meet your future team"}>Connect to your engine, then create agents with the roles and expertise you need. No agents are configured for you.</EmptyState> :
        <div className="grid">{agents.map(a => <article key={a.id}><h3>{a.name}</h3><p>{a.seniority} · {a.role}</p><small>{a.provider} / {a.model}</small><p><Button type="button" disabled={busy || saving || projectBusy || taskBusy || editor !== null} onClick={() => openEditor(a)}>Edit {a.name}</Button></p></article>)}</div>}
    </section>
    <section aria-label="Models and capacity" hidden={view !== 'providers'} className="page-view"><PageHeading eyebrow="PROVIDER READINESS" title="Models & capacity" description="Know what is available before you assign work." />
      <p>Shared provider pools appear once. Local compute is tracked separately.</p>
      {providers.length === 0 ? <EmptyState icon="providers" title="Your models, in one place">Connect your local engine to inspect provider declarations. Capacity stays unknown until there is measured evidence.</EmptyState> :
        <div className="grid">{providers.map(p => <article key={p.id}><h3>{p.id}</h3>
          <Badge state="unknown">Capacity unknown</Badge><p>{p.energy.kind === 'compute' ? 'Local compute' : 'Shared subscription pool'}</p>
          <small>{p.id === 'ollama' ? 'Installed weights are verified before each local run.' : 'Cloud execution is not available in this preview.'}</small></article>)}</div>}
    </section>

        <section className="page-view" hidden={view !== 'workspace'} aria-label="Workspace setup"><PageHeading eyebrow="MAKE YOURSELF AT HOME" title="Your workspace" description="Connect once. Bring your projects. Keep your work on your device." /><div className="setup-grid">
    <section aria-labelledby="connection"><h2 id="connection">Connect your engine</h2><p>Your session stays private on this device.</p>
      <form onSubmit={connect}><label htmlFor="token">Engine session token</label>
        <div className="connect"><input id="token" type="password" value={token} onChange={e => setToken(e.target.value)} disabled={busy || saving || projectBusy || taskBusy} autoComplete="off" required />
        <Button variant="primary" disabled={busy || saving || projectBusy || taskBusy || editor !== null}>{busy ? 'Connecting…' : 'Connect'}</Button></div></form>
      <p role="status">{status}</p></section>
    <section aria-labelledby="projects"><h2 id="projects">Add a project</h2><p>Bring any local Git repository into your workspace.</p>
      {selected && <p role="status">Selected {selected.name}: {selected.root}</p>}
      <form className="project-editor" onSubmit={registerProject}>
        <fieldset disabled={!session || busy || projectBusy || taskBusy}>
          <legend>Project details</legend>
          <label htmlFor="project-name">Project name<input id="project-name" required maxLength={120} pattern=".*\S.*"
            value={projectName} onChange={e => setProjectName(e.target.value)} /></label>
          <label htmlFor="project-root">Repository folder (absolute canonical path)<input id="project-root" required maxLength={4096}
            placeholder="/Users/you/Projects/repository" value={projectRoot} onChange={e => setProjectRoot(e.target.value)} /></label>
          <Button variant="primary">{projectBusy ? 'Checking project…' : 'Register project'}</Button>
        </fieldset>
      </form>
      {projectError && <p role="alert">{projectError} Registration entries are retained for retry.</p>}
      <p>Your registration is saved locally. Choose a project from the top bar to work on its missions.</p>
    </section>

        </div></section>
        <footer>Any agent. Any role. Any model. Any project.<span>Orbit · Local preview</span></footer>
      </div>
    </div>
  </main>;
}
createRoot(document.getElementById('root')!).render(<React.StrictMode><App /></React.StrictMode>);
