FROM apache/airflow:2.9.2-python3.11

# Install system-level dependencies as root
USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       git \
       fonts-liberation \
       libnss3 \
       libxss1 \
       libatk1.0-0 \
       libatk-bridge2.0-0 \
       libcups2 \
       libdrm2 \
       libxkbcommon0 \
       libxcomposite1 \
       libxdamage1 \
       libxfixes3 \
       libxrandr2 \
       libgbm1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages and Playwright browser as the airflow user
USER airflow
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt \
    && playwright install chromium

# Install Playwright system deps back as root, then restore user
USER root
RUN /home/airflow/.local/bin/playwright install-deps chromium
USER airflow
