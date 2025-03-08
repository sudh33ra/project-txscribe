FROM mongo:latest

COPY init.js /docker-entrypoint-initdb.d/
COPY wait-for-mongodb.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/wait-for-mongodb.sh

ENV MONGO_INITDB_ROOT_USERNAME=admin
ENV MONGO_INITDB_ROOT_PASSWORD=admin_password

CMD ["wait-for-mongodb.sh"] 