const express = require('express');
const router = express.Router();
const bcrypt = require('bcrypt');
const pool = require('../model/db');

router.post('/', async (req, res) => {
  const { email, password } = req.body;
  if (!email || !password) return res.status(400).json({ error: "Email & password required" });

  try {
    const result = await pool.query("SELECT * FROM users WHERE email=$1", [email]);
    if (!result.rows.length) return res.status(400).json({ error: "Invalid credentials" });

    const user = result.rows[0];
    const match = await bcrypt.compare(password, user.password);
    if (!match) return res.status(400).json({ error: "Invalid credentials" });

    // Simply overwrite session user data
    req.session.user = {
      id: user.id,
      name: user.name,
      email: user.email,
      organization_id: user.organization_id,
      role: user.role
    };

    res.json({ message: "Login successful" });

  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Server error" });
  }
});

module.exports = router;
