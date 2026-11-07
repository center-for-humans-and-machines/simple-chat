# Base stage
FROM node:22-bookworm AS build

# Set working directory
WORKDIR /usr/src/app

# Copy package files
COPY package*.json ./
COPY . /usr/src/app
# Install dependencies
RUN npm ci --include=dev && npm run build

# Development stage
FROM build AS development
EXPOSE 1234
CMD ["npm", "start"]

# Production stage
FROM nginx:alpine AS production

# Copy built files to Nginx web root
COPY --from=build /usr/src/app/dist /usr/share/nginx/html

# Expose port
EXPOSE 80
# Start Nginx
CMD ["nginx", "-g", "daemon off;"]
