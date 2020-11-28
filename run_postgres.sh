docker run --rm \
    --name metrics-postgres \
    -e POSTGRES_PASSWORD=metrics \
    -e POSTGRES_USER=metrics \
    -e POSTGRES_DB=metrics \
    -p 5432:5432 \
    postgres:12
