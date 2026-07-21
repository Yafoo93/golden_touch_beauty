import { ButtonLink } from "@/components/ui/button";
import { PageHero } from "@/components/ui/page-hero";


export default function NotFoundPage() {
  return (
    <main className="not-found-page">
      <PageHero
        eyebrow="404 - Page not found"
        title="We could not find"
        accentTitle="That Page"
        description="The page may have moved, the address may be incorrect, or the content may not be available yet."
        size="compact"
        actions={
          <>
            <ButtonLink href="/">Return home</ButtonLink>
            <ButtonLink href="/services" variant="black">
              Browse services
            </ButtonLink>
            <ButtonLink href="/shop" variant="outline">
              Visit the shop
            </ButtonLink>
          </>
        }
      />
    </main>
  );
}
