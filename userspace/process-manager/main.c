#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dirent.h>
#include <unistd.h>
#include <signal.h>
#include <sys/types.h>
#include <ctype.h>

#define PROC_DIR "/proc"
#define MAX_LINE 256

typedef struct {
    int pid;
    char name[256];
    char state;
    int ppid;
} ProcessInfo;

int is_number(const char *str) {
    while (*str) {
        if (!isdigit(*str)) return 0;
        str++;
    }
    return 1;
}

int read_process_info(int pid, ProcessInfo *info) {
    char path[512];
    FILE *fp;
    char line[MAX_LINE];

    snprintf(path, sizeof(path), "/proc/%d/stat", pid);
    fp = fopen(path, "r");
    if (!fp) return -1;

    if (fgets(line, sizeof(line), fp)) {
        sscanf(line, "%d %s %c %d", &info->pid, info->name, &info->state, &info->ppid);
        fclose(fp);
        return 0;
    }

    fclose(fp);
    return -1;
}

void list_processes(void) {
    DIR *dir;
    struct dirent *entry;
    ProcessInfo info;

    printf("%-8s %-20s %-8s %-8s\n", "PID", "NAME", "STATE", "PPID");
    printf("------------------------------------------------------------\n");

    dir = opendir(PROC_DIR);
    if (!dir) {
        perror("opendir");
        return;
    }

    while ((entry = readdir(dir)) != NULL) {
        if (is_number(entry->d_name)) {
            int pid = atoi(entry->d_name);
            if (read_process_info(pid, &info) == 0) {
                printf("%-8d %-20s %-8c %-8d\n", info.pid, info.name, info.state, info.ppid);
            }
        }
    }

    closedir(dir);
}

void find_zombies(void) {
    DIR *dir;
    struct dirent *entry;
    ProcessInfo info;
    int found = 0;

    printf("Zombie processes:\n");
    printf("%-8s %-20s %-8s\n", "PID", "NAME", "PPID");
    printf("--------------------------------------------\n");

    dir = opendir(PROC_DIR);
    if (!dir) {
        perror("opendir");
        return;
    }

    while ((entry = readdir(dir)) != NULL) {
        if (is_number(entry->d_name)) {
            int pid = atoi(entry->d_name);
            if (read_process_info(pid, &info) == 0 && info.state == 'Z') {
                printf("%-8d %-20s %-8d\n", info.pid, info.name, info.ppid);
                found = 1;
            }
        }
    }

    closedir(dir);

    if (!found) {
        printf("No zombie processes found.\n");
    }
}

void print_tree_recursive(int pid, int level) {
    DIR *dir;
    struct dirent *entry;
    ProcessInfo info;

    for (int i = 0; i < level; i++) {
        printf("  ");
    }

    if (read_process_info(pid, &info) == 0) {
        printf("|-- [%d] %s\n", info.pid, info.name);
    }

    dir = opendir(PROC_DIR);
    if (!dir) return;

    while ((entry = readdir(dir)) != NULL) {
        if (is_number(entry->d_name)) {
            int child_pid = atoi(entry->d_name);
            if (read_process_info(child_pid, &info) == 0 && info.ppid == pid) {
                print_tree_recursive(child_pid, level + 1);
            }
        }
    }

    closedir(dir);
}

void show_tree(void) {
    printf("Process tree:\n");
    print_tree_recursive(1, 0);
}

void kill_process(int pid) {
    if (kill(pid, SIGTERM) == 0) {
        printf("Sent SIGTERM to process %d\n", pid);
    } else {
        perror("kill");
    }
}

void print_usage(const char *prog) {
    printf("Usage: %s [OPTIONS]\n", prog);
    printf("Options:\n");
    printf("  --list       List all processes\n");
    printf("  --tree       Show process tree\n");
    printf("  --zombies    Find zombie processes\n");
    printf("  --kill PID   Kill process by PID\n");
    printf("  --help       Show this help\n");
}

int main(int argc, char *argv[]) {
    if (argc < 2) {
        print_usage(argv[0]);
        return 1;
    }

    if (strcmp(argv[1], "--list") == 0) {
        list_processes();
    } else if (strcmp(argv[1], "--tree") == 0) {
        show_tree();
    } else if (strcmp(argv[1], "--zombies") == 0) {
        find_zombies();
    } else if (strcmp(argv[1], "--kill") == 0 && argc == 3) {
        int pid = atoi(argv[2]);
        kill_process(pid);
    } else if (strcmp(argv[1], "--help") == 0) {
        print_usage(argv[0]);
    } else {
        printf("Unknown option: %s\n", argv[1]);
        print_usage(argv[0]);
        return 1;
    }

    return 0;
}
