from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from db_service import PostgresService
import pandas as pd
from io import BytesIO

app = Flask(__name__)
CORS(app)

# Initialize DB
try:
    db = PostgresService()
    print("✅ Connected to database")
except Exception as e:
    print("❌ DB connection failed:", e)

@app.route("/contacts", methods=["GET"])
def get_all_contacts():
    try:
        return jsonify(db.fetch_all_contacts())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/contacts/<int:contact_id>", methods=["GET"])
def get_contact(contact_id):
    try:
        contact = db.fetch_contact_by_id(contact_id)
        if contact:
            return jsonify(contact)
        return jsonify({"error": "Contact not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/contacts", methods=["POST"])
def create_contact():
    try:
        data = request.get_json()
        new_id = db.insert_contact(data)
        data["id"] = new_id
        return jsonify(data), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/contacts/<int:contact_id>", methods=["PUT"])
def update_contact(contact_id):
    try:
        data = request.get_json()
        db.update_contact(contact_id, data)
        return jsonify({"message": "Contact updated"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/contacts/<int:contact_id>", methods=["DELETE"])
def delete_contact(contact_id):
    try:
        db.delete_contact(contact_id)
        return jsonify({"message": "Contact deleted"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/contacts/import", methods=["POST"])
def import_contacts():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded."}), 400

    file = request.files['file']
    try:
        df = pd.read_excel(file)
        df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]

        required_cols = {"first_name", "last_name", "email", "phone", "company", "notes"}
        if not required_cols.issubset(df.columns):
            missing = required_cols - set(df.columns)
            return jsonify({
                "error": f"Missing required columns: {', '.join(missing)}",
                "columns_found": list(df.columns)
            }), 400

        inserted = 0
        skipped = 0
        for _, row in df.iterrows():
            contact = {
                "firstName": str(row.get("first_name", "")).strip(),
                "lastName": str(row.get("last_name", "")).strip(),
                "email": str(row.get("email", "")).strip(),
                "phone": str(row.get("phone", "")).strip(),
                "company": str(row.get("company", "")).strip(),
                "notes": str(row.get("notes", "")).strip(),
            }
            if db.contact_exists(contact["email"], contact["phone"]):
                skipped += 1
                continue
            db.insert_contact(contact)
            inserted += 1

        return jsonify({"message": f"Imported {inserted} contacts.", "skipped": skipped})

    except Exception as e:
        return jsonify({"error": f"Failed to process Excel file: {str(e)}"}), 500

@app.route("/contacts/export", methods=["GET"])
def export_contacts():
    try:
        contacts = db.fetch_all_contacts()
        if not contacts:
            return jsonify({"error": "No contacts to export"}), 400

        df = pd.DataFrame(contacts)
        df.rename(columns={
            "first_name": "First Name",
            "last_name": "Last Name",
            "email": "Email",
            "phone": "Phone",
            "company": "Company",
            "notes": "Notes"
        }, inplace=True)

        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Contacts')
        output.seek(0)

        return send_file(
            output,
            as_attachment=True,
            download_name="contacts.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        return jsonify({"error": f"Failed to export contacts: {str(e)}"}), 500


@app.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "Missing request data"}), 400

        email = data.get("username")
        password = data.get("password")

        if not email or not password:
            return jsonify({"success": False, "message": "Email and password required"}), 400

        admin = db.validate_admin(email, password)
        if admin:
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "message": "Invalid credentials"}), 401
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
