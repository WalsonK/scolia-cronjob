# Utiliser une image Python officielle comme base
FROM python:3.12-slim

# Définir le répertoire de travail dans le conteneur
WORKDIR /app

# Copier les fichiers nécessaires dans le conteneur
COPY generate_params.py /app/
COPY datas/ /app/datas/

RUN mkdir -p datas/logs

# Ajouter un cron job pour exécuter le script tous les soirs à minuit
RUN apt-get update && apt-get install -y cron && rm -rf /var/lib/apt/lists/*
RUN echo "0 0 * * * python /app/generate_params.py" > /etc/cron.d/generate_params_cron
RUN chmod 0644 /etc/cron.d/generate_params_cron
RUN crontab /etc/cron.d/generate_params_cron

# Démarrer le service cron
CMD ["cron", "-f"]