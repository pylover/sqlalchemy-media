
from .base import Store
from .filesystem import FileSystemStore
from .proxy import LocalProxyStore


current_store = LocalProxyStore()
