# React-Flask Integration

This template provides integration between React frontend and Flask backend.

## Configuration

1. **Frontend**: Update `src/utils/api.js` with correct API URL
2. **Backend**: Ensure CORS is enabled in `app.py`
3. **Environment**: Set `VITE_API_URL` in frontend `.env` file

## Connection Flow

1. Frontend makes API calls via `axios` to `/api/*` endpoints
2. Vite proxy forwards to `http://localhost:5000`
3. Flask backend handles requests and returns JSON

