FROM golang:1.22-alpine AS builder

WORKDIR /app

# Copy go.mod and go.sum first to leverage Docker cache
COPY go.mod go.sum ./

# Download Go modules
RUN go mod download

# Copy the rest of the application source code
COPY . .

# Build the Go application
# CGO_ENABLED=0 for static linking, GOOS=linux for Linux target
RUN CGO_ENABLED=0 GOOS=linux go build -o /app/bin/cli ./main.go

# Final stage: a minimal image to run the compiled application
FROM alpine:latest

WORKDIR /app

# Copy the compiled binary from the builder stage to a standard location
COPY --from=builder /app/bin/cli /usr/local/bin/cli

# Set the entry point for the container
ENTRYPOINT ["/usr/local/bin/cli"]
