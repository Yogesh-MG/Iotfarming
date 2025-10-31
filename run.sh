echo "Running medical2 application..."
echo "Select an option:/n 1. web/n 2. mobile apk/n 3. Deploy application"
read option
if [ "$option" = "1" ]; then
  echo "Starting web application..."
  chmod +x web.sh
  ./web.sh
elif [ "$option" = "2" ]; then
  echo "Starting mobile application..."
  chmod +x app.sh
  ./app.sh
elif [ "$option" = "3" ]; then
  echo "Starting Docker application..."
  #docker build -t mtorch:latest -f Dockerfile.Mtorch .
  docker-compose build
  docker-compose up -d
  docker-compose exec backend python manage.py migrate
  docker-compose exec backend python manage.py createsuperuser
else
  echo "Invalid option. Please select either 1 or 2."
fi


