# backend/app.py
from flask import Flask, jsonify, send_from_directory, send_file
from flask_cors import CORS
from data_analysis import compute_insights
from pathlib import Path

app = Flask(__name__, static_folder="../frontend", static_url_path="/")
CORS(app)  # Enable CORS for API calls

ROOT = Path(__file__).resolve().parent.parent

# Endpoint: compute insights (runs analysis and returns JSON)
@app.route("/api/insights", methods=["GET"])
def api_insights():
    try:
        result = compute_insights()
        return jsonify(result["avg_macros"])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Endpoint: get top recipes
@app.route("/api/recipes", methods=["GET"])
def api_recipes():
    try:
        result = compute_insights()
        return jsonify(result["top5"])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Endpoint: get clusters
@app.route("/api/clusters", methods=["GET"])
def api_clusters():
    try:
        result = compute_insights()
        return jsonify(result["most_common_cuisines"])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# NEW: Serve plot images
@app.route("/api/plots/<filename>", methods=["GET"])
def get_plot(filename):
    try:
        plot_path = ROOT / "outputs" / "plots" / filename
        return send_file(plot_path, mimetype='image/png')
    except Exception as e:
        return jsonify({"error": str(e)}), 404

# Serve frontend index.html
@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
