from flask import Flask, render_template, request, session, flash, redirect, url_for
import os
from dotenv import load_dotenv
from db import get_mysql_connection, init_schema
import datetime
import random
import pathlib


def create_app() -> Flask:
	app = Flask(__name__)
	# WARNING: replace this in production
	load_dotenv()  # load variables from a .env file if present
	app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")

	@app.route("/")
	def index():
		return render_template("index.html")

	@app.route("/AdminLogin")
	def admin_login():
		return render_template("AdminLogin.html")

	@app.route("/UserLogin")
	def user_login():
		return render_template("UserLogin.html")

	@app.route("/NewUser")
	def new_user():
		return render_template("NewUser.html")

	# Alias to support lowercase path commonly typed by users
	@app.route("/newuser", methods=["GET"])
	def new_user_alias():
		return render_template("NewUser.html")

	@app.route("/newuser", methods=["POST"])
	def new_user_submit():
		name = request.form.get("name", "")
		gender = request.form.get("gender", "")
		age = request.form.get("age", "")
		email = request.form.get("email", "")
		phone = request.form.get("phone", "")
		address = request.form.get("address", "")
		username = request.form.get("uname", "")
		password = request.form.get("psw", "")
		try:
			with get_mysql_connection() as conn:
				cur = conn.cursor()
				cur.execute(
					"""
					INSERT INTO regtb (Name, Gender, Age, Email, Mobile, Address, Username, Password)
					VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
					""",
					(name, gender, age, email, phone, address, username, password),
				)
				conn.commit()
			flash("Registered successfully. Please log in.")
		except Exception as e:
			flash(str(e))
		return render_template("UserLogin.html")

	@app.route("/Search")
	def search():
		rows = []
		username = session.get("uname")
		if username:
			with get_mysql_connection() as conn:
				cur = conn.cursor()
				cur.execute(
					"SELECT Type, date, Amount, Info FROM expensetb WHERE Username=%s ORDER BY date DESC, id DESC LIMIT 50",
					(username,),
				)
				rows = cur.fetchall()
		return render_template("Search.html", data=rows)

	@app.route("/AdminHome")
	def admin_home():
		# Placeholder: fetch and pass user list later
		data = []
		return render_template("AdminHome.html", data=data)

	@app.route("/SetLimit", methods=["GET", "POST"])
	def set_limit():
		username = session.get("uname")
		if request.method == "POST":
			if not username:
				flash("Please login first")
				return render_template("UserLogin.html")
			mon = int(request.form.get("mon", "0") or 0)
			yea = int(request.form.get("yea", "0") or 0)
			amt = request.form.get("amount", "0")
			with get_mysql_connection() as conn:
				cur = conn.cursor()
				# Upsert simple
				cur.execute(
					"SELECT id FROM limtb WHERE Username=%s AND mon=%s AND yea=%s",
					(username, mon, yea),
				)
				row = cur.fetchone()
				if row:
					cur.execute(
						"UPDATE limtb SET Amount=%s WHERE id=%s",
						(amt, row[0]),
					)
				else:
					cur.execute(
						"INSERT INTO limtb (Username, mon, yea, Amount) VALUES (%s,%s,%s,%s)",
						(username, mon, yea, amt),
					)
				conn.commit()
			flash("Limit saved")
		# GET view
		data = []
		if username:
			with get_mysql_connection() as conn:
				cur = conn.cursor()
				cur.execute("SELECT id, Username, mon, yea, Amount FROM limtb WHERE Username=%s ORDER BY yea DESC, mon DESC", (username,))
				data = cur.fetchall()
		return render_template("Limit.html", data=data)

	@app.route("/MonthReport", methods=["GET", "POST"])
	def month_report():
		username = session.get("uname")
		chart_path = None
		rows = []
		if request.method == "POST" and username:
			import matplotlib
			matplotlib.use("Agg")
			import matplotlib.pyplot as plt
			mon = int(request.form.get("mon", "0") or 0)
			yea = int(request.form.get("yea", "0") or 0)
			with get_mysql_connection() as conn:
				cur = conn.cursor()
				cur.execute(
					"SELECT Type, SUM(Amount) FROM expensetb WHERE Username=%s AND mon=%s AND yea=%s GROUP BY Type",
					(username, mon, yea),
				)
				aggs = cur.fetchall()
				cur.execute(
					"SELECT Username, Type, date, Amount, Info FROM expensetb WHERE Username=%s AND mon=%s AND yea=%s ORDER BY date DESC",
					(username, mon, yea),
				)
				rows = cur.fetchall()
			labels = [a[0] for a in aggs]
			values = [float(a[1] or 0) for a in aggs]
			if labels:
				pathlib.Path("static/plott").mkdir(parents=True, exist_ok=True)
				plt.figure(figsize=(6, 4))
				plt.bar(labels, values, color=["#fbbf24", "#ef4444", "#10b981", "#3b82f6", "#a855f7"])  # yellow, red, green, blue, purple
				plt.xlabel("Type")
				plt.ylabel("Total Expenses")
				plt.title("Monthly Expenses")
				img_name = f"static/plott/{random.randint(1111,9999)}.png"
				plt.tight_layout()
				plt.savefig(img_name)
				chart_path = img_name
		return render_template("MonthReport.html", data=rows, dataimg=chart_path)

	@app.route("/Categories")
	def categories():
		username = session.get("uname")
		items = []
		if username:
			with get_mysql_connection() as conn:
				cur = conn.cursor()
				cur.execute("SELECT DISTINCT Type FROM expensetb WHERE Username=%s ORDER BY Type", (username,))
				items = [r[0] for r in cur.fetchall()]
		return render_template("Categories.html", items=items)

	@app.route("/Report")
	def report():
		data = []
		return render_template("Report.html", data=data)

	@app.route("/UserHome")
	def user_home():
		data = []
		return render_template("UserHome.html", data=data)

	@app.route("/adminlogin", methods=["GET", "POST"])
	def adminlogin_post():
		if request.method == "POST":
			uname = request.form.get("uname", "")
			password = request.form.get("password", "")
			if uname == "admin" and password == "admin":
				try:
					with get_mysql_connection() as conn:
						cur = conn.cursor()
						cur.execute("SELECT Username, Email, Mobile FROM regtb ORDER BY id DESC")
						data = cur.fetchall()
				except Exception:
					data = []
				return render_template("AdminHome.html", data=data)
			flash("Username or password incorrect")
			return render_template("index.html")
		return render_template("AdminLogin.html")

	@app.route("/userlogin", methods=["GET", "POST"])
	def userlogin_post():
		if request.method == "POST":
			username = request.form.get("uname", "")
			password = request.form.get("password", "")
			if username and password:
				try:
					with get_mysql_connection() as conn:
						cur = conn.cursor()
						cur.execute(
							"SELECT id, Mobile FROM regtb WHERE Username=%s AND Password=%s",
							(username, password),
						)
						row = cur.fetchone()
						if row:
							session["uname"] = username
							session["uid"] = row[0]
							session["mobile"] = row[1]
							return render_template("UserHome.html", data=[])
				except Exception as e:
					flash(str(e))
			flash("Username or password incorrect")
			return render_template("UserLogin.html")
		return render_template("UserLogin.html")

	@app.route("/db-check")
	def db_check():
		try:
			with get_mysql_connection() as conn:
				cur = conn.cursor()
				cur.execute("SELECT 1")
				row = cur.fetchone()
				return {"ok": True, "result": row[0] if row else None}
		except Exception as e:
			return {"ok": False, "error": str(e)}, 500

	@app.route("/logout")
	def logout():
		session.clear()
		flash("Logged out")
		return redirect(url_for("index"))

	@app.route("/add-expense", methods=["POST"])
	def add_expense():
		username = session.get("uname")
		if not username:
			flash("Please login first")
			return render_template("UserLogin.html")
		type_val = request.form.get("type", "")
		date_str = request.form.get("date", "")
		amount_str = request.form.get("amount", "0")
		info = request.form.get("info", "")
		try:
			date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
		except Exception:
			flash("Invalid date")
			return render_template("Search.html")
		mon = int(date_obj.strftime("%m"))
		yea = int(date_obj.strftime("%Y"))
		amount = float(amount_str or 0)
		with get_mysql_connection() as conn:
			cur = conn.cursor()
			# Get limit
			cur.execute("SELECT Amount FROM limtb WHERE Username=%s AND mon=%s AND yea=%s", (username, mon, yea))
			lim_row = cur.fetchone()
			limit_amt = float(lim_row[0]) if lim_row and lim_row[0] else 0.0
			# Current spent in month
			cur.execute("SELECT COALESCE(SUM(Amount),0) FROM expensetb WHERE Username=%s AND mon=%s AND yea=%s", (username, mon, yea))
			current_sum = float(cur.fetchone()[0] or 0)
			will_be = current_sum + amount
			# Insert expense
			cur.execute(
				"""
				INSERT INTO expensetb (Username, Type, date, Amount, Info, Bill, mon, yea)
				VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
				""",
				(username, type_val, date_obj, amount, info, "", mon, yea),
			)
			conn.commit()
			if limit_amt and will_be > limit_amt:
				flash(f"Warning: limit exceeded. Limit {limit_amt}, spent {will_be}")
			else:
				flash("New Expense Info Saved")
		# fetch updated list to display below the form
		with get_mysql_connection() as conn:
			cur = conn.cursor()
			cur.execute(
				"SELECT Type, date, Amount, Info FROM expensetb WHERE Username=%s ORDER BY date DESC, id DESC LIMIT 50",
				(username,),
			)
			rows = cur.fetchall()
		return render_template("Search.html", data=rows)

	@app.route("/db-init")
	def db_init():
		try:
			init_schema()
			return {"ok": True}
		except Exception as e:
			return {"ok": False, "error": str(e)}, 500

	return app


if __name__ == "__main__":
	app = create_app()
	app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)


