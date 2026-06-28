from flask import Flask, render_template, jsonify, request, send_file
from datetime import datetime

from database import (
    init_db,
    seed_database_if_empty,
    get_all_clients,
    get_client_detail,
    create_client,
    save_report_history
)
from pdf_report import build_report_pdf

app = Flask(__name__)

# Initialize SQLite database when the app starts
init_db()
seed_database_if_empty()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/clients", methods=["GET"])
def api_clients():
    return jsonify(get_all_clients())


@app.route("/api/clients", methods=["POST"])
def api_create_client():
    data = request.get_json() or {}

    household_name = data.get("householdName", "").strip()
    client1_name = data.get("client1Name", "").strip()

    if not household_name:
        return jsonify({"error": "Household name is required."}), 400

    if not client1_name:
        return jsonify({"error": "Client 1 name is required."}), 400

    try:
        client_id = create_client(data)

        return jsonify({
            "message": "Client created successfully.",
            "clientId": client_id
        }), 201

    except Exception as error:
        print("Create client error:", error)
        return jsonify({
            "error": "Failed to create client."
        }), 500


@app.route("/api/clients/<int:client_id>")
def api_client_detail(client_id):
    client_detail = get_client_detail(client_id)

    if client_detail is None:
        return jsonify({"error": "Client not found"}), 404

    return jsonify(client_detail)


@app.route("/api/generate-pdf", methods=["POST"])
def generate_pdf():
    data = request.get_json() or {}

    buffer, history = build_report_pdf(data)

    client_id = data.get("clientId")
    if client_id:
        save_report_history(client_id, history)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="aw-client-sacs-tcc-report.pdf",
        mimetype="application/pdf"
    )


if __name__ == "__main__":
    app.run(debug=False)
