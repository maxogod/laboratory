# **Dependencies**
FROM golang:1.26.1 AS deps

WORKDIR /usr/src/app

COPY go.mod go.sum ./
RUN go mod download
RUN go install github.com/swaggo/swag/cmd/swag@v1.16.6

# **Build App**
FROM deps AS builder

WORKDIR /usr/src/app

COPY . .

RUN swag init --generalInfo cmd/main.go --output ./swagger

RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 \
    go build -o /usr/local/bin/app cmd/main.go

# **Run Compiled App**
FROM gcr.io/distroless/base-debian12 AS app

WORKDIR /usr/src/app

COPY --from=builder /usr/local/bin/app /usr/local/bin/app

USER nonroot:nonroot

EXPOSE 8080

ENTRYPOINT ["/usr/local/bin/app"]
