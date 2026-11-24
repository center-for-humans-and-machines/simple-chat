FROM node:25 AS build

WORKDIR /usr/src/app

# Copy package files
COPY package*.json ./
COPY . /usr/src/app
# Install dependencies
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
