const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const dotenv = require('dotenv');
const authRoutes = require('./src/routes/authRoutes');

dotenv.config();

const app = express();

app.use(cors());
app.use(express.json());

// Routes
app.use('/api/auth', authRoutes);

// Health check
app.get('/health', (req, res) => res.json({ status: 'OK', mongo: mongoose.connection.readyState === 1 }));

const PORT = process.env.PORT || 5000;
const MONGO_URI = process.env.MONGO_URI || 'mongodb://localhost:27017/careunify';

console.log('--- CareUnify Auth Service Starting ---');
console.log(`Connecting to: ${MONGO_URI}`);

mongoose.connect(MONGO_URI)
  .then(() => {
    console.log('✅ Connected to MongoDB');
  })
  .catch(err => {
    console.error('❌ MongoDB Connection Error!');
    console.error('Ensure MongoDB is installed and running on default port 27017.');
    console.error('Logic: The server will continue running but Auth will fail until DB is active.');
  });

app.listen(PORT, () => {
    console.log(`🚀 Auth Service listening on port ${PORT}`);
});
