// index.js
const express = require('express');
const session = require('express-session');
const cors = require('cors');
const path = require('path');
const dotenv = require('dotenv');
//const pool = require('/backend/model/db');
dotenv.config();

const app = express();
const PORT = process.env.PORT || 5000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(session({
  secret: '&483fkdnik43i#9458fkdjgdfg5435',
  resave: false,
  saveUninitialized: false,
  cookie: { maxAge: 1000*60*60*24 }, // 1 day
}));


// API routes
const userRoutes = require('./backend/routes/userRoutes');
const registerRoutes = require('./backend/routes/registerRoutes');
const loginRoutes = require('./backend/routes/loginRoutes');
const authRoutes = require('./backend/routes/authRoutes');
const logoutRoutes = require('./backend/routes/logoutRoutes');
const dashboardRoutes = require('./backend/routes/dashboardRoutes');
const settingRoutes = require('./backend/routes/settingRoutes');

app.use('/api/users', userRoutes);
app.use('/api/register', registerRoutes);
app.use('/api/login', loginRoutes);
app.use('/api/auth', authRoutes);
app.use('/api/logout', logoutRoutes);
app.use('/api/dashboard', dashboardRoutes);
app.use('/api/settings', settingRoutes);

// Serve static files from layout directory as root
app.use(express.static(path.join(__dirname, 'frontend', 'layout')));

// Serve JS and CSS from frontend root
app.use('/js', express.static(path.join(__dirname, 'frontend', 'js')));
app.use('/css', express.static(path.join(__dirname, 'frontend', 'css')));

// Root route - serve the main page
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'frontend', 'layout', 'index.html'));
});

// Serve specific HTML components that are being requested
app.get('/navbar.html', (req, res) => {
  res.sendFile(path.join(__dirname, 'frontend', 'layout', 'navbar.html'));
});

app.get('/sidebar.html', (req, res) => {
  res.sendFile(path.join(__dirname, 'frontend', 'layout', 'sidebar.html'));
});

app.listen(PORT, () => {
  console.log(`✅ Server running at http://localhost:${PORT}`);
});
