import type { Horizon } from "./inference";
import type { InferenceRun } from "./history";

export const GRAPH_OPTIONS = [
  { value: "offsets", label: "Action offsets" },
  { value: "fees", label: "Predicted fees" },
  { value: "runs", label: "Runs over time" },
] as const;

export type GraphKind = (typeof GRAPH_OPTIONS)[number]["value"];

export type ChartDatum = {
  label: string;
  value: number;
  displayValue: string;
};

export type RunSummary = {
  totalRuns: number;
  immediatePercent: number | null;
  averageOffset: number | null;
};

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

export function summarizeRuns(runs: readonly InferenceRun[]): RunSummary {
  if (runs.length === 0) {
    return { totalRuns: 0, immediatePercent: null, averageOffset: null };
  }
  const immediate = runs.filter((run) => run.selected_action_k === 0).length;
  const offsets = runs.reduce((total, run) => total + run.selected_action_k, 0);
  return {
    totalRuns: runs.length,
    immediatePercent: (immediate / runs.length) * 100,
    averageOffset: offsets / runs.length,
  };
}

function shortTime(value: string): string {
  const date = new Date(value);
  return `${date.getHours().toString().padStart(2, "0")}:${date
    .getMinutes()
    .toString()
    .padStart(2, "0")}`;
}

function shortDate(value: string): string {
  const date = new Date(value);
  return `${date.getDate()} ${MONTHS[date.getMonth()]}`;
}

export function formatRunDate(value: string): string {
  return `${shortDate(value)}, ${shortTime(value)}`;
}

export function formatGwei(value: number): string {
  const gwei = value / 1_000_000_000;
  if (gwei >= 100) {
    return `${gwei.toFixed(0)} Gwei`;
  }
  if (gwei >= 10) {
    return `${gwei.toFixed(1)} Gwei`;
  }
  return `${gwei.toFixed(2)} Gwei`;
}

export function chartData(
  kind: GraphKind,
  runs: readonly InferenceRun[],
  horizon: Horizon,
): ChartDatum[] {
  if (kind === "offsets") {
    return Array.from({ length: horizon }, (_, offset) => {
      const count = runs.filter((run) => run.selected_action_k === offset).length;
      return { label: String(offset), value: count, displayValue: String(count) };
    });
  }
  if (kind === "fees") {
    return runs
      .slice(0, 7)
      .reverse()
      .map((run) => {
        const gwei = run.predicted_minimum_base_fee_per_gas / 1_000_000_000;
        return { label: shortTime(run.ran_at), value: gwei, displayValue: gwei.toFixed(1) };
      });
  }

  const byDate = new Map<string, number>();
  for (const run of runs) {
    const label = shortDate(run.ran_at);
    byDate.set(label, (byDate.get(label) ?? 0) + 1);
  }
  return [...byDate.entries()]
    .slice(0, 7)
    .reverse()
    .map(([label, count]) => ({ label, value: count, displayValue: String(count) }));
}
