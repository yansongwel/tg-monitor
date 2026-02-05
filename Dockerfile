# Use python 3.9 slim as base
FROM python:3.9-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set working directory
WORKDIR /app

# Copy pyproject.toml and uv.lock
COPY pyproject.toml uv.lock ./

# Install dependencies into system python
# We export the lockfile to requirements.txt and install it globally
RUN uv export --frozen --format=requirements-txt > requirements.txt && \
    uv pip install --system -r requirements.txt

# Copy the rest of the application
COPY . .

# Run the application
CMD ["python", "main.py"]
