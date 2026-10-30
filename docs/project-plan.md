# One-Month Project Plan

## Objective

Deliver a complete Track 1 database application while making the project credible for data-analysis roles. Course grading remains the priority: source code 30%, video demonstration 20%, and written report 50%.

## Success Criteria

- A reviewer can start the system and complete an order without manual SQL.
- The schema supports menu, table, order, payment, and refund integrity.
- Checkout is atomic and protects table state.
- At least four analytical queries have business meanings and documented metric definitions.
- Tests prove the core transaction workflow and error handling.
- Query benchmarks compare data sizes and index choices.
- The report ties every major design to a course requirement or measurable result.
- The demo is 5–8 minutes and shows UI, query execution, data flow, and backend operations.

## Work Breakdown

### Week 1: Scope and Data Foundation

- Confirm real-world problem, users, and boundary.
- Finalize ER diagram and 3NF schema.
- Define status transitions and price-history rules.
- Build initialization and synthetic data scripts.
- Create the minimum menu, order, checkout, and analytics API contracts.

Exit condition: one order can be created, populated, checked out, and queried in MySQL.

### Week 2: Full-Stack Transaction Workflow

- Complete category, menu item, and table management.
- Complete order item updates and payment methods.
- Complete full and partial refunds.
- Add validation, conflict handling, and transaction rollback behavior.
- Build the staff-facing interface and automated transaction tests.

Exit condition: the complete UI workflow is demoable and tests pass.

### Week 3: Product Analytics and Evaluation

- Implement and validate the metric dictionary.
- Complete revenue, menu performance, refund, and hourly demand queries.
- Improve dashboard explanations and business interpretation.
- Generate 1,000, 10,000, and 50,000 order datasets.
- Benchmark queries with and without candidate indexes.
- Save `EXPLAIN` plans, timings, test output, and screenshots.

Exit condition: evaluation results can be copied directly into the report.

### Week 4: Report, Video, and Submission

- Write the report using `docs/report-outline.md`.
- Record contribution statements and verify every member can explain the system.
- Record the 5–8 minute video using `docs/demo-script.md`.
- Run the setup from a clean checkout and test every report link.
- Review originality, citations, naming, secrets, and repository history.

Exit condition: all three deliverables are complete and independently reviewable.

## Suggested Five-Person Ownership

### Member 1: Requirements and Report

- Problem statement, target users, scope, and related systems.
- Report integration and consistency.
- Contribution evidence and final submission links.

### Member 2: Database Design

- ER model, normalization, constraints, and schema evolution.
- Data dictionary and status-transition documentation.
- Database setup scripts and schema screenshots.

### Member 3: Backend and Transactions

- FastAPI services, order state machine, checkout, and refund behavior.
- Error responses, rollback tests, and concurrency behavior.
- Backend section of the video.

### Member 4: Frontend and Workflow

- Menu/table management and order-builder interface.
- Usability testing and screenshots.
- Live workflow section of the video.

### Member 5: Analytics and Evaluation

- Metric dictionary, analytical SQL, and dashboard.
- Synthetic scale tests, indexing strategy, and `EXPLAIN`.
- Results, insights, and evaluation section of the report.

The user's personal portfolio focus should be Member 5 plus database-design support from Member 2.

## Risk Register

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Full POS scope expands | Missing report and evaluation time | Freeze the workflow to menu, order, checkout, and refund |
| Team duplicates database queries | Inconsistent metric answers | Keep one metric dictionary and named analytical queries |
| ORM hides database reasoning | Weak report evidence | Document raw SQL, constraints, locks, indexes, and `EXPLAIN` |
| Synthetic data looks unrealistic | Low-quality analysis | Control meal hours, item mix, quantity, repeat customers, and refunds |
| AI feature distracts from Track 1 | Lower database depth | Keep AI outside the graded MVP |
| Late integration | Demo failures | Maintain one working vertical slice and merge tested increments |

## Definition of Done

- Setup works from a clean environment.
- Core tests pass.
- Database constraints and transactions are demonstrated.
- Analytical results use documented metric definitions.
- Report claims are backed by tests, screenshots, or benchmark output.
- The video stays within 5–8 minutes.
- All external code and resources are cited.
