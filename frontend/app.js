const state = {
  categories: [],
  menuItems: [],
  tables: [],
  orders: [],
  currentOrderId: null,
  analyticsFilters: { start_at: "", end_at: "" },
};

const currency = new Intl.NumberFormat("en-HK", {
  style: "currency",
  currency: "HKD",
});

function byId(id) {
  return document.getElementById(id);
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;",
  })[character]);
}

function showToast(message, isError = false) {
  const toast = byId("toast");
  toast.textContent = message;
  toast.style.background = isError ? "#a33d47" : "#183b56";
  toast.classList.add("show");
  window.setTimeout(() => toast.classList.remove("show"), 3000);
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `Request failed with status ${response.status}`);
  }
  return response.json();
}

function setOptions(select, values, placeholder) {
  select.innerHTML = values.length
    ? values.map((value) => `<option value="${value.id}">${escapeHtml(value.label)}</option>`).join("")
    : `<option value="">${escapeHtml(placeholder)}</option>`;
}

function currentOrder() {
  return state.orders.find((order) => order.id === state.currentOrderId);
}

function renderCurrentOrder() {
  const container = byId("current-order");
  const order = currentOrder();
  if (!order) {
    container.innerHTML = '<p class="empty-state">No active order selected.</p>';
    return;
  }
  const total = order.items.reduce((sum, item) => sum + Number(item.line_total), 0);
  const itemRows = order.items.map((item) => {
    const menuItem = state.menuItems.find((candidate) => candidate.id === item.menu_item_id);
    return `<li>${escapeHtml(menuItem?.name || `Item ${item.menu_item_id}`)} × ${item.quantity} — ${currency.format(item.line_total)}</li>`;
  }).join("");
  container.innerHTML = `
    <h4>${escapeHtml(order.order_no)}</h4>
    <p class="muted">Status: ${escapeHtml(order.status)} · Table ${escapeHtml(order.table_id)}</p>
    <ul>${itemRows || "<li>No items added yet.</li>"}</ul>
    <strong>Current total: ${currency.format(total)}</strong>
  `;
}

function renderOrders() {
  const body = byId("orders-body");
  byId("order-count").textContent = `${state.orders.length} records`;
  body.innerHTML = state.orders.length ? state.orders.map((order) => {
    const itemCount = order.items.reduce((sum, item) => sum + item.quantity, 0);
    return `
      <tr data-order-id="${order.id}">
        <td><strong>${escapeHtml(order.order_no)}</strong></td>
        <td>${escapeHtml(order.table_id)}</td>
        <td><span class="status ${escapeHtml(order.status)}">${escapeHtml(order.status.replaceAll("_", " "))}</span></td>
        <td>${itemCount}</td>
        <td>${currency.format(order.total_amount)}</td>
        <td>${new Date(order.placed_at).toLocaleString()}</td>
      </tr>
    `;
  }).join("") : '<tr><td colspan="6" class="empty-state">No orders yet.</td></tr>';
}

function renderCatalog() {
  setOptions(byId("order-table"), state.tables.filter((table) => table.status === "available").map((table) => ({
    id: table.id,
    label: `${table.name} · ${table.capacity} seats`,
  })), "No available tables");
  setOptions(byId("order-menu-item"), state.menuItems.filter((item) => item.is_available).map((item) => ({
    id: item.id,
    label: `${item.name} · ${currency.format(item.price)}`,
  })), "No available menu items");
  setOptions(byId("menu-category"), state.categories.map((category) => ({
    id: category.id,
    label: category.name,
  })), "Create a category first");

  byId("categories-list").innerHTML = state.categories
    .map((category) => `<span class="tag">${escapeHtml(category.name)}</span>`).join("");
  byId("menu-items-body").innerHTML = state.menuItems.map((item) => {
    const category = state.categories.find((candidate) => candidate.id === item.category_id);
    return `
      <tr>
        <td><strong>${escapeHtml(item.name)}</strong></td>
        <td>${escapeHtml(category?.name || "Unknown")}</td>
        <td>${currency.format(item.price)}</td>
        <td>${item.is_available ? "Available" : "Unavailable"}</td>
      </tr>
    `;
  }).join("");
  byId("tables-grid").innerHTML = state.tables.map((table) => `
    <div class="table-card">
      <strong>${escapeHtml(table.name)}</strong>
      <small>${table.capacity} seats</small>
      <span class="status ${escapeHtml(table.status)}">${escapeHtml(table.status.replaceAll("_", " "))}</span>
    </div>
  `).join("");
  renderCurrentOrder();
}

