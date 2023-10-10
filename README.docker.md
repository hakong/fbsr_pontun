# Docker / Podman:
## Building and Running
### Development

To build and run the application in a development environment, use the following commands:

```bash
podman-compose -f docker-compose.dev.yml up --build
```

### Production
#### 1. forward Privileged Ports to Unprivileged Ports:
#### firewall-cmd:
~~~
firewall-cmd --add-forward-port=port=80:proto=tcp:toport=10080 --permanent
firewall-cmd --add-forward-port=port=443:proto=tcp:toport=10443 --permanent
firewall-cmd --reload
~~~

#### iptables:
Note: replace `eth0` with your interface
~~~
iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 80 -j REDIRECT --to-port 10080
iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 443 -j REDIRECT --to-port 10443
~~~

#### 2. To build and run the application in a production environment:

```bash
podman-compose -f docker-compose.prod.yml build
podman-compose -f docker-compose.prod.yml up
```

#### 3. Running the stack as a service (rootless)

## Cleaning up Docker and Podman Resources

When working with containerized applications, it's common to accumulate old or unused images, containers, volumes, and networks.

Remove all unused containers, networks, images (both dangling and unused), and build cache
```
docker system prune -a
```

Remove all stopped containers, unsued networks and volumes, dangling images:
```
docker container prune
docker network prune
docker image prune
docker volume prune
```