import * as Clipboard from "expo-clipboard";
import { useEffect, useState } from "react";
import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";

import { ACTIVE_CHAIN, CHAIN_OPTIONS } from "../src/config";
import { formatNativeBalance } from "../src/format";
import { balanceNative, currentBlockNumber } from "../src/sepolia";
import { loadOrCreateBurnerWallet, type BurnerWallet } from "../src/wallet";

export default function WalletScreen() {
  const [wallet, setWallet] = useState<BurnerWallet | null>(null);
  const [balance, setBalance] = useState("0");
  const [currentBlock, setCurrentBlock] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setError(null);
    try {
      const burner = await loadOrCreateBurnerWallet();
      const [nextBalance, nextBlock] = await Promise.all([
        balanceNative(burner.address),
        currentBlockNumber(),
      ]);
      setWallet(burner);
      setBalance(nextBalance);
      setCurrentBlock(nextBlock);
    } catch (err) {
      setError(String(err));
    }
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <ScrollView contentContainerStyle={styles.page}>
      <View style={styles.header}>
        <Text style={styles.title}>Wallet</Text>
        <Pressable style={styles.button} onPress={load}>
          <Text style={styles.buttonText}>Refresh</Text>
        </Pressable>
      </View>

      <View style={styles.section}>
        <Text style={styles.label}>Chain</Text>
        <View style={styles.selector}>
          {CHAIN_OPTIONS.map((chain) => (
            <Pressable
              key={chain.key}
              style={[styles.option, chain.key === ACTIVE_CHAIN.key && styles.optionActive]}
            >
              <Text
                style={[
                  styles.optionText,
                  chain.key === ACTIVE_CHAIN.key && styles.optionTextActive,
                ]}
              >
                {chain.label}
              </Text>
            </Pressable>
          ))}
        </View>
      </View>

      <View style={styles.section}>
        <Text style={styles.label}>Account</Text>
        <Text selectable style={styles.address}>
          {wallet?.address ?? "loading"}
        </Text>
        <Text>{formatNativeBalance(balance, ACTIVE_CHAIN.nativeSymbol)}</Text>
        <Text>Block {currentBlock ?? "loading"}</Text>
        <Pressable
          style={[styles.button, !wallet && styles.buttonDisabled]}
          disabled={!wallet}
          onPress={() => wallet && Clipboard.setStringAsync(wallet.address)}
        >
          <Text style={styles.buttonText}>Copy Address</Text>
        </Pressable>
      </View>

      {error && <Text style={styles.error}>{error}</Text>}
    </ScrollView>
  );
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
    gap: 10,
    backgroundColor: "#fff",
  },
  label: { fontSize: 16, fontWeight: "700" },
  selector: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  option: {
    borderWidth: 1,
    borderColor: "#d0d7de",
    borderRadius: 6,
    paddingVertical: 8,
    paddingHorizontal: 12,
  },
  optionActive: { backgroundColor: "#1f6feb", borderColor: "#1f6feb" },
  optionText: { fontWeight: "700" },
  optionTextActive: { color: "#fff" },
  address: { fontSize: 13, lineHeight: 18 },
  button: {
    alignItems: "center",
    backgroundColor: "#1f6feb",
    borderRadius: 6,
    paddingHorizontal: 14,
    paddingVertical: 10,
  },
  buttonDisabled: { backgroundColor: "#8c959f" },
  buttonText: { color: "#fff", fontWeight: "700" },
  error: { color: "#cf222e" },
});
