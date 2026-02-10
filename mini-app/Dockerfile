# Mini App Dockerfile (Nginx for static files)
FROM node:20-alpine AS builder

WORKDIR /app

# API URL for production
ARG VITE_API_URL=https://seeyay-ai-api-445810320877.europe-west4.run.app
ENV VITE_API_URL=$VITE_API_URL

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build the app
RUN npm run build

# Production stage with Nginx
FROM nginx:alpine

# Copy built files to nginx
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Cloud Run expects port 8080
EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
