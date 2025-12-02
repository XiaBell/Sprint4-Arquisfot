const express = require('express');
const jwt = require('jsonwebtoken');
const jwksClient = require('jwks-rsa');
const cors = require('cors');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());

// Auth0 Configuration
const AUTH0_DOMAIN = process.env.AUTH0_DOMAIN;
const AUTH0_AUDIENCE = process.env.AUTH0_AUDIENCE;

// JWKS Client for Auth0
const client = jwksClient({
  jwksUri: `https://${AUTH0_DOMAIN}/.well-known/jwks.json`
});

// Function to get signing key
function getKey(header, callback) {
  client.getSigningKey(header.kid, (err, key) => {
    const signingKey = key.publicKey || key.rsaPublicKey;
    callback(null, signingKey);
  });
}

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'ok', service: 'auth-service' });
});

// Validate token endpoint
app.post('/api/v1/auth/validate', async (req, res) => {
  try {
    const { token } = req.body;

    if (!token) {
      return res.status(400).json({
        isValid: false,
        error: 'Token is required'
      });
    }

    // Verify and decode JWT
    jwt.verify(token, getKey, {
      audience: AUTH0_AUDIENCE,
      issuer: `https://${AUTH0_DOMAIN}/`,
      algorithms: ['RS256']
    }, (err, decoded) => {
      if (err) {
        return res.status(401).json({
          isValid: false,
          error: err.message
        });
      }

      // Extract role from custom claim
      const rol = decoded['https://provesi.com/rol'] || decoded.rol || null;
      const userId = decoded.sub || decoded.user_id || null;

      res.json({
        isValid: true,
        rol: rol,
        userId: userId,
        email: decoded.email || null,
        decoded: {
          sub: decoded.sub,
          aud: decoded.aud,
          iss: decoded.iss,
          exp: decoded.exp,
          iat: decoded.iat
        }
      });
    });
  } catch (error) {
    console.error('Error validating token:', error);
    res.status(500).json({
      isValid: false,
      error: 'Internal server error'
    });
  }
});

// Decode token endpoint (without verification, for debugging)
app.post('/api/v1/auth/decode', (req, res) => {
  try {
    const { token } = req.body;

    if (!token) {
      return res.status(400).json({
        error: 'Token is required'
      });
    }

    // Decode without verification (for debugging only)
    const decoded = jwt.decode(token, { complete: true });
    
    res.json({
      decoded: decoded
    });
  } catch (error) {
    console.error('Error decoding token:', error);
    res.status(500).json({
      error: 'Internal server error'
    });
  }
});

app.listen(PORT, () => {
  console.log(`Auth Service running on port ${PORT}`);
  console.log(`Auth0 Domain: ${AUTH0_DOMAIN}`);
  console.log(`Auth0 Audience: ${AUTH0_AUDIENCE}`);
});

