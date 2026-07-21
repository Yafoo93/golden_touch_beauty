import type { CSSProperties } from "react";


export type SkeletonProps = {
  variant?: "text" | "block" | "circle";
  width?: CSSProperties["width"];
  height?: CSSProperties["height"];
  className?: string;
};

export function Skeleton({
  variant = "block",
  width,
  height,
  className,
}: SkeletonProps) {
  return (
    <span
      className={[
        "skeleton",
        `skeleton--${variant}`,
        className ?? "",
      ]
        .filter(Boolean)
        .join(" ")}
      style={{ width, height }}
      aria-hidden="true"
    />
  );
}

export function CardSkeleton() {
  return (
    <article className="card-skeleton" aria-hidden="true">
      <Skeleton className="card-skeleton__image" />
      <div className="card-skeleton__body">
        <Skeleton variant="text" width="36%" />
        <Skeleton variant="text" width="72%" height="1.35rem" />
        <Skeleton variant="text" />
        <Skeleton variant="text" width="88%" />
        <div className="card-skeleton__footer">
          <Skeleton variant="text" width="30%" height="1.4rem" />
          <Skeleton width="7rem" height="2.75rem" />
        </div>
      </div>
    </article>
  );
}

export function ListSkeleton({ rows = 4 }: { rows?: number }) {
  return (
    <div className="list-skeleton" aria-hidden="true">
      {Array.from({ length: Math.max(1, rows) }, (_, index) => (
        <div className="list-skeleton__row" key={index}>
          <Skeleton variant="circle" width="2.75rem" height="2.75rem" />
          <div>
            <Skeleton variant="text" width="55%" />
            <Skeleton variant="text" width="82%" />
          </div>
        </div>
      ))}
    </div>
  );
}

export function PageSkeleton({ label = "Loading page" }: { label?: string }) {
  return (
    <main
      className="page-skeleton"
      role="status"
      aria-live="polite"
      aria-busy="true"
    >
      <span className="sr-only">{label}</span>
      <section className="page-skeleton__hero" aria-hidden="true">
        <Skeleton variant="text" width="12rem" />
        <Skeleton variant="text" width="min(80%, 42rem)" height="4rem" />
        <Skeleton variant="text" width="min(65%, 34rem)" />
        <Skeleton width="10rem" height="3.25rem" />
      </section>
      <section className="page-skeleton__content" aria-hidden="true">
        <Skeleton variant="text" width="16rem" height="2rem" />
        <div className="page-skeleton__grid">
          <CardSkeleton />
          <CardSkeleton />
          <CardSkeleton />
        </div>
      </section>
    </main>
  );
}
