FROM node:18-alpine

WORKDIR /app

COPY frontend/package.json /app/package.json
COPY frontend/tsconfig.json /app/tsconfig.json
COPY frontend/vite.config.ts /app/vite.config.ts
COPY frontend/index.html /app/index.html
COPY frontend/public /app/public
COPY frontend/src /app/src

RUN npm install && npm run build

EXPOSE 5173

CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0", "--port", "5173"]
