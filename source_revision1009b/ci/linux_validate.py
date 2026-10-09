"""## Executive summary (read this first)
Verify exact container source, restricted Linux behavior and current official output gates.
Inputs are invented fixtures. No target file, accuracy metric or actual House call is used.
Failed runs keep logs and fail the workflow; publication follows only complete validation.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
import tomllib
import uuid

import numpy as np
import pandas as pd

FILES = {"forecast.parquet", "forecast_meta.json", "forecast_rationale.md"}
GATES = ["g0_integrity", "g1_schema", "g2_cutoff_resource", "g3_domain_semantics"]


def run(command, timeout=120, stdout=None):
    result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
    if stdout:
        Path(str(stdout) + ".stdout.log").write_text(result.stdout)
        Path(str(stdout) + ".stderr.log").write_text(result.stderr)
    if result.returncode:
        raise RuntimeError(f"command failed ({result.returncode}): {command[:3]}")
    return result.stdout


def digest_tree(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*")) if p.is_file()}


def official_gates(card, output, destination):
    from qfbench2_common.manifest import assert_public_safe, verify_manifest
    errors = verify_manifest(card.parent) + assert_public_safe(card.parent)
    safety = {"executive_summary": "Exact input manifest and public-safety checks precede all output gates.",
              "passed": not errors, "errors": errors}
    Path(str(destination) + ".public-safety.json").write_text(json.dumps(safety, indent=2) + "\n")
    if errors:
        raise ValueError("official fixture manifest or public-safety failed")
    result = subprocess.run([sys.executable, "-m", "qfbench2_track_forecasting.scoring", "score",
                             "--card", str(card), "--forecast", str(output / "forecast.parquet")],
                            capture_output=True, text=True, timeout=30)
    destination.write_text(result.stdout)
    Path(str(destination) + ".stderr.log").write_text(result.stderr)
    report = json.loads(result.stdout)
    if result.returncode or not report.get("admissible") or report.get("scored") is not False:
        raise ValueError("official gate-only refusal")
    if report.get("gates") != dict.fromkeys(GATES, "pass"):
        raise ValueError("not all four official gates ran")
    return report


def verify_files(unit, output):
    if {p.name for p in output.iterdir()} != FILES:
        raise ValueError("output must contain exactly three files")
    card = tomllib.loads((unit / "card.toml").read_text())
    meta = json.loads((output / "forecast_meta.json").read_text())
    frame = pd.read_parquet(output / "forecast.parquet")
    assets, horizons = card["targets"]["asset_ids"], card["targets"]["horizons"]
    if len(frame) != 1000 * len(assets) * len(horizons) or list(frame.columns) != ["draw", "asset", "horizon", "value"]:
        raise ValueError("output grid size or schema mismatch")
    if not np.isfinite(frame.value).all() or frame.duplicated(["draw", "asset", "horizon"]).any():
        raise ValueError("nonfinite or duplicate output")
    expected = {(a, h) for a in assets for h in horizons}
    if set(frame.draw) != set(range(1000)) or any(set(zip(g.asset, g.horizon)) != expected for _, g in frame.groupby("draw")):
        raise ValueError("incomplete joint draw")
    if meta["asset_ids"] != assets or meta["horizons"] != horizons or meta["n_draws"] != 1000:
        raise ValueError("metadata grid mismatch")
    rationale = (output / "forecast_rationale.md").read_text()
    if not rationale.startswith("## Executive summary (read this first)") or not rationale.strip():
        raise ValueError("rationale must have an English executive summary")
    return frame


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True)
    parser.add_argument("--variant", choices=["release", "house"], required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--fixtures", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("validation output must be fresh")
    args.output.mkdir(parents=True)
    result = {"executive_summary": "Linux structure and gates only; no predictive score or real House call.",
              "variant": args.variant, "status": "running", "containers": [], "official_gates": [],
              "toolkit_version": importlib.metadata.version("qfbench2-common"),
              "track_version": importlib.metadata.version("qfbench2-track-forecasting")}
    destination = args.output / "RESULTS.json"
    def save(): destination.write_text(json.dumps(result, indent=2) + "\n")
    save()
    try:
        if result["toolkit_version"] != "2.6.0" or result["track_version"] != "3.1.0":
            raise ValueError("wrong official package versions")
        inspection = json.loads(run(["docker", "image", "inspect", args.image], timeout=30))[0]
        (args.output / "IMAGE_INSPECT.json").write_text(json.dumps(inspection, indent=2) + "\n")
        config = inspection["Config"]
        if inspection["Os"] != "linux" or inspection["Architecture"] != "amd64" or config.get("Volumes"):
            raise ValueError("image platform or declared VOLUME invalid")
        if config.get("User") != "65534:65534" or config.get("WorkingDir") != "/app":
            raise ValueError("image user or working directory invalid")
        if config.get("Labels", {}).get("qfbench2.interface_version") != "2.0":
            raise ValueError("missing official interface label")
        if config.get("Entrypoint") != ["/usr/local/bin/python", "-B", "/app/forecast.py"]:
            raise ValueError("unexpected forecast entrypoint")
        environment = dict(x.split("=", 1) for x in config.get("Env", []))
        if args.variant == "house" and environment.get("T2_STRATEGY") != "house":
            raise ValueError("House image does not default to House strategy")
        if args.variant == "release" and environment.get("T2_STRATEGY", "release") != "release":
            raise ValueError("release image does not default to release strategy")
        expected_sources = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in args.source.glob("*.py")
                            if not p.name.startswith("test_") and p.name not in {"census_release_evidence.py"}}
        probe_code = (
            "import hashlib,json,os,pathlib; "
            "assert os.getuid()==65534 and os.getgid()==65534; "
            "print(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in pathlib.Path('/app').glob('*.py')}))")
        hashes = json.loads(run(["docker", "run", "--rm", "--network=none", "--read-only", "--user=65534:65534",
                                "--cap-drop=ALL", "--security-opt=no-new-privileges", "--cpus=2", "--memory=4g",
                                "--memory-swap=4g", "--pids-limit=256", "--ulimit=nofile=1024:1024",
                                "--entrypoint=/usr/local/bin/python", args.image, "-B", "-c", probe_code], stdout=args.output / "source-probe"))
        if any(hashes.get(name) != value for name, value in expected_sources.items()):
            raise ValueError("image source hash mismatch")
        result["image_source_hashes"] = hashes
        input_before = digest_tree(args.fixtures)
        outputs = {}
        for unit in sorted(p for p in args.fixtures.iterdir() if p.is_dir()):
            for attempt in (1, 2):
                output = args.output / f"{unit.name}-repeat{attempt}"
                output.mkdir(); output.chmod(0o777)
                name = "t2-check-" + uuid.uuid4().hex
                record = {"name": name, "unit": unit.name, "attempt": attempt, "status": "attempted"}
                result["containers"].append(record); save()
                card = tomllib.loads((unit / "card.toml").read_text())
                asof = card["provenance"]["data_cutoff"]
                command = ["docker", "run", "--name", name, "--network=none", "--read-only", "--user=65534:65534",
                           "--cap-drop=ALL", "--security-opt=no-new-privileges", "--cpus=2", "--memory=4g", "--memory-swap=4g",
                           "--pids-limit=256", "--ulimit=nofile=1024:1024", "--tmpfs=/tmp:rw,noexec,nosuid,size=64m",
                           "--mount", f"type=bind,src={unit.resolve()},dst=/input,readonly",
                           "--mount", f"type=bind,src={output.resolve()},dst=/output",
                           "--env=QFBENCH_NETWORK=none", "--env=QFBENCH_SEED=103", args.image,
                           "forecast", "--panels", "/input/panels", "--text", "/input/text", "--asof", asof,
                           "--out", "/output/forecast.parquet"]
                started = time.monotonic()
                try:
                    run(command, stdout=args.output / f"{unit.name}-repeat{attempt}")
                    state = json.loads(run(["docker", "inspect", name], timeout=30))[0]
                    (args.output / f"{name}.inspect.json").write_text(json.dumps(state, indent=2) + "\n")
                    host = state["HostConfig"]
                    if (state["State"]["Running"] or state["State"]["ExitCode"] or not host["ReadonlyRootfs"]
                            or host["NetworkMode"] != "none" or state["Config"]["User"] != "65534:65534"
                            or host["Memory"] != 4 * 1024**3 or host["MemorySwap"] != 4 * 1024**3
                            or host["NanoCpus"] != 2 * 10**9 or host["PidsLimit"] != 256
                            or host.get("CapDrop") != ["ALL"]
                            or "no-new-privileges" not in " ".join(host.get("SecurityOpt", []))):
                        raise ValueError("container sandbox or termination invalid")
                    mounts = {m["Destination"]: m for m in state["Mounts"]}
                    if mounts.get("/input", {}).get("RW") is not False or mounts.get("/output", {}).get("RW") is not True:
                        raise ValueError("input/output mount permissions invalid")
                    frame = verify_files(unit, output)
                    gate = official_gates(unit / "card.toml", output, args.output / f"{unit.name}-repeat{attempt}.gates.json")
                    result["official_gates"].append(gate)
                    record.update({"status": "passed", "rows": len(frame), "elapsed_seconds": time.monotonic() - started})
                finally:
                    run(["docker", "rm", "--force", name], timeout=30)
                    remaining = run(["docker", "container", "ls", "--all", "--quiet", "--filter", f"name=^/{name}$"], timeout=30)
                    if remaining.strip():
                        raise ValueError("owned container was not removed")
                    record["cleanup_proved"] = True; save()
                if attempt == 1:
                    outputs[unit.name] = output
                elif (outputs[unit.name] / "forecast.parquet").read_bytes() != (output / "forecast.parquet").read_bytes():
                    raise ValueError("repeated-seed Parquet bytes differ")
        if digest_tree(args.fixtures) != input_before:
            raise ValueError("input fixture bytes changed")
        # Current official gate stack must detect an extra output artifact. This
        # ensures gate-only execution is real rather than prefilled as passed.
        unit = next(p for p in args.fixtures.iterdir() if p.is_dir())
        invalid = args.output / "negative-extra-file"
        shutil.copytree(outputs[unit.name], invalid)
        (invalid / "extra.txt").write_text("invented forbidden output")
        refused = subprocess.run([sys.executable, "-m", "qfbench2_track_forecasting.scoring", "score",
                                  "--card", str(unit / "card.toml"), "--forecast", str(invalid / "forecast.parquet")],
                                 capture_output=True, text=True, timeout=30)
        (args.output / "negative-extra-file.gates.json").write_text(refused.stdout)
        if refused.returncode != 1 or json.loads(refused.stdout).get("admissible") is not False:
            raise ValueError("extra output file unexpectedly passed official gates")
        result.update({"status": "passed", "repeated_seed_equal": True, "fixture_hashes_unchanged": True,
                       "negative_extra_output_refused": True, "actual_House_calls": 0, "accuracy_scores": 0})
        save()
    except Exception as error:
        result.update({"status": "failed", "error_type": type(error).__name__, "reason": str(error)})
        save()
        raise


if __name__ == "__main__":
    main()
