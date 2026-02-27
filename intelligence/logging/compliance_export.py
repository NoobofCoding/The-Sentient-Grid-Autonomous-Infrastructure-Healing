import csv
import sqlite3


def export_to_csv(db_path="audit.db", output_file="compliance_report.csv"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM events")
    rows = cursor.fetchall()

    with open(output_file, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerows(rows)

    conn.close()