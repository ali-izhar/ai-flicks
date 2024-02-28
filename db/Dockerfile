# MongoDB Dockerfile

# Use the official MongoDB image
FROM mongo:latest

# Copy the custom MongoDB configuration file into the container
COPY mongod.conf /etc/mongo/mongod.conf

# Expose the default MongoDB port
EXPOSE 27017

# Start the MongoDB server with the custom configuration file
CMD ["mongod", "--config", "/etc/mongo/mongod.conf"]
