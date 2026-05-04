from flask import Flask, jsonify, request, render_template, session
import uuid, time, random, json
from datetime import datetime

app = Flask(__name__)
app.secret_key = "canteeny-secret-2024"

# ─────────────────────────────────────────────
#  IN-MEMORY STORE  (no DB needed to run)
# ─────────────────────────────────────────────
MENU = [
    {"id":"samosa",   "name":"Samosa",          "price":15, "cat":"Snacks", "veg":True,  "emoji":"🥟", "desc":"Crispy lil triangles of joy"},
    {"id":"sandwich", "name":"Paneer Sandwich",  "price":45, "cat":"Snacks", "veg":True,  "emoji":"🥪", "desc":"Paneer doing its best"},
    {"id":"wrap",     "name":"Chicken Wrap",     "price":80, "cat":"Snacks", "veg":False, "emoji":"🌯", "desc":"A hug in a tortilla"},
    {"id":"rajma",    "name":"Rajma Chawal",     "price":70, "cat":"Meals",  "veg":True,  "emoji":"🍛", "desc":"Homesick? This fixes it"},
    {"id":"dal",      "name":"Dal Fry + Rice",   "price":60, "cat":"Meals",  "veg":True,  "emoji":"🍚", "desc":"Simple. Iconic. Unbeatable."},
    {"id":"biryani",  "name":"Veg Biryani",      "price":75, "cat":"Meals",  "veg":True,  "emoji":"🫕", "desc":"The main character energy"},
    {"id":"chai",     "name":"Masala Chai",      "price":15, "cat":"Drinks", "veg":True,  "emoji":"☕", "desc":"Liquid therapy fr fr"},
    {"id":"coffee",   "name":"Cold Coffee",      "price":40, "cat":"Drinks", "veg":True,  "emoji":"🥤", "desc":"Iced, baby. No cap."},
    {"id":"juice",    "name":"Lime Juice",       "price":30, "cat":"Drinks", "veg":True,  "emoji":"🧃", "desc":"Your body is begging"},
    {"id":"gulab",    "name":"Gulab Jamun",      "price":25, "cat":"Sweets", "veg":True,  "emoji":"🍮", "desc":"Diabetes speedrun"},
    {"id":"kheer",    "name":"Kheer",            "price":30, "cat":"Sweets", "veg":True,  "emoji":"🍨", "desc":"Grandma energy in a bowl"},
]

# orders dict: order_id -> order object
ORDERS = {}

# ─────────────────────────────────────────────
#  HELPER
# ─────────────────────────────────────────────
def make_order_id():
    return "C-" + str(random.randint(1000, 9999))

def get_tracking_stage(created_at):
    """Auto-advance tracking based on time elapsed."""
    elapsed = time.time() - created_at
    if elapsed < 10:   return 1   # placed
    if elapsed < 25:   return 2   # confirmed
    if elapsed < 50:   return 3   # cooking
    return 4                       # ready

# ─────────────────────────────────────────────
#  ROUTES
# ─────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")

# GET all menu items (optionally filter by cat)
@app.route("/api/menu")
def api_menu():
    cat = request.args.get("cat", "all")
    if cat == "all":
        return jsonify(MENU)
    return jsonify([m for m in MENU if m["cat"].lower() == cat.lower()])

# GET menu categories
@app.route("/api/categories")
def api_categories():
    cats = list(dict.fromkeys(m["cat"] for m in MENU))
    return jsonify(cats)

# POST — create new order
@app.route("/api/order", methods=["POST"])
def create_order():
    data = request.get_json()
    items   = data.get("items", [])       # [{id, qty}, ...]
    payment = data.get("payment", "UPI")
    name    = data.get("name", "Anonymous")

    if not items:
        return jsonify({"error": "No items selected"}), 400

    # Build line items
    line_items = []
    total = 0
    for entry in items:
        item = next((m for m in MENU if m["id"] == entry["id"]), None)
        if item:
            qty = int(entry.get("qty", 1))
            subtotal = item["price"] * qty
            total += subtotal
            line_items.append({
                "id":       item["id"],
                "name":     item["name"],
                "emoji":    item["emoji"],
                "price":    item["price"],
                "qty":      qty,
                "subtotal": subtotal,
            })

    order_id = make_order_id()
    order = {
        "order_id":   order_id,
        "name":       name,
        "items":      line_items,
        "total":      total,
        "payment":    payment,
        "status":     "placed",
        "created_at": time.time(),
        "placed_at":  datetime.now().strftime("%d %b %Y, %I:%M %p"),
    }
    ORDERS[order_id] = order
    return jsonify({"success": True, "order": order}), 201

# GET — order status / tracking
@app.route("/api/order/<order_id>")
def get_order(order_id):
    order = ORDERS.get(order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404

    stage = get_tracking_stage(order["created_at"])
    stages = ["placed", "confirmed", "cooking", "ready"]
    order["stage"]  = stage
    order["status"] = stages[stage - 1]
    return jsonify(order)

# GET — all orders (admin view)
@app.route("/api/orders")
def all_orders():
    result = []
    for o in ORDERS.values():
        stage = get_tracking_stage(o["created_at"])
        stages = ["placed","confirmed","cooking","ready"]
        o["stage"]  = stage
        o["status"] = stages[stage-1]
        result.append(o)
    result.sort(key=lambda x: x["created_at"], reverse=True)
    return jsonify(result)

# POST — validate payment (mock)
@app.route("/api/payment/validate", methods=["POST"])
def validate_payment():
    data    = request.get_json()
    method  = data.get("method", "")
    details = data.get("details", "")

    # Mock validation
    time.sleep(0.4)  # fake processing

    if method == "UPI" and "@" not in details:
        return jsonify({"success": False, "error": "Invalid UPI ID — needs an @ bro"}), 400

    if method == "Card":
        num = details.replace(" ", "")
        if not num.isdigit() or len(num) < 12:
            return jsonify({"success": False, "error": "Card number looks sus 👀"}), 400

    txn_id = "TXN" + str(random.randint(100000, 999999))
    return jsonify({"success": True, "txn_id": txn_id, "message": "Payment received! No cap ✓"})

if __name__ == "__main__":
    print("\n🍛  Canteeny backend running!")
    print("📍  Open http://localhost:5000\n")
    app.run(debug=True, port=5000)
