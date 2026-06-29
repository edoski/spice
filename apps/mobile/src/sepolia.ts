import "react-native-get-random-values";
import { JsonRpcProvider, Wallet, formatEther, isAddress, parseEther } from "ethers";
import { ACTIVE_CHAIN } from "./config";

export const provider = new JsonRpcProvider(ACTIVE_CHAIN.rpcUrl, ACTIVE_CHAIN.chainId);

export async function currentBlockNumber(): Promise<number> {
  return provider.getBlockNumber();
}

export async function balanceNative(address: string): Promise<string> {
  return formatEther(await provider.getBalance(address));
}

export async function sendNativeTransfer(
  privateKey: string,
  recipientAddress: string,
  amountNative: string,
): Promise<string> {
  if (!isAddress(recipientAddress)) {
    throw new Error("Recipient address is invalid");
  }
  const wallet = new Wallet(privateKey, provider);
  const tx = await wallet.sendTransaction({
    to: recipientAddress,
    value: parseEther(amountNative),
  });
  return tx.hash as string;
}

export async function waitForReceipt(txHash: string): Promise<number> {
  const receipt = await provider.waitForTransaction(txHash, 1, 180_000);
  if (!receipt) {
    throw new Error("Timed out waiting for transaction receipt");
  }
  return receipt.blockNumber;
}
