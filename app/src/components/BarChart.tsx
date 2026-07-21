import { StyleSheet, Text, View } from "react-native";

import type { ChartDatum } from "../analytics";
import { colors, radii } from "../theme";

export function BarChart({ data }: { data: readonly ChartDatum[] }) {
  const maximum = Math.max(...data.map((item) => item.value), 0);
  if (data.length === 0 || maximum === 0) {
    return (
      <View style={styles.empty}>
        <Text style={styles.emptyTitle}>No runs yet</Text>
        <Text style={styles.emptyText}>Completed inferences will populate this graph.</Text>
      </View>
    );
  }

  return (
    <View style={styles.chart}>
      {data.map((item, index) => {
        const height = Math.max(8, (item.value / maximum) * 132);
        return (
          <View key={`${item.label}:${index}`} style={styles.column}>
            <Text numberOfLines={1} style={styles.value}>
              {item.displayValue}
            </Text>
            <View style={styles.track}>
              <View style={[styles.bar, { height }]} />
            </View>
            <Text numberOfLines={1} style={styles.label}>
              {item.label}
            </Text>
          </View>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  chart: { alignItems: "flex-end", flexDirection: "row", gap: 7, height: 184 },
  column: { alignItems: "center", flex: 1, gap: 5 },
  value: { color: colors.blue, fontSize: 11, fontWeight: "700", maxWidth: 50 },
  track: { height: 132, justifyContent: "flex-end", width: "64%" },
  bar: { backgroundColor: colors.blue, borderRadius: radii.small, minWidth: 12, width: "100%" },
  label: { color: colors.muted, fontSize: 10, maxWidth: 50 },
  empty: { alignItems: "center", height: 184, justifyContent: "center", padding: 24 },
  emptyTitle: { color: colors.ink, fontSize: 16, fontWeight: "700" },
  emptyText: { color: colors.muted, fontSize: 13, marginTop: 5, textAlign: "center" },
});
