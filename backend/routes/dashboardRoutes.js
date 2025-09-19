const express = require('express');
const router = express.Router();
const pool = require('../model/db');

function ensureAuthenticated(req, res, next) {
  if (req.session.user) return next();
  res.status(401).json({ error: "Unauthorized" });
}

// Get organization-specific data
router.get('/data', ensureAuthenticated, async (req, res) => {
  const orgId = req.session.user.organization_id;
  try {
    const result = await pool.query("SELECT * FROM orders WHERE organization_id=$1", [orgId]);
    res.json(result.rows);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Server error" });
  }
});

module.exports = router;
