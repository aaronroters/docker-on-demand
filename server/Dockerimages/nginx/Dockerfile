FROM nginx:1.17-alpine
ARG port
ENV randomport $port 
#COPY <your static content> /usr/share/nginx/html
COPY nginx.conf /etc/nginx/
EXPOSE $port
CMD ["nginx"$port, "-g", "daemon off;"]
