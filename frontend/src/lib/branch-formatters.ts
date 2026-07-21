export function formatBranchTime(value: string) {
  const [hourValue, minute = "00"] = value.split(":");
  const hour = Number(hourValue);
  const suffix = hour >= 12 ? "PM" : "AM";
  return `${hour % 12 || 12}:${minute} ${suffix}`;
}

export function formatOpeningDays(days: string[]) {
  if (days.length === 0) return "Contact the branch for opening days";
  const capitalize = (day: string) => day[0].toUpperCase() + day.slice(1);
  if (days.length === 1) return capitalize(days[0]);
  return `${capitalize(days[0])} - ${capitalize(days.at(-1) ?? days[0])}`;
}

export function formatGhanaPhone(value: string) {
  const digits = value.replace(/\D/g, "");
  if (digits.length !== 12 || !digits.startsWith("233")) return value;
  return `+233 ${digits.slice(3, 6)} ${digits.slice(6, 9)} ${digits.slice(9)}`;
}

export function whatsappUrl(value: string) {
  return `https://wa.me/${value.replace(/\D/g, "")}`;
}
