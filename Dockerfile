# Flask App Dockerfile

# Use an official Python 3.11 runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install any needed packages specified in requirements.txt
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . /app

# Copy .env file
COPY .env /app

# Make port 80 available to the world outside this container
EXPOSE 80

# Run run.py when the container launches
CMD ["python", "run.py"]
