#ifndef ASTRA_EDITOR_DOCUMENT_H
#define ASTRA_EDITOR_DOCUMENT_H

#include <stdbool.h>
#include <stddef.h>

#define EDIT_MAX_LINES 32
#define EDIT_MAX_LINE_LENGTH 95

struct edit_document {
    char lines[EDIT_MAX_LINES][EDIT_MAX_LINE_LENGTH + 1];
    size_t count;
    bool dirty;
};

void edit_document_init(struct edit_document *doc);
int edit_document_insert(struct edit_document *doc, size_t index,
                         const char *text, size_t length);
int edit_document_delete(struct edit_document *doc, size_t index);

#endif
