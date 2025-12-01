# Etapa 1: Construcción (Build)
FROM node:18-alpine as build-stage
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Etapa 2: Servidor (Production)
FROM nginx:alpine as production-stage
# Copiamos los archivos construidos en la etapa anterior
COPY --from=build-stage /app/dist /usr/share/nginx/html
# Copiamos nuestra configuración de Nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf
# Cloud Run usa el puerto 8080 por defecto
EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]