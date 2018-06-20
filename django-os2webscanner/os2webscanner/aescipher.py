import binascii, os, datetime, logging
from Crypto.Util import Counter
from Crypto.Cipher import AES
from Crypto import Random

from django.conf import settings
from django.core.mail import EmailMessage

logger = logging.getLogger(__name__)

# AES supports multiple key sizes: 16 (AES128), 24 (AES192), or 32 (AES256).
key_bytes = 32

key_file_name = '.secret'


# Takes as input a 32-byte key and an arbitrary-length plaintext and returns a
# pair (iv, ciphtertext). "iv" stands for initialization vector.
def encrypt(plaintext):
    key = generate_key()

    # Choose a random, 16-byte IV.
    iv = Random.new().read(AES.block_size)

    # Convert the IV to a Python integer.
    iv_int = int(binascii.hexlify(iv), 16)

    # Create a new Counter object with IV = iv_int.
    ctr = Counter.new(AES.block_size * 8, initial_value=iv_int)

    # Create AES-CTR cipher.
    aes = AES.new(key, AES.MODE_CTR, counter=ctr)

    # Encrypt and return IV and ciphertext.
    ciphertext = aes.encrypt(plaintext)
    return (iv, ciphertext)


# Takes as input a 32-byte key, a 16-byte IV, and a ciphertext, and outputs the
# corresponding plaintext.
def decrypt(iv, ciphertext):
    key = generate_key()

    # Initialize counter for decryption. iv should be the same as the output of
    # encrypt().
    iv_int = int(binascii.hexlify(iv), 16)
    ctr = Counter.new(AES.block_size * 8, initial_value=iv_int)

    # Create AES-CTR cipher.
    aes = AES.new(key, AES.MODE_CTR, counter=ctr)

    # Decrypt and return the plaintext.
    plaintext = aes.decrypt(ciphertext)
    return plaintext.decode('utf-8')


def generate_key():
    key = None
    file_name = settings.PROJECT_DIR + '/' + key_file_name
    if os.path.isfile(file_name):
        key = key_file_handling(None, 'rb', file_name, False)
    else:
        key = Random.new().read(key_bytes)
        key_file_handling(key, 'ab', file_name, True)
        backup_file_name = settings.VAR_DIR + '/' + key_file_name + str(datetime.date.today())
        key_file_handling(key, 'ab', backup_file_name, True)
        try:
            message = EmailMessage('CRITICAL!',
                                   'New master key has been generated.',
                                   settings.ADMIN_EMAIL)
            message.send()
        except Exception as ex:
            logger.error('Error occured while sending email, regarding master key being generated.'.format(ex))
            pass

    return key


def key_file_handling(data, command, filename, create):
    file = None
    try:
        if create and not os.path.isfile(filename):
            os.mknod(filename)
        file = open(filename, command)
        if command is 'rb':
            data = file.read()
        elif command is 'ab':
            file.write(data)
    except (OSError, IOError) as ex:
        logger.error('An error occured while trying to {0} {1} file. {2}'.format(command, filename, ex))
    finally:
        if file is not None:
            file.close()
    return data

"""
    # Nominal way to generate a fresh key. This calls the system's random number
    # generator (RNG).
    key1 = Random.new().read(key_bytes)
    iv, ciphertext = aes.encrypt(key1, 'danni#!')
    print iv
    print ciphertext
    decrypted = aes.decrypt(key1, iv, ciphertext)
    print decrypted
"""
