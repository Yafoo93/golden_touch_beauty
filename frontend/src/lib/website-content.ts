export type WebsiteContentValues = Record<string, string>;

export type ManagementWebsiteContent = {
  id: string;
  key: string;
  page: string;
  section: string;
  label: string;
  value: string;
  is_published: boolean;
  updated_by: { id: string; full_name: string } | null;
  updated_at: string;
};

type PublicWebsiteContent = { key: string; value: string };

export async function getWebsiteContent(
  defaults: WebsiteContentValues,
): Promise<WebsiteContentValues> {
  const backendUrl =
    process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:8000";

  try {
    const response = await fetch(`${backendUrl}/api/v1/content/`, {
      cache: "no-store",
      headers: { Accept: "application/json" },
      signal: AbortSignal.timeout(10_000),
    });
    if (!response.ok) return defaults;
    const entries = (await response.json()) as PublicWebsiteContent[];
    return entries.reduce(
      (content, entry) => ({ ...content, [entry.key]: entry.value }),
      { ...defaults },
    );
  } catch {
    return defaults;
  }
}
