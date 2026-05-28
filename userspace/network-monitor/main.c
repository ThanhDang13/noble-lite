#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#define MAX_LINE 1024

void show_connections(void) {
    FILE *fp;
    char line[MAX_LINE];

    printf("TCP Connections:\n");
    printf("%-25s %-25s %-10s\n", "Local Address", "Remote Address", "State");
    printf("------------------------------------------------------------------------\n");

    fp = fopen("/proc/net/tcp", "r");
    if (!fp) {
        perror("fopen /proc/net/tcp");
        return;
    }

    if (fgets(line, sizeof(line), fp) == NULL) {
        fclose(fp);
        return;
    }

    while (fgets(line, sizeof(line), fp)) {
        unsigned long local_addr, remote_addr;
        int local_port, remote_port, state;

        sscanf(line, "%*d: %lx:%x %lx:%x %x",
               &local_addr, &local_port,
               &remote_addr, &remote_port,
               &state);

        printf("%lu.%lu.%lu.%lu:%-5d   %lu.%lu.%lu.%lu:%-5d   %02X\n",
               (local_addr) & 0xFF,
               (local_addr >> 8) & 0xFF,
               (local_addr >> 16) & 0xFF,
               (local_addr >> 24) & 0xFF,
               local_port,
               (remote_addr) & 0xFF,
               (remote_addr >> 8) & 0xFF,
               (remote_addr >> 16) & 0xFF,
               (remote_addr >> 24) & 0xFF,
               remote_port,
               state);
    }

    fclose(fp);
}

void show_ports(void) {
    FILE *fp;
    char line[MAX_LINE];

    printf("Listening Ports:\n");
    printf("%-10s %-25s\n", "Protocol", "Local Address");
    printf("----------------------------------------\n");

    fp = fopen("/proc/net/tcp", "r");
    if (fp) {
        if (fgets(line, sizeof(line), fp) == NULL) {
            fclose(fp);
        } else {
            while (fgets(line, sizeof(line), fp)) {
            unsigned long local_addr;
            int local_port, state;

            sscanf(line, "%*d: %lx:%x %*x:%*x %x",
                   &local_addr, &local_port, &state);

            if (state == 0x0A) {
                printf("%-10s %lu.%lu.%lu.%lu:%d\n",
                       "TCP",
                       (local_addr) & 0xFF,
                       (local_addr >> 8) & 0xFF,
                       (local_addr >> 16) & 0xFF,
                       (local_addr >> 24) & 0xFF,
                       local_port);
            }
            }

            fclose(fp);
        }
    }

    fp = fopen("/proc/net/udp", "r");
    if (fp) {
        if (fgets(line, sizeof(line), fp) == NULL) {
            fclose(fp);
        } else {
            while (fgets(line, sizeof(line), fp)) {
            unsigned long local_addr;
            int local_port;

            sscanf(line, "%*d: %lx:%x", &local_addr, &local_port);

            printf("%-10s %lu.%lu.%lu.%lu:%d\n",
                   "UDP",
                   (local_addr) & 0xFF,
                   (local_addr >> 8) & 0xFF,
                   (local_addr >> 16) & 0xFF,
                   (local_addr >> 24) & 0xFF,
                   local_port);
            }

            fclose(fp);
        }
    }
}

void show_network_stats(void) {
    FILE *fp;
    char line[MAX_LINE];

    printf("Network Interface Statistics:\n");
    printf("%-10s %15s %15s %15s %15s\n",
           "Interface", "RX Bytes", "RX Packets", "TX Bytes", "TX Packets");
    printf("--------------------------------------------------------------------------------\n");

    fp = fopen("/proc/net/dev", "r");
    if (!fp) {
        perror("fopen /proc/net/dev");
        return;
    }

    if (fgets(line, sizeof(line), fp) == NULL) {
        fclose(fp);
        return;
    }
    if (fgets(line, sizeof(line), fp) == NULL) {
        fclose(fp);
        return;
    }

    while (fgets(line, sizeof(line), fp)) {
        char iface[32];
        unsigned long rx_bytes, rx_packets, tx_bytes, tx_packets;

        sscanf(line, "%[^:]: %lu %lu %*u %*u %*u %*u %*u %*u %lu %lu",
               iface, &rx_bytes, &rx_packets, &tx_bytes, &tx_packets);

        printf("%-10s %15lu %15lu %15lu %15lu\n",
               iface, rx_bytes, rx_packets, tx_bytes, tx_packets);
    }

    fclose(fp);
}

void watch_network(int interval) {
    printf("Monitoring network (interval: %d seconds)\n", interval);
    printf("Press Ctrl+C to stop...\n\n");

    while (1) {
        if (system("clear") != 0) {
            perror("system");
        }
        show_network_stats();
        printf("\n");
        show_connections();
        sleep(interval);
    }
}

void print_usage(const char *prog) {
    printf("Usage: %s [OPTIONS]\n", prog);
    printf("Options:\n");
    printf("  --connections        Show active connections\n");
    printf("  --ports              Show listening ports\n");
    printf("  --stats              Show network statistics\n");
    printf("  --watch <interval>   Monitor network (interval in seconds)\n");
    printf("  --help               Show this help\n");
}

int main(int argc, char *argv[]) {
    if (argc < 2) {
        print_usage(argv[0]);
        return 1;
    }

    if (strcmp(argv[1], "--connections") == 0) {
        show_connections();
    } else if (strcmp(argv[1], "--ports") == 0) {
        show_ports();
    } else if (strcmp(argv[1], "--stats") == 0) {
        show_network_stats();
    } else if (strcmp(argv[1], "--watch") == 0 && argc == 3) {
        int interval = atoi(argv[2]);
        if (interval <= 0) {
            fprintf(stderr, "Invalid interval\n");
            return 1;
        }
        watch_network(interval);
    } else if (strcmp(argv[1], "--help") == 0) {
        print_usage(argv[0]);
    } else {
        printf("Unknown option: %s\n", argv[1]);
        print_usage(argv[0]);
        return 1;
    }

    return 0;
}
