import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import os

load_dotenv()

class PostgresService:
    def __init__(self):
        self.connection_params = {
            "dbname": os.getenv("DB_NAME"),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
            "host": os.getenv("DB_HOST"),
            "port": os.getenv("DB_PORT")
        }

    def connect(self):
        return psycopg2.connect(**self.connection_params)

    def fetch_all_contacts(self):
        with self.connect() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM contacts ORDER BY id")
                return cur.fetchall()

    def fetch_contact_by_id(self, contact_id):
        with self.connect() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM contacts WHERE id = %s", (contact_id,))
                return cur.fetchone()

    def insert_contact(self, data):
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO contacts (first_name, last_name, email, phone, company, notes)
                    VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
                """, (
                    data.get("firstName", ""),
                    data.get("lastName", ""),
                    data.get("email", ""),
                    data.get("phone", ""),
                    data.get("company", ""),
                    data.get("notes", "")
                ))
                conn.commit()
                return cur.fetchone()[0]

    def insert_many_contacts(self, contacts):
        with self.connect() as conn:
            with conn.cursor() as cur:
                for contact in contacts:
                    cur.execute("""
                        INSERT INTO contacts (first_name, last_name, email, phone, company, notes)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        contact.get("firstName", ""),
                        contact.get("lastName", ""),
                        contact.get("email", ""),
                        contact.get("phone", ""),
                        contact.get("company", ""),
                        contact.get("notes", "")
                    ))
            conn.commit()

    def update_contact(self, contact_id, data):
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE contacts SET
                    first_name=%s, last_name=%s, email=%s, phone=%s, company=%s, notes=%s
                    WHERE id=%s
                """, (
                    data.get("firstName", ""),
                    data.get("lastName", ""),
                    data.get("email", ""),
                    data.get("phone", ""),
                    data.get("company", ""),
                    data.get("notes", ""),
                    contact_id
                ))
                conn.commit()

    def delete_contact(self, contact_id):
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM contacts WHERE id = %s", (contact_id,))
                conn.commit()
