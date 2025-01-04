from api import create_app

api = create_app()


if __name__ == "__main__":
    api.run(host="0.0.0.0", port=5001, debug=False)