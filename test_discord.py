import asyncio
from discord_notifier import DiscordNotifier

async def test_notification():
    # Create some test items
    test_items = [
        {
            'o:id': '1',
            'o:title': 'Test Item 1',
            'o:created': '2024-03-20T10:00:00'
        },
        {
            'o:id': '2',
            'o:title': 'Test Item 2 with a Longer Title',
            'o:created': '2024-03-20T10:30:00'
        },
        {
            'o:id': '3',
            'o:title': 'Test Item 3 🔬 with Emoji',
            'o:created': '2024-03-20T11:00:00'
        }
    ]

    # Initialize Discord notifier and send test notification
    notifier = DiscordNotifier()
    if await notifier.connect():
        await notifier.send_notification(test_items)
        await notifier.close()

if __name__ == "__main__":
    asyncio.run(test_notification()) 