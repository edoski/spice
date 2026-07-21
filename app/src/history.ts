import AsyncStorage from "@react-native-async-storage/async-storage";

import type { Chain, Horizon, InferenceRequest, InferenceResponse } from "./inference";

const STORAGE_KEY = "fable.inference-runs";
const MAX_RUNS = 100;

export type InferenceRun = InferenceRequest &
  InferenceResponse & {
    id: string;
    ran_at: string;
  };

function isChain(value: unknown): value is Chain {
  return value === "ethereum" || value === "polygon" || value === "avalanche";
}

function isHorizon(value: unknown): value is Horizon {
  return value === 2 || value === 3 || value === 4 || value === 5;
}

function requireInteger(value: unknown, name: string): number {
  if (typeof value !== "number" || !Number.isInteger(value) || value < 0) {
    throw new Error(`Stored ${name} must be a nonnegative integer`);
  }
  return value;
}

function parseRun(value: unknown): InferenceRun {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new Error("Stored inference run must be an object");
  }
  const run = value as Record<string, unknown>;
  if (typeof run.id !== "string" || typeof run.ran_at !== "string") {
    throw new Error("Stored inference run identity is invalid");
  }
  if (!isChain(run.chain) || !isHorizon(run.K)) {
    throw new Error("Stored inference run selection is invalid");
  }
  const headBlock = requireInteger(run.head_block, "head block");
  const selectedAction = requireInteger(run.selected_action_k, "selected action");
  const targetBlock = requireInteger(run.target_block, "target block");
  const predictedMinimum = run.predicted_minimum_base_fee_per_gas;
  if (
    typeof predictedMinimum !== "number" ||
    !Number.isFinite(predictedMinimum) ||
    predictedMinimum <= 0
  ) {
    throw new Error("Stored predicted minimum base fee must be positive and finite");
  }
  if (selectedAction >= run.K || targetBlock !== headBlock + 1 + selectedAction) {
    throw new Error("Stored inference run geometry is invalid");
  }
  return {
    id: run.id,
    ran_at: run.ran_at,
    chain: run.chain,
    K: run.K,
    head_block: headBlock,
    selected_action_k: selectedAction,
    target_block: targetBlock,
    predicted_minimum_base_fee_per_gas: predictedMinimum,
  };
}

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

export async function loadRuns(): Promise<InferenceRun[]> {
  const stored = await AsyncStorage.getItem(STORAGE_KEY);
  if (stored === null) {
    return [];
  }
  const value: unknown = JSON.parse(stored);
  if (!Array.isArray(value)) {
    throw new Error("Stored inference history must be an array");
  }
  return value.map(parseRun).slice(0, MAX_RUNS);
}

export async function saveRuns(runs: readonly InferenceRun[]): Promise<void> {
  await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(runs.slice(0, MAX_RUNS)));
}
