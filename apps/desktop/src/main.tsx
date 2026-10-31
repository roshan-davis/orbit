import React, { useState } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';

type Agent = { id: string; name: string; role: string; seniority: string; provider: string; model: string };
type Provider = { id: string; execution_enabled: boolean; energy: { kind: string; status: string } };

function App() {
  const [token, setToken] = useState('');
  const [agents, setAgents] = useState<Agent[]>([]);
  const [providers, setProviders] = useState<Provider[]>([]);
  const [status, setStatus] = useState('Start the local engine, then connect.');
  const [busy, setBusy] = useState(false);
  async function connect(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setAgents([]); setProviders([]);
    try {
      const headers = { Authorization: `Bearer ${token}` };
      const responses = await Promise.all(['/agents', '/providers'].map(path =>
        fetch(`http://127.0.0.1:8765/v1${path}`, { headers, signal: AbortSignal.timeout(5000) })));
      if (responses.some(r => !r.ok)) throw new Error('Connection denied. Check the engine token.');
      const [nextAgents, nextProviders] = await Promise.all(responses.map(r => r.json()));
      setAgents(nextAgents); setProviders(nextProviders);
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
        <div className="connect"><input id="token" type="password" value={token} onChange={e => setToken(e.target.value)} autoComplete="off" required />
        <button disabled={busy}>{busy ? 'Connecting…' : 'Connect'}</button></div></form>
      <p role="status">{status}</p></section>
    <section aria-labelledby="energy"><h2 id="energy">Team energy</h2>
      <p>Shared provider pools appear once. Local compute is tracked separately.</p>
      {providers.length === 0 ? <p className="empty">Connect to view provider declarations. No live quota data is available.</p> :
        <div className="grid">{providers.map(p => <article key={p.id}><h3>{p.id}</h3>
          <strong>Unknown</strong><p>{p.energy.kind === 'compute' ? 'Local compute' : 'Shared subscription pool'}</p>
          <small>Telemetry not connected · execution disabled</small></article>)}</div>}
    </section>
    <section aria-labelledby="agents"><h2 id="agents">Persistent agents <span className="count">{agents.length}</span></h2>
      {agents.length === 0 ? <p className="empty">No agents loaded. Profiles can be created through the engine API; the agent editor is planned.</p> :
        <div className="grid">{agents.map(a => <article key={a.id}><h3>{a.name}</h3><p>{a.seniority} · {a.role}</p><small>{a.provider} / {a.model}</small></article>)}</div>}
    </section>
    <footer>Any agent. Any role. Any model. Any project.</footer>
  </main>;
}
createRoot(document.getElementById('root')!).render(<React.StrictMode><App /></React.StrictMode>);
