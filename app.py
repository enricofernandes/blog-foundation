from flask import Flask, render_template, request, redirect, url_for, abort, send_from_directory, Response
import markdown
import os
import sqlite3
import re
from datetime import datetime

app = Flask(__name__)

POSTS_DIR = "posts"
DB_PATH = "comments.db"

# Initialize DB
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS comments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    slug TEXT NOT NULL,
                    author TEXT NOT NULL,
                    body TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                 )''')
    conn.commit()
    conn.close()

# Get all posts
def get_post_list():
    posts = []
    for filename in sorted(os.listdir(POSTS_DIR)):
        if filename.endswith(".md"):
            path = os.path.join(POSTS_DIR, filename)
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()

            match = re.search(r'^---\s*title:\s*(.*?)\s*date:\s*(.*?)\s*---', content, re.MULTILINE | re.DOTALL)
            if match:
                title = match.group(1).strip()
                date_str = match.group(2).strip()
                date = datetime.strptime(date_str, "%Y-%m-%d")
            else:
                title = filename.replace(".md", "")
                date = datetime.now()

            slug = filename.replace(".md", "")
            posts.append({"title": title, "slug": slug, "date": date})

    posts.sort(key=lambda x: x["date"], reverse=True)
    return posts

# Get single post content
def render_markdown_post(slug):
    path = os.path.join(POSTS_DIR, f"{slug}.md")
    if not os.path.exists(path):
        abort(404)
    with open(path, 'r', encoding='utf-8') as f:
        html = markdown.markdown(f.read(), extensions=['fenced_code'])
    return html

# Fetch comments from DB
def get_comments(slug):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT author, body, created_at FROM comments WHERE slug = ? ORDER BY created_at DESC", (slug,))
    comments = c.fetchall()
    conn.close()
    return comments

# Insert new comment
def add_comment(slug, author, body):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO comments (slug, author, body) VALUES (?, ?, ?)", (slug, author, body))
    conn.commit()
    conn.close()

# Delete all comments from a slug
def delete_comments(slug):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM comments WHERE slug = ?", (slug,))
    conn.commit()
    conn.close()

@app.route("/")
def index():
    posts = get_post_list()
    return render_template("index.html", posts=posts)

@app.route("/whitepapers")
def whitepapers():
    posts = get_post_list()
    return render_template("whitepapers.html", posts=posts)

@app.route("/post/<slug>", methods=["GET", "POST"])
def post(slug):
    if request.method == "POST":
        if request.form.get("delete") == "true":
            delete_comments(slug)
            return redirect(url_for("post", slug=slug))
        author = request.form.get("author")
        body = request.form.get("body")
        if author and body:
            add_comment(slug, author, body)
            return redirect(url_for("post", slug=slug))
    content = render_markdown_post(slug)
    comments = get_comments(slug)
    return render_template("post.html", content=content, slug=slug, comments=comments)

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/robots.txt")
def robots():
    return send_from_directory("static", "robots.txt")

@app.route("/rss.xml")
def rss():
    posts = get_post_list()
    feed_items = ""
    for post in posts:
        pub_date = post["date"].strftime("%a, %d %b %Y %H:%M:%S +0000")
        feed_items += f"""
            <item>
                <title>{post['title']}</title>
                <link>https://rosadafernandes.com.br/post/{post['slug']}</link>
                <pubDate>{pub_date}</pubDate>
            </item>
        """

    rss_feed = f"""<?xml version="1.0" encoding="UTF-8" ?>
    <rss version="2.0">
    <channel>
        <title>Rosada Fernandes Blog</title>
        <link>https://rosadafernandes.com.br</link>
        <description>White Papers em Ciência da Computação</description>
        {feed_items}
    </channel>
    </rss>"""

    return Response(rss_feed, mimetype='application/rss+xml')

if __name__ == "__main__":
    init_db()
    app.run(debug=True)