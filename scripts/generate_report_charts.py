import json
from pathlib import Path
from xml.sax.saxutils import escape

from sqlalchemy import text

from app.database import SessionLocal


PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "docs" / "charts"
COLORS = ["#dc7b3c", "#246b8e", "#1e827a", "#7b61a8", "#b44f62"]


def write_svg(filename: str, title: str, content: str, width: int = 900, height: int = 520) -> None:
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<rect width="{width}" height="{height}" fill="#ffffff"/>
<text x="32" y="44" font-family="Segoe UI, Arial" font-size="24" font-weight="700" fill="#17232f">{escape(title)}</text>
{content}
</svg>
"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / filename).write_text(svg, encoding="utf-8")


def horizontal_bars(title: str, filename: str, rows: list[tuple[str, float]]) -> None:
    width = 900
    height = 120 + len(rows) * 52
    maximum = max(value for _, value in rows) or 1
    content = []
    for index, (label, value) in enumerate(rows):
        y = 86 + index * 52
        bar_width = 520 * value / maximum
        content.append(f'<text x="32" y="{y + 18}" font-family="Segoe UI, Arial" font-size="14" fill="#17232f">{escape(label)}</text>')
        content.append(f'<rect x="270" y="{y}" width="{bar_width:.2f}" height="26" rx="6" fill="{COLORS[index % len(COLORS)]}"/>')
        content.append(f'<text x="{280 + bar_width:.2f}" y="{y + 18}" font-family="Segoe UI, Arial" font-size="13" fill="#667582">{value:.3f}</text>')
    write_svg(filename, title, "\n".join(content), width, height)


def vertical_bars(title: str, filename: str, rows: list[tuple[str, float]]) -> None:
    width = 900
    height = 520
    maximum = max(value for _, value in rows) or 1
    content = ['<line x1="70" y1="440" x2="850" y2="440" stroke="#dfe6e9"/>']
    for index, (label, value) in enumerate(rows):
        x = 95 + index * (720 / len(rows))
        bar_height = 330 * value / maximum
        y = 440 - bar_height
        content.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="54" height="{bar_height:.2f}" rx="7" fill="#dc7b3c"/>')
        content.append(f'<text x="{x + 27:.2f}" y="{y - 10:.2f}" text-anchor="middle" font-family="Segoe UI, Arial" font-size="12" fill="#667582">{value:.0f}</text>')
        content.append(f'<text x="{x + 27:.2f}" y="468" text-anchor="middle" font-family="Segoe UI, Arial" font-size="12" fill="#17232f">{escape(label)}</text>')
    write_svg(filename, title, "\n".join(content), width, height)


def scaling_chart(results: list[dict]) -> None:
    width = 900
    height = 820
    content = []
    sizes = [1_000, 10_000, 50_000]
    x_positions = [190, 465, 740]
    baseline = [item for item in results if item["index_mode"] == "without_optional_indexes"]
    query_names = sorted({item["query_name"] for item in baseline})
    for index, query_name in enumerate(query_names):
        values = {item["scale_size"]: item["median_ms"] for item in baseline if item["query_name"] == query_name}
        panel_top = 82 + index * 136
        panel_bottom = panel_top + 82
        maximum = max(values.values()) * 1.18
        content.append(f'<text x="32" y="{panel_top + 4}" font-family="Segoe UI, Arial" font-size="15" font-weight="700" fill="#17232f">{escape(query_name)}</text>')
        content.append(f'<line x1="145" y1="{panel_bottom}" x2="815" y2="{panel_bottom}" stroke="#dfe6e9"/>')
        points = []
        for x, size in zip(x_positions, sizes):
            y = panel_bottom - (values[size] / maximum) * 70
            points.append((x, y))
            content.append(f'<circle cx="{x}" cy="{y:.2f}" r="5" fill="{COLORS[index % len(COLORS)]}"/>')
            content.append(f'<text x="{x}" y="{y - 11:.2f}" text-anchor="middle" font-family="Segoe UI, Arial" font-size="11" fill="#667582">{values[size]:.1f}</text>')
        point_text = " ".join(f"{x:.2f},{y:.2f}" for x, y in points)
        content.append(f'<polyline points="{point_text}" fill="none" stroke="{COLORS[index % len(COLORS)]}" stroke-width="3"/>')
    for x, size in zip(x_positions, sizes):
        content.append(f'<text x="{x}" y="{height - 18}" text-anchor="middle" font-family="Segoe UI, Arial" font-size="12" fill="#667582">{size:,} orders</text>')
    write_svg("benchmark_scaling.svg", "Query latency scaling by data size (milliseconds)", "\n".join(content), width, height)


def database_charts() -> None:
    database = SessionLocal()
    try:
        hourly = database.execute(text("""
            SELECT HOUR(placed_at), COUNT(*)
            FROM orders
            WHERE status IN ('paid', 'partially_refunded', 'refunded')
            GROUP BY HOUR(placed_at)
            ORDER BY HOUR(placed_at)
        """)).all()
        menu = database.execute(text("""
            SELECT menu_items.name, SUM(order_items.line_total) AS sales
            FROM order_items
            JOIN menu_items ON menu_items.id = order_items.menu_item_id
            JOIN orders ON orders.id = order_items.order_id
            WHERE orders.status IN ('paid', 'partially_refunded', 'refunded')
            GROUP BY menu_items.name
            ORDER BY sales DESC
            LIMIT 10
        """)).all()
    finally:
        database.close()
    vertical_bars("Hourly order demand", "hourly_demand.svg", [(str(row[0]), float(row[1])) for row in hourly])
    horizontal_bars("Menu sales contribution (HKD)", "menu_sales.svg", [(row[0], float(row[1])) for row in menu])


def main() -> None:
    results = json.loads((PROJECT_ROOT / "docs" / "evaluation_results.json").read_text(encoding="utf-8"))
    scale_rows = [
        (item["query_name"], item["median_ms"])
        for item in results
        if item["scale_size"] == 50_000 and item["index_mode"] == "without_optional_indexes"
    ]
    horizontal_bars("Median query latency at 50,000 orders (ms)", "benchmark_50k.svg", scale_rows)
    scaling_chart(results)
    database_charts()
    print(f"Wrote charts to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
