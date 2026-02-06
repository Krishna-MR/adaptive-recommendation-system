from flask import Flask, render_template, request, redirect, url_for, session
from news_service import get_news
import database
import random

app = Flask(__name__)
app.secret_key = "adaptive-recommendation-secret"

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

    # 🔹 SESSION AWARENESS
    recent_categories = session.get("recent_categories", [])

    # 🔹 GLOBAL TRENDS
    global_scores = database.get_global_category_scores()

    def category_score(category):
        base = preferences.get(category, 0)
        recent = recent_categories.count(category) * 0.5
        global_boost = global_scores.get(category, 0)
        return base + recent + global_boost

    # 🔹 EPSILON-GREEDY
    epsilon = 0.2
    if random.random() < epsilon:
        random.shuffle(categories)
    else:
        categories.sort(key=category_score, reverse=True)

    # 🔹 EXPLAINABILITY
    category_explanations = {}
    for category in categories:
        category_explanations[category] = {
            "base": round(preferences.get(category, 0), 2),
            "recent": round(recent_categories.count(category) * 0.5, 2),
            "global": round(global_scores.get(category, 0), 2),
        }

    # 🔹 FETCH NEWS (FIXED)
    articles = []
    for category in categories:
        articles.extend(get_news(category, page=page))

    return render_template(
        "home.html",
        username=username,
        user_id=user_id,
        articles=articles,
        page=page,
        explanations=category_explanations
    )


@app.route("/feedback", methods=["POST"])
def feedback():
    user_id = int(request.form["user_id"])
    category = request.form["category"]
    action = request.form["action"]

    reward = 1 if action == "like" else -1

    database.save_interaction(user_id, category, action)
    database.update_preference(user_id, category, reward)
    database.log_reward(user_id, reward)

    recent = session.get("recent_categories", [])
    recent.append(category)
    session["recent_categories"] = recent[-5:]

    return redirect(request.referrer)


@app.route("/save", methods=["POST"])
def save_article():
    user_id = int(request.form["user_id"])
    category = request.form["category"]

    database.save_article(
        user_id,
        request.form["title"],
        request.form["url"],
        category
    )

    database.update_preference(user_id, category, reward=2)

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

    articles = get_news(query, page=1)

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

