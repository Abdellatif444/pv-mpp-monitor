# Frontend Dockerfile
FROM node:20-alpine

WORKDIR /app

COPY package.json /app/package.json
RUN npm install --no-audit --no-fund

# Copy rest of the app
COPY . /app

EXPOSE 5173

CMD ["npm", "run", "dev"]
