# Base stage
FROM node:22-bookworm AS build

# Set working directory
WORKDIR /usr/src/app

# Copy package files
COPY package*.json ./
COPY . /usr/src/app
# Install dependencies
# Build-time settings, passed by compose.yml for the production profile
ARG REACT_APP_BACKEND_URL
ARG SENTRY_ENABLED
ARG SENTRY_DSN
RUN npm ci --include=dev && npm run build

# Development stage
FROM build AS development
EXPOSE 1234
CMD ["npm", "start"]

# Production stage
FROM nginx:alpine AS production

# Copy built files to Nginx web root
COPY --from=build /usr/src/app/dist /usr/share/nginx/html
# Adds the per-project frame-ancestors header when BACKEND_INTERNAL_URL is set
COPY --chmod=755 nginx/40-embed-policy.sh /docker-entrypoint.d/40-embed-policy.sh

# Expose port
EXPOSE 80
# Start Nginx
CMD ["nginx", "-g", "daemon off;"]
