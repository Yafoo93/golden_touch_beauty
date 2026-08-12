import type { Metadata } from "next";

import { ButtonLink } from "@/components/ui/button";
import { managementMetricDefinitions } from "@/lib/management-metric-definitions";

export const metadata: Metadata = { title: "Metric methodology | Management" };

export default function ReportMethodologyPage() {
  return (
    <main className="management-methodology">
      <header>
        <div>
          <p>Management / Reports / Governance</p>
          <h1>Metric methodology</h1>
          <span>Written formulas for every management overview and report summary number.</span>
        </div>
        <ButtonLink href="/management/reports" variant="outline">All reports</ButtonLink>
      </header>

      <aside className="management-report-note">
        <strong>Calculation rules:</strong> Currency is Ghana cedi unless stated otherwise. Counts and sums are calculated after branch permissions and selected filters are applied. Percentages and averages return zero when their denominator is zero. Money is displayed to two decimal places.
      </aside>

      <nav className="management-methodology__index" aria-label="Metric sections">
        {managementMetricDefinitions.map((section) => <a href={`#${section.id}`} key={section.id}>{section.title}</a>)}
      </nav>

      {managementMetricDefinitions.map((section) => (
        <section id={section.id} key={section.id}>
          <header><h2>{section.title}</h2><p>{section.scope}</p></header>
          <div className="management-table-wrap">
            <table>
              <thead><tr><th>Dashboard number</th><th>Written formula</th></tr></thead>
              <tbody>{section.metrics.map((metric) => <tr key={metric.name}><th scope="row">{metric.name}</th><td>{metric.formula}{metric.notes ? <small>{metric.notes}</small> : null}</td></tr>)}</tbody>
            </table>
          </div>
        </section>
      ))}
    </main>
  );
}
