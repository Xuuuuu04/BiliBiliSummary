import asyncio
import os
import sys

# Ensure src is in python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.backend.bilibili_service import BilibiliService

async def test_user_videos():
    service = BilibiliService()
    uid = 3493136900819691
    
    print(f"=== Testing User Info for UID: {uid} ===")
    user_res = await service.get_user_info(uid)
    if user_res['success']:
        print(f"User: {user_res['data']['name']}")
    else:
        print(f"User info failed: {user_res['error']}")

    print(f"\n=== Testing Recent Videos for UID: {uid} ===")
    recent_res = await service.get_user_recent_videos(uid, limit=10)
    if recent_res['success']:
        videos = recent_res['data']
        print(f"Found {len(videos)} videos.")
        for v in videos:
            print(f"  - {v['title']} ({v['bvid']}) | Play: {v['play']}")
    else:
        print(f"Recent videos failed: {recent_res['error']}")

if __name__ == '__main__':
    asyncio.run(test_user_videos())
