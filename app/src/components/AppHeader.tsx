import { StyleSheet, Text, View } from "react-native";

import { colors } from "../theme";

export type ServiceStatus = "checking" | "live" | "offline";

const STATUS = {
  checking: { color: colors.amber, label: "CHECKING" },
  live: { color: colors.green, label: "LIVE" },
  offline: { color: colors.red, label: "OFFLINE" },
} as const;

export function AppHeader({ status }: { status: ServiceStatus }) {
  const presentation = STATUS[status];
  return (
    <View style={styles.header}>
      <Text style={styles.brand}>FABLE</Text>
      <View
        accessibilityLabel={`Inference service ${presentation.label.toLowerCase()}`}
        accessibilityRole="text"
        style={styles.status}
      >
        <View style={[styles.dot, { backgroundColor: presentation.color }]} />
        <Text style={styles.statusText}>{presentation.label}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  header: {
    alignItems: "center",
    backgroundColor: colors.navy,
    flexDirection: "row",
    justifyContent: "space-between",
    minHeight: 58,
    paddingHorizontal: 20,
  },
  brand: { color: colors.surface, fontSize: 21, fontWeight: "800", letterSpacing: 1.5 },
  status: { alignItems: "center", flexDirection: "row", gap: 8 },
  dot: { borderRadius: 6, height: 10, width: 10 },
  statusText: { color: colors.surface, fontSize: 13, fontWeight: "800", letterSpacing: 0.7 },
});
