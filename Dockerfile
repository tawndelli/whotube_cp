FROM python:3.10-slim
 
# Create app directory
WORKDIR /app

# Install app dependencies
COPY requirements.txt ./
 
RUN pip install --no-cache-dir --upgrade -r requirements.txt
 
# Bundle app source
COPY . .

EXPOSE 8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"] 