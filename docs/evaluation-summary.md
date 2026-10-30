# Evaluation Summary

## Scale Test

| Query | 1,000 orders | 10,000 orders | 50,000 orders | Result rows |
| --- | ---: | ---: | ---: | ---: |
| `daily_sales` | 2.042 ms | 9.931 ms | 37.853 ms | 30 |
| `menu_performance` | 10.861 ms | 91.790 ms | 455.747 ms | 10 |
| `hourly_demand` | 1.733 ms | 8.284 ms | 32.475 ms | 7 |
| `recent_orders` | 1.806 ms | 5.981 ms | 21.733 ms | 50 |
| `customer_frequency` | 3.357 ms | 10.990 ms | 45.774 ms | 30 |

Each value is the median of seven executions after one warm-up execution.

## Optional Index Comparison at 50,000 Orders

| Query | Without optional indexes | With optional indexes | Change | Decision |
| --- | ---: | ---: | ---: | --- |
| `daily_sales` | 37.853 ms | 37.673 ms | -0.5% | Keep baseline |
| `menu_performance` | 455.747 ms | 493.067 ms | +8.2% | Keep baseline |
| `hourly_demand` | 32.475 ms | 31.984 ms | -1.5% | Keep baseline |
| `recent_orders` | 21.733 ms | 22.503 ms | +3.5% | Keep baseline |
| `customer_frequency` | 45.774 ms | 47.488 ms | +3.7% | Keep baseline |

The optional indexes did not produce a consistent improvement. Some measured queries became slower, so the evaluation rejects them instead of increasing write cost without a reliable read benefit. Required foreign-key indexes remain in the schema.

## Concurrency Test

- Simultaneous order attempts: 2
- Successful orders: 1
- Rejected conflicting requests: 1
- Result: passed

The table row lock serializes competing requests. Only the first transaction creates an order; the second receives HTTP 409 after the table becomes occupied.

## Limitations

- Measurements were run on a local Docker MySQL 9 instance and are not hardware-independent latency guarantees.
- Synthetic data approximates meal-hour demand, order size, customer repeat behavior, and refunds.
- The benchmark evaluates analytical reads; future work should also measure checkout throughput under sustained concurrent load.
