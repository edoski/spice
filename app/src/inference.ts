declare const process: {
  env: {
    EXPO_PUBLIC_FABLE_BACKEND_URL?: string;
  };
};

export const CHAINS = ["ethereum", "polygon", "avalanche"] as const;
export type Chain = (typeof CHAINS)[number];

export const HORIZONS = [2, 3, 4, 5] as const;
export type Horizon = (typeof HORIZONS)[number];

export const CHAIN_DETAILS: Record<Chain, { label: string }> = {
  ethereum: { label: "Ethereum" },
  polygon: { label: "Polygon" },
  avalanche: { label: "Avalanche" },
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

export type ChainSnapshot = {
  chain: Chain;
  head_block: number;
  current_base_fee_per_gas: number;
};

export type InferenceOutcome = {
  chain: Chain;
  immediate_block: number;
  selected_block: number;
  immediate_base_fee_per_gas: number;
  selected_base_fee_per_gas: number;
};

function backendUrl(): string {
  const value = process.env.EXPO_PUBLIC_FABLE_BACKEND_URL?.replace(/\/+$/, "");
  if (!value) {
    throw new Error("EXPO_PUBLIC_FABLE_BACKEND_URL is required");
  }
  return value;
}

async function requestJson<T>(path: string, init: RequestInit): Promise<T> {
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
    return JSON.parse(body) as T;
  } catch {
    throw new Error("Server returned invalid JSON");
  }
}

export async function requestInference(
  request: InferenceRequest,
  signal?: AbortSignal,
): Promise<InferenceResponse> {
  return requestJson<InferenceResponse>("/inference", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
    signal,
  });
}

export async function requestChainSnapshot(
  chain: Chain,
  signal?: AbortSignal,
): Promise<ChainSnapshot> {
  return requestJson<ChainSnapshot>(
    `/snapshot?chain=${encodeURIComponent(chain)}`,
    {
      method: "GET",
      signal,
    },
  );
}

export async function requestInferenceOutcome(
  chain: Chain,
  immediateBlock: number,
  selectedBlock: number,
  signal?: AbortSignal,
): Promise<InferenceOutcome> {
  const query = new URLSearchParams({
    chain,
    immediate_block: String(immediateBlock),
    selected_block: String(selectedBlock),
  });
  return requestJson<InferenceOutcome>(`/outcome?${query}`, {
    method: "GET",
    signal,
  });
}
