from flask import Flask, render_template, request, redirect, url_for, abort
import markdown
import os
import sqlite3

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
    for filename in sorted(os.listdir(POSTS_DIR), reverse=True):
        if filename.endswith(".md"):
            path = os.path.join(POSTS_DIR, filename)
            with open(path, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip().replace("# ", "")
            slug = filename.replace(".md", "")
            posts.append({"title": first_line, "slug": slug})
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

@app.route("/")
def index():
    posts = get_post_list()
    return render_template("index.html", posts=posts)

@app.route("/post/<slug>", methods=["GET", "POST"])
def post(slug):
    if request.method == "POST":
        author = request.form.get("author")
        body = request.form.get("body")
        if author and body:
            add_comment(slug, author, body)
            return redirect(url_for("post", slug=slug))
    content = render_markdown_post(slug)
    comments = get_comments(slug)
    print(f"DEBUG - comments for {slug}: {comments}")  # <- Aqui está o print de debug
    return render_template("post.html", content=content, slug=slug, comments=comments)

@app.route("/about")
def about():
    return render_template("about.html")

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
