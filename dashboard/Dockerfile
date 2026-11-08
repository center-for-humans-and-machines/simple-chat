FROM node:22 AS build

WORKDIR /usr/src/app

# Copy package files
COPY package*.json ./
COPY . /usr/src/app
# Install dependencies
# Build-time settings, passed by compose.yml for the production profile
ARG REACT_APP_BACKEND_URL
ARG REACT_APP_BACKEND_SOCKET_URL
ARG REACT_APP_FRONTEND_URL
RUN npm ci --include=dev && npm run build

# Development stage
FROM build AS development
EXPOSE 3001
CMD ["npm", "start"]

# Production stage
FROM nginx:alpine AS production

# Copy built files to Nginx web root
COPY --from=build /usr/src/app/build /usr/share/nginx/html

COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
