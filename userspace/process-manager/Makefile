CC = gcc
CFLAGS = -Wall -Wextra -O2 -g
TARGET = process-manager

$(TARGET): main.c
	$(CC) $(CFLAGS) -o $@ $^

clean:
	rm -f $(TARGET)
