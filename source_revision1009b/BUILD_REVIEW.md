## Executive summary (read this first)

The prepared `review_build_workflow.yml` imports a reviewed source release into `source_revision1009/`, preserves the original V2 runtime tree, builds numeric and House-default Linux/amd64 images, validates their exact bytes under the current official gate stack, and publishes separate immutable GHCR digests. It reruns both digests after anonymous pulls. It has not been submitted or executed by this author. Offline checks establish structure and numerical fallback, not forecast quality or actual House inference.

## Source release layout

Upload one small `source-revision-20261009.tar.gz` asset to the personal public repository's release named `source-revision-20261009`. It contains only the following independent tree:

```text
source_revision1009/
  Dockerfile
  Dockerfile.house
  METHOD_AUDIT.md
  HOUSE_METHOD.md
  source/
    forecast.py
    horizon_contract.py
    return_contract.py
    release_evidence.py
    bootstrap_forecast.py
    house_scenarios.py
    test_integration.py
    test_release_evidence.py
    test_bootstrap_forecast.py
    test_house_scenarios.py
  ci/
    linux_validate.py
    make_fixtures.py
  fixtures/
    FIXTURE_MANIFEST.json
    daily_return/
      card.toml
      forecast_spec.json
      panels/factors_daily.parquet
      text/corpus_index.json
      text/context.txt
    monthly_release/
      card.toml
      forecast_spec.json
      panels/macro_monthly.parquet
      text/corpus_index.json
      text/release.txt
  provenance/
    SOURCE_MANIFEST.json
```

The source manifest has `files: [{path, bytes, sha256}]`, with each path relative to `source_revision1009/`. Include every regular file except the manifest itself. Generate the two input-only fixtures once before freezing the archive using `ci/make_fixtures.py --output fixtures`. Their generated UUIDv4 canaries and input hashes are then frozen; the workflow does not regenerate them. Include no actual corpus, panel, reference, target outcome, golden output, cache or personal archive. Documentation and source freezes may be included if they contain no answer values and are declared in the manifest.

The workflow's fixed release URL and dispatched SHA256 pin the uploaded bytes. It refuses extra paths, traversal, symlinks, duplicate archive entries, members over 8 MiB and total compressed bytes over 20 MiB. It verifies the complete manifest roster before writing the independent directory. Existing different bytes at the same source path refuse rather than overwrite. Source commits are explicitly authored as GitHub Actions and contain only `source_revision1009/`. The original root `runtime/` remains untouched.

## Runtime and exact checks

Both Dockerfiles extend the retained public V2 Linux image at digest `a74cdd6d29b174144fd3e8a0a9aa3492d9d1228e4301d6ad74a835648e323092`. The image already has Python and numerical dependencies. The new builds install nothing, run with build network disabled, and copy only six runtime modules into `/app`. `Dockerfile.house` additionally defaults `T2_STRATEGY=house`; the numerical Dockerfile defaults to release assimilation. Both declare UID/GID 65534, `/app`, the actual Python forecast entrypoint, and `qfbench2.interface_version=2.0`.

Current official gates run on the Actions host using Python 3.13, `qfbench2-common` release `v2.6.0` and T2 revision `30c8019d997f930eab9ba569d089d12298d86d8c` (package 3.1.0). The workflow installs the common toolkit first through its official public URL and asserts final package versions. No scoring package or outcome is placed in the contestant image. Only the gate-only CLI is used; it must return all four published gates as passed and `scored:false`.

For each image the driver checks Linux/amd64, no declared VOLUME, exact interface label, user, working directory, entrypoint and default strategy. It hashes the six image runtime files and compares them with the imported source. Then each of two invented units runs twice using the same seed, for four actual forecast entrypoint invocations per image. Containers use network none, read-only root and input, nonroot user, dropped capabilities, no-new-privileges, two CPUs, four GiB memory with no extra swap, 256 PIDs, 1,024 file descriptors and a 64 MiB noexec/nosuid tmpfs.

The driver saves real container inspection and stdout/stderr, checks successful termination and owned-container cleanup, verifies the three-file output set, finite unique complete joint rows, metadata and English rationale summary, runs official public-safety and output gates, and verifies repeated-seed Parquet bytes. It hashes fixture inputs before and after. An added extra output file must fail the real official gates. House-default runs offline and must fall back to the numerical forecast; controlled House proxy tests run separately through pytest and are clearly synthetic.

## Publication and final evidence

Publication occurs only after both local images pass all checks. Tags are `revision1009-release-<source_commit>` and `revision1009-house-<source_commit>`. The push receipt establishes one GHCR digest per variant. The workflow logs out, uses an empty Docker configuration for anonymous pulls, removes local tags, pulls each digest, and repeats complete validation against the exact published reference. Anonymous pull fails if package visibility is private; it must not be silently accepted because authenticated push succeeded.

The `t2-revision1009-linux-<run_id>` artifact saves source import hash and commit, host dependency versions, image inspection, image source hashes, each actual gate receipt, outputs, run logs, publication digests and anonymous-pull logs. Artifact upload uses `always()` so partial failures remain inspectable. The job is bounded at 35 minutes. Actions references are full commits taken from the existing reviewed workflow conventions; the base image is an immutable digest. This source workflow uses only personal public GitHub/GHCR, not company or archived personal compute.

After checking the resulting artifact, the root task can pack separate descriptors with their corresponding immutable digest. The numeric image uses `models: []`. The House image must include the current five-field House disclosure: name `nvidia/nemotron-3-super-120b-a12b`, version and revision `rl-030326-fp8`, training cutoff `unpublished`, access `api`. Reseal descriptor digests with the common toolkit. Do not submit a block strategy image merely because its source and tests are packaged; that candidate still requires its own quality decision.

## Preparation status

`review_build_workflow.yml` parses as YAML and the two CI scripts parse as Python. Runtime files were not edited for this preparation. No Docker build, registry publication, GitHub commit, workflow dispatch, anonymous pull or official scoring was performed by this author. The first meaningful evidence comes from the actual dispatched run and its saved results.
