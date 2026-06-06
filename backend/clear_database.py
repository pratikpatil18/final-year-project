import os

from dotenv import load_dotenv

try:
    import mysql.connector
except ImportError as exc:
    raise SystemExit(
        "mysql-connector-python is not installed. Run the backend setup again before clearing data."
    ) from exc


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1").strip()
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "root").strip()
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "").strip()
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "ai_ranger").strip()


def clear_detections():
    connection = mysql.connector.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE,
    )
    cursor = connection.cursor()
    cursor.execute("DELETE FROM detection_history")
    deleted_rows = cursor.rowcount
    connection.commit()
    cursor.close()
    connection.close()
    print(f"Successfully deleted {deleted_rows} detection history rows.")


if __name__ == "__main__":
    clear_detections()
