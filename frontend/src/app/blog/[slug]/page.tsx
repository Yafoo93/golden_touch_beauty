import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { notFound } from "next/navigation";

import { ButtonLink } from "@/components/ui/button";
import { blogArticleContent, blogPosts } from "@/lib/blog";

type ArticlePageProps = {
  params: Promise<{ slug: string }>;
};

function getPost(slug: string) {
  return blogPosts.find((post) => post.slug === slug);
}

export function generateStaticParams() {
  return blogPosts.map((post) => ({ slug: post.slug }));
}

export async function generateMetadata({
  params,
}: ArticlePageProps): Promise<Metadata> {
  const { slug } = await params;
  const post = getPost(slug);

  if (!post) {
    return { title: "Article Not Found" };
  }

  return {
    title: post.title,
    description: post.excerpt,
    openGraph: {
      title: post.title,
      description: post.excerpt,
      images: [{ url: post.image, alt: post.imageAlt }],
      type: "article",
    },
  };
}

export default async function BlogArticlePage({ params }: ArticlePageProps) {
  const { slug } = await params;
  const post = getPost(slug);
  const article = blogArticleContent[slug];

  if (!post || !article) {
    notFound();
  }

  const relatedPosts = blogPosts
    .filter((candidate) => candidate.slug !== post.slug)
    .slice(0, 3);

  return (
    <main className="article-page">
      <article>
        <header className="article-hero">
          <div className="article-hero__image">
            <Image
              src={post.image}
              alt={post.imageAlt}
              fill
              priority
              sizes="100vw"
            />
          </div>
          <div className="article-hero__overlay" aria-hidden="true" />
          <div className="article-hero__content">
            <nav aria-label="Breadcrumb">
              <Link href="/">Home</Link>
              <span aria-hidden="true">/</span>
              <Link href="/blog">Beauty tips</Link>
            </nav>
            <div className="article-hero__meta">
              <span>{post.category}</span>
              <p>{post.readTime}</p>
            </div>
            <h1>{post.title}</h1>
            <p>{post.excerpt}</p>
          </div>
        </header>

        <div className="article-layout">
          <div className="article-body">
            <p className="article-body__introduction">{article.introduction}</p>

            {article.sections.map((section) => (
              <section key={section.heading}>
                <h2>{section.heading}</h2>
                {section.paragraphs.map((paragraph) => (
                  <p key={paragraph}>{paragraph}</p>
                ))}
                {section.bullets ? (
                  <ul>
                    {section.bullets.map((bullet) => (
                      <li key={bullet}>{bullet}</li>
                    ))}
                  </ul>
                ) : null}
              </section>
            ))}

            <p className="article-body__closing">{article.closing}</p>

            <aside className="article-disclaimer">
              <strong>Beauty and health information</strong>
              <p>
                This article provides general educational information. It does
                not replace diagnosis, treatment, or advice from an
                appropriately qualified healthcare professional.
              </p>
            </aside>
          </div>

          <aside className="article-sidebar">
            <p>Golden Touch guidance</p>
            <h2>Need advice for your own routine?</h2>
            <span>
              Contact a branch or book an appropriate consultation for
              individualized service guidance.
            </span>
            <ButtonLink href="/book">Book an appointment</ButtonLink>
            <ButtonLink href="/contact" variant="outline">
              Contact us
            </ButtonLink>
          </aside>
        </div>
      </article>

      <section className="related-articles" aria-labelledby="related-title">
        <div className="related-articles__heading">
          <p>Continue reading</p>
          <h2 id="related-title">More beauty guides</h2>
        </div>
        <div className="related-articles__grid">
          {relatedPosts.map((related) => (
            <article key={related.slug}>
              <span>{related.category}</span>
              <h3>
                <Link href={`/blog/${related.slug}`}>{related.title}</Link>
              </h3>
              <p>{related.excerpt}</p>
            </article>
          ))}
        </div>
        <ButtonLink href="/blog" variant="outline">
          View all beauty tips
        </ButtonLink>
      </section>
    </main>
  );
}
