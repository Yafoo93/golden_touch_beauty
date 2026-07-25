import type { Metadata } from "next";
import { cookies } from "next/headers";

import { ContentEditor } from "@/components/management/content-editor";
import { ButtonLink } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import type { ManagementWebsiteContent } from "@/lib/website-content";

export const metadata: Metadata = { title: "Manage Website Content" };

type LoadResult =
  | { status: "success"; items: ManagementWebsiteContent[] }
  | { status: "denied" }
  | { status: "error" };

async function loadContent(): Promise<LoadResult> {
  const backendUrl =
    process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:8000";
  const cookieHeader = (await cookies()).toString();
  try {
    const response = await fetch(`${backendUrl}/api/v1/content/management/`, {
      cache: "no-store",
      headers: { Accept: "application/json", Cookie: cookieHeader },
      signal: AbortSignal.timeout(15_000),
    });
    if (response.status === 401 || response.status === 403) {
      return { status: "denied" };
    }
    if (!response.ok) return { status: "error" };
    return {
      status: "success",
      items: (await response.json()) as ManagementWebsiteContent[],
    };
  } catch {
    return { status: "error" };
  }
}

export default async function ManagementContentPage() {
  const result = await loadContent();
  return (
    <main className="management-page management-page--content">
      <header className="management-page__header">
        <div>
          <p>Management · Website</p>
          <h1>Website content</h1>
          <span>
            Edit approved operational text without changing the website code or
            design.
          </span>
        </div>
        <div className="management-page__summary">
          <strong>Controlled publishing</strong>
          <span>
            Only reviewed fields appear here. Content is stored as plain text,
            and every update is attributed in the audit log.
          </span>
          <ButtonLink href="/" variant="outline" size="small">
            View website
          </ButtonLink>
        </div>
      </header>

      {result.status === "denied" ? (
        <EmptyState
          title="Owner access required"
          description="Sign in with the owner account to edit global website content."
          action={<ButtonLink href="/login">Sign in</ButtonLink>}
        />
      ) : result.status === "error" ? (
        <EmptyState
          title="Content could not be loaded"
          description="Check that Django is running, then try again."
          action={<ButtonLink href="/management/content">Try again</ButtonLink>}
        />
      ) : result.items.length === 0 ? (
        <EmptyState
          title="No approved content fields"
          description="Apply the latest backend migrations to install the approved content records."
        />
      ) : (
        <ContentEditor items={result.items} />
      )}
    </main>
  );
}
