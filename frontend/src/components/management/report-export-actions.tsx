type ExportFilters = Record<string, string | undefined>;

export function ReportExportActions({ report, filters }: { report: string; filters: ExportFilters }) {
  const href = (format: "pdf" | "xlsx" | "csv") => {
    const query = new URLSearchParams({ file_format: format });
    Object.entries(filters).forEach(([key, value]) => { if (value) query.set(key, value); });
    return `/backend-api/v1/reports/${report}/export?${query.toString()}`;
  };
  return <nav className="management-report-exports" aria-label="Export report">
    <span>Export:</span>
    <a href={href("pdf")}>PDF</a>
    <a href={href("xlsx")}>Excel</a>
    <a href={href("csv")}>CSV</a>
  </nav>;
}
