from flask import Flask, request, jsonify, render_template, redirect, session
from flask_cors import CORS
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
CORS(app)

app.secret_key = "your_secret_key_here"

# ---------------- DATABASE CONFIG ----------------


# 🔵 For CLOUD (Railway / Render)
# Uncomment and fill when deploying
 app.config['MYSQL_HOST'] = 'mysql.railway.internal'
 app.config['MYSQL_USER'] = 'root'
 app.config['MYSQL_PASSWORD'] = 'vFocZFEDyWgtKCEPrAPFahfxQvIfHbiR'
 app.config['MYSQL_DB'] = 'railway'
 app.config['MYSQL_PORT'] = 3306

mysql = MySQL(app)

# ---------------- HOME ----------------
@app.route('/')
def home():
    username = None
    if 'user_id' in session:
        cur = mysql.connection.cursor()
        cur.execute("SELECT username FROM users WHERE id=%s", (session['user_id'],))
        user = cur.fetchone()
        cur.close()
        if user:
            username = user[0]
    return render_template("index.html", username=username)

# ---------------- REGISTER ----------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        cur = mysql.connection.cursor()
        cur.execute(
            "INSERT INTO users (username, email, password) VALUES (%s,%s,%s)",
            (username, email, password)
        )
        mysql.connection.commit()
        cur.close()
        return redirect('/login')

    return render_template("register.html")

# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT id, password FROM users WHERE email=%s", (email,))
        user = cur.fetchone()
        cur.close()

        if user and check_password_hash(user[1], password):
            session['user_id'] = user[0]
            return redirect('/')
        else:
            return "Invalid Email or Password"

    return render_template("login.html")

# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# ---------------- ADD EXPENSE ----------------
@app.route('/add')
def add_page():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template("add.html")

@app.route('/api/add_expense', methods=['POST'])
def add_expense():
    if 'user_id' not in session:
        return jsonify({"error": "Not logged in"})

    data = request.json
    cur = mysql.connection.cursor()
    cur.execute(
        "INSERT INTO expenses (category, amount, date, note, user_id) VALUES (%s,%s,%s,%s,%s)",
        (data['category'], data['amount'], data['date'], data['note'], session['user_id'])
    )
    mysql.connection.commit()
    cur.close()

    return jsonify({"message": "Expense Added"})

# ---------------- VIEW EXPENSE ----------------
@app.route('/view')
def view_page():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template("view.html")

@app.route('/api/get_expenses')
def get_expenses():
    if 'user_id' not in session:
        return jsonify([])

    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT id, category, amount, date, note FROM expenses WHERE user_id=%s",
        (session['user_id'],)
    )
    rows = cur.fetchall()
    cur.close()

    return jsonify([
        {"id": r[0], "category": r[1], "amount": r[2], "date": r[3], "note": r[4]}
        for r in rows
    ])

# ---------------- GRAPH DATA ----------------
@app.route('/api/graph_data')
def graph_data():
    if 'user_id' not in session:
        return jsonify([])

    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT category, SUM(amount) FROM expenses WHERE user_id=%s GROUP BY category",
        (session['user_id'],)
    )
    category_rows = cur.fetchall()

    cur.execute(
        "SELECT date, SUM(amount) FROM expenses WHERE user_id=%s GROUP BY date ORDER BY date",
        (session['user_id'],)
    )
    date_rows = cur.fetchall()
    cur.close()

    return jsonify({
        "categoryLabels": [r[0] for r in category_rows],
        "categoryTotals": [r[1] for r in category_rows],
        "dateLabels": [r[0] for r in date_rows],
        "dateTotals": [r[1] for r in date_rows]
    })

# ---------------- DELETE EXPENSE ----------------
@app.route('/api/delete/<int:id>', methods=['DELETE'])
def delete_expense(id):
    if 'user_id' not in session:
        return jsonify({"error": "Not logged in"})

    cur = mysql.connection.cursor()
    cur.execute(
        "DELETE FROM expenses WHERE id=%s AND user_id=%s",
        (id, session['user_id'])
    )
    mysql.connection.commit()
    cur.close()

    return jsonify({"message": "Deleted"})

# ---------------- ML PREDICTION ----------------
@app.route('/api/predict')
def predict_expense():
    from sklearn.linear_model import LinearRegression

    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT date, amount FROM expenses WHERE user_id=%s ORDER BY date",
        (session['user_id'],)
    )
    rows = cur.fetchall()
    cur.close()

    if len(rows) < 3:
        return jsonify({"prediction": 0})

    days = [[i] for i in range(len(rows))]
    amounts = [r[1] for r in rows]

    model = LinearRegression()
    model.fit(days, amounts)

    prediction = model.predict([[len(rows)]])[0]
    return jsonify({"prediction": round(prediction, 2)})

# ---------------- RUN APP ----------------
if __name__ == "__main__":
    app.run()
