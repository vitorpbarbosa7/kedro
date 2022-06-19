# Start Daemon in mac:
Open the Application Docker Desktop with :
```bash
open -a Docker
```
Linux uses systemctl or sudo service

# Docker images and Containers
if you export container_name and image_name, you will thank me later:
```bash
export image_name=my_docker_image
export container_name=my_docker_container
```

#### List docker images (built from Dockerfiles ow directly from some image at DockerHub):
```bash
docker image ls
```

#### List docker containers (running from images):
```bash
docker ps
```
paused or exited continaers too:
```bash
docker ps -a
```

### Docker Build:
with dockerfile in cwd:
```bash
docker build -t $image_name .	
```

# Docker run and create
## Docker run Container
#### Docker run container from pre-built image
```bash
docker run -itd --name $container_name $image_name
```
Run container which is exited
```bash
docker start -i $container_name
```

#### Abrir container de terminal que esta sendo executado
```bash
docker exec -it $container_name bash
```

### It is not possible to update the image and container easily after altering the Dockerfile. You must stop and delete the container.
#### Docker stop container and remove it too
```bash
docker stop $container_name && docker rm $container_name
```

#### So useful command would be:
```bash
docker stop $container_name && docker rm $container_name && docker run -itd --name $container_name $image_name
```
#### and also even more useful command, which adds/alter the layers from the docker image after altered the dockerfile:
```bash
docker build -t $image_name . && docker stop $container_name && docker rm $container_name && docker run -itd --name $container_name $image_name
```

#### with also running this:
```bash
docker build -t $image_name . && docker stop $container_name && docker rm $container_name && docker run -itd --name $container_name $image_name && docker start -i $container_name
```


### Docker image delete:
```bash
docker images | $image_name | xargs docker image rm
```

