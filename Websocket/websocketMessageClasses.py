from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional
from python_to_typescript_interfaces import Interface
from realtime import List

@dataclass
class WebsocketMessageType(Interface, Enum):
    NULL = ""
    INIT = "init"
    SEND_MESSAGE = "sendMessage"
    SET_REMINDER = "setReminder"
    VOICE_STATE_UPDATE = "voiceStateUpdate"
    GET_MUSIC_PLAYLIST = "getMusicPlaylist"
    PLAYLIST_STATE_UPDATE = "playlistStateUpdate"
    PLAYLIST_SONG_SKIP = "playlistSongSkip"
    PLAYLIST_PAUSE = "playlistPause"
    PLAYLIST_RESUME = "playlistResume"
    PRESENCE_UPDATE = "presenceUpdate"
    TOGGLE_ROLE = "toggleRole"

@dataclass
class MemberStatus(Interface, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    IDLE = "idle"
    DND = "dnd"
    INVISIBLE = "invisible"

@dataclass
class ChannelType(Interface, Enum):
    Text = "0"
    DM = "1"
    Voice = "2"
    GroupDM = "3"
    Category = "4"
    News = "5"
    Store = "6"
    NewsThread = "10"
    PublicThread = "11"
    PrivateThread = "12"
    StageVoice = "13"
    Directory = "14"
    Forum = "15"
    GuildDirectory = "16"

@dataclass
class WebsocketInitChannels(Interface):
    channelId: str
    name: str
    connectedMemberIds: List[str]
    type: ChannelType

@dataclass
class WebsocketInitMembers(Interface):
    memberId: str
    avatarUrl: str
    name: str
    displayName: str
    bot: bool
    roleIds: List[str]
    activityName: Optional[str]
    status: MemberStatus

@dataclass
class WebsocketInitRoles(Interface):
    id: str
    name: str
    priority: int
    color: str
    displaySeparately: bool

@dataclass
class WebsocketInitServer(Interface):
    guildId: str
    guildName: str
    iconUrl: Optional[str]
    channels: Optional[List[WebsocketInitChannels]]
    members: Optional[List[WebsocketInitMembers]]
    roles: Optional[List[WebsocketInitRoles]]

@dataclass
class WebsocketInitResponse(Interface):
    gmtOffsetInHour: int
    servers: Optional[List[WebsocketInitServer]] 

@dataclass
class WebsocketSendMessageQuery(Interface):
    serverId: str
    channelId: str
    text: str

@dataclass
class WebsocketSetReminderQuery(Interface):
    serverId: str
    channelId: str
    memberId: str
    text: str
    date: datetime


@dataclass
class WebsocketIncomingMessageResponse(Interface):
    serverId: str
    channelId: str
    userId: str
    messageId: str
    text: str
    epoch: int

@dataclass
class WebsocketVoiceStateUpdateQuery(Interface):
    serverId: str
    channelId: str
    isDisconnect: bool

@dataclass
class WebsocketVoiceStateUpdateResponse(Interface):
    serverId: str
    memberId: str
    beforeChannel: Optional[str]
    afterChannel: Optional[str]
    epoch: int

@dataclass
class WebsocketGetMusicPlaylistQuery(Interface):
    serverId: str

""""""
@dataclass
class WebsocketMusic(Interface):
    index: int
    title: str
    artist: str
    lengthStr: str
    length: int
    filename: str

@dataclass
class WebsocketPlaylistState(Interface):
    serverId: str
    selectedSong: WebsocketMusic
    selectedModifiedAt: int
    isPlaying: bool
    songs: List[WebsocketMusic]
    playedDuration: int
""""""

@dataclass
class WebsocketGetMusicPlaylistResponse(Interface):
    serverId: str
    playlistState: WebsocketPlaylistState

@dataclass
class WebsocketPlaylistStateUpdateQuery(Interface):
    serverId: str

@dataclass
class WebsocketPlaylistStateUpdateResponse(Interface):
    serverId: str
    selectedSong: WebsocketMusic
    selectedModifiedAt: int
    isPlaying: bool
    playedDuration: int

@dataclass
class WebsocketPlaylistSongSkipQuery(Interface):
    serverId: str
    songIndex: int

@dataclass
class WebsocketPlaylistPauseQuery(Interface):
    serverId: str

@dataclass
class WebsocketPlaylistResumeQuery(Interface):
    serverId: str

@dataclass
class WebsocketPresenceUpdateResponse(Interface):
    serverId: str
    memberId: str
    newStatus: MemberStatus
    newDisplayName: str
    newActivityName: Optional[str]

@dataclass
class WebsocketToggleRoleQuery(Interface):
    serverId: str
    roleId: str
    memberId: str

@dataclass
class WebsocketToggleRoleResponse(Interface):
    serverId: str
    roleId: str
    memberId: str
    roleIsAdded: bool
