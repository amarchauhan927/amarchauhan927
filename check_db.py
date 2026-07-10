import mysql.connector

conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='!]vZ--xcre',
    database='shop_db'
)
cur = conn.cursor(dictionary=True)

print('=' * 60)
print('  ORDERS TABLE')
print('=' * 60)
cur.execute('SELECT id, full_name, email, city, country, grand_total, status, created_at FROM orders ORDER BY id DESC')
orders = cur.fetchall()
if orders:
    for o in orders:
        print("  Order #{}  |  {}  |  {}".format(o['id'], o['full_name'], o['email']))
        print("          City: {}, {}".format(o['city'], o['country']))
        print("          Total: ${}  |  Status: {}".format(o['grand_total'], o['status']))
        print("          Placed: {}".format(o['created_at']))
        print()
else:
    print("  (no orders yet)")

print('=' * 60)
print('  ORDER_ITEMS TABLE')
print('=' * 60)
cur.execute('SELECT * FROM order_items ORDER BY order_id DESC, id')
items = cur.fetchall()
if items:
    for i in items:
        print("  Item #{}  |  Order #{}  |  {}".format(i['id'], i['order_id'], i['name']))
        print("          ${} x {} = ${}".format(i['price'], i['quantity'], i['subtotal']))
        print()
else:
    print("  (no items)")

print('=' * 60)
print('  CART TABLE (current state)')
print('=' * 60)
cur.execute('SELECT c.id, p.name, c.quantity FROM cart c JOIN products p ON c.product_id = p.id')
cart = cur.fetchall()
if cart:
    for r in cart:
        print("  cart_id #{}  |  {}  x{}".format(r['id'], r['name'], r['quantity']))
else:
    print("  (empty - cleared after checkout)")

cur.close()
conn.close()
