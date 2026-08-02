export const STATUS_COLORS: Record<string, { fill: string; dark: string }> = {
    "not applied": { fill: "var(--color-not-applied)", dark: "var(--color-not-applied-d)" },
    "applied": { fill: "var(--color-applied)", dark: "var(--color-applied-d)" },
    "oa": { fill: "var(--color-oa)", dark: "var(--color-oa-d)" },
    "behavioral interview": { fill: "var(--color-behavioral)", dark: "var(--color-behavioral-d)" },
    "technical interview": { fill: "var(--color-technical)", dark: "var(--color-technical-d)" },
    "offer": { fill: "var(--color-offer)", dark: "var(--color-offer-d)" },
    "rejected": { fill: "var(--color-rejected)", dark: "var(--color-rejected-d)" },
    "withdrawn": { fill: "var(--color-withdrawn)", dark: "var(--color-withdrawn-d)" },
  };
  
  export const STATUS_LABELS: Record<string, string> = {
    "not applied": "not applied",
    "applied": "applied",
    "oa": "oa",
    "behavioral interview": "behavioral",
    "technical interview": "technical",
    "offer": "offer",
    "rejected": "rejected",
    "withdrawn": "withdrawn",
  };
  
  export const STATUS_ORDER = Object.keys(STATUS_COLORS);