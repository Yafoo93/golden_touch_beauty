import Image from "next/image";
import type { ReactNode } from "react";


export type PageHeroProps = {
  eyebrow?: string;
  title: string;
  accentTitle?: string;
  description?: string;
  backgroundImage?: string;
  backgroundPosition?: string;
  actions?: ReactNode;
  align?: "left" | "center";
  size?: "compact" | "large";
  className?: string;
};

export function PageHero({
  eyebrow,
  title,
  accentTitle,
  description,
  backgroundImage,
  backgroundPosition = "center",
  actions,
  align = "center",
  size = "compact",
  className,
}: PageHeroProps) {
  const classes = [
    "page-hero",
    `page-hero--${align}`,
    `page-hero--${size}`,
    backgroundImage ? "page-hero--with-image" : "",
    className ?? "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <section className={classes}>
      {backgroundImage ? (
        <Image
          src={backgroundImage}
          alt=""
          fill
          priority={size === "large"}
          sizes="100vw"
          className="page-hero__image"
          style={{ objectPosition: backgroundPosition }}
        />
      ) : null}
      <div className="page-hero__overlay" aria-hidden="true" />
      <div className="page-hero__content">
        {eyebrow ? (
          <p className="page-hero__eyebrow">
            <span aria-hidden="true" />
            {eyebrow}
            <span aria-hidden="true" />
          </p>
        ) : null}
        <h1>
          <span>{title}</span>
          {accentTitle ? (
            <span className="page-hero__accent">{accentTitle}</span>
          ) : null}
        </h1>
        {description ? <p className="page-hero__description">{description}</p> : null}
        {actions ? <div className="page-hero__actions">{actions}</div> : null}
      </div>
    </section>
  );
}
