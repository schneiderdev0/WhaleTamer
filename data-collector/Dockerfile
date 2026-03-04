FROM golang:1.22-alpine AS build
WORKDIR /src
COPY go.mod ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o /out/wt-data-collector ./main.go

FROM alpine:3.20
WORKDIR /app
COPY --from=build /out/wt-data-collector /app/wt-data-collector
ENV WT_INTERVAL_SECONDS=15
CMD ["/app/wt-data-collector"]

