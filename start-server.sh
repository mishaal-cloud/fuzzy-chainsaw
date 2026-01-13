#!/bin/bash
# Simple HTTP server to run the SSR web tool

echo "🚀 Starting Semantic Similarity Rating (SSR) Web Tool..."
echo ""
echo "The app will be available at:"
echo "  → http://localhost:8080"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python3 -m http.server 8080
