from flask import Flask, render_template, jsonify, request, send_file
from io import BytesIO

from database import (
    init_db,
    seed_database_if_empty,
    get_all_clients,
    get_client_detail,
    create_client,
    create_account,
    delete_account,
    create_liability,
    delete_liability,
    save_report_history
)

from pdf_report import build_report_pdf

app = Flask(__name__)

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


@app.route("/api/clients/<int:client_id>", methods=["GET"])
def api_client_detail(client_id):
    client_detail = get_client_detail(client_id)

    if client_detail is None:
        return jsonify({"error": "Client not found"}), 404

    return jsonify(client_detail)


@app.route("/api/clients/<int:client_id>/accounts", methods=["POST"])
def api_create_account(client_id):
    data = request.get_json() or {}

    owner = data.get("owner", "").strip()
    category = data.get("category", "").strip()
    account_type = data.get("accountType", "").strip()

    if owner not in ["client1", "client2", "joint"]:
        return jsonify({"error": "Owner must be client1, client2, or joint."}), 400

    if category not in ["retirement", "non_retirement"]:
        return jsonify({"error": "Category must be retirement or non_retirement."}), 400

    if not account_type:
        return jsonify({"error": "Account type is required."}), 400

    if get_client_detail(client_id) is None:
        return jsonify({"error": "Client not found."}), 404

    try:
        account_id = create_account(client_id, data)

        return jsonify({
            "message": "Account created successfully.",
            "accountId": account_id
        }), 201

    except Exception as error:
        print("Create account error:", error)
        return jsonify({
            "error": "Failed to create account."
        }), 500


@app.route("/api/accounts/<int:account_id>", methods=["DELETE"])
def api_delete_account(account_id):
    try:
        deleted = delete_account(account_id)

        if not deleted:
            return jsonify({"error": "Account not found."}), 404

        return jsonify({
            "message": "Account deleted successfully."
        }), 200

    except Exception as error:
        print("Delete account error:", error)
        return jsonify({
            "error": "Failed to delete account."
        }), 500


@app.route("/api/clients/<int:client_id>/liabilities", methods=["POST"])
def api_create_liability(client_id):
    data = request.get_json() or {}

    liability_type = data.get("liabilityType", "").strip()

    if not liability_type:
        return jsonify({"error": "Liability type is required."}), 400

    if get_client_detail(client_id) is None:
        return jsonify({"error": "Client not found."}), 404

    try:
        liability_id = create_liability(client_id, data)

        return jsonify({
            "message": "Liability created successfully.",
            "liabilityId": liability_id
        }), 201

    except Exception as error:
        print("Create liability error:", error)
        return jsonify({
            "error": "Failed to create liability."
        }), 500


@app.route("/api/liabilities/<int:liability_id>", methods=["DELETE"])
def api_delete_liability(liability_id):
    try:
        deleted = delete_liability(liability_id)

        if not deleted:
            return jsonify({"error": "Liability not found."}), 404

        return jsonify({
            "message": "Liability deleted successfully."
        }), 200

    except Exception as error:
        print("Delete liability error:", error)
        return jsonify({
            "error": "Failed to delete liability."
        }), 500


@app.route("/api/generate-pdf", methods=["POST"])
def generate_pdf():
    data = request.get_json() or {}

    try:
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

    except Exception as error:
        print("PDF generation error:", error)
        return jsonify({
            "error": "Failed to generate PDF."
        }), 500


if __name__ == "__main__":
    app.run(debug=False)