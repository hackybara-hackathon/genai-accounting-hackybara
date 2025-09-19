const express = require('express');
const router = express.Router();
const bcrypt = require('bcrypt');
const pool = require('../model/db');

// Registration endpoint
router.post('/', async (req, res) => {
  const { businessName, userName, email, password, confirmPassword } = req.body;

  // Basic validations
  if (!businessName || !userName || !email || !password || !confirmPassword) {
    return res.status(400).json({ error: "All fields are required" });
  }

  if (password !== confirmPassword) {
    return res.status(400).json({ error: "Passwords do not match" });
  }

  try {
    // Check if business name exists
    const orgCheck = await pool.query(
      "SELECT * FROM organizations WHERE name = $1",
      [businessName]
    );
    if (orgCheck.rows.length > 0) {
      return res.status(400).json({ error: "Business name already exists" });
    }

    // Check if email exists
    const emailCheck = await pool.query(
      "SELECT * FROM users WHERE email = $1",
      [email]
    );
    if (emailCheck.rows.length > 0) {
      return res.status(400).json({ error: "Email already exists" });
    }

    // Hash the password
    const hashedPassword = await bcrypt.hash(password, 10);

    // Insert organization
    const orgInsert = await pool.query(
      "INSERT INTO organizations (name) VALUES ($1) RETURNING id",
      [businessName]
    );
    const organizationId = orgInsert.rows[0].id;

    // Insert user
    await pool.query(
      "INSERT INTO users (organization_id, name, email, password) VALUES ($1, $2, $3, $4)",
      [organizationId, userName, email, hashedPassword]
    );

    res.status(201).json({ message: "Registration successful" });

  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Server error" });
  }
});

module.exports = router;
