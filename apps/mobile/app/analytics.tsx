import * as Linking from "expo-linking";
import { useEffect, useMemo, useState } from "react";
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";

import { fetchAnalytics } from "../src/api";
import { ACTIVE_CHAIN } from "../src/config";
import { formatGwei, formatOptionalGwei } from "../src/format";
import type { AnalyticsResponse } from "../src/types";

export default function AnalyticsScreen() {
  const [analytics, setAnalytics] = useState<AnalyticsResponse | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [updatedAt, setUpdatedAt] = useState<Date | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    if (refreshing) return;
    const startedAt = Date.now();
    setRefreshing(true);
    setError(null);
    try {
      setAnalytics(await fetchAnalytics());
      setUpdatedAt(new Date());
    } catch (err) {
      setError(String(err));
    } finally {
      const remainingMs = 350 - (Date.now() - startedAt);
      if (remainingMs > 0) {
        await delay(remainingMs);
      }
      setRefreshing(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  const observedRows = useMemo(
    () => analytics?.rows.filter((row) => row.tx_hash !== null) ?? [],
    [analytics],
  );

  return (
    <ScrollView contentContainerStyle={styles.page}>
      <View style={styles.header}>
        <Text style={styles.title}>Analytics</Text>
        <Pressable
          style={[styles.button, refreshing && styles.buttonDisabled]}
          disabled={refreshing}
          onPress={load}
        >
          {refreshing && <ActivityIndicator color="#fff" size="small" />}
          <Text style={styles.buttonText}>{refreshing ? "Refreshing" : "Refresh"}</Text>
        </Pressable>
      </View>

      {analytics && (
        <View style={styles.section}>
          <Text>Runs: {analytics.totals.run_count}</Text>
          <Text>Saved: {formatGwei(analytics.totals.savings_total_wei)} Gwei</Text>
          <Text>Avg savings: {analytics.totals.savings_percent.toFixed(2)}%</Text>
          <Text>
            Wins: {analytics.totals.win_count} / {analytics.totals.run_count}
          </Text>
          {updatedAt && <Text style={styles.updated}>Updated {formatClock(updatedAt)}</Text>}
        </View>
      )}

      <View style={styles.table}>
        <View style={[styles.row, styles.heading]}>
          <Text style={styles.cell}>Wait</Text>
          <Text style={styles.cell}>Base Gwei</Text>
          <Text style={styles.cell}>Model Gwei</Text>
          <Text style={styles.cell}>Saved Gwei</Text>
          <Text style={styles.cell}>Tx</Text>
        </View>
        {observedRows.map((row) => (
          <View key={row.request_id} style={styles.row}>
            <Text style={styles.cell}>{row.wait_seconds}s</Text>
            <Text style={styles.cell}>{formatOptionalGwei(row.baseline_fee_wei, 0)}</Text>
            <Text style={styles.cell}>{formatOptionalGwei(row.model_fee_wei, 0)}</Text>
            <Text style={styles.cell}>{formatOptionalGwei(row.savings_wei, 0)}</Text>
            <Pressable
              style={styles.cell}
              disabled={!row.tx_hash}
              onPress={() => row.tx_hash && Linking.openURL(`${ACTIVE_CHAIN.explorerTxUrl}${row.tx_hash}`)}
            >
              <Text style={styles.link}>{row.tx_hash ? "Open" : "-"}</Text>
            </Pressable>
          </View>
        ))}
      </View>
      {error && <Text style={styles.error}>{error}</Text>}
    </ScrollView>
  );
}

function formatClock(value: Date): string {
  return value.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

const styles = StyleSheet.create({
  page: { padding: 20, gap: 16 },
  header: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  title: { fontSize: 26, fontWeight: "700" },
  section: {
    borderWidth: 1,
    borderColor: "#d0d7de",
    borderRadius: 8,
    padding: 14,
    gap: 8,
    backgroundColor: "#fff",
  },
  button: {
    alignItems: "center",
    backgroundColor: "#1f6feb",
    borderRadius: 6,
    flexDirection: "row",
    gap: 8,
    minWidth: 104,
    justifyContent: "center",
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  buttonDisabled: { backgroundColor: "#8c959f" },
  buttonText: { color: "#fff", fontWeight: "700" },
  updated: { color: "#57606a", fontSize: 12 },
  table: { borderWidth: 1, borderColor: "#d0d7de", borderRadius: 8, overflow: "hidden" },
  row: { flexDirection: "row", borderBottomWidth: 1, borderBottomColor: "#d0d7de" },
  heading: { backgroundColor: "#f6f8fa" },
  cell: { flex: 1, padding: 8, fontSize: 12 },
  link: { color: "#1f6feb", fontWeight: "700" },
  error: { color: "#cf222e" },
});
