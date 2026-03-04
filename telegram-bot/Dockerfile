FROM golang:1.22-alpine AS build
WORKDIR /src
COPY go.mod ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o /out/wt-telegram-bot ./main.go

FROM alpine:3.20
WORKDIR /app
COPY --from=build /out/wt-telegram-bot /app/wt-telegram-bot
ENV WT_BOT_STATE_PATH=/data/state.json
CMD ["/app/wt-telegram-bot"]

