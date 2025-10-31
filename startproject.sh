read -p "Enter project name: " project_name
read -p "Do you want to create a new project directory? (y/n): " create_dir

if [ "$create_dir" = "y" ]; then
    mkdir "$project_name"
    cd "$project_name"

    mkdir frontend
    mkdir backend
    mkdir app
    touch README.md
    touch .gitignore
    touch Dockerfile
    touch app.sh
    touch web.sh
    touch run.sh
    touch .env
    virtualenv venv

fi

read -p "Do you want to start creating the backend using Django? (1): do you want to push to git(2): Link github to local(3)" create_backend
if [ "$create_backend" = "1" ]; then
    source venv/script/activate
    pip install django
    cd backend
    django-admin startproject "backend" .
    read -p "Do you want to create app within the Django project? (y/n): " create_app
    if [ "$create_app" = "y" ]; then
        read -p "Enter app name: " app_name
        python manage.py startapp "$app_name"
    fi
    deactivate
    cd ..
fi

if [ "$create_backend" = "2" ]; then
    cd 
    git add .
    git commit -m "Initial commit"
fi

if [ "$create_backend" = "3" ]; then
    read -p "Enter your GitHub repository URL: " repo_url
    read -p "Enter project folder name: " project_name
    cd "$project_name"
    
    if [ -z "$(git rev-parse --is-inside-work-tree 2>/dev/null)" ]; then
        git init
    fi
    git add ..
    git commit -m "first commit"
    git branch -M main
    git remote add origin "$repo_url"
    git push -u origin main
fi

