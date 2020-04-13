import os

from flask import Flask, session, abort, flash, jsonify, redirect, url_for, make_response
from flask import render_template, request
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import requests

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/mainpage")
def index():
    if not session.get('logged_in'):
        return redirect("/login")
    else:
        booksEmpty = []
        return render_template("main.html", books=booksEmpty)


@app.route("/login", methods=["POST", "GET"])
def login():
    session.clear()
    if request.method == "GET":
        if session.get("logged_in"):
            flash("You are already logged in")
            return redirect("/mainpage")
        else:
            return render_template("login.html")

    if request.method == "POST":
        # Get username and password
        username = request.form['username']
        password = request.form['password']
        userDB = db.execute(
            "SELECT * FROM public.user WHERE username = :username", {"username": username}).fetchone()
        # validation for username
        if userDB is None:
            return render_template("login.html", message="error")

        # Validate password
        if userDB.username == username and userDB.password == password:
            session["logged_in"] = True
            session["username"] = username
            session["userId"] = userDB.user_id
            return redirect(url_for('index'))
        else:
            return render_template("login.html", message="error")


@app.route('/logout')
def logout():
    # Forget any user
    session.clear()
    flash("Logout succesfull")
    # Redirect to mainpage Login
    return redirect("/login")


@app.route("/registration", methods=["POST", "GET"])
def registration():
    if request.method == "POST":
        usersDB = db.execute("SELECT * FROM public.user").fetchall()
        newusername = request.form['newusername']
        newpassword = request.form['newpassword']
        # validatation
        userDB = db.execute(
            "SELECT * FROM public.user WHERE username = :username", {"username": newusername}).fetchone()
        if not userDB is None:
            return render_template("registration.html", message="Username already in use")
        else:
            db.execute("INSERT INTO public.user (username, password) VALUES (:username, :password)",
                       {"username": newusername, "password": newpassword})
        # Commiting to database
        db.commit()
        return render_template("registration.html", message="Successfull register, now Login")
    else:
        if not session.get('logged_in'):
            return render_template("registration.html", message=" ")
        else:
            return redirect("/mainpage")


@app.route("/mainpage/books", methods=["GET", "POST"])
def search():
    if session.get("logged_in"):
        if request.method == 'POST':
            value = request.form['textBook']
            # Take input and add a wildcard
            query = "%" + request.form['textBook'] + "%"
            # Capitalize all words of input for search
            # https://docs.python.org/3.7/library/stdtypes.html?highlight=title#str.title
            query = query.title()
            rows = db.execute("SELECT * FROM book WHERE \
                            isbn LIKE :query OR \
                            title LIKE :query OR \
                            author LIKE :query LIMIT 15",
                            {"query": query})
            if rows.rowcount == 0:
                null = []
                flash('No book match the criteria', 'info')
                return render_template("main.html", books=null)

            books = rows.fetchall()
            return render_template("main.html", books=books)
        else:
            return redirect("/mainpage")
    else:
        return render_template("login.html")
    
@app.route("/book/<string:isbn>", methods=["GET"])
def bookDetails(isbn):
    if session.get("logged_in"):
        session["isbn"] = isbn
        row = db.execute("SELECT book_id, isbn, title, author, year FROM book WHERE isbn = :isbn", {"isbn": isbn})

        bookInfo = row.fetchone()
        bookId = bookInfo[0]

        key = '2FaWYjxO1u5L3GJkyzxzpA'
        r = requests.get(
            'https://www.goodreads.com/book/review_counts.json?isbns='+isbn+'&key='+key)
        jsonObject = r.json()
        countRating = float(jsonObject['books'][0]['work_ratings_count'])
        ratingBook = float(jsonObject['books'][0]['average_rating'])
        reviews = getReviewsFromDatabase(bookId)
        return render_template('bookDetails.html',  title=bookInfo.title, author=bookInfo.author, isbn=isbn, year=bookInfo.year, rating=ratingBook, countRating=countRating, reviews=reviews)
    else:
        return render_template("login.html")
    
    
#Extern method, it doesnt has a route. It gets the reviews from the database

def getReviewsFromDatabase(book_id):
    rows = db.execute("SELECT * FROM public.review WHERE book_id = :book_id LIMIT 10", {"book_id": book_id})
    if rows.rowcount == 0:
        null = []
        return null
    else:
        reviews = rows.fetchall()
        return reviews

#Extern method, it doesnt has a route. It validate the review
def validatationReview(bookId):
    id_user = session.get('userId')

    userRatings = db.execute("SELECT * FROM public.review WHERE user_id = :userid AND book_id= :book_id", 
                {"userid": id_user, "book_id":bookId }).fetchone()
    
    if userRatings is None:
        print(True)
        return True
    else:
        print(False)
        return False

@app.route("/<string:oldPath>/new-review", methods = ["POST"])
def newReview(oldPath):
    #Finish, it check if the user already submit a review, if not: insert the review to de DB, otherwise,
    # notifices the user that he cannot update a review to the book. 
    row = db.execute("SELECT book_id FROM book WHERE isbn = :isbn", {"isbn": session.get('isbn')})
    bookId = row.fetchone()
    bookId= bookId[0] #I get the book_id

    if (validatationReview(bookId)) == True:
        #insertar la review
        bookInfo = row.fetchone()
        textReview = request.form['text-area']
        ratingReview = request.form['number-rating']
        
        id_user = session.get('userId')
        db.execute("INSERT INTO public.review (user_id, comentary, score, book_id) VALUES(:user_id, :comentary, :score, :book_id)",
        {"user_id":id_user, "comentary":textReview, "score":ratingReview, "book_id": bookId})

        db.commit()
        flash('Review submitted!', 'info')
        return redirect("/book/"+session.get('isbn'))
    else:
        flash('You already submitted a review for this book', 'warning')
        return redirect("/book/" + session.get('isbn'))
'''
@app.errorhandler(404)
def resource_not_found(e):
    return jsonify(error=str(e)), 404
'''
@app.route("/api/<string:isbn>")
def book_api(isbn):
    #API, only one book return
    
    #Make sure the book exists
    row = db.execute("SELECT isbn, title, author, year, \
                    COUNT(review.review_id) AS review_count, \
                    AVG(review.score) AS average_score \
                    FROM book INNER JOIN review ON book.book_id = review.book_id \
                    WHERE isbn = :isbn \
                    GROUP BY title, author, year, isbn",
                    {"isbn": isbn})
   # if row.rowcount != 1
   # 0380795272
    if row.rowcount != 1:
        return make_response(render_template('error404.html'), 404)
    else:
        book = row.fetchone()
        return jsonify({
            "title": book.title,
            "author": book.author,
            "year": book.year,
            "isbn": book.isbn,
            "review_count": book.review_count,
            "average_score": float('%.2f'%(book.average_score))       
        })