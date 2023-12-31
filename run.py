from app import create_app

app = create_app()

if __name__ == "__main__":
    # Azure will set the environment variable PORT to 8000
    app.run(host='0.0.0.0', port=8000)

    # Localhost
    # app.run()
