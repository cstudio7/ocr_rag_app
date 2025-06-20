#!/bin/bash

# Check if Node.js and npm are installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js and npm first."
    echo "Visit https://nodejs.org/ to download and install Node.js."
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install npm first."
    echo "npm usually comes with Node.js installation."
    exit 1
fi

# Navigate to frontend directory
cd frontend

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Build React app
echo "🔨 Building React app..."
npm run build

# Return to root directory
cd ..

echo "✅ React build complete! The app is ready to be served by Flask."
