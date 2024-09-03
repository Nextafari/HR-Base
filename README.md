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

#### Deployment Guide
Setup a free tier of AWS EC2 instance. Click on connect and choose EC2 instance connect which opens a shell session for you on the web.

```bash
sudo yum install docker git nginx
```

Install latest version of docker-compose from Github.

[Resource 1](https://stackoverflow.com/questions/63708035/installing-docker-compose-on-amazon-ec2-linux-2-9kb-docker-compose-file)
[Resource 2](https://gist.github.com/npearce/6f3c7826c7499587f00957fee62f8ee9)
```bash
sudo curl -L https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m) -o /usr/local/bin/docker-compose
```

Configure Nginx for Reverse proxy
```bash
sudo nano /etc/nginx/sites-available/myproject
```

Paste this in your conf file from above
```bash
server {
        listen 80;
        server_name your_domain or IP_address;

        location = /favicon.ico { access_log off; log_not_found off ;}
        location /static/ {
            root /path/to_your_static_files;
        }

        location / {
                proxy_pass http://localhost:port;
                proxy_http_version 1.1;
                proxy_set_header Upgrade $http_upgrade;
                proxy_set_header Connection 'upgrade';
                proxy_set_header Host $host;
                proxy_cache_bypass $http_upgrade;
        }
}
```

When done with the above run this, ensure to add this inside the http directive of Nginx's default config file (nginx.conf) as seen [here](https://github.com/Nextafari/HR-Base/blob/main/Screenshot_2024-09-03_at_18.42.06.png)
```bash
include /etc/nginx/sites-enabled/*.conf;
```

```bash
sudo ln -s /etc/nginx/sites-available/myproject /etc/nginx/sites-enabled
```

```bash
sudo nginx -t
```

```bash
sudo systemctl restart nginx
```

Build and run containers to start project
```bash
docker-compose build && docker-compose up --no-deps -d
```
