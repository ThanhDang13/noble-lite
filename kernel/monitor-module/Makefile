obj-m += monitor.o

KDIR := /lib/modules/$(shell uname -r)/build
PWD := $(shell pwd)

all:
	make -C $(KDIR) M=$(PWD) modules

clean:
	make -C $(KDIR) M=$(PWD) clean

install:
	sudo insmod monitor.ko

uninstall:
	sudo rmmod monitor

test:
	cat /proc/process_monitor

.PHONY: all clean install uninstall test
