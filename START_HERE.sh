#!/bin/bash

echo "=========================================="
echo "Sentra Google OAuth2 Setup"
echo "=========================================="
echo ""

# Step 1: Install backend dependencies
echo "Step 1: Installing backend dependencies..."
cd BackendAPI
pip install -r requirements.txt
echo "✅ Backend dependencies installed"
echo ""

# Step 2: Setup database
echo "Step 2: Setting up authentication database..."
python setup_auth_database.py
echo ""

# Step 3: Install frontend dependencies
echo "Step 3: Installing frontend dependencies..."
cd ../Frontend
npm install
echo "✅ Frontend dependencies installed"
echo ""

echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Start backend:  cd BackendAPI && python Agent_Trigger.py"
echo "2. Start frontend: cd Frontend && npm run dev"
echo "3. Open browser: http://localhost:5173"
echo "4. Click 'Sign in with Google'"
echo ""
