"""
app.py — Flask Backend for E-Commerce Shopping Cart + Billing
=============================================================
Requirements:
    pip install flask mysql-connector-python

Run:
    python app.py
"""

from flask import Flask, jsonify, render_template, request
import mysql.connector

app = Flask(__name__)

# ─────────────────────────────────────────────
#  DATABASE CONFIGURATION
#  ↓ Replace the values below with your own ↓
# ─────────────────────────────────────────────
DB_CONFIG = {
    "host":     "localhost",
    "user":     "root",           # ← your MySQL username
    "password": "!]vZ--xcre",  # ← your MySQL password HERE
    "database": "shop_db",
}
# ─────────────────────────────────────────────


def get_db():
    """Open and return a new MySQL connection + cursor."""
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)   # rows come back as dicts
    return conn, cursor


# ───────── PAGES ─────────────────────────────

@app.route("/")
def index():
    """Render the main shop page."""
    return render_template("index.html")


@app.route("/checkout")
def checkout_page():
    """Render the checkout / billing page."""
    return render_template("checkout.html")


@app.route("/orders")
def orders_page():
    """Render the order history page."""
    return render_template("orders.html")


# ───────── PRODUCTS API ──────────────────────

@app.route("/api/products", methods=["GET"])
def get_products():
    """Return all products as JSON."""
    conn, cur = get_db()
    cur.execute("SELECT * FROM products")
    products = cur.fetchall()
    cur.close(); conn.close()
    return jsonify(products)


# ───────── CART API ──────────────────────────

@app.route("/api/cart", methods=["GET"])
def get_cart():
    """
    Return all cart items joined with product details.
    Includes a computed `subtotal` per line.
    """
    conn, cur = get_db()
    cur.execute("""
        SELECT
            c.id        AS cart_id,
            p.id        AS product_id,
            p.name,
            p.price,
            p.image_url,
            c.quantity,
            ROUND(p.price * c.quantity, 2) AS subtotal
        FROM cart c
        JOIN products p ON c.product_id = p.id
        ORDER BY c.id
    """)
    items = cur.fetchall()
    cur.close(); conn.close()
    return jsonify(items)


@app.route("/api/cart", methods=["POST"])
def add_to_cart():
    """
    Add a product to the cart.
    Body (JSON): { "product_id": <int> }
    If the product is already in the cart, increment its quantity.
    """
    data       = request.get_json()
    product_id = data.get("product_id")

    if not product_id:
        return jsonify({"error": "product_id is required"}), 400

    conn, cur = get_db()

    # Check if the item already exists in cart
    cur.execute("SELECT id, quantity FROM cart WHERE product_id = %s", (product_id,))
    existing = cur.fetchone()

    if existing:
        # Increment quantity
        cur.execute(
            "UPDATE cart SET quantity = quantity + 1 WHERE id = %s",
            (existing["id"],)
        )
    else:
        # Insert new row
        cur.execute(
            "INSERT INTO cart (product_id, quantity) VALUES (%s, 1)",
            (product_id,)
        )

    conn.commit()
    cur.close(); conn.close()
    return jsonify({"success": True, "message": "Item added to cart"})


@app.route("/api/cart/<int:cart_id>", methods=["PUT"])
def update_cart(cart_id):
    """
    Update quantity of a cart item.
    Body (JSON): { "quantity": <int> }
    If quantity <= 0, the item is removed.
    """
    data     = request.get_json()
    quantity = data.get("quantity", 1)

    conn, cur = get_db()

    if quantity <= 0:
        # Remove item if quantity reaches zero
        cur.execute("DELETE FROM cart WHERE id = %s", (cart_id,))
    else:
        cur.execute(
            "UPDATE cart SET quantity = %s WHERE id = %s",
            (quantity, cart_id)
        )

    conn.commit()
    cur.close(); conn.close()
    return jsonify({"success": True})


@app.route("/api/cart/<int:cart_id>", methods=["DELETE"])
def delete_cart_item(cart_id):
    """Remove a single item from the cart by its cart row id."""
    conn, cur = get_db()
    cur.execute("DELETE FROM cart WHERE id = %s", (cart_id,))
    conn.commit()
    cur.close(); conn.close()
    return jsonify({"success": True, "message": "Item removed"})


