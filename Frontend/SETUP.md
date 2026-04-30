# Golf Shot Analysis - React Frontend

Your React frontend is now ready to connect to the FastAPI backend!

## ✅ Project Setup Complete

This project was scaffolded with **Vite + React 19** and includes:
- ⚡ Fast development server with Hot Module Replacement (HMR)
- 🔗 Pre-configured API client for backend communication
- 📦 Production-ready build configuration
- 🌐 Backend proxy setup for local development

## 🚀 Getting Started

### 1. Start the Frontend Development Server

```bash
cd Frontend
npm run dev
```

The app will be available at `http://localhost:5173`

### 2. Start Your Backend (in another terminal)

```bash
cd Backend
source venv/bin/activate
python -m uvicorn api.main:app --reload
```

Backend will be at `http://localhost:8000`

### 3. Check Backend Status

The app automatically checks if the backend is running on startup. You'll see a status indicator at the top showing:
- ✅ Connected (green) - Backend is running
- ❌ Disconnected (red) - Backend is not reachable

## 📁 File Structure

```
Frontend/
├── src/
│   ├── App.jsx              # Main app component (edit this!)
│   ├── App.css              # App styles
│   ├── main.jsx             # Entry point
│   └── services/
│       └── api.js           # API client for backend communication
├── public/                  # Static assets
├── index.html               # HTML template
├── vite.config.js           # Vite configuration (includes API proxy)
├── .env                     # Environment variables (local dev)
├── .env.development         # Dev-specific config
├── .env.production          # Production config
└── package.json             # Dependencies & scripts
```

## 🔗 Using the API Client

The API client is already set up to communicate with your backend. Here's how to use it:

### In your React components:

```javascript
import apiClient from './services/api';

// GET request
const data = await apiClient.get('/endpoint');

// POST request with data
const result = await apiClient.post('/endpoint', { key: 'value' });

// PUT request
const updated = await apiClient.put('/endpoint', { key: 'newValue' });

// DELETE request
await apiClient.delete('/endpoint');

// Health check
await apiClient.healthCheck();
```

### Environment Variables

- **Development**: `VITE_API_URL=http://localhost:8000`
- **Production**: `VITE_API_URL=/api` (proxied by your server)

Access in your code: `import.meta.env.VITE_API_URL`

## 📝 npm Scripts

```bash
npm run dev      # Start development server (port 5173)
npm run build    # Build for production (creates /dist folder)
npm run lint     # Run ESLint
npm run preview  # Preview production build locally
```

## 🛠️ Next Steps

1. **Connect to your backend endpoints** - Update the API client calls to match your FastAPI routes
2. **Build your UI** - Edit `src/App.jsx` and create new components in `src/`
3. **Create more services** - Add additional API calls in `src/services/` as needed
4. **Deploy** - Run `npm run build` and serve the `/dist` folder with your backend

## 📚 Useful Links

- [Vite Documentation](https://vite.dev/)
- [React Documentation](https://react.dev/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Your Backend API Docs](http://localhost:8000/docs) (when running)

## 🐛 Troubleshooting

### Backend not connecting?
- Make sure your FastAPI backend is running on `http://localhost:8000`
- Check that CORS is enabled on your backend (should be set up in FastAPI)
- Open browser DevTools (F12) → Network tab to see API requests

### Port already in use?
- Change the dev server port in `vite.config.js`: `server: { port: 3000 }`
- Or kill the existing process and restart

### Node version issues?
- This project requires Node 20.18+ (you have v20.18.3 ✓)
- If issues persist, run: `npm install` again

---

Happy building! 🎉
