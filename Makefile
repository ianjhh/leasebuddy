# Makefile

.PHONY: start_docker stop_docker logs backend-shell db-shell

# Start all Docker services in the background (-d means detached)
start_docker:
	docker-compose -f infra/docker/docker-compose.yml up -d

# Stop all Docker services
stop_docker:
	docker-compose -f infra/docker/docker-compose.yml down

# View logs from all services
logs:
	docker-compose -f infra/docker/docker-compose.yml logs -f

# Open a terminal inside the running backend container
backend-shell:
	docker-compose -f infra/docker/docker-compose.yml exec backend bash

# Open a database connection in the terminal
db-shell:
	docker-compose -f infra/docker/docker-compose.yml exec postgres psql -U postgres -d leasebuddy