from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from db_service import PostgresService
import pandas as pd
from io import BytesIO

app = Flask(__name__)
CORS(app)

db = PostgresService()

@app.route("/contacts", methods=["GET"])
def get_all_contacts():
    return jsonify(db.fetch_all_contacts())

@app.route("/contacts/<int:contact_id>", methods=["GET"])
def get_contact(contact_id):
    contact = db.fetch_contact_by_id(contact_id)
    if contact:
        return jsonify(contact)
    return jsonify({"error": "Contact not found"}), 404

@app.route("/contacts", methods=["POST"])
def create_contact():
    data = request.get_json()
    new_id = db.insert_contact(data)
    data["id"] = new_id
    return jsonify(data), 201

@app.route("/contacts/<int:contact_id>", methods=["PUT"])
def update_contact(contact_id):
    data = request.get_json()
    db.update_contact(contact_id, data)
    return jsonify({"message": "Contact updated"})

@app.route("/contacts/<int:contact_id>", methods=["DELETE"])
def delete_contact(contact_id):
    db.delete_contact(contact_id)
    return jsonify({"message": "Contact deleted"})

@app.route("/contacts/import", methods=["POST"])
def import_contacts():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded."}), 400

    file = request.files['file']
    try:
        df = pd.read_excel(file)
        required_cols = {"First Name", "Last Name", "Email", "Phone", "Company", "Notes"}
        if not required_cols.issubset(df.columns):
            return jsonify({"error": "Missing required columns in Excel."}), 400

        inserted = 0
        for _, row in df.iterrows():
            contact = {
                "firstName": row["First Name"],
                "lastName": row["Last Name"],
                "email": row["Email"],
                "phone": str(row["Phone"]),
                "company": row.get("Company", ""),
                "notes": row.get("Notes", "")
            }
            db.insert_contact(contact)
            inserted += 1

        return jsonify({"message": f"Imported {inserted} contacts from Excel."})
    except Exception as e:
        return jsonify({"error": f"Failed to process Excel file: {str(e)}"}), 500

@app.route("/contacts/export", methods=["GET"])
def export_contacts():
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

if __name__ == "__main__":
    app.run(debug=True)
