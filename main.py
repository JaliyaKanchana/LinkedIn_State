from flask import Flask, jsonify, request
import json
from linkedIn import master

app = Flask(__name__)

@app.route("/scrape", methods=["POST"])
def api_scrape():
    content = request.json
    # Expecting "profile_urls" to be a list of URLs.
    profile_urls = content.get("profile_urls")

    if not profile_urls:
        return jsonify({"error": "Profile URL list is required."}), 400

    try:
        # Now passing a dictionary with "profile_urls" as expected by the master function.
        data = master({"profile_urls": profile_urls})
        return jsonify(data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
