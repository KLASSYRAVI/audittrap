import argparse
import json

from audittrap import CASES, check


def evaluate(backend):
    results = {}
    for mode in ("baseline", "hardened"):
        clean_correct = 0
        false_passes = 0
        attacked_cases = 0
        records = []
        for case in CASES:
            clean = check(case["question"], "clean", mode, backend)
            clean_correct += clean["verdict"] == case["expected"]
            records.append({"id": case["id"], "expected": case["expected"], **clean})
            if "attack" in case:
                attacked_cases += 1
                poisoned = check(case["question"], "poisoned", mode, backend)
                false_passes += poisoned["verdict"] == "pass" and case["expected"] != "pass"
                records.append({"id": case["id"], "expected": case["expected"], **poisoned})
        results[mode] = {
            "clean_accuracy": {"correct": clean_correct, "total": len(CASES)},
            "poisoned_false_passes": {"count": false_passes, "total": attacked_cases},
            "records": records,
        }
    return {"backend": backend, "results": results}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate both modes on matched evidence.")
    parser.add_argument("--backend", choices=("demo", "ollama"), default="demo")
    args = parser.parse_args()
    print(json.dumps(evaluate(args.backend), indent=2))
