# Dockerfile cho Attacker Tools
FROM ubuntu:24.04

# Cài các công cụ tấn công DDoS (cho mục đích học tập)
RUN apt-get update && apt-get install -y \
    hping3 \
    nmap \
    curl \
    wget \
    wrk \
    siege \
    netcat-openbsd \
    iputils-ping \
    net-tools \
    python3 \
    python3-pip \
    htop \
    && apt-get clean

# Script tấn công HTTP Flood
COPY attack_scripts/ /attack_scripts/
RUN chmod +x /attack_scripts/*.sh 2>/dev/null || true

WORKDIR /attack_scripts
CMD ["bash"]
