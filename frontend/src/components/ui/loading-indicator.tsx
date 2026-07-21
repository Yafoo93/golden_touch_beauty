export type LoadingIndicatorProps = { label?: string; size?: "small" | "medium" | "large"; presentation?: "inline" | "panel" };

export function LoadingIndicator({ label = "Loading", size = "medium", presentation = "inline" }: LoadingIndicatorProps) {
  return <div className={`loading-indicator loading-indicator--${presentation}`} role="status" aria-live="polite"><span className={`loading-indicator__spinner loading-indicator__spinner--${size}`} aria-hidden="true" /><span>{label}</span></div>;
}
