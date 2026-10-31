import React from 'react';

export type IconName = 'orbit' | 'missions' | 'agents' | 'providers' | 'workspace' | 'plus' | 'arrow' | 'sun' | 'moon' | 'refresh';
const paths: Record<IconName, React.ReactNode> = {
  orbit: <><circle cx="12" cy="12" r="3" /><ellipse cx="12" cy="12" rx="10" ry="5" transform="rotate(-35 12 12)" /><circle cx="19" cy="6" r="1.6" fill="currentColor" stroke="none" /></>,
  missions: <><rect x="4" y="4" width="16" height="16" rx="4" /><path d="m8 12 3 3 5-6" /></>,
  agents: <><circle cx="9" cy="8" r="3" /><path d="M3 20v-2a6 6 0 0 1 12 0v2M16 5a3 3 0 0 1 0 6m3 9v-2a6 6 0 0 0-3-5" /></>,
  providers: <><path d="M12 3 3 8l9 5 9-5-9-5Zm-9 9 9 5 9-5M3 16l9 5 9-5" /></>,
  workspace: <><rect x="3" y="4" width="18" height="13" rx="3" /><path d="M8 21h8m-4-4v4M7 8h4" /></>,
  plus: <path d="M12 5v14M5 12h14" />,
  arrow: <path d="M5 12h14m-6-6 6 6-6 6" />,
  sun: <><circle cx="12" cy="12" r="4" /><path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1 1m12 12 1 1M5 19l1-1M18 6l1-1" /></>,
  moon: <path d="M20 15a9 9 0 0 1-11-11 9 9 0 1 0 11 11Z" />,
  refresh: <><path d="M20 8a8 8 0 1 0 0 8M20 3v5h-5" /></>,
};
export function Icon({ name, className = '' }: { name: IconName; className?: string }) {
  return <svg className={`icon ${className}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{paths[name]}</svg>;
}
export function Button({ variant = 'secondary', className = '', children, ...props }:
  React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: 'primary' | 'secondary' | 'quiet' | 'danger' }) {
  return <button className={`button button--${variant} ${className}`} {...props}>{children}</button>;
}
export function Panel({ className = '', ...props }: React.HTMLAttributes<HTMLElement>) {
  return <section className={`panel ${className}`} {...props} />;
}
export function Badge({ state, children }: { state: string; children?: React.ReactNode }) {
  const tone = ['running', 'available', 'connected'].includes(state) ? 'active' :
    ['awaiting_review', 'awaiting_approval', 'blocked'].includes(state) ? 'attention' :
    ['failed', 'cancelled'].includes(state) ? 'muted' : state === 'completed' ? 'success' : 'neutral';
  return <span className={`badge badge--${tone}`}><span className="badge-dot" />{children ?? state.replaceAll('_', ' ')}</span>;
}
export function EmptyState({ icon = 'orbit', title, children, action }: {
  icon?: IconName; title: string; children: React.ReactNode; action?: React.ReactNode;
}) {
  return <div className="empty-state"><div className="empty-state-symbol"><Icon name={icon} /></div>
    <h3>{title}</h3><p>{children}</p>{action}</div>;
}
export function PageHeading({ eyebrow, title, description, action }: {
  eyebrow: string; title: string; description: string; action?: React.ReactNode;
}) {
  return <header className="page-heading"><div><span className="eyebrow">{eyebrow}</span><h1>{title}</h1><p>{description}</p></div>{action}</header>;
}

export function Tabs({ id, items, value, onChange }: { id: string; items: { id: string; label: string }[];
  value: string; onChange: (value: string) => void }) {
  return <div className="tabs" role="tablist" aria-label="Mission detail views">{items.map((item, index) =>
    <Button key={item.id} type="button" variant="quiet" role="tab" id={`${id}-tab-${item.id}`} aria-controls={`${id}-panel-${item.id}`}
      aria-selected={value === item.id} tabIndex={value === item.id ? 0 : -1} onClick={() => onChange(item.id)}
      onKeyDown={event => {
        let next = index;
        if (event.key === 'ArrowRight') next = (index + 1) % items.length;
        else if (event.key === 'ArrowLeft') next = (index + items.length - 1) % items.length;
        else if (event.key === 'Home') next = 0;
        else if (event.key === 'End') next = items.length - 1;
        else return;
        event.preventDefault(); onChange(items[next].id);
        (event.currentTarget.parentElement?.querySelectorAll<HTMLButtonElement>('[role="tab"]')[next])?.focus();
      }}>{item.label}</Button>)}</div>;
}
