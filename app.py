from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from news_service import get_news
import database
import random

app = Flask(__name__)
app.secret_key = "adaptive-recommendation-secret"

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

    recent_categories = session.get("recent_categories", [])
    global_scores = database.get_global_category_scores()

    def category_score(category):
        base = preferences.get(category, 0)
        recent = recent_categories.count(category) * 0.5
        global_boost = global_scores.get(category, 0)
        return base + recent + global_boost

    epsilon = 0.2
    if random.random() < epsilon:
        random.shuffle(categories)
    else:
        categories.sort(key=category_score, reverse=True)

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


# 🔥 LOAD MORE — AJAX (NO REFRESH)
@app.route("/load_more")
def load_more():
    user_id = int(request.args.get("user_id"))
    page = int(request.args.get("page"))

    preferences = database.get_preferences(user_id)
    categories = ["general", "sports", "technology", "entertainment", "health"]

    recent_categories = session.get("recent_categories", [])
    global_scores = database.get_global_category_scores()

    def category_score(category):
        base = preferences.get(category, 0)
        recent = recent_categories.count(category) * 0.5
        global_boost = global_scores.get(category, 0)
        return base + recent + global_boost

    epsilon = 0.2
    if random.random() < epsilon:
        random.shuffle(categories)
    else:
        categories.sort(key=category_score, reverse=True)

    articles = []
    for category in categories:
        articles.extend(get_news(category, page=page))

    return jsonify({"articles": articles})


# 🔥 FEEDBACK — AJAX
@app.route("/feedback", methods=["POST"])
def feedback():
    data = request.get_json()

    user_id = data["user_id"]
    category = data["category"]
    action = data["action"]

    reward = 1 if action == "like" else -1

    database.save_interaction(user_id, category, action)
    database.update_preference(user_id, category, reward)
    database.log_reward(user_id, reward)

    recent = session.get("recent_categories", [])
    recent.append(category)
    session["recent_categories"] = recent[-5:]

    return jsonify({"message": "Feedback recorded"})


# 🔥 SAVE — AJAX
@app.route("/save", methods=["POST"])
def save_article():
    data = request.get_json()

    user_id = data["user_id"]
    title = data["title"]
    url = data["url"]
    category = data["category"]

    database.save_article(user_id, title, url, category)
    database.update_preference(user_id, category, reward=2)

    return jsonify({"message": "Article saved"})


@app.route("/saved/<username>")
def saved_articles(username):
    user_id = database.get_or_create_user(username)
    articles = database.get_saved_articles(user_id)
    return render_template("saved.html", username=username, articles=articles)


@app.route("/search")
def search():
    query = request.args.get("q")
    if not query:
        return redirect(url_for("login"))

    articles = get_news(query)

    return render_template(
        "home.html",
        username="Search Results",
        user_id=0,
        articles=articles,
        page=1
    )


@app.route("/metrics/<username>")
def metrics(username):
    user_id = database.get_or_create_user(username)
    rewards = database.get_reward_history(user_id)

    avg_reward = round(sum(rewards) / len(rewards), 2) if rewards else 0

    return render_template(
        "metrics.html",
        avg_reward=avg_reward,
        interactions=len(rewards),
        username=username
    )


if __name__ == "__main__":
    app.run(debug=True)


