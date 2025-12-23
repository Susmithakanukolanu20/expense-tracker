from flask import Flask, request, jsonify, render_template, redirect, session
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector

app = Flask(__name__)
CORS(app)

# ---------------- BASIC CONFIG ----------------
app.secret_key = "supersecretkey123"

# ---------------- MYSQL CONFIG (RAILWAY) ----------------
app.config['MYSQL_HOST'] = 'yamabiko.proxy.rlwy.net'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'vFocZFEDyWgtKCEPrAPFahfxQvIfHbiR'
app.config['MYSQL_DB'] = 'railway'
app.config['MYSQL_PORT'] = 3306


# ---------------- DB CONNECTION ----------------
def get_db_connection():
    return mysql.connector.connect(
        host=app.config['MYSQL_HOST'],
        user=app.config['MYSQL_USER'],
        password=app.config['MYSQL_PASSWORD'],
        database=app.config['MYSQL_DB'],
        port=app.config['MYSQL_PORT']
    )


# ---------------- HOME ----------------
@app.route('/')
def home():
    username = None
    if session.get('user_id'):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT username FROM users WHERE id=%s", (session['user_id'],))
        user = cur.fetchone()
        cur.close()
        conn.close()
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

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
            (username, email, password)
        )
        conn.commit()
        cur.close()
        conn.close()

        return redirect('/login')

    return render_template("register.html")


# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, password FROM users WHERE email=%s", (email,))
        user = cur.fetchone()
        cur.close()
        conn.close()

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
    if not session.get('user_id'):
        return redirect('/login')
    return render_template("add.html")


@app.route('/api/add_expense', methods=['POST'])
def add_expense():
    if not session.get('user_id'):
        return jsonify({"error": "Not logged in"})

    data = request.json

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO expenses (category, amount, date, note, user_id)
        VALUES (%s, %s, STR_TO_DATE(%s,'%%Y-%%m-%%d'), %s, %s)
        """,
        (data['category'], data['amount'], data['date'], data['note'], session['user_id'])
    )
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"message": "Expense Added"})


# ---------------- VIEW EXPENSES ----------------
@app.route('/view')
def view_page():
    if not session.get('user_id'):
        return redirect('/login')
    return render_template("view.html")


@app.route('/api/get_expenses')
def get_expenses():
    if not session.get('user_id'):
        return jsonify([])

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, category, amount, date, note FROM expenses WHERE user_id=%s",
        (session['user_id'],)
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify([
        {"id": r[0], "category": r[1], "amount": r[2], "date": str(r[3]), "note": r[4]}
        for r in rows
    ])


# ---------------- GRAPH DATA ----------------
@app.route('/api/graph_data')
def graph_data():
    if not session.get('user_id'):
        return jsonify({})

    conn = get_db_connection()
    cur = conn.cursor()

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
    conn.close()

    return jsonify({
        "categoryLabels": [r[0] for r in category_rows],
        "categoryTotals": [float(r[1]) for r in category_rows],
        "dateLabels": [str(r[0]) for r in date_rows],
        "dateTotals": [float(r[1]) for r in date_rows]
    })


# ---------------- DELETE EXPENSE ----------------
@app.route('/api/delete/<int:id>', methods=['DELETE'])
def delete_expense(id):
    if not session.get('user_id'):
        return jsonify({"error": "Not logged in"})

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM expenses WHERE id=%s AND user_id=%s",
        (id, session['user_id'])
    )
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"message": "Deleted"})


# ---------------- ML PREDICTION ----------------
# @app.route('/api/predict')
#def predict_expense():
  #  if not session.get('user_id'):
    #    return jsonify({"prediction": 0})

    #conn = get_db_connection()
    #cur = conn.cursor()
    #cur.execute(
    #    "SELECT amount FROM expenses WHERE user_id=%s ORDER BY date",
     #   (session['user_id'],)
   # )
    #rows = cur.fetchall()
    #cur.close()
    #conn.close()

    #if len(rows) < 3:
     #   return jsonify({"prediction": 0})

   # X = [[i] for i in range(len(rows))]
   # y = [float(r[0]) for r in rows]

    #model = LinearRegression()
   # model.fit(X, y)

    #prediction = model.predict([[len(rows)]])[0]
    #return jsonify({"prediction": round(prediction, 2)})


# ---------------- RUN APP ----------------
if __name__ == "__main__":
    app.run()
