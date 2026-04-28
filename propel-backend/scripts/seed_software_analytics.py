from seed_data import db, run_analytics_seed


if __name__ == "__main__":
    try:
        print("Software analytics demo seed baslatiliyor...\n")
        run_analytics_seed()
    finally:
        db.close()
