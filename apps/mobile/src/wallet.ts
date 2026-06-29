import "react-native-get-random-values";
import * as SecureStore from "expo-secure-store";
import { Wallet } from "ethers";

const PRIVATE_KEY_KEY = "spice.sepolia.privateKey";

export type BurnerWallet = {
  address: string;
  privateKey: string;
};

export async function loadOrCreateBurnerWallet(): Promise<BurnerWallet> {
  let privateKey = await SecureStore.getItemAsync(PRIVATE_KEY_KEY);
  if (!privateKey) {
    privateKey = Wallet.createRandom().privateKey;
    await SecureStore.setItemAsync(PRIVATE_KEY_KEY, privateKey);
  }
  const wallet = new Wallet(privateKey);
  return { address: wallet.address, privateKey };
}
