export type ModelInfo = {
  chain_name: string;
  chain_id: number;
  artifact_id: string;
  model_family: string;
  max_delay_seconds: number;
  slot_spacing_seconds: number;
  demo_contract_address: string;
};

export type Prediction = {
  request_id: string;
  chain_name: string;
  chain_id: number;
  artifact_id: string;
  observed_block: number;
  observed_timestamp: number;
  baseline_block: number;
  broadcast_after_block: number;
  target_block: number;
  target_timestamp_estimate: number;
  selected_offset: number;
  recommended_wait_seconds: number;
  expires_at_unix: number;
  support_start_block: number;
  support_end_block: number;
};

export type ObserveResult = {
  request_id: string;
  tx_hash: string;
  included_block: number;
  gas_used: string;
  baseline_block: number;
  baseline_fee_wei: string;
  model_fee_wei: string;
  savings_wei: string;
  savings_percent: number;
};

export type AnalyticsResponse = {
  totals: {
    run_count: number;
    baseline_fee_total_wei: string;
    model_fee_total_wei: string;
    savings_total_wei: string;
    savings_percent: number;
    win_count: number;
  };
  rows: Array<{
    request_id: string;
    created_at: string;
    tx_hash: string | null;
    wait_seconds: number;
    baseline_block: number;
    included_block: number | null;
    baseline_fee_wei: string | null;
    model_fee_wei: string | null;
    savings_wei: string | null;
    savings_percent: number | null;
  }>;
};

export type RunState =
  | "idle"
  | "predicting"
  | "scheduled"
  | "broadcasting"
  | "confirming"
  | "complete"
  | "failed"
  | "expired";
