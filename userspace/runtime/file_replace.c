#include "file_replace.h"
#include "../syscall.h"

static int same_text(const char *a, const char *b) {
    while (*a && *a == *b) {
        a++;
        b++;
    }
    return *a == *b;
}

static void copy_path(char destination[16], const char *source) {
    size_t i = 0;
    while (source[i] && i < 15) {
        destination[i] = source[i];
        i++;
    }
    destination[i] = '\0';
}

int user_valid_file_path(const char *candidate) {
    if (!candidate || candidate[0] != '/' || !candidate[1]) return 0;

    size_t name = 0;
    size_t extension = 0;
    int dot = 0;
    for (size_t i = 1; candidate[i]; i++) {
        char c = candidate[i];
        if (c == '.') {
            if (dot || name == 0) return 0;
            dot = 1;
            continue;
        }
        if (!((c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') ||
              (c >= '0' && c <= '9') || c == '_' || c == '-')) return 0;
        if (dot) {
            if (++extension > 3) return 0;
        } else if (++name > 8) return 0;
    }
    return !dot || extension > 0;
}

static int file_exists(const char *path) {
    long fd = sys_open(path);
    if (fd < 0) return 0;
    sys_close((int)fd);
    return 1;
}

static void sidecar_path(char output[16], long pid, int attempt,
                         const char extension[4]) {
    unsigned int number = (unsigned int)(pid >= 0 ? pid : -pid) % 1000;
    output[0] = '/';
    output[1] = 'A';
    output[2] = 'T';
    output[3] = (char)('0' + number / 100);
    output[4] = (char)('0' + number / 10 % 10);
    output[5] = (char)('0' + number % 10);
    output[6] = (char)('0' + attempt / 100);
    output[7] = (char)('0' + attempt / 10 % 10);
    output[8] = (char)('0' + attempt % 10);
    output[9] = '.';
    output[10] = extension[0];
    output[11] = extension[1];
    output[12] = extension[2];
    output[13] = '\0';
}

static int write_all(int fd, const char *data, size_t length) {
    size_t written = 0;
    while (written < length) {
        long count = sys_write(fd, data + written, length - written);
        if (count <= 0) return -1;
        written += (size_t)count;
    }
    return 0;
}

/* A failed metadata syscall may still have changed the directory entry. */
static int file_matches(const char *path, const char *data, size_t length) {
    long fd = sys_open(path);
    if (fd < 0) return 0;

    char buffer[128];
    size_t offset = 0;
    int matches = 1;
    while (offset < length) {
        size_t chunk = length - offset;
        if (chunk > sizeof(buffer)) chunk = sizeof(buffer);
        long count = sys_read((int)fd, buffer, chunk);
        if (count <= 0) {
            matches = 0;
            break;
        }
        for (long i = 0; i < count; i++) {
            if (buffer[i] != data[offset + (size_t)i]) matches = 0;
        }
        if (!matches) break;
        offset += (size_t)count;
    }
    if (matches) {
        char extra;
        matches = sys_read((int)fd, &extra, 1) == 0;
    }
    if (sys_close((int)fd) < 0) matches = 0;
    return matches;
}

int user_replace_file(const char *path, const char *data, size_t length,
                      char recovery_path[16]) {
    if (recovery_path) recovery_path[0] = '\0';
    if (!user_valid_file_path(path) || (!data && length))
        return USER_REPLACE_INVALID_PATH;

    char temporary[16];
    char backup[16];
    long fd = -1;
    for (int attempt = 0; attempt < 100; attempt++) {
        sidecar_path(temporary, sys_getpid(), attempt, "TMP");
        sidecar_path(backup, sys_getpid(), attempt, "BAK");
        if (same_text(path, temporary) || same_text(path, backup) ||
            file_exists(backup)) continue;
        fd = sys_create(temporary);
        if (fd >= 0) break;
    }
    if (fd < 0) return USER_REPLACE_NO_TEMP;

    if (write_all((int)fd, data, length) < 0) {
        sys_close((int)fd);
        sys_unlink(temporary);
        return USER_REPLACE_WRITE_FAILED;
    }
    if (sys_close((int)fd) < 0) {
        sys_unlink(temporary);
        return USER_REPLACE_WRITE_FAILED;
    }

    int had_original = file_exists(path);
    if (had_original && sys_rename(path, backup) < 0) {
        if (file_exists(path) || !file_exists(backup)) {
            sys_unlink(temporary);
            return USER_REPLACE_BACKUP_FAILED;
        }
    }
    if (sys_rename(temporary, path) < 0) {
        if (file_matches(path, data, length)) {
            /* The rename reached disk even though its completion reported error. */
            if (had_original && sys_unlink(backup) < 0 && file_exists(backup)) {
                if (recovery_path) copy_path(recovery_path, backup);
                return USER_REPLACE_BACKUP_LEFT;
            }
            return USER_REPLACE_OK;
        }
        if (had_original && sys_rename(backup, path) < 0) {
            if (file_exists(path) && !file_exists(backup)) {
                sys_unlink(temporary);
                return USER_REPLACE_PROMOTE_FAILED;
            }
            if (recovery_path) copy_path(recovery_path, backup);
            return USER_REPLACE_RESTORE_FAILED;
        }
        sys_unlink(temporary);
        return USER_REPLACE_PROMOTE_FAILED;
    }
    if (had_original && sys_unlink(backup) < 0 && file_exists(backup)) {
        if (recovery_path) copy_path(recovery_path, backup);
        return USER_REPLACE_BACKUP_LEFT;
    }
    return USER_REPLACE_OK;
}
