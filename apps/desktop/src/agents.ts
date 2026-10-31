export type Profile = {
  name: string; role: string; seniority: string; expertise: string[];
  skills: string[]; instructions: string; tools: string[]; provider: string; model: string;
};
export type Agent = Profile & { id: string };
export const emptyProfile = (): Profile => ({ name: '', role: '', seniority: 'unspecified',
  expertise: [], skills: [], instructions: '', tools: [], provider: 'ollama', model: '' });
export function profileOf(agent: Agent): Profile {
  const { id: _id, ...profile } = agent;
  return { ...profile, expertise: [...profile.expertise], skills: [...profile.skills], tools: [...profile.tools] };
}
export async function request<T>(token: string, path: string, profile?: Profile | { name: string; root: string }): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`http://127.0.0.1:8765/v1${path}`, {
      method: profile ? ((path === '/agents' || path === '/projects') ? 'POST' : 'PUT') : 'GET',
      headers: { Authorization: `Bearer ${token}`, ...(profile ? { 'Content-Type': 'application/json' } : {}) },
      ...(profile ? { body: JSON.stringify(profile) } : {}), signal: AbortSignal.timeout(5000),
    });
  } catch { throw new Error('Engine unavailable or request timed out. Check the local engine and retry.'); }
  if (!response.ok) {
    if (response.status === 401) throw new Error('Connection denied. Check the engine session token.');
    if (path.startsWith('/projects')) {
      if (response.status === 409) throw new Error('Root already registered or selected checkout unavailable. Check its canonical root.');
      if (response.status === 422) throw new Error('Project rejected. Enter a name and an existing absolute canonical Git checkout root, without symlinks.');
      if (response.status === 404) throw new Error('Project no longer exists. Reconnect to refresh.');
    }
    if (response.status === 404) throw new Error('Agent no longer exists. Reconnect to refresh the list.');
    if (response.status === 422) throw new Error('Profile rejected. Check name, role, seniority, provider and model.');
    throw new Error(`Engine request failed (${response.status}). Retry when the engine is ready.`);
  }
  return response.json();
}
