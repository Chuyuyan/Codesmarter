# CORS Configuration for React-Flask Integration

CORS_CONFIG = {
    'origins': ['http://localhost:3000', 'http://localhost:5173'],
    'methods': ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    'allow_headers': ['Content-Type', 'Authorization'],
    'supports_credentials': True
}

