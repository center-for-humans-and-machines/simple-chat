FROM node:22 AS build

RUN apt-get update && apt-get install -y wget \
    && wget https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh -O /usr/local/bin/wait-for-it.sh \
    && chmod +x /usr/local/bin/wait-for-it.sh

WORKDIR /usr/src/app

# Copy package files
COPY package*.json ./
COPY . /usr/src/app
# Install dependencies
RUN npm install --include=dev

RUN npm run build

RUN ls -la /usr/src/app

# Development stage
FROM build AS development
RUN echo "development stage"
EXPOSE 3001
CMD ["npm", "start"]

# Production stage
FROM nginx:alpine AS production
RUN echo "production stage"

# Copy built files to Nginx web root
COPY --from=build /usr/src/app/build /usr/share/nginx/html

COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
