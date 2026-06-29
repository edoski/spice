import * as Linking from "expo-linking";
import { useEffect, useMemo, useRef, useState } from "react";
import {
  AppState,
  Modal,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import Slider from "@react-native-community/slider";
import { isAddress } from "ethers";

import { fetchModelInfo, observeTransaction, requestPrediction } from "../src/api";
import { ACTIVE_CHAIN, chainLabel, modelLabel } from "../src/config";
import { formatGwei, shortHash } from "../src/format";
import { currentBlockNumber, sendNativeTransfer, waitForReceipt } from "../src/sepolia";
import { waitForBroadcastBlock } from "../src/scheduler";
import type { ModelInfo, ObserveResult, Prediction, RunState } from "../src/types";
import { loadOrCreateBurnerWallet, type BurnerWallet } from "../src/wallet";

type SubmittedTransfer = {
  recipient: string;
  amount: string;
};

export default function RunScreen() {
  const [model, setModel] = useState<ModelInfo | null>(null);
  const [wallet, setWallet] = useState<BurnerWallet | null>(null);
  const [maxWait, setMaxWait] = useState(0);
  const [state, setState] = useState<RunState>("idle");
  const [prediction, setPrediction] = useState<Prediction | null>(null);
  const [currentBlock, setCurrentBlock] = useState<number | null>(null);
  const [recipient, setRecipient] = useState("");
  const [amount, setAmount] = useState("0.001");
  const [submittedTransfer, setSubmittedTransfer] = useState<SubmittedTransfer | null>(null);
  const [result, setResult] = useState<ObserveResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [detailsVisible, setDetailsVisible] = useState(false);
  const stateRef = useRef<RunState>("idle");
  const cancelScheduledRunRef = useRef(false);

  function setRunState(nextState: RunState) {
    stateRef.current = nextState;
    setState(nextState);
  }

  useEffect(() => {
    let mounted = true;
    async function load() {
      const [modelInfo, burner, blockNumber] = await Promise.all([
        fetchModelInfo(),
        loadOrCreateBurnerWallet(),
        currentBlockNumber(),
      ]);
      if (!mounted) return;
      setModel(modelInfo);
      setMaxWait(modelInfo.max_delay_seconds);
      setWallet(burner);
      setCurrentBlock(blockNumber);
    }
    load().catch((err) => setError(String(err)));
    return () => {
      mounted = false;
    };
  }, []);

  useEffect(() => {
    const subscription = AppState.addEventListener("change", (nextState) => {
      if (nextState !== "active" && stateRef.current === "scheduled") {
        cancelScheduledRunRef.current = true;
        setRunState("expired");
        setError("Prediction expired because the app left the foreground.");
      }
    });
    return () => subscription.remove();
  }, []);

  const canRun = useMemo(
    () =>
      model !== null &&
      wallet !== null &&
      isAddress(recipient.trim()) &&
      Number.isFinite(Number(amount)) &&
      Number(amount) > 0 &&
      (state === "idle" || state === "complete" || state === "failed" || state === "expired"),
    [amount, model, recipient, state, wallet],
  );

  async function run() {
    if (!model || !wallet) return;
    cancelScheduledRunRef.current = false;
    setError(null);
    setResult(null);
    const nextTransfer = {
      recipient: recipient.trim(),
      amount: amount.trim(),
    };
    setSubmittedTransfer(nextTransfer);
    setRunState("predicting");
    try {
      const nextPrediction = await requestPrediction(Math.round(maxWait));
      setPrediction(nextPrediction);
      setRunState("scheduled");
      await waitForBroadcastBlock(nextPrediction, {
        isCancelled: () => cancelScheduledRunRef.current,
        onBlock: setCurrentBlock,
        onExpired: () => {
          cancelScheduledRunRef.current = true;
          setRunState("expired");
          setError("Prediction expired before broadcast.");
        },
      });
      if (cancelScheduledRunRef.current) return;
      setRunState("broadcasting");
      const txHash = await sendNativeTransfer(wallet.privateKey, nextTransfer.recipient, nextTransfer.amount);
      setRunState("confirming");
      await waitForReceipt(txHash);
      const observed = await observeTransaction(nextPrediction.request_id, txHash);
      setResult(observed);
      setRunState("complete");
      setDetailsVisible(true);
    } catch (err) {
      const expired = cancelScheduledRunRef.current || stateRef.current === "expired";
      if (!expired) {
        setError(String(err));
      }
      setRunState(expired ? "expired" : "failed");
    }
  }

  return (
    <ScrollView contentContainerStyle={styles.page}>
      <Text style={styles.title}>SPICE Demo</Text>

      <View style={styles.panel}>
        <Text style={styles.label}>Runtime</Text>
        <View style={styles.grid}>
          <Metric label="Chain" value={model ? chainLabel(model.chain_name) : ACTIVE_CHAIN.label} />
          <Metric label="Model" value={model ? modelLabel(model.model_family) : "loading"} />
          <Metric
            label="Artifact"
            value={model ? shortHash(model.artifact_id, 10, 4) : "loading"}
          />
          <Metric label="Block" value={currentBlock?.toString() ?? "loading"} />
        </View>
      </View>

      <View style={styles.panel}>
        <View style={styles.headerRow}>
          <Text style={styles.label}>Transaction</Text>
          <Text style={styles.valueStrong}>{Math.round(maxWait)}s</Text>
        </View>
        <TextInput
          autoCapitalize="none"
          autoCorrect={false}
          keyboardType="default"
          onChangeText={setRecipient}
          placeholder="Recipient address"
          style={styles.input}
          value={recipient}
        />
        <View style={styles.amountRow}>
          <TextInput
            keyboardType="decimal-pad"
            onChangeText={setAmount}
            placeholder="Amount"
            style={[styles.input, styles.amountInput]}
            value={amount}
          />
          <Text style={styles.unit}>{ACTIVE_CHAIN.nativeSymbol}</Text>
        </View>
        <Text style={styles.muted}>Max wait before broadcast</Text>
        <Slider
          minimumValue={0}
          maximumValue={model?.max_delay_seconds ?? 0}
          step={1}
          value={maxWait}
          onValueChange={setMaxWait}
        />
        <Button label="Submit Timed Transfer" disabled={!canRun} onPress={run} />
      </View>

      <View style={styles.panel}>
        <View style={styles.headerRow}>
          <Text style={styles.label}>Run</Text>
          <Text style={styles.state}>{state}</Text>
        </View>
        {prediction ? (
          <View style={styles.timeline}>
            <Metric label="Observed" value={String(prediction.observed_block)} />
            <Metric label="Broadcast" value={String(prediction.broadcast_after_block)} />
            <Metric label="Target" value={String(prediction.target_block)} />
            <Metric label="Wait" value={`${prediction.recommended_wait_seconds}s`} />
          </View>
        ) : (
          <Text style={styles.muted}>No run yet</Text>
        )}
        {result && (
          <View style={styles.resultBar}>
            <Text style={styles.resultText}>Saved {formatGwei(result.savings_wei)} Gwei</Text>
            <Text style={styles.resultText}>{result.savings_percent.toFixed(2)}%</Text>
            <Pressable onPress={() => setDetailsVisible(true)}>
              <Text style={styles.link}>Details</Text>
            </Pressable>
          </View>
        )}
        {error && <Text style={styles.error}>{error}</Text>}
      </View>

      <RunDetails
        visible={detailsVisible}
        prediction={prediction}
        result={result}
        transfer={submittedTransfer}
        onClose={() => setDetailsVisible(false)}
      />
    </ScrollView>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.metric}>
      <Text style={styles.metricLabel}>{label}</Text>
      <Text style={styles.metricValue}>{value}</Text>
    </View>
  );
}

