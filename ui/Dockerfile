# Use the official Deno image
FROM denoland/deno:1.37

# Create app directory
WORKDIR /app

# Copy dependency files
COPY import_map.json deno.json ./
COPY src ./src

# Cache the dependencies
RUN deno cache --import-map=import_map.json src/main.ts

# Create .env file from example if not exists
COPY .env.example .env.example
RUN if [ ! -f .env ]; then cp .env.example .env; fi

# Grant required permissions
ENV DENO_DIR=/deno-dir
ENV DENO_INSTALL_ROOT=/usr/local

# The app binds to port 3000 (if needed)
EXPOSE 3000

# Run the app with necessary permissions
CMD ["deno", "run", "--allow-net", "--allow-env", "--import-map=import_map.json", "src/main.ts"]
