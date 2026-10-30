#include "file_commands.h"
#include "../syscall.h"

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
    long fd = sys_create(path);
    if (fd < 0) {
        if (sys_truncate(path, 0) < 0) {
            print_text("write: cannot create or truncate file\n");
            return;
        }
        fd = sys_open_write(path);
        if (fd < 0) {
            print_text("write: cannot open file\n");
            return;
        }
    }

    size_t length = text_length(arg);
    size_t offset = 0;
    while (offset < length) {
        long n = sys_write((int)fd, arg + offset, length - offset);
        if (n <= 0) {
            print_text("write: save failed\n");
            sys_close((int)fd);
            return;
        }
        offset += (size_t)n;
    }
    if (sys_write((int)fd, "\n", 1) != 1) {
        print_text("write: save failed\n");
        sys_close((int)fd);
        return;
    }
    if (sys_close((int)fd) < 0) {
        print_text("write: close failed\n");
        return;
    }
    print_text("saved\n");
}
