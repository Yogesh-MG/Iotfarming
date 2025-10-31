echo "Starting to execute the web commands"
cd frontend
if [ ! -d "node_modules" ]; then
  echo "node_modules directory not found. Installing dependencies..."
  npm install
else
  echo "node_modules directory found. Skipping npm install."
fi
npm run build
npm run preview
