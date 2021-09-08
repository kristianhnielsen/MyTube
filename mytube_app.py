from datetime import datetime
import re
import tkinter as tk
from tkinter import ttk, messagebox
from urllib.error import HTTPError
import webbrowser
from tkinter.filedialog import askdirectory
import os
from threading import Thread
from difflib import SequenceMatcher
from pathlib import Path
import helium
from bs4 import BeautifulSoup
from time import sleep
from pytube import Playlist, YouTube, Channel, request, exceptions

WINDOW_HEIGHT = 300
WINDOW_WIDTH = 500
LABEL_WIDTH = 15
STANDARD_FONT = (14)
ENTRY_WIDTH = 40
DOWNLOAD_BUTTON_COLOR = 'lightgray'
DOWNLOAD_BUTTON_WIDTH = 18
DOWNLOAD_BUTTON_HEIGHT = 1

class Resolution:
    def __init__(self) -> None:
        self.options = [
            '144p',
            '360p',
            '480p',
            '720p'
            ]        
        self.default_res = self.options[3]

    
    def downgrade(self, current_resolution: str):
        next_resolution_index = self.options.index(current_resolution) - 1
        if next_resolution_index == -1:
            return None
        return self.options[next_resolution_index]


class App:
    def __init__(self, root) -> None:
        self.root = root
        self._root_setup()
        self._tabs_setup()
        self._generate_tabs(['Video', 'Channel', 'Playlist', 'Options', 'About'])
        self.options = {
            'resolution' : '',
            'dir' : ''
        }
        self._build_tabs()

    def _root_setup(self):
        self.root.title('MyTube')
        self.root.geometry(f'{WINDOW_WIDTH}x{WINDOW_HEIGHT}')
        self.root.maxsize(width=WINDOW_WIDTH, height=WINDOW_HEIGHT)
        self.root.minsize(width=WINDOW_WIDTH, height=WINDOW_HEIGHT)

    def _tabs_setup(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(pady=10)

    def _generate_tabs(self, tab_names: list):
        self.tabs = {}
        for tab_name in tab_names:
            self.tabs[tab_name] = tk.Frame(self.notebook, width=WINDOW_WIDTH, height=WINDOW_HEIGHT)

    def _build_tabs(self):
        for name, frame in self.tabs.items():
            frame.grid(columnspan=3)
            self.notebook.add(frame, text=name)


class OptionsTab:
    def __init__(self, app: App) -> None:
        self.frame = app.tabs.get('Options')
        self.messages = Messages()
        self.root = root
        self.res_elements = {}
        self.dir_elements = {}
        self.stringvars = {
            'resolution' : tk.StringVar(),
            'directory' : tk.StringVar()
        }
        self._generate_resolution_elements()
        self._generate_save_dir_elements()
        self._build()

    def _browse_dir(self):
        self.stringvars.get('directory').set(askdirectory(parent=self.frame))

    def _generate_resolution_elements(self):
        _resolution_options = Resolution().options
        self.stringvars['resolution'].set(Resolution().default_res)
        self.res_elements['label'] = tk.Label(self.frame, text='Preferred resolution', width=LABEL_WIDTH)
        self.res_elements['button'] = tk.OptionMenu(self.frame, self.stringvars.get('resolution'), *_resolution_options)

    def _generate_save_dir_elements(self):
        self.stringvars['directory'].set(os.getcwd())
        self.dir_elements['label'] = tk.Label(self.frame, text='Save in', width=LABEL_WIDTH)
        self.dir_elements['field'] = tk.Entry(self.frame, textvariable=self.stringvars.get('directory'), width=ENTRY_WIDTH)
        self.dir_elements['button'] = tk.Button(self.frame, text='Browse', command=self._browse_dir, width=10)

    def _build(self):
        self.res_elements['label'].grid(column=0, row=1, sticky=tk.W, padx=10, pady=15)
        self.res_elements['button'].grid(column=1, row=1, sticky=tk.W)

        self.dir_elements['label'].grid(column=0, row=2, sticky=tk.W, padx=10, pady=15)
        self.dir_elements['field'].grid(column=1, row=2, sticky=tk.W)
        self.dir_elements['button'].grid(column=2, row=2, sticky=tk.W, padx=5)

    def get_resolution(self):
        return self.stringvars.get('resolution').get()
    
    def get_save_dir(self):
        save_dir = self.stringvars.get('directory').get()
        if save_dir == None or save_dir.strip() == '':
            self.messages.invalid_save_dir()
            return
        return save_dir
        
   
class VideoTab:
    def __init__(self, app: App, options: OptionsTab) -> None:
        self.frame = app.tabs.get('Video')
        self.root = app.root
        self.options = options
        self.validate = Validate()
        self.messages = Messages()
        self.url = ''
        self.output_filename = None
        self.dl_button = None
        self.url_elements = {}
        self.rename_file_elements = {}
        self.stringvars = {
            'url' : tk.StringVar(),
            'filename' : tk.StringVar()
        }
        self._generate_download_button()
        self._generate_rename_file_elements()
        self._generate_url_elements()
        self._build()

    def _generate_url_elements(self):
        self.url_elements['label'] = tk.Label(self.frame, text='Video URL', width=LABEL_WIDTH)
        self.url_elements['field'] = tk.Entry(self.frame, width=ENTRY_WIDTH, textvariable=self.stringvars['url'])

    def _generate_rename_file_elements(self):
        self.rename_file_elements['label'] = tk.Label(self.frame, text='Rename file as', width=LABEL_WIDTH)
        self.rename_file_elements['field'] = tk.Entry(self.frame, width=ENTRY_WIDTH, textvariable=self.stringvars.get('filename'))

    def _generate_download_button(self):
        self.dl_button = tk.Button(self.frame, text='DOWNLOAD', bg=DOWNLOAD_BUTTON_COLOR, height=DOWNLOAD_BUTTON_HEIGHT, width=DOWNLOAD_BUTTON_WIDTH, command=self._start_video_download)

    def _start_video_download(self):
        thread = Thread(target=self.download)
        thread.start()

    def _build(self):
        self.url_elements.get('label').grid(column=0, row=0, sticky=tk.W, padx=10, pady=15)
        self.url_elements.get('field').grid(column=1, row=0, sticky=tk.W)

        self.rename_file_elements.get('label').grid(column=0, row=1, sticky=tk.W, padx=10)
        self.rename_file_elements.get('field').grid(column=1, row=1, sticky=tk.W)
        
        self.dl_button.grid(column=1, row=2, pady=10)

    def download(self):
        progress_bar = ProgressBar(self.root)
        filename = self.stringvars['filename'].get()        
        downloader = VideoDownloader(
            url=self.stringvars['url'].get(), 
            save_directory=self.validate.validate_save_directory(self.options.get_save_dir(), []),
            resolution=self.options.get_resolution(),
            )
        progress_bar.update_status_downloading(1, 1)
        downloader.set_progress_bar(progress_bar)
        downloader.set_output_filename(filename)
        downloader.add_resolution_prefix()
        try:
            downloader.download_video()
        except exceptions.RegexMatchError:
            progress_bar.kill()
            return Messages().invalid_video_url()
        progress_bar.kill()
        self.messages.download_complete()


class ChannelTab:
    def __init__(self, app: App, options: OptionsTab) -> None:
        self.frame = app.tabs.get('Channel')
        self.root = app.root
        self.validate = Validate()
        self.messages = Messages()
        self.output_filename = None
        self.a_tags = None
        self.dl_button = None
        self.channel_name_elements = {}
        self.keyword_elements = {}
        self.timeframe_elements = {}
        self.stringvars = {
            'channel name' : tk.StringVar(),
            'timeframe' : tk.StringVar(),
            'keywords' : tk.StringVar()
            }
        self.timeframe_options = {
            'Day' : 1,
            'Week' : 7,
            'Month' : 31,
            'Year' : 365,
            'All Time' : 10_000
            }
        
        self._generate_download_button()
        self._generate_channel_name_elements()
        self._generate_keyword_elements()
        self._generate_timeframe_elements()
        self._build()

    def _generate_channel_name_elements(self):
        self.channel_name_elements['label'] = tk.Label(self.frame, text='Channel name', width=LABEL_WIDTH)
        self.channel_name_elements['field'] = tk.Entry(self.frame, width=ENTRY_WIDTH, textvariable=self.stringvars['channel name'])
        
    def _generate_keyword_elements(self):
        self.keyword_elements['label'] = tk.Label(self.frame, text='Keywords', width=LABEL_WIDTH)
        self.keyword_elements['field'] = tk.Entry(self.frame, width=ENTRY_WIDTH, textvariable=self.stringvars['keywords'])

    def _generate_timeframe_elements(self):
        self.timeframe_elements['label'] = tk.Label(self.frame, text='Within the past', width=LABEL_WIDTH)
        self.stringvars['timeframe'].set('All Time')
        self.timeframe_elements['menu'] = tk.OptionMenu(self.frame, self.stringvars['timeframe'], *self.timeframe_options)

    def _generate_download_button(self):
        self.dl_button = tk.Button(self.frame, text='DOWNLOAD', bg=DOWNLOAD_BUTTON_COLOR, height=DOWNLOAD_BUTTON_HEIGHT, width=DOWNLOAD_BUTTON_WIDTH, command=self._start_channel_download)

    def _start_channel_download(self):
        '''Starts a new thread for channel download.'''
        thread = Thread(target=self.download_channel)
        thread.start()

    def _build(self):
        '''Places all the elements in the grid. Seperated from instancing for better overview.'''
        self.channel_name_elements['label'].grid(column=0, row=1, sticky=tk.W, padx=10, pady=15)
        self.channel_name_elements['field'].grid(column=1, row=1, sticky=tk.W)

        self.timeframe_elements['label'].grid(column=0, row=3, sticky=tk.EW, padx=10, pady=20)
        self.timeframe_elements['menu'].grid(column=1, row=3)

        self.keyword_elements['label'].grid(column=0, row=4, sticky=tk.EW, padx=10, pady=20)
        self.keyword_elements['field'].grid(column=1, row=4)

        self.dl_button.grid(column=1, row=5, pady=20, padx=10, sticky=tk.EW)

    def video_within_timeframe(self, video: YouTube):
        '''
        Returns True if video has been publishing within the given timeframe.
        Always returns True if the given timeframe is "All Time".
        '''
        if self.stringvars['timeframe'].get() == 'All Time':
            return True

        days_since_upload = (datetime.today() - video.publish_date).days
        if days_since_upload <= self.timeframe_options[self.stringvars['timeframe'].get()]:
            return True
        else:
            return False      

    def video_match_keywords(self, video: YouTube):
        '''Returns True if any keyword given by the user, matches the keywords set by the video'''
        user_keywords = self.stringvars['keywords'].get().split(',')

        # Default, no keywords
        if len(user_keywords) == 0:
            return True
        
        for video_keyword in video.keywords:
            for user_keyword in user_keywords:
                user_keyword = user_keyword.strip().lower()
                video_keyword = video_keyword.strip().lower()
                video_title = video.title.lower()

                user_keyword_in_video_title = re.search(re.compile(fr'{user_keyword}'), video_title)

                if user_keyword == video_keyword or user_keyword_in_video_title is not None:
                    return True
        
        return False

    def filter_channel_videos(self, channel: Channel):
        '''
        Return a list of YouTube object which, 
        matches any timeframe,  
        and contains the keywords given, if any.

        Keyword searches returns True if
        keyword is found in the keywords given by the author, 
        or in the the video title.

        Since video keywords may contain sentences, 
        keywords given by the user will only be seperated by commas (,). 
        '''

        macthing_videos = []
        for video in channel.videos:
            if self.video_within_timeframe(video):
                if self.video_match_keywords(video):
                    macthing_videos.append(video) 
            else:
                # the channel.videos list is ordered by newest first, 
                # so if timeframe does not match once, the following won't match either.
                break 
        return macthing_videos

    def download_channel(self):
        '''
        Primary method of this class.
        Downloads any videos from the channel which meets the conditions given.
        '''
        progress_bar = ProgressBar(self.root)
        if self.stringvars['channel name'].get() == '':
            self.messages.invalid_channel_name()
            progress_bar.kill()
            return
        progress_bar.update_status('Searching for channel')
        channel_name = self.validate.validate_channel_name(self.stringvars['channel name'].get())
        channel = Channel(f"https://www.youtube.com/c/{channel_name}")

        try:
            if len(channel.videos) == 0:
                self.messages.invalid_channel_name()
                progress_bar.kill()
                return
        except HTTPError:
            self.messages.connection_error()
            progress_bar.kill()
            return 

        progress_bar.update_status('Looking for videos')
        filtered_videos = self.filter_channel_videos(channel)
        if len(filtered_videos) == 0:
            progress_bar.kill()
            self.messages.no_videos_found()
            return 

        for index, video in enumerate(filtered_videos):
            progress_bar.update_status_downloading(index, len(filtered_videos))
            downloader = VideoDownloader(
                url=video.watch_url, 
                resolution=options.get_resolution(), 
                save_directory=self.validate.validate_save_directory(options.get_save_dir(), [video.author])
                )
            downloader.set_progress_bar(progress_bar)
            downloader.add_resolution_prefix()
            downloader.download_video()
        
        progress_bar.kill()
        self.messages.download_complete()


class PlaylistTab:
    def __init__(self, app: App, options: OptionsTab) -> None:
        self.root = app.root
        self.url_frame = tk.Frame(app.tabs.get('Playlist'), width=WINDOW_WIDTH, height=WINDOW_HEIGHT/2)
        self.playlist_frame = tk.Frame(app.tabs.get('Playlist'), width=WINDOW_WIDTH, height=WINDOW_HEIGHT/2)
        self.validate = Validate() 
        self.messages = Messages()
        self.output_filename = None
        self.temp_playlist_data = []
        self.url_elements = {}
        self.channel_elements = {}
        self.playlist_elements = {}
        self.stringvars = {
            'url' : tk.StringVar(),
            'channel name' : tk.StringVar(),
            'playlist name' : tk.StringVar()
            }
        self.timeframe_options = {
            'Day' : 1,
            'Week' : 7,
            'Month' : 31,
            'Year' : 365,
            'All Time' : 10_000
            }
        self._generate_channel_name_elements()
        self._generate_playlist_name_elements()
        self._generate_url_elements()
        self._build()

    def _generate_url_elements(self):
        self.url_elements['label'] = tk.Label(self.url_frame, text='Playlist URL', width=LABEL_WIDTH)
        self.url_elements['field'] = tk.Entry(self.url_frame, width=ENTRY_WIDTH, textvariable=self.stringvars['url'])
        self.url_elements['button'] = tk.Button(self.url_frame, text='DOWNLOAD', bg=DOWNLOAD_BUTTON_COLOR, height=DOWNLOAD_BUTTON_HEIGHT, width=DOWNLOAD_BUTTON_WIDTH, command=self._start_playlist_download)

    def _generate_channel_name_elements(self):
        self.channel_elements['label'] = tk.Label(self.playlist_frame, text='Channel name', width=LABEL_WIDTH)
        self.channel_elements['field'] = tk.Entry(self.playlist_frame, width=ENTRY_WIDTH, textvariable=self.stringvars['channel name'])
   
    def _generate_playlist_name_elements(self):
        self.playlist_elements['label'] = tk.Label(self.playlist_frame, text='Playlist name', width=LABEL_WIDTH)
        self.playlist_elements['field'] = tk.Entry(self.playlist_frame, width=ENTRY_WIDTH, textvariable=self.stringvars['playlist name'])
        self.playlist_elements['button'] = tk.Button(self.playlist_frame, text='DOWNLOAD', bg=DOWNLOAD_BUTTON_COLOR, height=DOWNLOAD_BUTTON_HEIGHT, width=DOWNLOAD_BUTTON_WIDTH, command=self._start_channel_playlist_download)

    def _validate_channel_name(self, channel_name: str):
        '''
        Returns a string without whitespace.
        To prevent user from downloading the wrong channel, e.g. the channel 'tech', when searching for channel name 'tech tips'.
        '''
        return channel_name.replace(' ', '').strip()

    def _start_playlist_download(self):
        '''Starts a new thread for channel download.'''
        if self.stringvars['url'].get() == '':
            self.messages.invalid_playlist_url()
            return
        thread = Thread(target=self.download_playlist)
        thread.start()

    def _start_channel_playlist_download(self):
        '''Starts a new thread for channel download.'''
        if self.stringvars['channel name'].get() == '':
            self.messages.invalid_channel_name()
            return 
        elif self.stringvars['playlist name'] == '':
            self.messages.invalid_playlist_name()
            return 
        user_accept = self.messages.process_time_warning()
        if not user_accept:
            return
        thread = Thread(target=self.download_channel_playlist)
        thread.start()

    def _build(self):
        '''Places all the elements in the grid. Seperated from instancing for better overview.'''
        self.url_frame.grid(columnspan=3)
        self.playlist_frame.grid(columnspan=3)

        self.url_elements['label'].grid(column=0, row=0, sticky=tk.W, padx=10, pady=15)
        self.url_elements['field'].grid(column=1, row=0, sticky=tk.W)
        self.url_elements['button'].grid(column=1, row=1, pady=10)
     
        self.channel_elements['label'].grid(column=0, row=0, sticky=tk.W, padx=10, pady=15)
        self.channel_elements['field'].grid(column=1, row=0, sticky=tk.W)

        self.playlist_elements['label'].grid(column=0, row=1, sticky=tk.W, padx=10, pady=15)
        self.playlist_elements['field'].grid(column=1, row=1, sticky=tk.W)
        self.playlist_elements['button'].grid(column=1, row=2, pady=10)

    def _get_playlist_data(self):
        url = f"https://www.youtube.com/c/{self.stringvars['channel name'].get()}/playlists"
        playlist_data = []
        with helium.start_firefox(url, headless=True) as browser:
            if browser.current_url.startswith('https://consent.youtube.com'):
                helium.press(helium.PAGE_DOWN)
                helium.click(helium.Button("I agree"))
            sleep(10)
            soup = BeautifulSoup(browser.page_source, 'html.parser')
            for a_tag in soup.find_all('a', id='video-title'):
                playlist_data.append([a_tag.attrs['title'], a_tag.attrs['href']])
        return playlist_data

    def _generate_playlists(self):
        playlists = []
        for a_tag in self.a_tags:
            playlist_id = a_tag.attrs['href']
            playlists.append(Playlist(f'https://www.youtube.com{playlist_id}'))

        return playlists

    def _similar(self, a: str, b: str):
        '''Returns a float percentage of how similiar two strings are.'''
        return SequenceMatcher(None, a, b).quick_ratio()

    def _suggest_playlist(self, playlist: Playlist):
        '''Suggest a playlist to user.'''
        return self.messages.suggest_playlist(playlist)

    def find_playlist(self):
        '''Returns the Playlist object of it matches the playlist name, the user is looking for.'''
        playlist_name = self.stringvars['playlist name'].get()
        playlist_data = self._get_playlist_data()

        for playlist in playlist_data:
            title = playlist[0]
            href = playlist[1]
            if playlist_name.lower() == title.lower():
                return Playlist(href) 
        else:
            # if no 100% match, look for 85%+ matches
            for playlist in playlist_data:
                title = playlist[0]
                href = playlist[1]
                if self._similar(playlist_name.lower(), title.lower()) >= 0.85:
                    playlist = Playlist(href)
                    accept_suggestion = self._suggest_playlist(playlist)
                    if accept_suggestion:
                        return playlist
            self.messages.channel_playlist_not_found()
            return None

    def download_playlist(self):
        progress_bar = ProgressBar(self.root)
        progress_bar.update_status('Searching for playlist')
        playlist = Playlist(self.stringvars['url'].get())

        progress_bar.update_status('Finding videos in playlist')
        if len(playlist.videos) == 0 or playlist._html is None:
            self.messages.invalid_playlist_url()
            progress_bar.kill()
            return

        for index, video in enumerate(playlist.videos):
            progress_bar.update_status_downloading(index, len(playlist.videos))
            downloader = VideoDownloader(
                url=video.watch_url, 
                resolution=options.get_resolution(), 
                save_directory=self.validate.validate_save_directory(options.get_save_dir(), [video.author, playlist.title])
                )
            downloader.set_progress_bar(progress_bar)
            downloader.add_resolution_prefix()
            downloader.download_video()
        
        progress_bar.kill()
        self.messages.download_complete()
    
    def download_channel_playlist(self):
        progress_bar = ProgressBar(self.root)
        progress_bar.update_status('Searching for playlist')
        relevant_playlist = self.find_playlist()
        
        progress_bar.update_status('Finding videos in playlist')
        if relevant_playlist is None:
            # Either wrong channel name or channel has no playlists
            progress_bar.kill()
            return
        
        for index, video in enumerate(relevant_playlist.videos):
            progress_bar.update_status_downloading(index, len(relevant_playlist.videos))
            downloader = VideoDownloader(
                url=video.watch_url, 
                resolution=options.get_resolution(), 
                save_directory=self.validate.validate_save_directory(options.get_save_dir(), [video.author])
                )
            downloader.set_progress_bar(progress_bar)
            downloader.add_resolution_prefix()
            downloader.download_video()
        
        progress_bar.kill()
        self.messages.download_complete()


class AboutTab:
    def __init__(self, app: App) -> None:
        self.frame = app.tabs.get('About')
        self.root = app.root
        self.messages = Messages()
        self.stringvars = {
            'about' : tk.StringVar(),
            'filename' : tk.StringVar()
        }
        self.elements = {}
        self._generate_elements()
        self._build()
    
    def _generate_elements(self):
        self.elements['about'] = tk.Label(self.frame, text='About')
        self.elements['disclaimer'] = tk.Label(self.frame, text='This software is only for educational use.\nThe author takes no responsibility for downloading unauthorized content.')
        self.elements['github'] = tk.Label(self.frame, text='Github', fg="blue", cursor="hand2")
        self.elements['license'] = tk.Label(self.frame, text='License', fg="blue", cursor="hand2")

    def _open_hyperlink(self, url: str):
        webbrowser.open_new(url)

    def _build(self):
        self.elements['about'].pack(fill='x', pady=10)
        self.elements['disclaimer'].pack(fill='x', pady=10)
        self.elements['github'].pack(fill='none', pady=10)
        self.elements['license'].pack(fill='none', pady=10)
        self.elements['github'].bind('<Button-1>', lambda e: self._open_hyperlink("https://github.com/kristianhnielsen/MyTube"))
        self.elements['license'].bind('<Button-1>', lambda e: self._open_hyperlink("https://github.com/kristianhnielsen/MyTube/blob/main/LICENSE"))


class ProgressBar:
    def __init__(self, root: tk.Tk) -> None:
        self.top = tk.Toplevel(root)
        self.video_name = tk.StringVar()
        self.status = tk.StringVar()
        self.download_percentage = tk.StringVar()
        
        self._setup_window()
        self.bar = ttk.Progressbar(self.top, orient=tk.HORIZONTAL, length=100, mode='determinate')
        self.video_name_label = tk.Label(self.top, textvariable=self.video_name)
        self.status_label = tk.Label(self.top, textvariable=self.status)
        self.download_percentage_label = tk.Label(self.top, textvariable=self.download_percentage)
        self.update_status('Getting ready...')
        self._update_download_percent(0.0)
        self.cancel_button = tk.Button(self.top, text='Cancel', command=self.top.destroy)
        self._build()
    
    def _build(self):
        self.video_name_label.pack(expand=True, fill='both', pady=5, padx=10, anchor=tk.NW)
        self.status_label.pack(expand=True, fill='both', pady=5, padx=10, anchor=tk.N)
        self.bar.pack(expand=True, pady=10, fill='both', padx=15)
        self.download_percentage_label.pack(expand=True, fill='both', pady=5, padx=10, anchor=tk.N)
        self.cancel_button.pack(expand=True, pady=15)

    def _setup_window(self):
        self.top.title("Progress")
        self.window_width = 400
        self.window_height = 200
        self.top.geometry(f'{self.window_width}x{self.window_height}')

    def update_video_name(self, name: str):
        self.video_name.set(name)

    def update_status_downloading(self, item_num: int, total_item_num: int):
        if self.download_percentage.get() == "100%":
            self.update_status('Download complete\nPreparing for the next download!')
        else:  
            self.update_status(f'Downloading video {item_num + 1} of {total_item_num}')

    def update_status(self, new_status: str):
        self.status.set(new_status)

    def _update_download_percent(self, dl_percent: float):
        if dl_percent == 100.0:
            self.download_percentage.set('100%')
            return
        self.download_percentage.set(f'{dl_percent:.1f}%')

    def update_progress(self, percent: float):
        self.bar['value'] = percent
        self._update_download_percent(percent)
       
    def kill(self):
        self.top.destroy()


class VideoDownloader:
    def __init__(self, url: str, save_directory=os.getcwd(), resolution=Resolution().default_res) -> None:
        self.url = url
        self.progress_bar = None
        self.resolution = resolution
        self.output_filename = None
        self.save_directory = save_directory
        self.resolution_prefix = False
        self.percent_downloaded = 0
    
    def _validate_filename(self):
        if self.output_filename.strip() == '':
            return None
        if not self.output_filename.endswith('mp4'):
            self.output_filename += '.mp4'
        return self.output_filename

    def _call_on_progress_each_MB(self, MB: int):
        # on_progress_callback called every X MB downloaded
        request.default_range_size = 1048576 * MB 

    def progress_check(self, stream=None, chunk = None, remaining = None):
        # Gets the percentage of the file that has been downloaded.
        percent_downloaded = (100*(stream.filesize - remaining))/stream.filesize
        self.progress_bar.update_progress(percent_downloaded)
        self.progress_bar.update_video_name(f'Video: {self.currently_downloading_title}')
        
    def add_resolution_prefix(self):
        self.resolution_prefix = True
    
    def set_resolution(self, res: str):
        if res in Resolution().options:
            self.resolution = res
    
    def set_output_filename(self, output_name: str):  
        self.output_filename = output_name  
    
    def set_save_directory(self, save_directory: str):
        self.save_directory = save_directory
    
    def get_possible_resolutions(self, streams):
        possible_resolutions = []
        for stream in streams.filter(type='mp4'):
            res_num = int(stream.resolution[:-1])
            if res_num not in possible_resolutions:
                possible_resolutions.append(res_num)

        possible_resolutions = sorted(possible_resolutions)

        return possible_resolutions

    def set_progress_bar(self, bar: ProgressBar):
        self.progress_bar = bar

    def download_video(self):
        self._call_on_progress_each_MB(1)
        video = YouTube(url=self.url, on_progress_callback=self.progress_check)
        self.currently_downloading_title = video.title
        if self.resolution is None:
            return

        prefix = None
        if self.resolution_prefix:
            prefix = f'[{self.resolution}] '
        try:
            stream = video.streams.filter(
                type='video',
                res=self.resolution,
                progressive=True
                ).first()
            stream.download(
                            output_path=self.save_directory,
                            filename_prefix=prefix
                            )
        except AttributeError:
            # The resolution wanted, was not available. Reducing to the next available resolution and retry.
            self.resolution = Resolution().downgrade(self.resolution)
            self.download_video()
        except tk._tkinter.TclError:
            # Download was stopped unexpectedly (probably manually)
            # Delete current file, as the download is incomplete
            Messages().download_stopped()
            os.unlink(stream.get_file_path(output_path=self.save_directory, filename_prefix=prefix))


class Messages:
    def download_complete(self):
        t = 'Complete'
        m = 'Download complete!'
        return messagebox.showinfo(title=t, message=m)
    
    def no_videos_found(self):
        t = 'No videos'
        m = 'Could not find any videos matching the requirements'
        return messagebox.showerror(title=t, message=m)
    
    def download_stopped(self):
        t = 'Download stopped'
        m = 'Current download has stopped unexpectedly'
        return messagebox.showerror(title=t, message=m)
   
    def connection_error(self):
        t = 'Connection error'
        m = 'Something went wrong\nPlease check your internet connection and try again'
        return messagebox.showerror(title=t, message=m)
    
    def invalid_channel_name(self):
        t = 'Invalid channel name'
        m = 'Please enter a valid Youtube channel name'
        return messagebox.showerror(title=t, message=m)

    def invalid_playlist_url(self):
        t = 'Invalid URL'
        m = 'Please enter a valid Youtube playlist URL'
        return messagebox.showerror(title=t, message=m)
 
    def channel_playlist_not_found(self):
        t = 'Playlist Error'
        m = 'Channel playlists not found'
        return messagebox.showerror(title=t, message=m)

    def invalid_playlist_name(self):
        t = 'Invalid playlist name'
        m = 'Please enter a valid playlist name'
        return messagebox.showerror(title=t, message=m)

    def invalid_video_url(self):
        t = 'Invalid URL'
        m = 'Please enter a valid YouTube URL'
        return messagebox.showerror(title=t, message=m)

    def invalid_save_dir(self):
        t = 'Invalid directory'
        m = 'Please enter a valid save directory'
        return messagebox.showerror(title=t, message=m)

    def process_time_warning(self):
        t = 'Process time warning'
        m = 'WARNING!\n\nThis method is very slow.\nIt is highly recommended to use the playlist URL function instead.\n\nDo you want to continue anyways?'
        return messagebox.askyesno(title=t, message=m)

    def suggest_playlist(self, playlist: Playlist):
        t = 'Suggestion'
        m = f'Found the playlist called {playlist.title}\nThe name looks similar to what you were looking for!\nDo you want to download it?'
        return messagebox.askyesno(title=t, message=m)


class Validate:
    def _delete_special_chars(self, text: str):
        special_chars = ['\\', '/', '|', ':', '&', '*', '?', '>', '<']
        for char in special_chars:
            text = text.replace(char, '')
        return text

    def validate_save_directory(self, base_save_dir: str, subfolders: list):
        validated_subfolders = []
        for subfolder in subfolders:
            validated_subfolders.append(self._delete_special_chars(subfolder))

        validated_subfolders = '/'.join(validated_subfolders)
        path = Path(base_save_dir).joinpath(validated_subfolders)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def validate_channel_name(self, channel_name: str):
        '''
        Returns a string without whitespace.
        To prevent user from downloading the wrong channel, e.g. the channel 'tech', when searching for channel name 'tech tips'.
        '''
        return channel_name.replace(' ', '').strip()

def main():
    root = tk.Tk()
    app = App(root)

    options = OptionsTab(app)
    video = VideoTab(app, options=options)
    channel = ChannelTab(app, options=options)
    playlist = PlaylistTab(app, options=options)
    about = AboutTab(app)

    root.mainloop()

if __name__ == '__main__':
    main()