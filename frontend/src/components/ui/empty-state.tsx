import type { ReactNode } from "react";

export type EmptyStateProps = { title: string; description: string; action?: ReactNode; icon?: ReactNode };

function DefaultEmptyIcon() { return <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7.5h16v11H4z" /><path d="M8 7.5V5.8A1.8 1.8 0 0 1 9.8 4h4.4A1.8 1.8 0 0 1 16 5.8v1.7M9 12h6" /></svg>; }

export function EmptyState({ title, description, action, icon = <DefaultEmptyIcon /> }: EmptyStateProps) {
  return <section className="empty-state"><div className="empty-state__icon">{icon}</div><h2>{title}</h2><p>{description}</p>{action ? <div className="empty-state__action">{action}</div> : null}</section>;
}
