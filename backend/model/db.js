// models/db.js
const { Pool } = require('pg');
require('dotenv').config();

const pool = new Pool({
  user: "postgres",
  host: "hackybara-accounting.cteao02mo068.ap-southeast-1.rds.amazonaws.com",
  database: "postgres",
  password: "hackybara4321",
  port: 5432,
  ssl: {
  require: true,
  rejectUnauthorized: false,
}
});

module.exports = pool;
