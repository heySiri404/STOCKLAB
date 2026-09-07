"""Research entry point for the overlapping strategy.

Use either:

    python -m research.research
    python research/research.py

Importing this module does not start a backtest automatically.
"""

import sys
from pathlib import Path

if __package__:
    from .overlapping_strategy import Overlapping_Strategy
else:
    # Support running this file directly from the project root.
    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(PROJECT_ROOT))
    from overlapping_strategy import Overlapping_Strategy


SYMBOLS = [
    "VIC", "VCB", "CTG", "HPG", "STB", "VNM", "FPT", "MSN", "SSI", "BVH",
    "HCM", "EIB", "GMD", "REE", "KBC", "VND", "KDH", "SBT", "HAG", "PVD",
    "ACB", "BID", "MBB", "TCB", "VPB", "VIB", "OCB", "SHB", "LPB", "TPB",
    "MSB", "HDB", "VIX", "VCI", "VDS", "CTS", "BSI", "ORS", "VCG", "HHV",
    "CII", "DIG", "DXG", "NLG", "PDR", "NVL", "CEO", "IJC", "KHG", "TCH",
    "HDC", "SZC", "IDC", "BCM", "SIP", "DGC", "DHG", "DPM", "DCM", "CSV",
    "NKG", "HSG", "TLH", "VGS", "VTP", "MWG", "PNJ", "DGW", "SAB", "BHN",
    "VHC", "ANV", "IDI", "FMC", "ASM", "HAX", "PLX", "GAS", "POW", "PPC",
    "NT2", "PHR", "DPR", "VRE", "VHM", "VJC", "HVN", "CTR", "BWE", "QNS"
]

START_DATE = "2023-07-01"
END_DATE = "2026-08-31"
TOTAL_CAPITAL = 100_000
K = 3


def main() -> None:
    strategy = Overlapping_Strategy(
        total_capital=TOTAL_CAPITAL,
        start_date=START_DATE,
        end_date=END_DATE,
        K=K,
    )

    result = strategy.run(
        symbols=SYMBOLS,
        start_date=START_DATE,
        end_date=END_DATE,
    )

    if result.empty:
        print("The strategy returned no results.")
    else:
        print("\nBacktest result:")
        print(result.to_string(index=False))


if __name__ == "__main__":
    main()
