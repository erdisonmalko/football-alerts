FROM node:20-alpine

# Set working directory
WORKDIR /app

# Copy package files and change ownership
COPY package*.json ./
RUN npm install

# Copy the rest of the files and ensure node user owns them
COPY --chown=node:node . .

# Set execution permissions for the node_modules binaries
RUN chmod +x node_modules/.bin/*

# Switch to the non-root user
USER node

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
