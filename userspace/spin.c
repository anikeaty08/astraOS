#include "syscall.h"

static volatile uint64_t iterations;

int main(void) {
    static const char message[] = "SPIN_READY\n";
    sys_write(1, message, sizeof(message) - 1);

    /* Deliberately never enter the kernel or yield after this point. */
    for (;;) {
        iterations++;
    }
}
