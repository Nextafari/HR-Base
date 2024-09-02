# HR-Base

#### Overview
HR Base is an HR Tool for job management and organization administration written in Django. It provides various functionalities for users, organizations and job listings.

This application is ideal for organizations that need a simple web-based solution for managing staff, job posting, and job applications. It servers as a basic HR managment tool facilitating internal and external recruitment processes while maintaining control over organization-specific data.

#### Run application locally

Build docker containers
```bash
docker-compose build && docker-compose up --no-deps -d 
```

View server logs
```bash
docker logs -f app
```

terminate server logs and return back to shell
```bash
ctrl + c
```

terminate all running containers
```bash
docker-compose down --remove-orphans 
```
