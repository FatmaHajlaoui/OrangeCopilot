import pymysql
from main import create_app
from main.user_managment.services.user_service import UserService
from main.utils.extensions import db

app = create_app()


@app.before_first_request
def initialize():
    # Create database if it doesn't exist
    conn = pymysql.connect(
    host='localhost',
    user='root',
    password='Mysql@2026'
)
    cursor = conn.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS projet_pfe")
    conn.commit()
    conn.close()

    # Create database tables if they don't exist
    db.create_all()

    # add default admin account
    UserService.add_default_admin_user()


if __name__ == "__main__":
    app.run(host="localhost", debug=True)
