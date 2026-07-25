import type { Metadata } from "next";
import { cookies } from "next/headers";

import { GalleryManager } from "@/components/management/gallery-manager";
import { ButtonLink } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import type { ManagementGalleryItem } from "@/lib/gallery";

export const metadata: Metadata = { title: "Manage Gallery" };

type LoadResult =
  | { status: "success"; items: ManagementGalleryItem[] }
  | { status: "denied" }
  | { status: "error" };

async function loadGallery(): Promise<LoadResult> {
  const backendUrl = process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:8000";
  const cookieHeader = (await cookies()).toString();
  try {
    const response = await fetch(`${backendUrl}/api/v1/gallery/management/`, {
      cache: "no-store",
      headers: { Accept: "application/json", Cookie: cookieHeader },
      signal: AbortSignal.timeout(15_000),
    });
    if (response.status === 401 || response.status === 403) return { status: "denied" };
    if (!response.ok) return { status: "error" };
    return { status: "success", items: (await response.json()) as ManagementGalleryItem[] };
  } catch {
    return { status: "error" };
  }
}

export default async function ManagementGalleryPage() {
  const result = await loadGallery();
  return (
    <main className="management-page management-page--gallery">
      <header className="management-page__header">
        <div>
          <p>Management · Website</p>
          <h1>Gallery</h1>
          <span>Upload, describe, arrange, review, and publish approved beauty-work images.</span>
        </div>
        <div className="management-page__summary">
          <strong>Responsible publishing</strong>
          <span>Only publish images approved for public use. Descriptive alternative text is required for accessibility.</span>
          <ButtonLink href="/gallery" variant="outline" size="small">View public gallery</ButtonLink>
        </div>
      </header>
      {result.status === "denied" ? (
        <EmptyState title="Owner access required" description="Sign in with the owner account to manage the public gallery." action={<ButtonLink href="/login">Sign in</ButtonLink>} />
      ) : result.status === "error" ? (
        <EmptyState title="Gallery could not be loaded" description="Check that Django is running, then try again." action={<ButtonLink href="/management/gallery">Try again</ButtonLink>} />
      ) : (
        <GalleryManager initialItems={result.items} />
      )}
    </main>
  );
}
