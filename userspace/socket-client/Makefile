CC = gcc
CFLAGS = -Wall -Wextra -O2 -g
TARGET = socket-client

$(TARGET): main.c
	$(CC) $(CFLAGS) -o $@ $^

clean:
	rm -f $(TARGET)
