# 5–8 Minute Demonstration Script

Target duration: 7 minutes.

## 0:00–0:40 — Problem and Users

Show the application title and state the problem:

> A restaurant needs one reliable data path from menu and table master data to orders, checkout, and refunds. Managers then need trustworthy operating metrics instead of manually combining spreadsheets.

Name the primary users: cashier/server, shift supervisor, restaurant manager, and data analyst.

## 0:40–1:20 — Architecture and Data Model

Show the architecture diagram and ER diagram.

Explain:

- MySQL is the system of record.
- FastAPI owns transaction and query behavior.
- The interface supports full-stack application requirements.
- Order items snapshot purchase prices to preserve historical revenue.
- Foreign keys, check constraints, and state rules maintain integrity.

## 1:20–3:30 — Complete Order Workflow

Perform one uninterrupted workflow:

1. Open Menu & Tables and identify an available table.
2. Create an order and optionally enter a customer phone.
3. Add two different menu items and change the quantity.
4. Show the current order total.
5. Select a payment method and check out.
6. Show that the table returns to `available`.
7. Open the recent-orders table and select the completed order.

Explain that checkout recalculates the order total from historical line prices and commits the payment, status history, and table release in one transaction.

## 3:30–4:30 — Query and Analytics

Open Analytics and explain the KPI definitions:

- Gross completed revenue.
- Completed orders.
- Average order value.
- Recorded refund amount.

Show menu sales and hourly demand. Mention that menu analysis uses historical `line_total`, not the current menu price.

Use one concrete observation, for example:

> In the seeded dataset, Seafood Pasta contributes the largest sales share, while demand concentrates in the 12:00 and 19:00 meal periods.

## 4:30–5:45 — Data Flow and Backend Operations

Switch to API documentation or terminal output.

Demonstrate:

- `POST /api/orders`
- `POST /api/orders/{id}/items`
- `POST /api/orders/{id}/checkout`
- `GET /api/analytics/summary`

Explain the table row lock that prevents two simultaneous orders from occupying the same table. Show the concurrency result: one request succeeds and the other receives HTTP 409.

## 5:45–6:35 — Evaluation and Indexing

Show the benchmark chart and evaluation table.

State the measured result:

> At 50,000 orders, analytical queries complete in approximately 22–456 milliseconds on the local test environment.

Explain the indexing decision:

- Required indexes support primary/foreign-key access.
- Two optional indexes were measured at 1,000, 10,000, and 50,000 orders.
- They did not improve queries consistently and increased some measured latency.
- The final design keeps them out rather than claiming an unproven optimization.

## 6:35–7:00 — Challenges and Conclusion

Conclude with three lessons:

- Reliable metrics require deliberate transactional data design.
- Indexing must be measured against representative workloads.
- Separating gross revenue, refunds, and net sales prevents misleading product analytics.

Finish with repository and report links.

## Recording Checklist

- Reset and seed the database before recording.
- Close unrelated tabs and mute notifications.
- Keep browser zoom at 100%.
- Confirm the recorded display is readable at 1080p.
- Keep the final recording between 5 and 8 minutes.
- Upload to a shared drive and verify the link in a private browser window.