function Button({
  label,
  disabled,
  onPress,
}: {
  label: string;
  disabled?: boolean;
  onPress: () => void;
}) {
  return (
    <Pressable
      style={[styles.button, disabled && styles.buttonDisabled]}
      disabled={disabled}
      onPress={onPress}
    >
      <Text style={styles.buttonText}>{label}</Text>
    </Pressable>
  );
}

function RunDetails({
  visible,
  prediction,
  result,
  transfer,
  onClose,
}: {
  visible: boolean;
  prediction: Prediction | null;
  result: ObserveResult | null;
  transfer: SubmittedTransfer | null;
  onClose: () => void;
}) {
  return (
    <Modal animationType="slide" transparent visible={visible} onRequestClose={onClose}>
      <View style={styles.modalBackdrop}>
        <View style={styles.modal}>
          <View style={styles.headerRow}>
            <Text style={styles.label}>Run Details</Text>
            <Pressable onPress={onClose}>
              <Text style={styles.link}>Close</Text>
            </Pressable>
          </View>
          {prediction && (
            <>
              <Detail label="Observed" value={String(prediction.observed_block)} />
              <Detail label="Baseline" value={String(prediction.baseline_block)} />
              <Detail label="Broadcast after" value={String(prediction.broadcast_after_block)} />
              <Detail label="Target" value={String(prediction.target_block)} />
            </>
          )}
          {result && (
            <>
              <Detail label="Included" value={String(result.included_block)} />
              <Detail label="Gas used" value={result.gas_used} />
              {transfer && (
                <>
                  <Detail label="Recipient" value={transfer.recipient} />
                  <Detail label="Amount" value={`${transfer.amount} ${ACTIVE_CHAIN.nativeSymbol}`} />
                </>
              )}
              <Detail label="Baseline fee" value={`${formatGwei(result.baseline_fee_wei)} Gwei`} />
              <Detail label="Model fee" value={`${formatGwei(result.model_fee_wei)} Gwei`} />
              <Detail label="Saved" value={`${formatGwei(result.savings_wei)} Gwei`} />
              <Pressable
                onPress={() => Linking.openURL(`${ACTIVE_CHAIN.explorerTxUrl}${result.tx_hash}`)}
              >
                <Text style={styles.link}>{shortHash(result.tx_hash, 12, 8)}</Text>
              </Pressable>
            </>
          )}
        </View>
      </View>
    </Modal>
  );
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.detailRow}>
      <Text style={styles.detailLabel}>{label}</Text>
      <Text selectable style={styles.detailValue}>
        {value}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  page: { padding: 20, gap: 14 },
  title: { fontSize: 26, fontWeight: "700" },
  panel: {
    backgroundColor: "#fff",
    borderColor: "#d0d7de",
    borderRadius: 8,
    borderWidth: 1,
    gap: 10,
    padding: 14,
  },
  label: { fontSize: 16, fontWeight: "700" },
  headerRow: { alignItems: "center", flexDirection: "row", justifyContent: "space-between" },
  grid: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  metric: { minWidth: "47%", gap: 2 },
  metricLabel: { color: "#57606a", fontSize: 12 },
  metricValue: { fontSize: 14, fontWeight: "700" },
  valueStrong: { fontSize: 16, fontWeight: "700" },
  input: {
    borderColor: "#d0d7de",
    borderRadius: 6,
    borderWidth: 1,
    fontSize: 15,
    paddingHorizontal: 10,
    paddingVertical: 9,
  },
  amountRow: { alignItems: "center", flexDirection: "row", gap: 8 },
  amountInput: { flex: 1 },
  unit: { fontWeight: "700" },
  timeline: { flexDirection: "row", flexWrap: "wrap", gap: 10 },
  state: { color: "#1f6feb", fontWeight: "700" },
  muted: { color: "#57606a" },
  resultBar: {
    alignItems: "center",
    backgroundColor: "#f6f8fa",
    borderRadius: 6,
    flexDirection: "row",
    gap: 10,
    justifyContent: "space-between",
    padding: 10,
  },
  resultText: { fontWeight: "700" },
  button: {
    alignItems: "center",
    backgroundColor: "#1f6feb",
    borderRadius: 6,
    paddingHorizontal: 14,
    paddingVertical: 10,
  },
  buttonDisabled: { backgroundColor: "#8c959f" },
  buttonText: { color: "#fff", fontWeight: "700" },
  link: { color: "#1f6feb", fontWeight: "700" },
  error: { color: "#cf222e" },
  modalBackdrop: {
    backgroundColor: "rgba(0, 0, 0, 0.24)",
    flex: 1,
    justifyContent: "flex-end",
  },
  modal: {
    backgroundColor: "#fff",
    borderTopLeftRadius: 12,
    borderTopRightRadius: 12,
    gap: 12,
    padding: 20,
  },
  detailRow: { gap: 2 },
  detailLabel: { color: "#57606a", fontSize: 12 },
  detailValue: { fontSize: 14 },
});
