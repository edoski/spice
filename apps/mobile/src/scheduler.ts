import type { Prediction } from "./types";
import { currentBlockNumber } from "./sepolia";

export type ScheduleCallbacks = {
  isCancelled?: () => boolean;
  onBlock?: (blockNumber: number) => void;
  onExpired?: () => void;
};

export async function waitForBroadcastBlock(
  prediction: Prediction,
  callbacks: ScheduleCallbacks = {},
): Promise<void> {
  while (true) {
    if (callbacks.isCancelled?.()) {
      throw new Error("Prediction cancelled");
    }
    const nowSeconds = Math.floor(Date.now() / 1000);
    if (nowSeconds > prediction.expires_at_unix) {
      callbacks.onExpired?.();
      throw new Error("Prediction expired");
    }
    const blockNumber = await currentBlockNumber();
    if (callbacks.isCancelled?.()) {
      throw new Error("Prediction cancelled");
    }
    callbacks.onBlock?.(blockNumber);
    if (blockNumber >= prediction.broadcast_after_block) {
      return;
    }
    await sleep(3000);
  }
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
