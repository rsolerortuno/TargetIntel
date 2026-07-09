# Benchmark snapshot

This directory contains a versioned output snapshot of the TargetIntel-IO
internal therapeutic-intent benchmark.

The snapshot was generated from repository commit `200bba472b544bdca5f256b628484d82b8d38d99` using the curated
56-target benchmark in `configs/benchmark_targets.yaml`.

## Summary

| Metric | Result |
|---|---:|
| Benchmark targets | 56 |
| Benchmark targets evaluated | 56 |
| Missing benchmark targets | 0 |
| TargetIntel evaluation coverage | 100.0% |
| Open Targets retrieved benchmark targets | 25 |
| Open Targets top-300 retrieval coverage | 44.6% |
| Stable-role accuracy | 100.0% |
| Stable-role macro F1 | 100.0% |
| Strict primary-intent accuracy | 91.1% |
| Strict primary-intent macro F1 | 91.5% |
| Acceptable-intent accuracy | 100.0% |
| Cross-intent specificity | 90.6% |
| Control not-prioritized rate | 100.0% |
| Mean top-5 recall | 32.4% |
| Mean top-10 recall | 58.1% |
| Mean top-20 recall | 79.5% |

## Results by therapeutic intent

| Intent | Expected targets | Primary-intent accuracy | Acceptable-intent accuracy | Top-10 recall | Top-20 recall |
|---|---:|---:|---:|---:|---:|
| antibody_io | 19 | 94.7% | 100.0% | 52.6% | 84.2% |
| biomarker | 24 | 91.7% | 100.0% | 41.7% | 54.2% |
| small_molecule | 10 | 80.0% | 100.0% | 80.0% | 100.0% |
| none | 3 | 100.0% | 100.0% | N/A | N/A |

## Included files

| File | Description |
|---|---|
| `benchmark_predictions.csv` | Per-target expected and predicted roles, intents, scores, ranks, and correctness flags |
| `benchmark_summary.csv` | Benchmark-level metrics in tabular format |
| `benchmark_summary.json` | Machine-readable benchmark-level metrics |
| `intent_metrics.csv` | Metrics separated by therapeutic intent |
| `role_confusion_matrix.csv` | Stable-role classification confusion matrix |
| `snapshot_manifest.json` | Source commit, file hashes, and snapshot metadata |

## Interpretation

This benchmark is an internal, rule-based sanity validation. It tests whether
the framework behaves consistently across curated biological and translational
examples.

It is not an independent clinical gold standard and does not demonstrate
therapeutic efficacy, biomarker qualification, or prospective predictive
performance.

The augmented benchmark universe deliberately includes curated targets that
were not retrieved among the top 300 Open Targets melanoma associations. This
keeps two concepts separate:

- Open Targets retrieval coverage;
- TargetIntel-IO rule-evaluation coverage.

## Reproduce the snapshot

Build the augmented benchmark universe:

~~~bash
python scripts/09_build_benchmark_universe.py \
  --page-size 100 \
  --max-pages 3
~~~

Run the benchmark:

~~~bash
python scripts/08_run_benchmark.py \
  --input results/benchmark/ranked_targets_benchmark_universe.csv \
  --config configs/benchmark_targets.yaml \
  --outdir results/benchmark \
  --show-missing \
  --show-errors
~~~
