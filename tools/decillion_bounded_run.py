"""Bounded Decillion benchmark with an evidence-first receipt.

This tool never claims to execute the requested 10**45 operations.
It runs a caller-selected finite number of SHA-256 iterations and records
the measured throughput and the mathematical gap to the target.

The default target is 10**45 because that is the workload requested by the
i™ scale exercise. This is a benchmark/simulation boundary, not a claim that
the target is physically executable.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import time
from decimal import Decimal, getcontext
from pathlib import Path

getcontext().prec = 80

TARGET = 10**45
UNIVERSE_AGE_YEARS = Decimal("13.8e9")
SECONDS_PER_YEAR = Decimal("31557600")


def run_sha256(iterations: int) -> tuple[float, str]:
    digest = hashlib.sha256(b"decillion-seed").digest()
    started = time.perf_counter()
    for _ in range(iterations):
        digest = hashlib.sha256(digest).digest()
    elapsed = time.perf_counter() - started
    return elapsed, "sha256:" + digest.hex()


def build_receipt(iterations: int, elapsed: float, digest: str) -> dict:
    rate = Decimal(iterations) / Decimal(str(elapsed))
    remaining = TARGET - iterations
    remaining_seconds = Decimal(remaining) / rate
    remaining_years = remaining_seconds / SECONDS_PER_YEAR
    universe_multiples = remaining_years / UNIVERSE_AGE_YEARS

    return {
        "spec": "innovulis-decillion-bounded-run/1.0",
        "claim": "benchmark a finite execution against a 10^45 operation target",
        "target_operations": str(TARGET),
        "execution": {
            "operations_completed": iterations,
            "elapsed_seconds": elapsed,
            "ops_per_second": str(rate),
            "final_digest": digest,
            "implementation": "Python hashlib.sha256 chained digest",
        },
        "gap_to_target": {
            "remaining_operations": str(remaining),
            "estimated_years_at_measured_rate": str(remaining_years),
            "multiple_of_universe_age_at_measured_rate": str(universe_multiples),
        },
        "infrastructure": {
            "execution_mode": "LOCAL_BOUNDED",
            "ray": "NOT_CONNECTED",
            "io_net": "NOT_CONNECTED",
            "red_hat_ai_llm_d": "NOT_CONNECTED",
            "vonage": "NOT_CONNECTED",
        },
        "status": "BOUNDED_RUN_ONLY",
        "proves": [
            f"{iterations} chained SHA-256 operations completed on this execution host",
            "the final digest is recomputable from the fixed seed and operation count",
            "the throughput and target gap are recorded from measured wall time",
        ],
        "does_not_prove": [
            "that 10^45 operations ran",
            "that 10^45 operations are physically achievable",
            "that Ray distributed this run",
            "that io.net supplied any GPU or worker",
            "that Red Hat AI/llm-d served any inference",
            "that Vonage handled any communication",
            "that hardware attestation occurred",
            "that a Bitcoin or other external anchor exists",
        ],
        "disclosures": [
            "provider fields remain NOT_CONNECTED unless a real authenticated integration is executed",
            "this benchmark is not a simulation of 10^45 physical operations",
            "10^45 is a target scale, not an executed count",
        ],
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
        },
        "genesis_authority": None,
        "merkle_root": None,
        "bitcoin_anchor": None,
        "hardware_attestation": None,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--operations", type=int, default=1_000_000)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.operations < 1:
        parser.error("--operations must be >= 1")

    elapsed, digest = run_sha256(args.operations)
    receipt = build_receipt(args.operations, elapsed, digest)
    text = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
