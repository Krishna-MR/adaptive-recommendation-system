from flask import Flask, render_template, request, redirect, url_for
from news_service import get_news
import database

app = Flask(__name__)

# Initialize database tables
database.init_db()


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        return redirect(url_for("home", username=username))
    return render_template("login.html")


@app.route("/home/<username>")
def home(username):
    user_id = database.get_or_create_user(username)
    page = int(request.args.get("page", 1))

    preferences = database.get_preferences(user_id)
    categories = ["general", "sports", "technology", "entertainment", "health"]

    # Sort categories using Q-values (RL logic)
    categories.sort(key=lambda c: preferences.get(c, 0), reverse=True)

    articles = []
    for category in categories:
        articles.extend(get_news(category, page=page))

    return render_template(
        "home.html",
        username=username,
        user_id=user_id,
        articles=articles,
        page=page
    )


@app.route("/feedback", methods=["POST"])
def feedback():
    user_id = int(request.form["user_id"])
    category = request.form["category"]
    action = request.form["action"]

    reward = 1 if action == "like" else -1

    database.save_interaction(user_id, category, action)
    database.update_preference(user_id, category, reward)

    return redirect(request.referrer)


@app.route("/save", methods=["POST"])
def save_article():
    database.save_article(
        request.form["user_id"],
        request.form["title"],
        request.form["url"],
        request.form["category"]
    )
    return redirect(request.referrer)


@app.route("/saved/<username>")
def saved_articles(username):
    user_id = database.get_or_create_user(username)
    articles = database.get_saved_articles(user_id)

    return render_template(
        "saved.html",
        username=username,
        articles=articles
    )


@app.route("/search")
def search():
    query = request.args.get("q")
    if not query:
        return redirect(url_for("login"))

    articles = get_news(category="general", page=1)

    filtered = [
        a for a in articles
        if query.lower() in (a.get("title") or "").lower()
    ]

    return render_template(
        "home.html",
        username="Search Results",
        user_id=0,
        articles=filtered,
        page=1
    )


if __name__ == "__main__":
    app.run(debug=True)
