FROM node:18-alpine

WORKDIR /app

RUN apk add --no-cache docker-cli

# Enable Corepack for Yarn 4 support
RUN corepack enable

# Copy package files and Yarn 4 configuration
COPY package.json yarn.lock ./
COPY .yarn ./.yarn

# Install dependencies
RUN yarn install --immutable

# Copy built application
COPY dist ./dist

ENV NODE_ENV=production

ENTRYPOINT ["node", "dist/index.js"]
