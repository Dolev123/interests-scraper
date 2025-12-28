import ntfpy

RANSOMWARELIVE_URL = "https://push.ransomware.live"

client = ntfpy.NTFYClient(
    server=ntfpy.NTFYServer(RANSOMWARELIVE_URL),
    topic="victims",
)

async def save_notification(ntf: ntfpy.types.NTFYMessage):
    pass


def list_notifications():
    pass

if __name__ == '__name__':
    pass
