#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>

#define BUFFER_SIZE 4096

int connect_to_server(const char *host, int port) {
    int sock;
    struct sockaddr_in server_addr;

    sock = socket(AF_INET, SOCK_STREAM, 0);
    if (sock < 0) {
        perror("socket");
        return -1;
    }

    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(port);

    if (inet_pton(AF_INET, host, &server_addr.sin_addr) <= 0) {
        perror("inet_pton");
        close(sock);
        return -1;
    }

    if (connect(sock, (struct sockaddr *)&server_addr, sizeof(server_addr)) < 0) {
        perror("connect");
        close(sock);
        return -1;
    }

    return sock;
}

void send_message(int sock, const char *message) {
    ssize_t bytes_sent = write(sock, message, strlen(message));
    if (bytes_sent < 0) {
        perror("write");
        return;
    }

    printf("Sent %zd bytes\n", bytes_sent);

    char buffer[BUFFER_SIZE];
    ssize_t bytes_read = read(sock, buffer, sizeof(buffer) - 1);
    if (bytes_read > 0) {
        buffer[bytes_read] = '\0';
        printf("Server response: %s", buffer);
    } else if (bytes_read < 0) {
        perror("read");
    }
}

void print_usage(const char *prog) {
    printf("Usage: %s --host <host> --port <port> --message <message>\n", prog);
    printf("Options:\n");
    printf("  --host <host>        Server hostname or IP\n");
    printf("  --port <port>        Server port\n");
    printf("  --message <message>  Message to send\n");
    printf("  --help               Show this help\n");
}

int main(int argc, char *argv[]) {
    char *host = NULL;
    int port = 0;
    char *message = NULL;

    if (argc < 7) {
        print_usage(argv[0]);
        return 1;
    }

    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--host") == 0 && i + 1 < argc) {
            host = argv[i + 1];
            i++;
        } else if (strcmp(argv[i], "--port") == 0 && i + 1 < argc) {
            port = atoi(argv[i + 1]);
            i++;
        } else if (strcmp(argv[i], "--message") == 0 && i + 1 < argc) {
            message = argv[i + 1];
            i++;
        } else if (strcmp(argv[i], "--help") == 0) {
            print_usage(argv[0]);
            return 0;
        }
    }

    if (!host || port <= 0 || port > 65535 || !message) {
        fprintf(stderr, "Invalid arguments\n");
        print_usage(argv[0]);
        return 1;
    }

    int sock = connect_to_server(host, port);
    if (sock < 0) {
        return 1;
    }

    printf("Connected to %s:%d\n", host, port);
    send_message(sock, message);

    close(sock);
    return 0;
}
