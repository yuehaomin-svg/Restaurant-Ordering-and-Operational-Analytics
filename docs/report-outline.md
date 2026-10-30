# Written Report Outline

Use this outline to satisfy the 50% written-report component exactly.

## 1. Group Information

- Full names and undergraduate majors.
- Lecture group and team number.

## 2. Contribution Statement

- Member-by-member roles and concrete outputs.
- Shared responsibilities and integration work.
- Evidence such as pull requests, documents, SQL files, tests, or screenshots.

## 3. Project Overview

- Problem: restaurant staff need transaction-safe ordering and managers need trustworthy operating information.
- Target users: cashier/server, shift supervisor, restaurant manager, and data analyst.
- Goals: reliable transactions, meaningful queries, efficient data access, and actionable analysis.
- Scope: menu, table, order, checkout, refund, and operational analytics.
- References to Floreant POS, uniCenta oPOS, classicmodels, and the Chen ER paper.

## 4. Technical Design

- Full-stack architecture diagram.
- Technology choices and reasons.
- Data flow from UI to service, transaction, persistence, query, and dashboard.
- Error handling and state-transition behavior.

## 5. Database Design

- ER diagram.
- 3NF schema and table descriptions.
- Keys, constraints, relationships, and snapshot-price rule.
- Transaction boundaries and concurrency behavior.
- Indexing strategy.
- Four sample queries with business questions.

## 6. Implementation

- Menu and table management.
- Order item workflow.
- Atomic checkout and payment.
- Full/partial refund behavior.
- Analytical endpoints and dashboard.
- Testing strategy and test results.

## 7. Evaluation and Results

- Synthetic data generation and its distribution assumptions.
- Query correctness checks.
- Performance at 1,000, 10,000, and 50,000 orders.
- Before/after index comparison with query time and `EXPLAIN`.
- Usability demonstration through the complete staff workflow.
- At least three data-informed operating findings.

Recommended tables:

| Query | Data size | Time before index | Time after index | Index |
| --- | ---: | ---: | ---: | --- |

Recommended charts:

- Query execution time by data size.
- Menu sales contribution.
- Hourly demand.
- Revenue and refund trend.

## 8. Challenges and Lessons Learned

- Balancing normalized transaction data with analytical usability.
- Preserving historical prices.
- Preventing double checkout and inconsistent table state.
- Avoiding misleading metric definitions.
- Coordinating application, database, and report work in a team.

## 9. References and Deliverable Links

- Academic and product references with complete citations.
- GitHub repository URL.
- Accessible video URL.
- Appendix: API examples, SQL queries, or additional test output.

## Writing Rules

- Tie each design decision to a requirement, risk, or measured result.
- Do not claim performance improvements without captured benchmark data.
- Use code and schema screenshots only after the repository matches them.
- State limitations clearly instead of hiding them.
- Keep gross revenue, refund amount, and net sales conceptually separate.
