#include "file_commands.h"
#include "../syscall.h"
#include "../runtime/file_replace.h"

static size_t text_length(const char *text) {
    size_t length = 0;
    while (text[length]) length++;
    return length;
}

static void print_text(const char *text) {
    sys_write(1, text, text_length(text));
}

void user_cat_file(const char *path) {
    char buf[128];
    long fd = sys_open(path);

    if (fd < 0) {
        print_text("cat: cannot open file\n");
        return;
    }

    for (;;) {
        long n = sys_read((int)fd, buf, sizeof(buf));
        if (n < 0) {
            print_text("cat: read failed\n");
            break;
        }
        if (n == 0) break;
        sys_write(1, buf, (size_t)n);
    }

    sys_close((int)fd);
    print_text("\n");
}

void user_write_file(char *arg) {
    char *path = arg;
    while (*arg && *arg != ' ') arg++;
    if (*arg != ' ' || arg == path || arg[1] == '\0') {
        print_text("usage: write <path> <text>\n");
        return;
    }

    *arg++ = '\0';
    if (!user_valid_file_path(path)) {
        print_text("write: use a root-level 8.3 path\n");
        return;
    }
    size_t length = text_length(arg);
    char output[128];
    if (length + 1 > sizeof(output)) {
        print_text("write: text too long\n");
        return;
    }
    for (size_t i = 0; i < length; i++) output[i] = arg[i];
    output[length++] = '\n';

    char recovery_path[16];
    int result = user_replace_file(path, output, length, recovery_path);
    if (result < 0) {
        print_text("write: save failed\n");
        if (result == USER_REPLACE_RESTORE_FAILED) {
            print_text("write: recover previous data from ");
            print_text(recovery_path);
            print_text("\n");
        }
        return;
    }
    print_text("saved\n");
    if (result == USER_REPLACE_BACKUP_LEFT) {
        print_text("write: old backup remains at ");
        print_text(recovery_path);
        print_text("\n");
    }
}
