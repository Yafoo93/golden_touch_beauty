export type GalleryDisplaySize = "standard" | "wide" | "tall";

export type GalleryItem = {
  id: string;
  title: string;
  category: string;
  alt_text: string;
  image_url: string;
  display_size: GalleryDisplaySize;
  display_order: number;
};

export type ManagementGalleryItem = GalleryItem & {
  is_published: boolean;
  updated_by: { id: string; full_name: string } | null;
  created_at: string;
  updated_at: string;
};

export async function getGalleryItems(): Promise<GalleryItem[]> {
  const backendUrl =
    process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:8000";
  try {
    const response = await fetch(`${backendUrl}/api/v1/gallery/`, {
      cache: "no-store",
      headers: { Accept: "application/json" },
      signal: AbortSignal.timeout(10_000),
    });
    if (!response.ok) return [];
    return (await response.json()) as GalleryItem[];
  } catch {
    return [];
  }
}
