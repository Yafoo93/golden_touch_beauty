import { ButtonLink } from "@/components/ui/button";

export function ManagementModuleLanding({
  eyebrow,
  title,
  description,
  stage,
}: {
  eyebrow: string;
  title: string;
  description: string;
  stage: string;
}) {
  return (
    <main className="portal-landing">
      <header>
        <p>Management · {eyebrow}</p>
        <h1>{title}</h1>
        <span>{description}</span>
      </header>
      <section className="portal-landing__panel">
        <h2>Workspace ready</h2>
        <p>
          This navigation destination is connected. Its operational tables,
          filters, actions, and permissions will be completed in {stage}, as
          defined in the project checklist.
        </p>
        <div>
          <ButtonLink href="/management" variant="outline">
            Management overview
          </ButtonLink>
        </div>
      </section>
    </main>
  );
}
