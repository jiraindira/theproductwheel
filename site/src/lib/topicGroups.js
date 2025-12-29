// src/lib/topicGroups.js
export const GROUPS = [
  { key: "home", label: "Home", categories: ["home_and_kitchen", "food_and_cooking", "pets"] },
  { key: "life", label: "Life", categories: ["health_and_fitness", "beauty_and_grooming", "fashion", "parenting_and_family"] },
  { key: "work_money", label: "Work & Money", categories: ["finance_and_productivity"] },
  { key: "tech_travel", label: "Tech & Travel", categories: ["technology", "outdoors_and_travel"] },
];

export function groupForCategory(category) {
  const g = GROUPS.find((x) => x.categories.includes(category));
  return g ? { key: g.key, label: g.label } : { key: "other", label: "Other" };
}

export function prettyCategory(s) {
  if (!s) return "";
  return s
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase())
    .replace(/\bAnd\b/g, "&");
}
