const express = require('express');
const router = express.Router();
const pool = require('../model/db');

router.get('/current', async (req, res) => {
  if (!req.session.user) return res.status(401).json({ error: "Unauthorized" });

  try {
    const orgResult = await pool.query(
      "SELECT name FROM organizations WHERE id = $1",
      [req.session.user.organization_id]
    );
    const organization = orgResult.rows[0];

    res.json({
      user: {
        id: req.session.user.id,
        name: req.session.user.name,
        email: req.session.user.email,
        organization_id: req.session.user.organization_id,
        role: req.session.user.role,
        organization_name: organization.name
      }
    });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Server error" });
  }
});

module.exports = router;
