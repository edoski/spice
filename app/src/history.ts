import AsyncStorage from "@react-native-async-storage/async-storage";

import type {
  InferenceOutcome,
  InferenceRequest,
  InferenceResponse,
} from "./inference";

const STORAGE_KEY = "fable.inference-runs-v3";
export const MAX_RUNS = 100;

export type InferenceRun = InferenceRequest &
  InferenceResponse & {
    id: string;
    ran_at: string;
    outcome?: RunOutcome;
  };

export type RunOutcome = {
  resolved_at: string;
  immediate_base_fee_per_gas: number;
  selected_base_fee_per_gas: number;
};

export function createRun(
  request: InferenceRequest,
  response: InferenceResponse,
): InferenceRun {
  const ranAt = new Date().toISOString();
  return {
    id: `${ranAt}:${request.chain}:${request.K}:${response.head_block}`,
    ran_at: ranAt,
    ...request,
    ...response,
  };
}

export function recordOutcome(
  run: InferenceRun,
  outcome: InferenceOutcome,
): InferenceRun {
  return {
    ...run,
    outcome: {
      resolved_at: new Date().toISOString(),
      immediate_base_fee_per_gas: outcome.immediate_base_fee_per_gas,
      selected_base_fee_per_gas: outcome.selected_base_fee_per_gas,
    },
  };
}

export async function loadRuns(): Promise<InferenceRun[]> {
  const stored = await AsyncStorage.getItem(STORAGE_KEY);
  if (stored === null) {
    return [];
  }
  return (JSON.parse(stored) as InferenceRun[]).slice(0, MAX_RUNS);
}

export async function saveRuns(runs: readonly InferenceRun[]): Promise<void> {
  await AsyncStorage.setItem(
    STORAGE_KEY,
    JSON.stringify(runs.slice(0, MAX_RUNS)),
  );
}