function renderAnalytics(summary, menuEngineering, hourlyDemand, customerRepeat) {
  byId("kpi-gross-sales").textContent = currency.format(summary.gross_sales);
  byId("kpi-net-sales").textContent = currency.format(summary.net_sales);
  byId("kpi-orders").textContent = summary.order_count;
  byId("kpi-aov").textContent = currency.format(summary.average_order_value);
  byId("kpi-refunds").textContent = currency.format(summary.refund_total);
  byId("kpi-refund-rate").textContent = `${(Number(summary.refund_rate) * 100).toFixed(1)}%`;

  byId("menu-performance-body").innerHTML = menuEngineering.length ? menuEngineering.map((item) => `
    <tr>
      <td><strong>${escapeHtml(item.name)}</strong></td>
      <td>${escapeHtml(item.category_name || "Uncategorized")}</td>
      <td><span class="menu-segment ${escapeHtml(item.menu_segment.toLowerCase())}">${escapeHtml(item.menu_segment)}</span></td>
      <td>${item.quantity}</td>
      <td>${currency.format(item.net_sales)}</td>
      <td>${escapeHtml(item.recommendation)}</td>
    </tr>
  `).join("") : '<tr><td colspan="6" class="empty-state">Complete an order to populate analytics.</td></tr>';

  const maxOrders = Math.max(...hourlyDemand.map((item) => item.orders), 1);
  byId("hourly-chart").innerHTML = hourlyDemand.length ? hourlyDemand.map((item) => `
    <div class="bar-column" title="${item.orders} orders · ${currency.format(item.net_sales)} net sales">
      <div class="bar" style="height: ${Math.max(4, (item.orders / maxOrders) * 88)}%"></div>
      <span>${String(item.hour).padStart(2, "0")}</span>
    </div>
  `).join("") : '<p class="empty-state">No completed orders.</p>';

  byId("repeat-customer-rate").textContent = `${(Number(customerRepeat.repeat_customer_rate) * 100).toFixed(1)}%`;
  byId("repeat-order-rate").textContent = `${(Number(customerRepeat.repeat_order_rate) * 100).toFixed(1)}%`;
  byId("repeat-average-orders").textContent = customerRepeat.average_orders_per_customer;
  byId("repeat-net-sales").textContent = currency.format(customerRepeat.repeat_customer_net_sales);
  const maximumCustomers = Math.max(...customerRepeat.frequency_distribution.map((item) => item.customer_count), 1);
  byId("repeat-distribution").innerHTML = customerRepeat.frequency_distribution.map((item) => `
    <div class="frequency-row">
      <span>${escapeHtml(item.frequency_band)}</span>
      <div class="frequency-track"><div class="frequency-fill" style="width: ${(item.customer_count / maximumCustomers) * 100}%"></div></div>
      <strong>${item.customer_count}</strong>
    </div>
  `).join("");
}

async function loadCatalog() {
  const [categories, menuItems, tables] = await Promise.all([
    api("/api/categories"),
    api("/api/menu-items"),
    api("/api/tables"),
  ]);
  state.categories = categories;
  state.menuItems = menuItems;
  state.tables = tables;
  renderCatalog();
}

async function loadOrders(selectNewest = false) {
  state.orders = await api("/api/orders");
  if (selectNewest && state.orders.length) {
    state.currentOrderId = state.orders[0].id;
  }
  renderOrders();
  renderCurrentOrder();
}

async function loadAnalytics() {
  const parameters = new URLSearchParams();
  if (state.analyticsFilters.start_at) parameters.set("start_at", state.analyticsFilters.start_at);
  if (state.analyticsFilters.end_at) parameters.set("end_at", state.analyticsFilters.end_at);
  const query = parameters.toString() ? `?${parameters.toString()}` : "";
  const [summary, menuEngineering, hourlyDemand, customerRepeat] = await Promise.all([
    api(`/api/analytics/summary${query}`),
    api(`/api/analytics/menu-engineering${query}`),
    api(`/api/analytics/hourly-demand${query}`),
    api(`/api/analytics/customer-repeat${query}`),
  ]);
  renderAnalytics(summary, menuEngineering, hourlyDemand, customerRepeat);
}

async function runAction(action, successMessage, reload = true) {
  try {
    await action();
    if (reload) {
      await Promise.all([loadCatalog(), loadOrders()]);
    }
    showToast(successMessage);
  } catch (error) {
    showToast(error.message, true);
  }
}

