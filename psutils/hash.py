
import hashlib


# https://stackoverflow.com/a/3431835/8896374

def hash_bytestr_iter(bytesiter, hasher, ashexstr=False):
    for block in bytesiter:
        hasher.update(block)
    return hasher.hexdigest() if ashexstr else hasher.digest()

def file_as_blockiter(afile, blocksize=65536):
    with afile:
        block = afile.read(blocksize)
        while len(block) > 0:
            yield block
            block = afile.read(blocksize)

def get_file_hash(afile):
    return hash_bytestr_iter(file_as_blockiter(open(afile, 'rb')), hashlib.sha256())
