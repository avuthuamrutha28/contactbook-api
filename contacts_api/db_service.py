import os
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

class PostgresService:
    def __init__(self):
        self.conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            port=os.getenv("DB_PORT", "5432")
        )
        self.conn.autocommit = True
        self.cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    def fetch_all_contacts(self):
        self.cur.execute("SELECT * FROM contacts ORDER BY id")
        return self.cur.fetchall()

    def fetch_contact_by_id(self, contact_id):
        self.cur.execute("SELECT * FROM contacts WHERE id = %s", (contact_id,))
        return self.cur.fetchone()

    def insert_contact(self, contact):
        self.cur.execute("""
            INSERT INTO contacts (first_name, last_name, email, phone, company, notes)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            contact["firstName"],
            contact["lastName"],
            contact["email"],
            contact["phone"],
            contact.get("company", ""),
            contact.get("notes", "")
        ))
        return self.cur.fetchone()["id"]

    def update_contact(self, contact_id, contact):
        self.cur.execute("""
            UPDATE contacts
            SET first_name = %s,
                last_name = %s,
                email = %s,
                phone = %s,
                company = %s,
                notes = %s
            WHERE id = %s
        """, (
            contact["firstName"],
            contact["lastName"],
            contact["email"],
            contact["phone"],
            contact.get("company", ""),
            contact.get("notes", ""),
            contact_id
        ))

    def delete_contact(self, contact_id):
        self.cur.execute("DELETE FROM contacts WHERE id = %s", (contact_id,))

    def contact_exists(self, email, phone):
        self.cur.execute(
            "SELECT 1 FROM contacts WHERE email = %s AND phone = %s LIMIT 1",
            (email, phone)
        )
        return self.cur.fetchone() is not None

    def validate_admin(self, email, password):
        self.cur.execute(
            "SELECT * FROM admins WHERE email = %s AND password = %s",
            (email, password)
        )
        return self.cur.fetchone()

