# Restaurant Ordering and Management System with Operational Analytics

## 1. Group Information

Team member names and undergraduate majors will be inserted before submission.

## 2. Contribution Statement

The final report will record each member's design, implementation, testing, documentation, and presentation contributions. Supporting evidence will include source files, experiment outputs, and report sections.

## 3. Project Overview

Restaurants rely on transaction data for checkout and for operating decisions, but a system that only performs CRUD operations cannot answer questions such as which menu items contribute the most sales, when demand peaks, or how often customers return. This project implements a MySQL-centered full-stack application for menu management, table assignment, ordering, checkout, and refunds, then converts the resulting records into operational analytics.

Target users are cashiers, servers, shift supervisors, restaurant managers, and data analysts. The system solves a real-world data problem by maintaining reliable business state and meaningful analytical queries in one data model.

The application follows the restaurant workflows found in Floreant POS and uniCenta oPOS, uses the classicmodels sample database as order/order-item design inspiration, and applies Chen's entity-relationship approach to conceptual modeling.

## 4. Technical Design

The system uses a three-layer design:

- A browser interface for staff operations and analytics.
- A FastAPI application for validation, services, transactions, and analytical endpoints.
- MySQL 9 as the relational system of record.

Menu and table operations write master data. Opening an order reserves a table. Item additions write price snapshots. Checkout creates a payment, closes the order, and releases the table atomically. Refunds append financial events and update the payment/order state without deleting history. Analytical endpoints then aggregate the same transaction tables.

The project structure, dependencies, and setup procedure are documented in the repository README.

## 5. Database Design

The relational design reaches 3NF. Menu categories, menu items, dining tables, customers, staff, orders, order items, payments, refunds, and order status history are separate entities. Foreign keys maintain relationships; unique keys prevent duplicate order numbers, phone numbers, and table names; check constraints protect quantity, price, and amount values.

Historical correctness is a key design decision. `order_items.unit_price` and `order_items.line_total` preserve the price paid at transaction time, while `menu_items.price` remains editable current master data.

The database design document includes the ER diagram, normalization argument, state transitions, and transaction boundaries. The generated DDL is available in `sql/schema.sql`.

## 6. Implementation

The implementation includes category, menu-item, and table management; order creation; order-item updates; checkout; payment recording; full/partial refunds; and operational analytics. The web interface follows the same endpoints exposed in the OpenAPI documentation.

Automated tests cover the complete create/add/checkout/refund workflow, rejection of a second order for an occupied table, and rejection of empty-order checkout. A MySQL concurrency script verifies that two simultaneous attempts to open the same table create only one successful order.

## 7. Evaluation and Results

The synthetic data generator creates deterministic meal-hour demand, order quantities, customer repeat behavior, payments, and refunds. Queries were evaluated at 1,000, 10,000, and 50,000 orders. Each benchmark reports the median of seven executions after warm-up.

At 50,000 orders:

| Query | Median latency |
| --- | ---: |
| Daily sales | 37.853 ms |
| Menu performance | 455.747 ms |
| Hourly demand | 32.475 ms |
| Recent orders | 21.733 ms |
| Customer frequency | 45.774 ms |

Menu performance is the most expensive query because it aggregates all order-item quantities and historical sales before ranking items. Nevertheless, all five tested queries remain below half a second at the tested scale.

Two optional indexes were also evaluated. At 50,000 orders, daily sales and hourly demand improved by less than 2%, while menu performance, recent orders, and customer frequency became slower by 3.5–8.2%. The measured results do not justify the extra index maintenance cost, so those optional indexes were rejected. Required primary/foreign-key indexes remain.

The concurrency test produced one successful order and one HTTP 409 conflict from simultaneous requests. This demonstrates that row locking serializes table assignment and protects business state.

Charts and raw measurements are included in `docs/charts`, `docs/evaluation_results.csv`, and `docs/evaluation-summary.md`.

### 7.1 System Data Analysis

The restaurant analysis layer uses three MySQL views: `v_order_financials`, `v_order_item_sales`, and `v_customer_order_summary`. The deterministic dataset contains 1,000 completed orders. It produces HK$340,957 gross sales, HK$13,705 refunds, HK$327,252 net sales, and a 4.02% refund rate. The calculation `gross_sales - refund_amount = net_sales` passes exactly.

Product engineering classifies demand against net-sales contribution. Seafood Pasta is the highest net-sales item and falls in the `Stars` segment. The generated distribution produces all four segments: Stars, Plowhorses, Puzzles, and Dogs. This verifies that the menu-analysis workflow can turn order items into product decisions.

Hourly demand peaks in the simulated 19:00 period with 217 orders, representing 21.7% of completed orders. The identified-customer view contains 155 customers; 114 have multiple orders in the selected data, producing a 73.6% repeat-customer rate and a 74.2% repeat-order rate. These results verify metric computation but are not claims about real restaurant behavior.

### 7.2 Real Behavior Validation

The external validation uses UCI Online Retail II, containing 1,067,371 transaction lines and 53,628 orders from December 2009 to December 2011. The cleaned fact table preserves invoice-line grain and maps orders, products, customers, prices, timestamps, and returns to the restaurant analytical model.

The real dataset produces £20,972,968.12 gross sales, £1,685,717.57 refunds, £19,287,250.55 net sales, and an 8.04% refund rate. Product engineering identifies 5,304 products: 813 Stars, 396 Plowhorses, 348 Puzzles, and 3,747 Dogs. The highest net-sales product is `REGENCY CAKESTAND 3 TIER` at £327,813.65.

Hourly behavior peaks at 12:00 with 8,098 orders, or 15.1% of orders. Among 5,942 identified customers, 4,481 repeat, producing a 75.4% repeat-customer rate and an 86.8% repeat-order rate. Actual return records validate the refund methods more strongly than synthetic data.

### 7.3 Method Validation

| Method | Restaurant system | Real behavior | Result |
| --- | --- | --- | --- |
| Gross/refund/net sales | Identity check passed | £19.29m net sales | Transferable |
| Product engineering | 10 items, four segments | 5,304 products, four segments | Transferable |
| Hourly demand | 19:00 simulated peak | 12:00 real peak | Transferable |
| Repeat customer rate | 73.6% | 75.4% | Transferable |
| Repeat order rate | 74.2% | 86.8% | Transferable |
| Refund analysis | 4.02% refund rate | 8.04% refund rate | Transferable |

The analysis supports technical and methodological feasibility. It does not show that the restaurant would achieve the real dataset's outcomes. Real data comes from online retail, lacks product costs, and cannot validate table turnover or seating efficiency. Restaurant-specific operational analysis still requires table-session, preparation, staffing, and seat-capacity data.

## 8. Challenges and Lessons Learned

- Separating current menu prices from historical purchase prices prevents incorrect revenue calculations.
- Transaction boundaries must include payment, order state, status history, and table release together.
- Index creation cannot be treated as automatically beneficial; representative measurements are required.
- Metrics need explicit gross revenue, refund, and net-sales definitions to avoid misleading product analysis.
- Team development requires stable data contracts and one reproducible setup path.

## 9. References and Deliverable Links

- GitHub repository URL: to be inserted after repository creation.
- Video demonstration: to be inserted after recording.
- Chen, P. P.-S. (1976). The Entity-Relationship Model—Toward a Unified View of Data. ACM TODS.
- Floreant POS: https://floreant.org/
- uniCenta oPOS: https://unicenta.com/
- MySQL Sample Database: https://www.mysqltutorial.org/getting-started-with-mysql/mysql-sample-database/
- UCI Online Retail II: https://archive.ics.uci.edu/dataset/502/online+retail+ii
