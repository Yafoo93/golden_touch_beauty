import type { Metadata } from "next";
import Image from "next/image";
import { notFound } from "next/navigation";

import { ProductPurchasePanel } from "@/components/shop/product-purchase-panel";
import { ProductCard } from "@/components/catalogue/product-card";
import { ButtonLink } from "@/components/ui/button";
import { getProductDetail, getRelatedProducts } from "@/lib/products";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const product = await getProductDetail(slug);
  if (!product) return { title: "Product Not Found" };
  return { title: product.name, description: product.description };
}

export default async function ProductDetailPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const product = await getProductDetail(slug);
  if (!product) notFound();
  const relatedProducts = await getRelatedProducts(product);
  const images = product.images.length
    ? product.images
    : ["/images/hero2.jpeg"];

  return (
    <main className="product-detail-page">
      <section className="product-detail">
        <div className="product-detail__gallery">
          <div className="product-detail__main-image">
            <Image
              src={images[0]}
              alt={product.name}
              fill
              priority
              sizes="(max-width: 55rem) 100vw, 50vw"
            />
          </div>
          {images.length > 1 ? (
            <div className="product-detail__thumbnails">
              {images.map((image, index) => (
                <div key={`${image}-${index}`}>
                  <Image
                    src={image}
                    alt={`${product.name} view ${index + 1}`}
                    fill
                    sizes="8rem"
                  />
                </div>
              ))}
            </div>
          ) : null}
        </div>

        <div className="product-detail__content">
          <p>{product.category}</p>
          <h1>{product.name}</h1>
          {product.brand ? <span>By {product.brand}</span> : null}
          <div className="product-detail__description">
            {product.description
              .split(/\n+/)
              .filter(Boolean)
              .map((paragraph) => <p key={paragraph}>{paragraph}</p>)}
          </div>
          <ProductPurchasePanel product={product} />
          <ButtonLink href="/shop" variant="outline" size="small">
            Back to shop
          </ButtonLink>
        </div>
      </section>

      {relatedProducts.length ? (
        <section className="related-catalogue" aria-labelledby="related-products-title">
          <header className="related-catalogue__heading">
            <p>You may also like</p>
            <h2 id="related-products-title">Related products</h2>
            <span>More products from the {product.category} collection.</span>
          </header>
          <div className="catalogue-grid">
            {relatedProducts.map((relatedProduct) => (
              <ProductCard key={relatedProduct.slug} {...relatedProduct} />
            ))}
          </div>
        </section>
      ) : null}
    </main>
  );
}
