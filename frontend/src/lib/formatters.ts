const ghanaCediFormatter = new Intl.NumberFormat("en-GH", {
  style: "currency",
  currency: "GHS",
  minimumFractionDigits: 0,
  maximumFractionDigits: 2,
});

export function formatGhanaCedis(value: number | string) {
  const amount = typeof value === "string" ? Number(value) : value;
  return ghanaCediFormatter.format(Number.isFinite(amount) ? amount : 0);
}
