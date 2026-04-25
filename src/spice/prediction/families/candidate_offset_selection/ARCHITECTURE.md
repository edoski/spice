# Candidate Offset Selection Architecture

## Purpose

This family models prediction as selecting one legal candidate offset.

## Theory

This is a classification problem. The model emits one logit per candidate slot. Invalid slots are masked before probability or argmax operations. The loss compares logits against the target offset.

## Invariants

Masking must guarantee at least one valid slot per sample. Decoding returns `DecodedOffsets`. The family owns classification metrics such as offset accuracy; evaluators own economic metrics.

## Extension Points

Extend this family for offset-classification variants that keep the same decoded output. Use a new family if decoded semantics change.

## Runtime Shape

```text
sample i
  candidates:  offset 0 | offset 1 | offset 2 | ...
  logits:        z0     |    z1    |    z2    | ...
  mask:        valid    |  valid   | invalid  | ...
  target: one integer offset
```

## Learning Interpretation

Cross entropy teaches the model to put probability mass on the target offset. During decoding, the highest valid logit becomes the chosen offset. Economic evaluation happens later after this offset is realized in a problem store.
