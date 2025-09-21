const express = require('express');
const router = express.Router();
const AWS = require('aws-sdk');
const pool = require('../model/db');

// POST /api/report/generate - trigger Lambda to generate report
router.post('/generate', async (req, res) => {
  const lambda = new AWS.Lambda({ region: process.env.AWS_REGION || 'ap-southeast-1' });
  const params = {
    FunctionName: process.env.REPORT_LAMBDA_NAME || 'lambda-generate-report',
    InvocationType: 'RequestResponse',
    Payload: JSON.stringify({})
  };
  try {
    const result = await lambda.invoke(params).promise();
    const payload = JSON.parse(result.Payload);
    if (payload.status === 'success') {
      res.json({ success: true, url: payload.url });
    } else {
      res.status(500).json({ success: false, error: 'Lambda failed', details: payload });
    }
  } catch (err) {
    res.status(500).json({ success: false, error: err.message });
  }
});

// GET /api/report/list - fetch report list
router.get('/list', async (req, res) => {
  try {
    const result = await pool.query('SELECT * FROM reports ORDER BY created_at DESC');
    res.json({ reports: result.rows });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;
