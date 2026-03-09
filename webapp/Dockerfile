FROM node:18-alpine

WORKDIR /app/webapp

COPY package.json package-lock.json* ./
RUN npm install --include=dev
COPY . .
RUN npm run build

EXPOSE 3000
CMD ["npx", "vite", "preview", "--host", "0.0.0.0", "--port", "3000"]
