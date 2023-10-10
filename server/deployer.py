#!/opt/homebrew/bin/python3
import docker
from config import *
import re

def deploy(image_id, public_port, container_name):
    if image_id in images:
        print("Deploying,", images[image_id])
        local_port = images[image_id]["local_port"]
        client = docker.from_env()
        container_name = re.sub('[^A-Za-z0-9]+', '_',
                                container_name) + "_" + str(public_port)
        container = client.containers.run(
            image_id, ports={f"{local_port}": public_port}, detach=True, name=container_name)
        container_id = container.id
        client.close()
        return container_id
    return None


def kill(container_id):
    try:
        client = docker.from_env()
        container = client.containers.get(container_id)
        container.kill()
        container.remove()
        client.close()
    except:
        return False
    finally:
        return True


def pull():
    ## Connect to local Docker engine ##
    client = docker.from_env()
    
    ## Get Images already pulled and parse them into list ##
    images_pulled = client.images.list()
    images_pulled_parsed = []
    for i in images_pulled:
        tmp1 = str(i).split("'")
        tmp2 = str(tmp1[1]).split(":")
        images_pulled_parsed.append(tmp2[0])
    ## parse images defined in config ##
    images_parsed = []
    for key in images:
        images_parsed.append(key)
   
   ## Debug ## 
    #print(images_parsed)
    #print(images_pulled_parsed)
    
    ## pull images which are defined but not yet pulled ##
    for i in images_parsed:
        if i in images_pulled_parsed:
            print("image already pulled: ", i)
        else:
            try:
                client.images.pull(i)
                print("Image pulled successfully:", i)
            except docker.errors.APIError as e:
                print("Error pulling image:", str(e))
pull()
    