from app import create_app
import os

app = create_app()

if __name__ == "__main__":
    if os.getenv('FLASK_DEBUG') == 'production':
        # Azure deployment
        port = int(os.environ.get('PORT', 8000))
        app.run(host='0.0.0.0', port=port)
    else:
        # Local development
        app.run(debug=True)
