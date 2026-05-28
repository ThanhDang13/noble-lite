CC = gcc
CFLAGS = -Wall -Wextra -O2 -g
TARGET = network-monitor

$(TARGET): main.c
	$(CC) $(CFLAGS) -o $@ $^

clean:
	rm -f $(TARGET)
