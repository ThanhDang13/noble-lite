#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <dirent.h>
#include <unistd.h>
#include <time.h>
#include <pwd.h>
#include <grp.h>
#include <sys/inotify.h>

#define MAX_PATH 4096
#define EVENT_SIZE (sizeof(struct inotify_event))
#define EVENT_BUF_LEN (1024 * (EVENT_SIZE + 16))

void print_permissions(mode_t mode) {
    printf((S_ISDIR(mode)) ? "d" : "-");
    printf((mode & S_IRUSR) ? "r" : "-");
    printf((mode & S_IWUSR) ? "w" : "-");
    printf((mode & S_IXUSR) ? "x" : "-");
    printf((mode & S_IRGRP) ? "r" : "-");
    printf((mode & S_IWGRP) ? "w" : "-");
    printf((mode & S_IXGRP) ? "x" : "-");
    printf((mode & S_IROTH) ? "r" : "-");
    printf((mode & S_IWOTH) ? "w" : "-");
    printf((mode & S_IXOTH) ? "x" : "-");
}

void analyze_file(const char *path) {
    struct stat st;

    if (stat(path, &st) != 0) {
        perror("stat");
        return;
    }

    printf("File: %s\n", path);
    printf("Size: %ld bytes\n", st.st_size);
    printf("Permissions: ");
    print_permissions(st.st_mode);
    printf(" (%o)\n", st.st_mode & 0777);

    struct passwd *pw = getpwuid(st.st_uid);
    struct group *gr = getgrgid(st.st_gid);
    printf("Owner: %s (%d)\n", pw ? pw->pw_name : "unknown", st.st_uid);
    printf("Group: %s (%d)\n", gr ? gr->gr_name : "unknown", st.st_gid);

    printf("Last access: %s", ctime(&st.st_atime));
    printf("Last modification: %s", ctime(&st.st_mtime));
    printf("Last status change: %s", ctime(&st.st_ctime));
}

void analyze_directory(const char *path) {
    DIR *dir;
    struct dirent *entry;
    struct stat st;
    char full_path[MAX_PATH];

    dir = opendir(path);
    if (!dir) {
        perror("opendir");
        return;
    }

    printf("Analyzing directory: %s\n", path);
    printf("%-40s %-12s %-10s\n", "Name", "Type", "Size");
    printf("------------------------------------------------------------------------\n");

    while ((entry = readdir(dir)) != NULL) {
        if (strcmp(entry->d_name, ".") == 0 || strcmp(entry->d_name, "..") == 0)
            continue;

        snprintf(full_path, sizeof(full_path), "%s/%s", path, entry->d_name);

        if (stat(full_path, &st) == 0) {
            printf("%-40s %-12s %-10ld\n",
                   entry->d_name,
                   S_ISDIR(st.st_mode) ? "DIR" : "FILE",
                   st.st_size);
        }
    }

    closedir(dir);
}

void watch_directory(const char *path) {
    int fd, wd;
    char buffer[EVENT_BUF_LEN];

    fd = inotify_init();
    if (fd < 0) {
        perror("inotify_init");
        return;
    }

    wd = inotify_add_watch(fd, path, IN_CREATE | IN_DELETE | IN_MODIFY | IN_MOVED_FROM | IN_MOVED_TO);
    if (wd < 0) {
        perror("inotify_add_watch");
        close(fd);
        return;
    }

    printf("Watching directory: %s\n", path);
    printf("Press Ctrl+C to stop...\n\n");

    while (1) {
        ssize_t length = read(fd, buffer, EVENT_BUF_LEN);
        if (length < 0) {
            perror("read");
            break;
        }

        ssize_t i = 0;
        while (i < length) {
            struct inotify_event *event = (struct inotify_event *)&buffer[i];

            if (event->len) {
                if (event->mask & IN_CREATE) {
                    printf("[CREATE] %s\n", event->name);
                }
                if (event->mask & IN_DELETE) {
                    printf("[DELETE] %s\n", event->name);
                }
                if (event->mask & IN_MODIFY) {
                    printf("[MODIFY] %s\n", event->name);
                }
                if (event->mask & IN_MOVED_FROM) {
                    printf("[MOVED_FROM] %s\n", event->name);
                }
                if (event->mask & IN_MOVED_TO) {
                    printf("[MOVED_TO] %s\n", event->name);
                }
            }

            i += EVENT_SIZE + event->len;
        }
    }

    inotify_rm_watch(fd, wd);
    close(fd);
}

void print_usage(const char *prog) {
    printf("Usage: %s [OPTIONS] <path>\n", prog);
    printf("Options:\n");
    printf("  --analyze <file>     Analyze file metadata\n");
    printf("  --scan <dir>         Scan directory contents\n");
    printf("  --watch <dir>        Watch directory for changes\n");
    printf("  --help               Show this help\n");
}

int main(int argc, char *argv[]) {
    if (argc < 3) {
        print_usage(argv[0]);
        return 1;
    }

    if (strcmp(argv[1], "--analyze") == 0) {
        analyze_file(argv[2]);
    } else if (strcmp(argv[1], "--scan") == 0) {
        analyze_directory(argv[2]);
    } else if (strcmp(argv[1], "--watch") == 0) {
        watch_directory(argv[2]);
    } else if (strcmp(argv[1], "--help") == 0) {
        print_usage(argv[0]);
    } else {
        printf("Unknown option: %s\n", argv[1]);
        print_usage(argv[0]);
        return 1;
    }

    return 0;
}
