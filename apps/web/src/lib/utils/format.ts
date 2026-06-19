export function formatScore(value: string | number | null | undefined, suffix = ""): string {
  if (value === null || value === undefined || value === "") return "—";
  const num = typeof value === "string" ? Number(value) : value;
  if (Number.isNaN(num)) return String(value);
  return `${num.toFixed(1)}${suffix}`;
}

export function formatPercent(value: string | number | null | undefined): string {
  return formatScore(value, "%");
}

export function formatLabel(value: string | null | undefined): string {
  if (!value) return "—";
  return value.replaceAll("_", " ");
}
