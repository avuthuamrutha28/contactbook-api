from flask import Flask, request, jsonify
from flask_cors import CORS
from db_service import PostgresService

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

if __name__ == "__main__":
    app.run(debug=True)
