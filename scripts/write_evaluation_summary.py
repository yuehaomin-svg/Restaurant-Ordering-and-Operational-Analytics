import json
from pathlib import Path


def main() -> None:
    project_root = Path(__file__).resolve().parent.parent
    results = json.loads((project_root / "docs" / "evaluation_results.json").read_text(encoding="utf-8"))
    concurrency = json.loads((project_root / "docs" / "concurrency_result.json").read_text(encoding="utf-8"))
    without = {
        item["query_name"]: item
        for item in results
        if item["scale_size"] == 50_000 and item["index_mode"] == "without_optional_indexes"
    }
    with_indexes = {
        item["query_name"]: item
        for item in results
        if item["scale_size"] == 50_000 and item["index_mode"] == "with_optional_indexes"
    }

    lines = [
        "# Evaluation Summary",
        "",
        "## Scale Test",
        "",
        "| Query | 1,000 orders | 10,000 orders | 50,000 orders | Result rows |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    query_names = list(without)
    for query_name in query_names:
        values = {
            item["scale_size"]: item
            for item in results
            if item["query_name"] == query_name and item["index_mode"] == "without_optional_indexes"
        }
        lines.append(
            f"| `{query_name}` | {values[1_000]['median_ms']:.3f} ms | "
            f"{values[10_000]['median_ms']:.3f} ms | {values[50_000]['median_ms']:.3f} ms | "
            f"{without[query_name]['result_rows']} |"
        )

    lines.extend([
        "",
        "Each value is the median of seven executions after one warm-up execution.",
        "",
        "## Optional Index Comparison at 50,000 Orders",
        "",
        "| Query | Without optional indexes | With optional indexes | Change | Decision |",
        "| --- | ---: | ---: | ---: | --- |",
    ])
    for query_name in query_names:
        baseline = without[query_name]["median_ms"]
        indexed = with_indexes[query_name]["median_ms"]
        change = ((indexed - baseline) / baseline) * 100
        decision = "Keep baseline" if change > -5 else "Consider optional index"
        lines.append(
            f"| `{query_name}` | {baseline:.3f} ms | {indexed:.3f} ms | {change:+.1f}% | {decision} |"
        )

    lines.extend([
        "",
        "The optional indexes did not produce a consistent improvement. Some measured queries became slower, so the evaluation rejects them instead of increasing write cost without a reliable read benefit. Required foreign-key indexes remain in the schema.",
        "",
        "## Concurrency Test",
        "",
        f"- Simultaneous order attempts: {concurrency['created_orders'] + concurrency['conflicting_requests']}",
        f"- Successful orders: {concurrency['created_orders']}",
        f"- Rejected conflicting requests: {concurrency['conflicting_requests']}",
        f"- Result: {'passed' if concurrency['passed'] else 'failed'}",
        "",
        "The table row lock serializes competing requests. Only the first transaction creates an order; the second receives HTTP 409 after the table becomes occupied.",
        "",
        "## Limitations",
        "",
        "- Measurements were run on a local Docker MySQL 9 instance and are not hardware-independent latency guarantees.",
        "- Synthetic data approximates meal-hour demand, order size, customer repeat behavior, and refunds.",
        "- The benchmark evaluates analytical reads; future work should also measure checkout throughput under sustained concurrent load.",
    ])
    output_path = project_root / "docs" / "evaluation-summary.md"
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
