# Agenthon Track 2 forecasting

This repository contains the exact official V2 forecasting runtime and compact research evidence for Track 2. The other tracks use separate repositories. The source export preserves the existing experiment trees.

Run the frozen CLI with Python3.13 and the versions in requirements.txt:

```sh
python runtime/forecast.py forecast --panels /path/to/panels --text /path/to/text --asof YYYY-MM-DD --out /path/to/output/forecast.parquet --n-draws 1000 --seed 0
```

The supplied panels/text must include the current task card, exact target grid and timestamped corpus index. Monthly targets require explicit observation-period metadata. The runtime produces forecast.parquet, forecast_meta.json and forecast_rationale.md. It uses CPU numerical libraries; no runtime network/model client is included.

The official V2 image is ghcr.io/kouzhizhuo/agenthon-t2@sha256:a74cdd6d29b174144fd3e8a0a9aa3492d9d1228e4301d6ad74a835648e323092. Submission968315 was received on8October2026. The latest saved official receipt checked14:18Shanghai still reports Submitting, with no score/rank/logs; organizer dispatch and accuracy remain pending. This status is a saved snapshot, not a new live check.

V5’s historical mixture gate, V6’s DNS center, V7’s cell-specific drift correction and V8’s common Treasury location gate were rejected for promotion. V8 preserved raw variogram through one common scalar, but gained only0.62%on already consumed validation, below its frozen2%usefulness target, at12.78times v2’s mean all-domain model-call cost. Four admitted validation origins worsened. Its53controls,48path synthetic study and346origin development comparison remain documented in research/v8; the first failed bool-serialization attempt and repeated first synthetic pair are disclosed. These are local consumed-data evidence, not an official rank.

LICENSE and notices preserve the organizer’s MIT software license and upstream third-party/data rights. Third-party dependencies retain their own licenses. No panels, source text corpora, generated target rows, private credentials, team proof files, OCI blobs or archived personal material are included. Full experiment outputs and failed predecessors remain in their original workspace folders; historical manifests reference those source locations.

EXPORT_MANIFEST.json records every exported file/hash/size and its original path or generated provenance. Runtime source hashes match the submitted V2 manifest. Git initialization and any publication are handled separately.

The final V8 saved development audit reproduces the exact 346-origin / 2,076-row roster, means, intervals, family results, gate calls and timing without runtime imports or forecast reruns. Its rejection is final. The exported research receipt files are sufficient to read the decision; full raw experiment data and failed predecessors remain in the original workspace. This clean local export is ready for the owner’s existing public GitHub repository at https://github.com/kouzhizhuo/agenthon-t2; no Git initialization, network push or company GitHub access was performed while preparing it.
