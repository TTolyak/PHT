class Config:
    SECRET_KEY = 'd9f8c7b6a5e4d3c2b1a0f9e8d7c6b5a4d3c2b1a0f9e8d7c6b5a4d3c2b1a0f9e8d7c6'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///database.db'

    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024