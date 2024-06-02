FROM haproxy:2.9.7-alpine
WORKDIR /app
COPY ./region_configs ./region_configs
CMD haproxy -f /app/region_configs/haproxy_${FLY_REGION}.cfg