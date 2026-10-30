#include "syscall.h"

static void print_text(const char *text) {
    size_t length = 0;
    while (text[length]) length++;
    sys_write(1, text, length);
}

static void print_digit(int value) {
    char digit = (char)('0' + value);
    sys_write(1, &digit, 1);
}

int main(int argc, char **argv) {
    print_text("argc=");
    print_digit(argc);
    print_text("\n");
    for (int i = 0; i < argc; i++) {
        print_text("arg");
        print_digit(i);
        print_text("=");
        print_text(argv[i]);
        print_text("\n");
    }
    return 0;
}
