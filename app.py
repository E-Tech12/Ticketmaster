from flask import Flask, render_template, jsonify
import requests
import os

app = Flask(__name__)

TICKETMASTER_API_KEY = "03US815ciVS9pnXYWG4XUd9oAvRiMAUV"

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/search")
def search_events():

    url = f"https://app.ticketmaster.com/discovery/v2/events.json?keyword=BTS&apikey={TICKETMASTER_API_KEY}"

    response = requests.get(url)
    data = response.json()

    events = []

    if "_embedded" in data:
        for event in data["_embedded"]["events"]:
            events.append({
                "name": event["name"],
                "date": event["dates"]["start"]["localDate"],
                "image": event["images"][0]["url"]
            })

    return jsonify(events)

if __name__ == "__main__":
    app.run(debug=True)