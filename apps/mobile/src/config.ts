export const BACKEND_URL =
  process.env.EXPO_PUBLIC_SPICE_BACKEND_URL ?? "http://127.0.0.1:8000";

const SEPOLIA_RPC_URL =
  process.env.EXPO_PUBLIC_SEPOLIA_RPC_URL ??
  "https://ethereum-sepolia-rpc.publicnode.com";

export type ChainKey = "sepolia";

export type ChainOption = {
  key: ChainKey;
  label: string;
  chainId: number;
  nativeSymbol: string;
  rpcUrl: string;
  explorerTxUrl: string;
};

export const CHAIN_OPTIONS: ChainOption[] = [
  {
    key: "sepolia",
    label: "Sepolia",
    chainId: 11155111,
    nativeSymbol: "ETH",
    rpcUrl: SEPOLIA_RPC_URL,
    explorerTxUrl: "https://sepolia.etherscan.io/tx/",
  },
];

export const ACTIVE_CHAIN = CHAIN_OPTIONS[0];

export function chainLabel(chainName: string): string {
  return CHAIN_OPTIONS.find((chain) => chain.key === chainName)?.label ?? chainName;
}

export function modelLabel(modelFamily: string): string {
  const acronyms = new Map([
    ["lstm", "LSTM"],
    ["mlp", "MLP"],
    ["cnn", "CNN"],
    ["rnn", "RNN"],
  ]);
  return modelFamily
    .split("_")
    .map((part) => acronyms.get(part.toLowerCase()) ?? part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}
