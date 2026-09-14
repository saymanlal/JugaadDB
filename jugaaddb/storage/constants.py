PAGE_SIZE = 4096

FILE_MAGIC = b"JUGAADDB"
FILE_VERSION = 1

HEADER_SIZE = 16

# Page 1 starts with a 4-byte payload length.
PAYLOAD_LENGTH_SIZE = 4