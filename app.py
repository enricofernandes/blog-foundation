from flask import Flask, render_template, request, redirect, url_for, abort, send_from_directory, Response
import markdown
import os
import sqlite3
import re
from datetime import datetime

app = Flask(__name__)

POSTS_DIR = "posts"

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

# Get single post content and date
def render_markdown_post(slug):
    path = os.path.join(POSTS_DIR, f"{slug}.md")
    if not os.path.exists(path):
        abort(404)
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    match = re.search(r'^---\s*title:\s*(.*?)\s*date:\s*(.*?)\s*---', content, re.MULTILINE | re.DOTALL)
    if match:
        content = content[match.end():].strip()
        date_str = match.group(2).strip()
        date = datetime.strptime(date_str, "%Y-%m-%d")
    else:
        date = datetime.now()

    html = markdown.markdown(content, extensions=['fenced_code'])
    return html, date

@app.route("/")
def index():
    posts = get_post_list()
    return render_template("index.html", posts=posts)

@app.route("/whitepapers")
def whitepapers():
    posts = get_post_list()
    return render_template("whitepapers.html", posts=posts)

@app.route("/post/<slug>")
def post(slug):
    content, date = render_markdown_post(slug)
    return render_template("post.html", content=content, slug=slug, date=date)

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
    app.run(debug=True)