from database import init_db, seed_database_if_empty

if __name__ == "__main__":
    init_db()
    seed_database_if_empty()
    print("Database initialized and seeded successfully.")