import mysql.connector

def get_connection():
    return mysql.connector.connect(
        host="192.168.217.144",
        user="clinic_user",
        password="clinic123",
        database="ngiponch_clinic",
        port=3307
    )
