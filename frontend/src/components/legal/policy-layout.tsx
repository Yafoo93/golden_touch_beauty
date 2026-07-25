import Link from "next/link";
import type { ReactNode } from "react";

export type PolicySection = {
  id: string;
  title: string;
  content: ReactNode;
};

type PolicyLayoutProps = {
  eyebrow: string;
  title: string;
  description: string;
  status: string;
  sections: PolicySection[];
};

export function PolicyLayout({
  eyebrow,
  title,
  description,
  status,
  sections,
}: PolicyLayoutProps) {
  return (
    <main className="legal-page">
      <header className="legal-hero">
        <div>
          <p>{eyebrow}</p>
          <h1>{title}</h1>
          <span>{description}</span>
          <div className="legal-hero__status" role="note">
            <strong>Development draft</strong>
            <p>{status}</p>
          </div>
        </div>
      </header>

      <div className="legal-layout">
        <aside className="legal-navigation">
          <p>On this page</p>
          <nav aria-label={`${title} sections`}>
            {sections.map((section, index) => (
              <a href={`#${section.id}`} key={section.id}>
                <span>{String(index + 1).padStart(2, "0")}</span>
                {section.title}
              </a>
            ))}
          </nav>
        </aside>

        <article className="legal-content">
          {sections.map((section, index) => (
            <section id={section.id} key={section.id}>
              <div className="legal-content__section-heading">
                <span>{String(index + 1).padStart(2, "0")}</span>
                <h2>{section.title}</h2>
              </div>
              <div className="legal-content__copy">{section.content}</div>
            </section>
          ))}

          <footer className="legal-content__footer">
            <p>
              Questions about this draft can be directed to a Golden Touch
              branch while final legal contact information is being approved.
            </p>
            <Link href="/contact">View branch contacts</Link>
          </footer>
        </article>
      </div>
    </main>
  );
}
