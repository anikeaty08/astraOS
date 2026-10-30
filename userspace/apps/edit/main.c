#include "document.h"
#include "../../syscall.h"
#include "../../runtime/file_replace.h"

static struct edit_document document;
static char path[16];
static char saved_text[EDIT_MAX_LINES * (EDIT_MAX_LINE_LENGTH + 1)];

static size_t text_length(const char *text) {
    size_t length = 0;
    while (text[length]) length++;
    return length;
}

static void print_text(const char *text) {
    sys_write(1, text, text_length(text));
}

static void print_number(size_t number) {
    char digits[24];
    size_t count = 0;
    do {
        digits[count++] = (char)('0' + number % 10);
        number /= 10;
    } while (number && count < sizeof(digits));
    while (count) sys_write(1, &digits[--count], 1);
}

/* Read a whole command. Reject and drain an overlong line. */
static int read_line(char *buffer, size_t capacity) {
    size_t used = 0;
    int overflow = 0;

    for (;;) {
        char c;
        if (sys_read(0, &c, 1) != 1) continue;
        if (c == '\n') break;
        if (c == '\r') continue;
        if (used + 1 < capacity) buffer[used++] = c;
        else overflow = 1;
    }

    buffer[used] = '\0';
    return overflow ? -1 : 0;
}

static int load_file(void) {
    long fd = sys_open(path);
    if (fd < 0) {
        long writable = sys_open_write(path);
        if (writable >= 0) {
            sys_close((int)writable);
            print_text("edit: file exists but cannot be read\n");
            return -1;
        }
        print_text("new file\n");
        return 0;
    }

    char current[EDIT_MAX_LINE_LENGTH + 1];
    size_t length = 0;
    char bytes[128];
    for (;;) {
        long count = sys_read((int)fd, bytes, sizeof(bytes));
        if (count < 0) {
            print_text("edit: read failed\n");
            sys_close((int)fd);
            return -1;
        }
        if (count == 0) break;
        for (long i = 0; i < count; i++) {
            char c = bytes[i];
            if (c == '\n') {
                if (edit_document_insert(&document, document.count, current, length) < 0) {
                    print_text("edit: file exceeds editor limits\n");
                    sys_close((int)fd);
                    return -1;
                }
                length = 0;
            } else if (c == '\0' || (c < ' ' && c != '\r' && c != '\t')) {
                print_text("edit: binary file refused\n");
                sys_close((int)fd);
                return -1;
            } else if (c != '\r') {
                if (length >= EDIT_MAX_LINE_LENGTH) {
                    print_text("edit: line exceeds editor limit\n");
                    sys_close((int)fd);
                    return -1;
                }
                current[length++] = c;
            }
        }
    }
    if (length && edit_document_insert(&document, document.count, current, length) < 0) {
        print_text("edit: file exceeds editor limits\n");
        sys_close((int)fd);
        return -1;
    }
    if (sys_close((int)fd) < 0) {
        print_text("edit: close failed\n");
        return -1;
    }
    document.dirty = false;
    print_text("loaded ");
    print_number(document.count);
    print_text(" lines\n");
    return 0;
}

static int save_file(void) {
    size_t length = 0;
    for (size_t line = 0; line < document.count; line++) {
        const char *text = document.lines[line];
        for (size_t column = 0; text[column]; column++) {
            saved_text[length++] = text[column];
        }
        saved_text[length++] = '\n';
    }

    char recovery_path[16];
    int result = user_replace_file(path, saved_text, length, recovery_path);
    if (result < 0) {
        print_text("edit: save failed (code ");
        print_number((size_t)-result);
        print_text(")\n");
        if (result == USER_REPLACE_RESTORE_FAILED) {
            print_text("edit: recover previous data from ");
            print_text(recovery_path);
            print_text("\n");
        } else {
            print_text("edit: original file preserved if present\n");
        }
        return -1;
    }
    document.dirty = false;
    print_text("saved\n");
    if (result == USER_REPLACE_BACKUP_LEFT) {
        print_text("edit: old backup remains at ");
        print_text(recovery_path);
        print_text("\n");
    }
    return 0;
}

static int parse_line_number(const char *text, size_t *value) {
    size_t number = 0;
    if (!*text) return -1;
    while (*text >= '0' && *text <= '9') {
        number = number * 10 + (size_t)(*text - '0');
        if (number > EDIT_MAX_LINES + 1) return -1;
        text++;
    }
    if (*text != '\0' && *text != ' ') return -1;
    if (number == 0) return -1;
    *value = number;
    return 0;
}

static void print_document(void) {
    for (size_t line = 0; line < document.count; line++) {
        print_number(line + 1);
        print_text(": ");
        print_text(document.lines[line]);
        print_text("\n");
    }
    if (!document.count) print_text("(empty)\n");
}

static void help(void) {
    print_text("p print | a <text> append | i <n> <text> insert | d <n> delete\n");
    print_text("w save | q quit if clean | q! discard | h help\n");
}

int main(void) {
    char command[160];
    edit_document_init(&document);
    print_text("AstraOS line editor\npath: ");
    if (read_line(path, sizeof(path)) < 0 || !user_valid_file_path(path)) {
        print_text("edit: use a root-level 8.3 path such as /NOTE.TXT\n");
        return 1;
    }
    if (load_file() < 0) return 1;
    help();

    for (;;) {
        print_text("edit> ");
        if (read_line(command, sizeof(command)) < 0) {
            print_text("edit: command too long\n");
            continue;
        }

        if (command[0] == 'p' && !command[1]) {
            print_document();
        } else if (command[0] == 'a' &&
                   (command[1] == '\0' || command[1] == ' ')) {
            const char *text = command[1] ? command + 2 : "";
            if (edit_document_insert(&document, document.count, text, text_length(text)) < 0)
                print_text("edit: document or line limit reached\n");
        } else if (command[0] == 'i' && command[1] == ' ') {
            size_t number;
            char *argument = command + 2;
            if (parse_line_number(argument, &number) < 0 || number > document.count + 1) {
                print_text("edit: invalid line number\n");
                continue;
            }
            while (*argument >= '0' && *argument <= '9') argument++;
            if (*argument != ' ') {
                print_text("usage: i <n> <text>\n");
                continue;
            }
            argument++;
            if (edit_document_insert(&document, number - 1, argument,
                                     text_length(argument)) < 0)
                print_text("edit: document or line limit reached\n");
        } else if (command[0] == 'd' && command[1] == ' ') {
            size_t number;
            char *end = command + 2;
            while (*end >= '0' && *end <= '9') end++;
            if (parse_line_number(command + 2, &number) < 0 || *end != '\0' ||
                edit_document_delete(&document, number - 1) < 0)
                print_text("edit: invalid line number\n");
        } else if (command[0] == 'w' && !command[1]) {
            save_file();
        } else if (command[0] == 'q' && !command[1]) {
            if (document.dirty) print_text("edit: unsaved changes; use w or q!\n");
            else return 0;
        } else if (command[0] == 'q' && command[1] == '!' && !command[2]) {
            return 0;
        } else if (command[0] == 'h' && !command[1]) {
            help();
        } else {
            print_text("edit: unknown command; type h\n");
        }
    }
}
