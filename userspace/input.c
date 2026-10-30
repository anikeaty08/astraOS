#include "syscall.h"

int main(void) {
    char line[32];
    long count = sys_read(0, line, sizeof(line) - 1);
    if (count < 0) {
        sys_write(1, "INPUT_DENIED\n", 13);
        return 0;
    }
    line[count] = '\0';
    sys_write(1, "INPUT_OK ", 9);
    sys_write(1, line, (size_t)count);
    return 0;
}
