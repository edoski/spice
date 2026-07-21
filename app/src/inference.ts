declare const process: {
  env: {
    EXPO_PUBLIC_FABLE_BACKEND_URL?: string;
  };
};

export const CHAINS = ["ethereum", "polygon", "avalanche"] as const;
export type Chain = (typeof CHAINS)[number];

export const HORIZONS = [2, 3, 4, 5] as const;
export type Horizon = (typeof HORIZONS)[number];

export const CHAIN_DETAILS: Record<
  Chain,
  { label: string; mark: string; color: string }
> = {
  ethereum: { label: "Ethereum", mark: "E", color: "#627EEA" },
  polygon: { label: "Polygon", mark: "P", color: "#8247E5" },
  avalanche: { label: "Avalanche", mark: "A", color: "#E84142" },
};

export type InferenceRequest = {
  chain: Chain;
  K: Horizon;
};

export type InferenceResponse = {
  head_block: number;
  selected_action_k: number;
  target_block: number;
  predicted_minimum_base_fee_per_gas: number;
};

export type HealthResponse = {
  chain: Chain;
  head_block: number;
};

function backendUrl(): string {
  const value = process.env.EXPO_PUBLIC_FABLE_BACKEND_URL?.replace(/\/+$/, "");
  if (!value) {
    throw new Error("EXPO_PUBLIC_FABLE_BACKEND_URL is required");
  }
  return value;
}

async function requestJson(path: string, init: RequestInit): Promise<unknown> {
  let response: Response;
  try {
    response = await fetch(backendUrl() + path, init);
  } catch (error) {
    if (error instanceof Error && error.name === "AbortError") {
      throw error;
    }
    const message = error instanceof Error ? error.message : String(error);
    throw new Error("Network error: " + message);
  }
  const body = await response.text();
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${body.trim()}`);
  }
  try {
    return JSON.parse(body) as unknown;
  } catch {
    throw new Error("Server returned invalid JSON");
  }
}

function requireObject(value: unknown): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new Error("Server response must be an object");
  }
  return value as Record<string, unknown>;
}

function requireInteger(value: unknown, name: string): number {
  if (typeof value !== "number" || !Number.isInteger(value) || value < 0) {
    throw new Error(`${name} must be a nonnegative integer`);
  }
  return value;
}

export async function requestInference(
  request: InferenceRequest,
  signal?: AbortSignal,
): Promise<InferenceResponse> {
  const value = requireObject(
    await requestJson("/inference", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
      signal,
    }),
  );
  const headBlock = requireInteger(value.head_block, "head_block");
  const selectedAction = requireInteger(value.selected_action_k, "selected_action_k");
  const targetBlock = requireInteger(value.target_block, "target_block");
  const predictedMinimum = value.predicted_minimum_base_fee_per_gas;
  if (
    typeof predictedMinimum !== "number" ||
    !Number.isFinite(predictedMinimum) ||
    predictedMinimum <= 0
  ) {
    throw new Error("predicted_minimum_base_fee_per_gas must be positive and finite");
  }
  if (selectedAction >= request.K || targetBlock !== headBlock + 1 + selectedAction) {
    throw new Error("Server returned invalid inference geometry");
  }
  return {
    head_block: headBlock,
    selected_action_k: selectedAction,
    target_block: targetBlock,
    predicted_minimum_base_fee_per_gas: predictedMinimum,
  };
}

export async function checkHealth(chain: Chain, signal?: AbortSignal): Promise<HealthResponse> {
  const value = requireObject(
    await requestJson(`/health?chain=${encodeURIComponent(chain)}`, { method: "GET", signal }),
  );
  if (value.chain !== chain) {
    throw new Error("Health response chain does not match the request");
  }
  return { chain, head_block: requireInteger(value.head_block, "head_block") };
}
