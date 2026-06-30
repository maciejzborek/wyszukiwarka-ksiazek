#!/bin/bash
set -e

# Update system
yum update -y

# Install Docker
yum install -y docker
systemctl enable docker
systemctl start docker

# Add ec2-user to docker group (allows running docker without sudo)
usermod -aG docker ec2-user

# Install Docker Compose plugin (v2)
mkdir -p /usr/local/lib/docker/cli-plugins
curl -SL https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64 \
     -o /usr/local/lib/docker/cli-plugins/docker-compose
chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

# Install AWS CLI (pre-installed on AL2023, this ensures it's current)
yum install -y aws-cli

# Create app directory and pull config files from GitHub
mkdir -p /opt/book-search-api
chown ec2-user:ec2-user /opt/book-search-api

GITHUB_RAW="https://raw.githubusercontent.com/maciejzborek/wyszukiwarka-ksiazek/main"
curl -fsSL "$GITHUB_RAW/docker-compose.prod.yml" -o /opt/book-search-api/docker-compose.prod.yml
curl -fsSL "$GITHUB_RAW/nginx/nginx.conf"        -o /opt/book-search-api/nginx.conf
chown ec2-user:ec2-user /opt/book-search-api/*

# Install CloudWatch agent for log collection
yum install -y amazon-cloudwatch-agent

cat > /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json << 'EOF'
{
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/lib/docker/containers/**/*-json.log",
            "log_group_name": "/ec2/book-search-api",
            "log_stream_name": "{instance_id}",
            "timestamp_format": "%Y-%m-%dT%H:%M:%S"
          }
        ]
      }
    }
  }
}
EOF

systemctl enable amazon-cloudwatch-agent
systemctl start amazon-cloudwatch-agent
