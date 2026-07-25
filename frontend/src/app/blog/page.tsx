import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";

import { ButtonLink } from "@/components/ui/button";
import { PageHero } from "@/components/ui/page-hero";
import { blogPosts } from "@/lib/blog";

export const metadata: Metadata = {
  title: "Beauty Tips",
  description:
    "Practical skincare, hair-care, bridal preparation, and beauty-product guides from Golden Touch Beauty Centre.",
};

export default function BlogPage() {
  const [featuredPost, ...posts] = blogPosts;

  return (
    <main className="blog-page">
      <PageHero
        eyebrow="Golden Touch journal"
        title="Beauty Tips for"
        accentTitle="Everyday Care"
        description="Practical guidance for thoughtful skincare, hair care, bridal preparation, and personal-care routines."
        backgroundImage="/images/body_cream1.jpeg"
        backgroundPosition="center 48%"
        size="compact"
      />

      <section className="blog-page__content" aria-labelledby="blog-title">
        <div className="blog-page__heading">
          <p>Latest guides</p>
          <h2 id="blog-title">Learn, prepare, and care with confidence</h2>
          <span>
            These general educational guides do not replace individualized
            medical advice, diagnosis, or treatment.
          </span>
        </div>

        <article className="blog-featured">
          <Link
            href={`/blog/${featuredPost.slug}`}
            className="blog-featured__image"
            aria-label={`Read ${featuredPost.title}`}
          >
            <Image
              src={featuredPost.image}
              alt={featuredPost.imageAlt}
              fill
              sizes="(max-width: 800px) 100vw, 52vw"
              priority
            />
          </Link>
          <div className="blog-featured__content">
            <div className="blog-card__meta">
              <span>{featuredPost.category}</span>
              <p>{featuredPost.readTime}</p>
            </div>
            <h3>
              <Link href={`/blog/${featuredPost.slug}`}>
                {featuredPost.title}
              </Link>
            </h3>
            <p>{featuredPost.excerpt}</p>
            <ButtonLink href={`/blog/${featuredPost.slug}`} variant="outline">
              Read guide
            </ButtonLink>
          </div>
        </article>

        <div className="blog-grid">
          {posts.map((post) => (
            <article className="blog-card" key={post.slug}>
              <Link
                href={`/blog/${post.slug}`}
                className="blog-card__image"
                aria-label={`Read ${post.title}`}
              >
                <Image
                  src={post.image}
                  alt={post.imageAlt}
                  fill
                  sizes="(max-width: 720px) 100vw, 33vw"
                />
              </Link>
              <div className="blog-card__content">
                <div className="blog-card__meta">
                  <span>{post.category}</span>
                  <p>{post.readTime}</p>
                </div>
                <h3>
                  <Link href={`/blog/${post.slug}`}>{post.title}</Link>
                </h3>
                <p>{post.excerpt}</p>
                <Link className="blog-card__read-link" href={`/blog/${post.slug}`}>
                  Read guide <span aria-hidden="true">→</span>
                </Link>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="blog-cta" aria-labelledby="blog-cta-title">
        <div>
          <p>Personalized care</p>
          <h2 id="blog-cta-title">Need guidance for your own beauty goals?</h2>
          <span>
            Book a consultation or contact a Golden Touch branch for assistance.
          </span>
        </div>
        <div className="blog-cta__actions">
          <ButtonLink href="/contact" variant="outline">
            Contact us
          </ButtonLink>
          <ButtonLink href="/book">Book an appointment</ButtonLink>
        </div>
      </section>
    </main>
  );
}
