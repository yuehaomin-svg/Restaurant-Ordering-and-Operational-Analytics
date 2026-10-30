def create_catalog(client) -> tuple[int, int, int]:
    category = client.post("/api/categories", json={"name": "Mains"}).json()
    menu_item = client.post("/api/menu-items", json={
        "category_id": category["id"],
        "name": "Grilled Chicken",
        "price": 69.00,
        "is_available": True,
    }).json()
    dining_table = client.post("/api/tables", json={"name": "T-01", "capacity": 4, "status": "available"}).json()
    return category["id"], menu_item["id"], dining_table["id"]


def test_order_checkout_refund_flow(client) -> None:
    _, menu_item_id, table_id = create_catalog(client)
    order = client.post("/api/orders", json={"table_id": table_id, "customer_phone": "13800000001"}).json()
    order = client.post(f"/api/orders/{order['id']}/items", json={"menu_item_id": menu_item_id, "quantity": 2}).json()
    assert order["items"][0]["line_total"] == "138.00"

    checked_out = client.post(f"/api/orders/{order['id']}/checkout", json={"payment_method": "card"}).json()
    assert checked_out["status"] == "paid"
    assert checked_out["total_amount"] == "138.00"
    assert checked_out["payments"][0]["status"] == "completed"

    refunded = client.post(f"/api/orders/{order['id']}/refund", json={"amount": 38.00, "reason": "Item adjustment"}).json()
    assert refunded["status"] == "partially_refunded"
    assert refunded["payments"][0]["status"] == "partially_refunded"

    tables = client.get("/api/tables").json()
    assert tables[0]["status"] == "available"


def test_open_order_prevents_second_order_on_table(client) -> None:
    _, _, table_id = create_catalog(client)
    first_response = client.post("/api/orders", json={"table_id": table_id})
    second_response = client.post("/api/orders", json={"table_id": table_id})
    assert first_response.status_code == 201
    assert second_response.status_code == 409


def test_empty_order_cannot_checkout(client) -> None:
    _, _, table_id = create_catalog(client)
    order = client.post("/api/orders", json={"table_id": table_id}).json()
    response = client.post(f"/api/orders/{order['id']}/checkout", json={"payment_method": "cash"})
    assert response.status_code == 409