@app.route("/api/cart/clear", methods=["DELETE"])
def clear_cart():
    """Remove every item from the cart (used after checkout)."""
    conn, cur = get_db()
    cur.execute("DELETE FROM cart")
    conn.commit()
    cur.close(); conn.close()
    return jsonify({"success": True, "message": "Cart cleared"})


# ───────── CHECKOUT API ──────────────────────

@app.route("/api/checkout", methods=["POST"])
def checkout():
    """
    Place an order.
    Body (JSON): {
        full_name, email, phone, address, city, state, zip_code, country
    }
    1. Validates the cart is not empty
    2. Creates an `orders` row with billing details
    3. Inserts all cart items into `order_items`
    4. Clears the cart
    """
    data = request.get_json()

    required = ["full_name", "email", "phone", "address", "city", "zip_code", "country"]
    for field in required:
        if not data.get(field, "").strip():
            return jsonify({"error": f"'{field}' is required"}), 400

    conn, cur = get_db()

    # ── 1. Load current cart ──
    cur.execute("""
        SELECT
            c.id        AS cart_id,
            p.id        AS product_id,
            p.name,
            p.price,
            c.quantity,
            ROUND(p.price * c.quantity, 2) AS subtotal
        FROM cart c
        JOIN products p ON c.product_id = p.id
    """)
    cart = cur.fetchall()

    if not cart:
        cur.close(); conn.close()
        return jsonify({"error": "Cart is empty"}), 400

    grand_total = sum(float(item["subtotal"]) for item in cart)

    # ── 2. Insert order ──
    cur.execute("""
        INSERT INTO orders
            (grand_total, full_name, email, phone, address, city, state, zip_code, country)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        round(grand_total, 2),
        data["full_name"].strip(),
        data["email"].strip(),
        data["phone"].strip(),
        data["address"].strip(),
        data["city"].strip(),
        data.get("state", "").strip(),
        data["zip_code"].strip(),
        data["country"].strip(),
    ))
    order_id = cur.lastrowid

    # ── 3. Insert order items ──
    for item in cart:
        cur.execute("""
            INSERT INTO order_items (order_id, product_id, name, price, quantity, subtotal)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            order_id,
            item["product_id"],
            item["name"],
            float(item["price"]),
            item["quantity"],
            float(item["subtotal"]),
        ))

    # ── 4. Clear cart ──
    cur.execute("DELETE FROM cart")

    conn.commit()
    cur.close(); conn.close()

    return jsonify({
        "success":     True,
        "order_id":    order_id,
        "grand_total": round(grand_total, 2),
        "message":     f"Order #{order_id} placed successfully!"
    })


# ───────── ORDERS API ────────────────────────

@app.route("/api/orders", methods=["GET"])
def get_orders():
    """Return all orders (newest first) with their line items."""
    conn, cur = get_db()

    cur.execute("SELECT * FROM orders ORDER BY created_at DESC")
    orders = cur.fetchall()

    for order in orders:
        # Convert datetime to string for JSON serialisation
        order["created_at"] = str(order["created_at"])
        cur.execute(
            "SELECT * FROM order_items WHERE order_id = %s",
            (order["id"],)
        )
        order["items"] = cur.fetchall()

    cur.close(); conn.close()
    return jsonify(orders)


@app.route("/api/orders/<int:order_id>", methods=["GET"])
def get_order(order_id):
    """Return a single order with its line items."""
    conn, cur = get_db()
    cur.execute("SELECT * FROM orders WHERE id = %s", (order_id,))
    order = cur.fetchone()

    if not order:
        cur.close(); conn.close()
        return jsonify({"error": "Order not found"}), 404

    order["created_at"] = str(order["created_at"])
    cur.execute("SELECT * FROM order_items WHERE order_id = %s", (order_id,))
    order["items"] = cur.fetchall()

    cur.close(); conn.close()
    return jsonify(order)


# ───────── ENTRY POINT ───────────────────────

if __name__ == "__main__":
    # debug=True — disable in production!
    app.run(debug=True, port=5000)
