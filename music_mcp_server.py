#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
免费音乐 MCP 服务器（stdio 版）

供 mcp_pipe.py 拉起，由 mcp_pipe 转发小智接入点的请求。
注意：工具返回的是文本，当前曲库为模拟数据，不会真的在设备上播放音频。
"""

import logging
from typing import Any, Dict, List

from mcp.server.fastmcp import FastMCP

# 日志必须走 stderr，stdout 留给 JSON-RPC
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP("music-mcp-server")

# 模拟音乐数据库
MOCK_MUSIC_DATABASE: List[Dict[str, Any]] = [
    {"id": "1", "name": "青花瓷", "artist": "周杰伦", "album": "我很忙", "duration": 238},
    {"id": "2", "name": "稻香", "artist": "周杰伦", "album": "魔杰座", "duration": 223},
    {"id": "3", "name": "夜曲", "artist": "周杰伦", "album": "十一月的萧邦", "duration": 237},
    {"id": "4", "name": "告白气球", "artist": "周杰伦", "album": "周杰伦的床边故事", "duration": 207},
    {"id": "5", "name": "晴天", "artist": "周杰伦", "album": "叶惠美", "duration": 269},
    {"id": "6", "name": "演员", "artist": "薛之谦", "album": "绅士", "duration": 253},
    {"id": "7", "name": "体面", "artist": "于文文", "album": "体面", "duration": 247},
    {"id": "8", "name": "成都", "artist": "赵雷", "album": "无法长大", "duration": 327},
    {"id": "9", "name": "南山南", "artist": "马頔", "album": "孤岛", "duration": 293},
    {"id": "10", "name": "理想", "artist": "赵雷", "album": "吉姆餐厅", "duration": 279},
]

# 播放状态
playback_state: Dict[str, Any] = {
    "current_song": None,
    "playlist": [],
    "is_playing": False,
    "volume": 50,
    "position": 0,
}


def _search(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    query_lower = query.lower()
    results = [
        song
        for song in MOCK_MUSIC_DATABASE
        if query_lower in song["name"].lower()
        or query_lower in song["artist"].lower()
        or query_lower in song["album"].lower()
    ][:limit]
    return results or MOCK_MUSIC_DATABASE[:limit]


@mcp.tool()
def search_music(query: str, limit: int = 10) -> str:
    """搜索音乐，支持按歌曲名、歌手名、专辑名搜索。"""
    results = _search(query, limit)
    lines = [f"搜索 '{query}' 的结果：\n"]
    for i, song in enumerate(results, 1):
        lines.append(f"{i}. {song['name']} - {song['artist']}")
        lines.append(f"   专辑: {song['album']}")
        lines.append(f"   时长: {song['duration']}秒")
        lines.append(f"   ID: {song['id']}\n")
    return "\n".join(lines)


@mcp.tool()
def play_music(song_id: str, song_name: str = "未知歌曲", artist: str = "未知歌手") -> str:
    """播放指定歌曲，需要先通过 search_music 拿到 song_id。"""
    playback_state["current_song"] = {"id": song_id, "name": song_name, "artist": artist}
    playback_state["is_playing"] = True
    playback_state["position"] = 0
    return f"正在播放: {song_name} - {artist}"


@mcp.tool()
def pause_music() -> str:
    """暂停当前播放的音乐。"""
    playback_state["is_playing"] = False
    return "音乐已暂停"


@mcp.tool()
def resume_music() -> str:
    """继续播放已暂停的音乐。"""
    playback_state["is_playing"] = True
    current = playback_state["current_song"]
    if current:
        return f"继续播放: {current['name']} - {current['artist']}"
    return "没有可继续播放的歌曲"


@mcp.tool()
def stop_music() -> str:
    """停止播放音乐。"""
    playback_state["is_playing"] = False
    playback_state["current_song"] = None
    playback_state["position"] = 0
    return "音乐已停止"


@mcp.tool()
def set_volume(volume: int) -> str:
    """设置播放音量，范围 0-100。"""
    volume = max(0, min(100, volume))
    playback_state["volume"] = volume
    return f"音量已设置为: {volume}%"


@mcp.tool()
def add_to_playlist(song_id: str, song_name: str = "未知歌曲", artist: str = "未知歌手") -> str:
    """将歌曲添加到播放列表。"""
    playback_state["playlist"].append({"id": song_id, "name": song_name, "artist": artist})
    return f"已添加到播放列表: {song_name} - {artist}"


@mcp.tool()
def get_playlist() -> str:
    """获取当前播放列表。"""
    playlist = playback_state["playlist"]
    if not playlist:
        return "播放列表为空"
    lines = ["当前播放列表:\n"]
    for i, song in enumerate(playlist, 1):
        lines.append(f"{i}. {song['name']} - {song['artist']}")
    return "\n".join(lines)


@mcp.tool()
def clear_playlist() -> str:
    """清空播放列表。"""
    playback_state["playlist"] = []
    return "播放列表已清空"


@mcp.tool()
def next_song() -> str:
    """播放下一首歌曲。"""
    playlist = playback_state["playlist"]
    if not playlist:
        return "播放列表为空，无法切换到下一首"
    current = playback_state["current_song"]
    if current:
        try:
            index = next(i for i, s in enumerate(playlist) if s["id"] == current["id"])
            index = (index + 1) % len(playlist)
        except StopIteration:
            index = 0
    else:
        index = 0
    song = playlist[index]
    playback_state["current_song"] = song
    playback_state["is_playing"] = True
    return f"下一首: {song['name']} - {song['artist']}"


@mcp.tool()
def previous_song() -> str:
    """播放上一首歌曲。"""
    playlist = playback_state["playlist"]
    if not playlist:
        return "播放列表为空，无法切换到上一首"
    current = playback_state["current_song"]
    if current:
        try:
            index = next(i for i, s in enumerate(playlist) if s["id"] == current["id"])
            index = (index - 1) % len(playlist)
        except StopIteration:
            index = len(playlist) - 1
    else:
        index = len(playlist) - 1
    song = playlist[index]
    playback_state["current_song"] = song
    playback_state["is_playing"] = True
    return f"上一首: {song['name']} - {song['artist']}"


if __name__ == "__main__":
    logger.info("启动免费音乐 MCP 服务器 (stdio)")
    mcp.run(transport="stdio")
