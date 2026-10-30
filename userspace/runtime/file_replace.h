#ifndef ASTRA_USER_FILE_REPLACE_H
#define ASTRA_USER_FILE_REPLACE_H

#include <stddef.h>

enum user_replace_result {
    USER_REPLACE_OK = 0,
    USER_REPLACE_BACKUP_LEFT = 1,
    USER_REPLACE_INVALID_PATH = -1,
    USER_REPLACE_NO_TEMP = -2,
    USER_REPLACE_WRITE_FAILED = -3,
    USER_REPLACE_BACKUP_FAILED = -4,
    USER_REPLACE_PROMOTE_FAILED = -5,
    USER_REPLACE_RESTORE_FAILED = -6,
};

/* Root-level FAT16 8.3 path accepted by the current user file tools. */
int user_valid_file_path(const char *path);

/*
 * Replace through a unique temporary file. On RESTORE_FAILED,
 * recovery_path names the backup holding the previous contents.
 * On BACKUP_LEFT, it names a backup that could not be removed.
 * This is best-effort rollback, not a power-loss transaction.
 */
int user_replace_file(const char *path, const char *data, size_t length,
                      char recovery_path[16]);

#endif
