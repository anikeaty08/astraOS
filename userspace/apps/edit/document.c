#include "document.h"

void edit_document_init(struct edit_document *doc) {
    doc->count = 0;
    doc->dirty = false;
}

int edit_document_insert(struct edit_document *doc, size_t index,
                         const char *text, size_t length) {
    if (!doc || !text || index > doc->count ||
        doc->count >= EDIT_MAX_LINES || length > EDIT_MAX_LINE_LENGTH) {
        return -1;
    }

    for (size_t line = doc->count; line > index; line--) {
        for (size_t column = 0; column <= EDIT_MAX_LINE_LENGTH; column++) {
            doc->lines[line][column] = doc->lines[line - 1][column];
        }
    }
    for (size_t column = 0; column < length; column++) {
        doc->lines[index][column] = text[column];
    }
    doc->lines[index][length] = '\0';
    doc->count++;
    doc->dirty = true;
    return 0;
}

int edit_document_delete(struct edit_document *doc, size_t index) {
    if (!doc || index >= doc->count) return -1;

    for (size_t line = index; line + 1 < doc->count; line++) {
        for (size_t column = 0; column <= EDIT_MAX_LINE_LENGTH; column++) {
            doc->lines[line][column] = doc->lines[line + 1][column];
        }
    }
    doc->count--;
    doc->dirty = true;
    return 0;
}
