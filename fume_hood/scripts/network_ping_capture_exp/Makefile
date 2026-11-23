# Makefile

CC = gcc
CFLAGS = -Wall -Wextra -Werror -pedantic -ggdb
TARGET = capture_ping
SRC = main.c

all: $(TARGET)

$(TARGET): $(SRC)
	$(CC) $(CFLAGS) -o $(TARGET) $(SRC)

clean:
	rm -f $(TARGET)
