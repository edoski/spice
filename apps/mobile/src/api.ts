import { BACKEND_URL } from "./config";
import type { AnalyticsResponse, ModelInfo, ObserveResult, Prediction } from "./types";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BACKEND_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });
  if (!response.ok) {
    const body = await response.text();
    throw new Error(`${response.status} ${body}`);
  }
  return (await response.json()) as T;
}

export function fetchModelInfo(): Promise<ModelInfo> {
  return request<ModelInfo>("/v1/model");
}

export function requestPrediction(maxWaitSeconds: number): Promise<Prediction> {
  return request<Prediction>("/v1/predictions", {
    method: "POST",
    body: JSON.stringify({ max_wait_seconds: maxWaitSeconds }),
  });
}

export function observeTransaction(
  requestId: string,
  txHash: string,
): Promise<ObserveResult> {
  return request<ObserveResult>(`/v1/transactions/${requestId}/observe`, {
    method: "POST",
    body: JSON.stringify({ tx_hash: txHash }),
  });
}

export function fetchAnalytics(): Promise<AnalyticsResponse> {
  return request<AnalyticsResponse>(`/v1/analytics?ts=${Date.now()}`);
}
