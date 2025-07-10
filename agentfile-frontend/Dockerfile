FROM golang:1.21-alpine AS builder

WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download

COPY main.go ./
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o agentfile-frontend .

FROM scratch
COPY --from=builder /src/agentfile-frontend /usr/bin/agentfile-frontend
ENTRYPOINT ["/usr/bin/agentfile-frontend"]
