from src import app, db
from flask import render_template, redirect, url_for, session, request, jsonify
from flask_login import login_user, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from flask_paginate import Pagination, get_page_parameter
import requests, datetime, time, os

starSize = ["full", "half", "full", "half", "full",
		    "half", "full", "half", "full", "half"]
starValue = [5, 4.5, 4, 3.5, 3, 2.5, 2, 1.5, 1, 0.5]
starRating = ["star5", "star4half", "star4", "star3half", "star3", 
			  "star2half", "star2", "star1half", "star1", "starhalf"]
starTitle = ["Awesome - 5 stars", "Pretty good - 4.5 stars", "Pretty good - 4 stars", 
			 "Meh - 3.5 stars", "Meh - 3 stars", "Kinda bad - 2.5 stars", "Kinda bad - 2 stars", 
			 "Meh - 1.5 stars", "Sucks big time - 1 star", "Sucks big time - 0.5 stars"]

@app.route("/")
def index():
	# check if the user is logged in
	if not session.get('logged_in'):
		return render_template("login.html")
	else:
		return render_template('search.html')

	# if not current_user.is_authenticated:
	# 		return render_template("login.html")
	# else:
	# 		return render_template('search.html')

@app.route("/delete", methods=['GET'])
def delete():
	db.execute("DELETE FROM users")
	db.commit()
	return redirect(url_for('index'))

@app.route("/register", methods=['GET', 'POST'])
def register():
	if request.method == 'GET':
		if session.get('logged_in'):
			return render_template('search.html', username=session.get('logged_in'))
		else:
			return render_template("register.html")
	else:
		# get form information
		username = request.form.get("username")
		password = request.form.get("password")
		rePassword = request.form.get("rePassword")

		if not username or not password or not rePassword:
			return render_template("error.html", message="Fields can't be empty!")

		# checks if the username exists
		if db.execute("SELECT * FROM users WHERE username = :username", {"username": username}).rowcount != 0:
			return render_template("error.html", message=username+" has already been used!")

		# checks if the password is correct
		elif password != rePassword:
			return render_template("error.html", message="Password doesn't match")

		# insert it to the database
		db.execute("INSERT INTO users (username, password) VALUES (:username, :password)", 
				   {"username": username, "password": generate_password_hash(password)})
		db.commit()
		return redirect(url_for('index'))

@app.route("/login", methods=['POST'])
def login():
	# get form information
	username = request.form.get("username")
	password = request.form.get("password")

	if not username or not password:
		return render_template("error.html", message="Fields can't be empty!")
	
	# checks if the username exists
	result = db.execute("SELECT id, password FROM users WHERE username = :username", {"username": username}).fetchone()

	# logs in the user if username exists and password is right
	if not result:
		return render_template("error.html", message="User not found! Try registering an account")
	elif check_password_hash(result['password'], password):				
		session['logged_in'] = result['id']
		# login_user("H")
		return redirect(url_for('index'))
	else:
		return render_template("error.html", message="Password doesn't match")

@app.route("/logout", methods=['GET'])
def logout():
	session.pop('logged_in')
	# logout_user()
	return redirect(url_for('index'))

@app.route("/results", methods=['GET'])
def results():
	if not session.get('logged_in'):
		return render_template('error.html', message="ERROR 401 Unauthorised - Please log in first!")

	query = request.args.get("search").lower()
	session['query'] = query
	if not query:
		return render_template("error.html", message="Query can't be empty!")
		
	pageNo = request.args.get("page")
	session['pageNo'] = pageNo
	if not pageNo:
		pageNo = 0
	else:
		pageNo = int(pageNo) - 1

	results = db.execute("SELECT isbn, title, author, yearPublished \
						  FROM books \
						  WHERE isbn LIKE :query OR \
								lower(title) LIKE :query OR \
								lower(author) LIKE :query", {"query": '%' + query + '%'}).fetchall()
	
	page = request.args.get(get_page_parameter(), type=int, default=1)
	pagination = Pagination(page = page, total = len(results), record_name='results')
									
	return render_template("results.html", query = query, results = results[(10 * pageNo):((pageNo*10)+10)], 
							pagination = pagination, css_framework='bootstrap4')

@app.route("/result", methods=['GET', 'POST'])
def result():
	if not session.get('logged_in'):
		return render_template('error.html', message="ERROR 401 Unauthorised - Please log in first!")

	# retrieve old reviews
	if request.method == 'GET':
		isbn = request.args.get("search")
		if not isbn:
			return render_template('error.html', message="GET Query not found!")

		# get book data
		book = db.execute("SELECT isbn, title, author, yearPublished \
						FROM books \
						WHERE isbn = :isbn", {"isbn": isbn}).fetchone()
		# get user's review
		review = db.execute("SELECT review, star \
							FROM reviews \
							WHERE id = :id AND isbn = :isbn", {"id" : session.get('logged_in'), "isbn" : isbn}).fetchone()
		
		# get all reviews
		reviews = db.execute("SELECT * \
							  FROM reviews \
							  WHERE isbn = :isbn", {"isbn" : isbn}).fetchall()

		if not book:
			return render_template("error.html", message = "Book not found!")
		
		# get goodread's review
		res = requests.get("https://www.goodreads.com/book/review_counts.json", 
							params={"key": os.environ.get("GOODREAD_KEY"), "isbns": isbn}).json()['books'][0]

		if res:
			rating_count = res['ratings_count']
			avg_rating = res['average_rating']

		return render_template("result.html", book = book, review = review, reviews = reviews, rating_count = rating_count, 
								avg_rating = avg_rating, starDesc = zip(starRating, starValue, starSize, starTitle))

	# if user wants to add a new review
	else:
		# retrieve info from forms
		rating = request.form.get("rating")
		review = request.form.get("review")
		isbn = request.form.get("search")
		currentTime = time.time()
		ts = datetime.datetime.fromtimestamp(currentTime).strftime('%Y-%m-%d %H:%M:%S')
		username = db.execute("SELECT username FROM users WHERE id = :id", {"id" : session.get('logged_in')}).fetchone()[0]

		if not rating:
			return render_template("error.html", message="Rating can't be empty!")
		elif not review:
			return render_template("error.html", message="Review field can't be empty!")

		# insert it to the database
		db.execute("INSERT INTO reviews (id, username, isbn, star, review, review_timestamp) \
					VALUES (:id, :username, :isbn, :star, :review, :ts)", 
				   {"id": session.get('logged_in'), "username": username, "isbn": isbn,
				   "star": rating, "review": review, "ts": ts})
		db.commit()

		return redirect(url_for('results', search=session['query'], page=session['pageNo']))

@app.route("/api/<string:isbn>", methods=['GET'])
def api(isbn):
	if not isbn:
		return jsonify({"error" : "Bad request!"}), 400

	# get book data
	book = db.execute("SELECT isbn, title, author, yearPublished \
					FROM books \
					WHERE isbn = :isbn", {"isbn": isbn}).fetchone()

	if not book:
		return jsonify({"error" : "Book not found"}), 404

	# get goodread's review
	res = requests.get("https://www.goodreads.com/book/review_counts.json", 
						params={"key": app.config["GOODREAD_KEY"], "isbns": isbn}).json()['books'][0]

	return jsonify({'title' : book.title, 'author' : book.author, 
					'year' : book.yearpublished, 'isbn' : book.isbn, 
					'review_count' : res['ratings_count'], 
					'average_score' : res['average_rating']}), 200