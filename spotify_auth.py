import multiprocessing
import os
import string

from random import SystemRandom

from dotenv import load_dotenv
from flask import Flask, render_template, redirect, request
from waitress import serve

set = string.ascii_letters + string.digits
state = None
load_dotenv()
app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login")
def login():
    gen = SystemRandom()
    global state
    state = "".join(gen.choices(set, k=16))
    params = "response_type=code" \
             f"&client_id={os.getenv('client_id')}" \
             "&scope=playlist-read-private playlist-read-collaborative" \
             "&redirect_uri=http%3A%2F%2Flocalhost%3A6969%2Fcallback" \
             f"&state={state}"
    return redirect("https://accounts.spotify.com/en/authorize?" + params)


@app.route("/callback")
def callback():
    args = request.args
    try:
        global state
        code = args["code"]
        if args["state"] != state:
            return render_template("error.html", error="State does not match.")
        else:
            queue.put(code)
            return render_template("success.html")
    except KeyError:
        error = args["error"]
        return render_template("error.html", error=error)


def run(q: multiprocessing.Queue):
    global queue
    queue = q
    serve(app, port=6969)  # 8080 already being used, 8888 jupyter server
