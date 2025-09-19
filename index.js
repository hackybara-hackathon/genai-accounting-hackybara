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

// Serve frontend
app.use(express.static(path.join(__dirname, 'frontend')));

app.listen(PORT, () => {
  console.log(`✅ Server running at http://localhost:${PORT}`);
});
