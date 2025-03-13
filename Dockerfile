# Use an official Python image as a base image
FROM python:3.12-alpine

# Set the working directory in the container
WORKDIR /web_app

# Copy the application files into the container
COPY ./web_app /web_app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port on which the application will run
EXPOSE 5000

# Command to execute the application
CMD ["flask", "run", "--host=0.0.0.0"]