function activateView(viewName, updateUrl = true) {
  const targetButton = document.querySelector(`.tab[data-view="${viewName}"]`);
  if (!targetButton) return;
  document.querySelectorAll(".tab").forEach((candidate) => candidate.classList.remove("active"));
  document.querySelectorAll(".view").forEach((candidate) => candidate.classList.remove("active"));
  targetButton.classList.add("active");
  byId(viewName).classList.add("active");
  if (updateUrl) history.replaceState(null, "", `#${viewName}`);
  if (viewName === "analytics") loadAnalytics().catch((error) => showToast(error.message, true));
}

document.querySelectorAll(".tab").forEach((button) => {
  button.addEventListener("click", () => activateView(button.dataset.view));
});

byId("create-order").addEventListener("click", () => runAction(async () => {
  const tableId = Number(byId("order-table").value);
  if (!tableId) throw new Error("Select an available table first.");
  const phone = byId("customer-phone").value.trim();
  const order = await api("/api/orders", {
    method: "POST",
    body: JSON.stringify({ table_id: tableId, customer_phone: phone || null }),
  });
  state.currentOrderId = order.id;
}, "Order created."));

byId("add-order-item").addEventListener("click", () => runAction(async () => {
  const order = currentOrder();
  const menuItemId = Number(byId("order-menu-item").value);
  const quantity = Number(byId("order-quantity").value);
  if (!order) throw new Error("Create or select an open order first.");
  if (!menuItemId) throw new Error("Select an available menu item.");
  await api(`/api/orders/${order.id}/items`, {
    method: "POST",
    body: JSON.stringify({ menu_item_id: menuItemId, quantity }),
  });
}, "Item added to the order."));

byId("checkout-order").addEventListener("click", () => runAction(async () => {
  const order = currentOrder();
  if (!order) throw new Error("Create or select an open order first.");
  await api(`/api/orders/${order.id}/checkout`, {
    method: "POST",
    body: JSON.stringify({ payment_method: byId("payment-method").value }),
  });
  await loadAnalytics().catch(() => undefined);
}, "Order checked out."));

byId("create-category").addEventListener("click", () => runAction(async () => {
  const name = byId("category-name").value.trim();
  if (!name) throw new Error("Enter a category name.");
  await api("/api/categories", { method: "POST", body: JSON.stringify({ name }) });
  byId("category-name").value = "";
}, "Category created."));

byId("create-menu-item").addEventListener("click", () => runAction(async () => {
  const categoryId = Number(byId("menu-category").value);
  const name = byId("menu-item-name").value.trim();
  const price = Number(byId("menu-item-price").value);
  if (!categoryId || !name || !Number.isFinite(price)) throw new Error("Complete all menu item fields.");
  await api("/api/menu-items", {
    method: "POST",
    body: JSON.stringify({ category_id: categoryId, name, price, is_available: true }),
  });
  byId("menu-item-name").value = "";
  byId("menu-item-price").value = "";
}, "Menu item created."));

byId("create-table").addEventListener("click", () => runAction(async () => {
  const name = byId("table-name").value.trim();
  const capacity = Number(byId("table-capacity").value);
  if (!name || !Number.isFinite(capacity)) throw new Error("Complete all table fields.");
  await api("/api/tables", {
    method: "POST",
    body: JSON.stringify({ name, capacity, status: "available" }),
  });
  byId("table-name").value = "";
}, "Dining table created."));

byId("orders-body").addEventListener("click", (event) => {
  const row = event.target.closest("tr[data-order-id]");
  if (!row) return;
  state.currentOrderId = Number(row.dataset.orderId);
  renderCurrentOrder();
});

byId("refresh-orders").addEventListener("click", () => runAction(() => loadOrders(), "Orders refreshed.", false));
byId("refresh-analytics").addEventListener("click", () => runAction(() => loadAnalytics(), "Analytics refreshed.", false));
byId("apply-analytics-filter").addEventListener("click", () => runAction(async () => {
  const startAt = byId("analytics-start").value;
  const endAt = byId("analytics-end").value;
  if (startAt && endAt && startAt > endAt) throw new Error("The start date must be before the end date.");
  state.analyticsFilters = { start_at: startAt, end_at: endAt };
  await loadAnalytics();
}, "Date filter applied.", false));

async function initialize() {
  try {
    await Promise.all([loadCatalog(), loadOrders(), loadAnalytics()]);
    const requestedView = window.location.hash.replace("#", "");
    if (requestedView) activateView(requestedView, false);
  } catch (error) {
    showToast(error.message, true);
  }
}

initialize();
