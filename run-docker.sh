docker stop invite0-container
docker rm invite0
docker build --tag invite0 .
docker run --detach -p 8000:8000 --env-file=.env --name invite0-container invite0
