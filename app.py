from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
import os

app = Flask(__name__)
DB_PATH = "store.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            description TEXT,
            stock INTEGER DEFAULT 0,
            image_url TEXT
        );

        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            customer_email TEXT NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 1,
            total_price REAL NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products(id)
        );
    """)

    # Seed data
    cur.execute("SELECT COUNT(*) FROM products")
    if cur.fetchone()[0] == 0:
        products = [
            ("Ноутбук ASUS ROG Strix", "Ноутбуки", 89999, "Игровой ноутбук 15.6\", RTX 4060, i7-13700H, 16GB RAM, 512GB SSD", 5, "laptop"),
            ("Ноутбук Lenovo ThinkPad X1", "Ноутбуки", 124990, "Бизнес-ноутбук 14\", Intel Core i7, 32GB RAM, 1TB SSD", 3, "laptop"),
            ("ПК MSI Gaming Desktop", "Компьютеры", 74990, "Готовый игровой ПК, RTX 4070, Ryzen 7 7700X, 32GB RAM", 7, "desktop"),
            ("Монитор Samsung 27\" QHD", "Мониторы", 32490, "27 дюймов, 2560×1440, 165Hz, IPS-матрица, 1ms", 12, "monitor"),
            ("Монитор LG UltraWide 34\"", "Мониторы", 48990, "34 дюйма, 3440×1440, VA, 144Hz, HDR400", 6, "monitor"),
            ("Клавиатура Keychron K2", "Периферия", 8990, "Механическая, Bluetooth/USB, RGB-подсветка, Hot-swap", 20, "keyboard"),
            ("Мышь Logitech G Pro X", "Периферия", 7490, "Беспроводная игровая мышь, 25600 DPI, 60H батарея", 15, "mouse"),
            ("SSD Samsung 980 Pro 1TB", "Комплектующие", 11990, "NVMe M.2, скорость до 7000 МБ/с, PCIe 4.0", 30, "ssd"),
            ("Видеокарта RTX 4080 Super", "Комплектующие", 89990, "16GB GDDR6X, DLSS 3, ray tracing, для 4K-гейминга", 4, "gpu"),
            ("Наушники Sony WH-1000XM5", "Аудио", 29990, "Беспроводные, шумоподавление, 30ч батарея, Hi-Res Audio", 8, "headphones"),
        ]
        cur.executemany(
            "INSERT INTO products (name, category, price, description, stock, image_url) VALUES (?,?,?,?,?,?)",
            products
        )
    conn.commit()
    conn.close()

@app.route("/")
def index():
    conn = get_db()
    categories = conn.execute("SELECT DISTINCT category FROM products").fetchall()
    selected = request.args.get("category", "")
    search = request.args.get("search", "")
    query = "SELECT * FROM products WHERE 1=1"
    params = []
    if selected:
        query += " AND category = ?"
        params.append(selected)
    if search:
        query += " AND (name LIKE ? OR description LIKE ?)"
        params += [f"%{search}%", f"%{search}%"]
    products = conn.execute(query, params).fetchall()
    conn.close()
    return render_template("index.html", products=products, categories=categories, selected=selected, search=search)

@app.route("/product/<int:pid>")
def product(pid):
    conn = get_db()
    p = conn.execute("SELECT * FROM products WHERE id = ?", (pid,)).fetchone()
    conn.close()
    if not p:
        return redirect(url_for("index"))
    return render_template("product.html", product=p)

@app.route("/order/<int:pid>", methods=["GET", "POST"])
def order(pid):
    conn = get_db()
    p = conn.execute("SELECT * FROM products WHERE id = ?", (pid,)).fetchone()
    if not p:
        conn.close()
        return redirect(url_for("index"))
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        qty = int(request.form.get("quantity", 1))
        if name and email and qty > 0:
            total = p["price"] * qty
            conn.execute(
                "INSERT INTO orders (customer_name, customer_email, product_id, quantity, total_price) VALUES (?,?,?,?,?)",
                (name, email, pid, qty, total)
            )
            conn.execute("UPDATE products SET stock = stock - ? WHERE id = ?", (qty, pid))
            conn.commit()
            conn.close()
            return render_template("success.html", name=name, product=p["name"], total=total)
    conn.close()
    return render_template("order.html", product=p)

@app.route("/admin")
def admin():
    conn = get_db()
    orders = conn.execute("""
        SELECT o.*, p.name as product_name
        FROM orders o JOIN products p ON o.product_id = p.id
        ORDER BY o.created_at DESC
    """).fetchall()
    stats = conn.execute("""
        SELECT COUNT(*) as total_orders, SUM(total_price) as revenue FROM orders
    """).fetchone()
    conn.close()
    return render_template("admin.html", orders=orders, stats=stats)

if __name__ == "__main__":
    init_db()
    print("=" * 50)
    print("  TechStore запущен!")
    print("  Откройте: http://127.0.0.1:5000")
    print("=" * 50)
    app.run(debug=True)
