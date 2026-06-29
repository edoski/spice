const WEI_PER_GWEI = 1_000_000_000n;

export function formatGwei(valueWei: string, fractionDigits = 2): string {
  return formatWeiUnit(valueWei, WEI_PER_GWEI, fractionDigits);
}

export function formatOptionalGwei(valueWei: string | null, fractionDigits = 2): string {
  return valueWei === null ? "-" : formatGwei(valueWei, fractionDigits);
}

export function formatNativeBalance(value: string, symbol: string): string {
  return `${Number(value).toFixed(5)} ${symbol}`;
}

export function shortHash(value: string, head = 6, tail = 4): string {
  return `${value.slice(0, head)}...${value.slice(-tail)}`;
}

function formatWeiUnit(valueWei: string, unitWei: bigint, fractionDigits: number): string {
  const value = BigInt(valueWei);
  const negative = value < 0n;
  const absolute = negative ? -value : value;
  const whole = absolute / unitWei;
  const remainder = absolute % unitWei;
  const scale = 10n ** BigInt(fractionDigits);
  const roundedFraction = (remainder * scale + unitWei / 2n) / unitWei;
  const carry = roundedFraction >= scale ? 1n : 0n;
  const fraction = roundedFraction >= scale ? 0n : roundedFraction;
  const sign = negative ? "-" : "";
  if (fractionDigits === 0) {
    return `${sign}${whole + carry}`;
  }
  return `${sign}${whole + carry}.${fraction.toString().padStart(fractionDigits, "0")}`;
}
