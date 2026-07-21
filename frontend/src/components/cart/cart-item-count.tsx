export function CartItemCount({ count, className = "cart-link__count" }: { count: number; className?: string }) {
  if (count <= 0) return null;
  return <span className={className} aria-hidden="true">{count > 99 ? "99+" : count}</span>;
}
