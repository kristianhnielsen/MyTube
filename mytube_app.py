from datetime import datetime
import re
from tkinter import *
from tkinter import ttk, messagebox
from tkinter.filedialog import askdirectory
import os
import threading
from pytube import Playlist, YouTube, Channel
from requests_html import HTMLSession
from difflib import SequenceMatcher



WINDOW_HEIGHT = 400
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
        self._generate_tabs(['Video', 'Channel', 'Playlist', 'Options'])
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
            self.tabs[tab_name] = Frame(self.notebook, width=WINDOW_WIDTH, height=WINDOW_HEIGHT)

    def _build_tabs(self):
        for name, frame in self.tabs.items():
            frame.grid(columnspan=3)
            self.notebook.add(frame, text=name)


class OptionsTab:
    def __init__(self, frame: Frame) -> None:
        self.frame = frame
        self.root = root
        self.res_elements = {}
        self.dir_elements = {}
        self.stringvars = {
            'resolution' : StringVar(),
            'directory' : StringVar()
        }
        self._generate_resolution_elements()
        self._generate_save_dir_elements()
        self._build()

    def _browse_dir(self):
        self.stringvars.get('directory').set(askdirectory(parent=self.frame))

    def _generate_resolution_elements(self):
        _resolution_options = Resolution().options
        self.stringvars['resolution'].set(Resolution().default_res)
        self.res_elements['label'] = Label(self.frame, text='Preferred resolution', width=LABEL_WIDTH)
        self.res_elements['button'] = OptionMenu(self.frame, self.stringvars.get('resolution'), *_resolution_options)

    def _generate_save_dir_elements(self):
        self.stringvars['directory'].set(os.getcwd())
        self.dir_elements['label'] = Label(self.frame, text='Save in', width=LABEL_WIDTH)
        self.dir_elements['field'] = Entry(self.frame, textvariable=self.stringvars.get('directory'), width=ENTRY_WIDTH)
        self.dir_elements['button'] = Button(self.frame, text='Browse', command=self._browse_dir, width=10)

    def _build(self):
        self.res_elements['label'].grid(column=0, row=1, sticky=W, padx=10, pady=15)
        self.res_elements['button'].grid(column=1, row=1, sticky=W)

        self.dir_elements['label'].grid(column=0, row=2, sticky=W, padx=10, pady=15)
        self.dir_elements['field'].grid(column=1, row=2, sticky=W)
        self.dir_elements['button'].grid(column=2, row=2, sticky=W, padx=5)

    def get_resolution(self):
        return self.stringvars.get('resolution').get()
    
    def get_save_dir(self):
        save_dir = self.stringvars.get('directory').get()
        if save_dir == None or save_dir.strip() == '':
            messagebox.showerror(title='Save directory error', message='Please enter a valid save directory.')
            return
        return save_dir
        
   
class VideoTab:
    def __init__(self, frame: Frame, options: OptionsTab) -> None:
        self.frame = frame
        self.url = ''
        self.output_filename = None
        self.dl_button = None
        self.url_elements = {}
        self.rename_file_elements = {}
        self.stringvars = {
            'url' : StringVar(),
            'filename' : StringVar()
        }
        self._generate_download_button()
        self._generate_rename_file_elements()
        self._generate_url_elements()
        self._build()

    def _generate_url_elements(self):
        self.url_elements['label'] = Label(self.frame, text='Video URL', width=LABEL_WIDTH)
        self.url_elements['field'] = Entry(self.frame, width=ENTRY_WIDTH, textvariable=self.stringvars['url'])

    def _generate_rename_file_elements(self):
        self.rename_file_elements['label'] = Label(self.frame, text='Rename file as', width=LABEL_WIDTH)
        self.rename_file_elements['field'] = Entry(self.frame, width=ENTRY_WIDTH, textvariable=self.stringvars.get('filename'))

    def _generate_download_button(self):
        self.dl_button = Button(self.frame, text='DOWNLOAD', bg=DOWNLOAD_BUTTON_COLOR, height=DOWNLOAD_BUTTON_HEIGHT, width=DOWNLOAD_BUTTON_WIDTH, command=self._start_video_download)

    def _start_video_download(self):
        thread = threading.Thread(target=self.download)
        thread.start()
        messagebox.showinfo(title='Complete', message='Download complete!')

    def _validate_url(self, url: str):
        if url == '' or url is None:
            messagebox.showerror(title='No URL found', message='Please enter a valid YouTube URL')
            return
        return url

    def _build(self):
        self.url_elements.get('label').grid(column=0, row=0, sticky=W, padx=10, pady=15)
        self.url_elements.get('field').grid(column=1, row=0, sticky=W)

        self.rename_file_elements.get('label').grid(column=0, row=1, sticky=W, padx=10)
        self.rename_file_elements.get('field').grid(column=1, row=1, sticky=W)
        
        self.dl_button.grid(column=1, row=2, pady=10)

    def download(self):    
        filename = self.stringvars['filename'].get()
        url = self._validate_url(self.stringvars['url'].get())
        downloader = VideoDownloader(
            url=url, 
            save_directory=options.get_save_dir(),
            resolution=options.get_resolution()
            )
        downloader.set_output_filename(filename)
        downloader.add_resolution_prefix()
        downloader.download_video()


class ChannelTab:
    def __init__(self, frame: Frame, options: OptionsTab) -> None:
        self.frame = frame
        self.output_filename = None
        self.a_tags = None
        self.dl_button = None
        self.channel_name_elements = {}
        self.keyword_elements = {}
        self.timeframe_elements = {}
        self.stringvars = {
            'channel name' : StringVar(),
            'timeframe' : StringVar(),
            'keywords' : StringVar()
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
        self.channel_name_elements['label'] = Label(self.frame, text='Channel name', width=LABEL_WIDTH)
        self.channel_name_elements['field'] = Entry(self.frame, width=ENTRY_WIDTH, textvariable=self.stringvars['channel name'])
        
    def _generate_keyword_elements(self):
        self.keyword_elements['label'] = Label(self.frame, text='Keywords', width=LABEL_WIDTH)
        self.keyword_elements['field'] = Entry(self.frame, width=ENTRY_WIDTH, textvariable=self.stringvars['keywords'])

    def _generate_timeframe_elements(self):
        self.timeframe_elements['label'] = Label(self.frame, text='Within the past', width=LABEL_WIDTH)
        self.stringvars['timeframe'].set('All Time')
        self.timeframe_elements['menu'] = OptionMenu(self.frame, self.stringvars['timeframe'], *self.timeframe_options)

    def _generate_download_button(self):
        self.dl_button = Button(self.frame, text='DOWNLOAD', bg=DOWNLOAD_BUTTON_COLOR, height=DOWNLOAD_BUTTON_HEIGHT, width=DOWNLOAD_BUTTON_WIDTH, command=self._start_channel_download)

    def _validate_channel_name(self, channel_name: str):
        '''
        Returns a string without whitespace.
        To prevent user from downloading the wrong channel, e.g. the channel 'tech', when searching for channel name 'tech tips'.
        '''
        return channel_name.replace(' ', '').strip()

    def _start_channel_download(self):
        '''Starts a new thread for channel download.'''
        thread = threading.Thread(target=self.download_channel)
        thread.start()
        messagebox.showinfo(title='Complete', message='Download complete!')

    def _build(self):
        '''Places all the elements in the grid. Seperated from instancing for better overview.'''
        self.channel_name_elements['label'].grid(column=0, row=1, sticky=W, padx=10, pady=15)
        self.channel_name_elements['field'].grid(column=1, row=1, sticky=W)

        self.timeframe_elements['label'].grid(column=0, row=3, sticky=EW, padx=10, pady=20)
        self.timeframe_elements['menu'].grid(column=1, row=3)

        self.keyword_elements['label'].grid(column=0, row=4, sticky=EW, padx=10, pady=20)
        self.keyword_elements['field'].grid(column=1, row=4)

        self.dl_button.grid(column=1, row=5, pady=20, padx=10, sticky=EW)

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
        if self.stringvars['channel name'].get() == '':
            messagebox.showerror(title='Channel name error', message='Please enter a Youtube channel name')
            return
        channel_name = self._validate_channel_name(self.stringvars['channel name'].get())
        filtered_videos = self.filter_channel_videos(channel=Channel(f"https://www.youtube.com/c/{channel_name}"))

        for video in filtered_videos:
            downloader = VideoDownloader(
                url=video.watch_url, 
                resolution=options.get_resolution(), 
                save_directory=f'{options.get_save_dir()}\\{video.author}'
                )
            downloader.add_resolution_prefix()
            downloader.download_video()


class PlaylistTab:
    def __init__(self, frame: Frame, options: OptionsTab) -> None:
        self.url_frame = Frame(frame, width=WINDOW_WIDTH, height=WINDOW_HEIGHT/2)
        self.playlist_frame = Frame(frame, width=WINDOW_WIDTH, height=WINDOW_HEIGHT/2)
        self.output_filename = None
        self.a_tags = None
        self.url_elements = {}
        self.channel_elements = {}
        self.playlist_elements = {}
        self.stringvars = {
            'url' : StringVar(),
            'channel name' : StringVar(),
            'playlist name' : StringVar()
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
        self.url_elements['label'] = Label(self.url_frame, text='Playlist URL', width=LABEL_WIDTH)
        self.url_elements['field'] = Entry(self.url_frame, width=ENTRY_WIDTH, textvariable=self.stringvars['url'])
        self.url_elements['button'] = Button(self.url_frame, text='DOWNLOAD', bg=DOWNLOAD_BUTTON_COLOR, height=DOWNLOAD_BUTTON_HEIGHT, width=DOWNLOAD_BUTTON_WIDTH, command=self._start_playlist_download)

    def _generate_channel_name_elements(self):
        self.channel_elements['label'] = Label(self.playlist_frame, text='Channel name', width=LABEL_WIDTH)
        self.channel_elements['field'] = Entry(self.playlist_frame, width=ENTRY_WIDTH, textvariable=self.stringvars['channel name'])
   
    def _generate_playlist_name_elements(self):
        self.playlist_elements['label'] = Label(self.playlist_frame, text='Playlist name', width=LABEL_WIDTH)
        self.playlist_elements['field'] = Entry(self.playlist_frame, width=ENTRY_WIDTH, textvariable=self.stringvars['playlist name'])
        self.playlist_elements['button'] = Button(self.playlist_frame, text='DOWNLOAD', bg=DOWNLOAD_BUTTON_COLOR, height=DOWNLOAD_BUTTON_HEIGHT, width=DOWNLOAD_BUTTON_WIDTH, command=self._start_channel_playlist_download)

    def _validate_channel_name(self, channel_name: str):
        '''
        Returns a string without whitespace.
        To prevent user from downloading the wrong channel, e.g. the channel 'tech', when searching for channel name 'tech tips'.
        '''
        return channel_name.replace(' ', '').strip()

    def _start_playlist_download(self):
        '''Starts a new thread for channel download.'''
        thread = threading.Thread(target=self.download_playlist)
        thread.start()
        messagebox.showinfo(title='Complete', message='Download complete!')

    def _start_channel_playlist_download(self):
        '''Starts a new thread for channel download.'''
        self._get_playlist_atags()
        thread = threading.Thread(target=self.download_channel_playlist)
        thread.start()
        messagebox.showinfo(title='Complete', message='Download complete!')

    def _build(self):
        '''Places all the elements in the grid. Seperated from instancing for better overview.'''
        self.url_frame.grid(columnspan=3)
        self.playlist_frame.grid(columnspan=3)

        self.url_elements['label'].grid(column=0, row=0, sticky=W, padx=10, pady=15)
        self.url_elements['field'].grid(column=1, row=0, sticky=W)
        self.url_elements['button'].grid(column=1, row=1, pady=10)
     
        self.channel_elements['label'].grid(column=0, row=0, sticky=W, padx=10, pady=15)
        self.channel_elements['field'].grid(column=1, row=0, sticky=W)

        self.playlist_elements['label'].grid(column=0, row=1, sticky=W, padx=10, pady=15)
        self.playlist_elements['field'].grid(column=1, row=1, sticky=W)
        self.playlist_elements['button'].grid(column=1, row=2, pady=10)

    def _get_playlist_atags(self):
        with HTMLSession() as session:
            response = session.get(f"https://www.youtube.com/c/{self.stringvars['channel name'].get()}/playlists")
            response.html.render(sleep=1, timeout=100)
            self.a_tags = response.html.find('a#video-title')
        
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
        return messagebox.askyesno(
            title='Suggest close match', 
            message=f'Found the playlist called {playlist.title}\nThe name looks similar to what you were looking for!\nDo you want to download it?'
            )

    def find_playlist(self):
        '''Returns the Playlist object of it matches the playlist name, the user is looking for.'''
        playlist_name = self.stringvars['playlist name'].get()
        playlists = self._generate_playlists()

        for playlist in playlists:
            if playlist_name.lower() == playlist.title.lower():
                return playlist 
        else:
            # if no 100% match, look for 85%+ matches
            for playlist in playlists:
                if self._similar(playlist_name.lower(), playlist.title.lower()) >= 0.85:
                    accept_suggestion = self._suggest_playlist(playlist)
                    if accept_suggestion:
                        return playlist
            messagebox.showerror(
                title='Channel playlists not found',
                message='Channel playlists not found.\nPlease that the channel name is correct.'
            )
            return None

    def download_playlist(self):
        playlist = Playlist(self.stringvars['url'].get())
        for video in playlist.videos:
            downloader = VideoDownloader(
                url=video.watch_url, 
                resolution=options.get_resolution(), 
                save_directory=f'{options.get_save_dir()}\\{video.author}\\{playlist.title}'
                )
            downloader.add_resolution_prefix()
            downloader.download_video()
    
    def download_channel_playlist(self):
        relevant_playlist = self.find_playlist()
        if relevant_playlist is None:
            # Either wrong channel name or channel has no playlists
            return
            
        
        for video in relevant_playlist.videos:
            downloader = VideoDownloader(
                url=video.watch_url, 
                resolution=options.get_resolution(), 
                save_directory=f'{options.get_save_dir()}\\{video.author}'
                )
            downloader.add_resolution_prefix()
            downloader.download_video()


class VideoDownloader:
    def __init__(self, url: str, save_directory=os.getcwd(), resolution=Resolution().default_res) -> None:
        self.url = url
        self.resolution = resolution
        self.output_filename = None
        self.save_directory = save_directory
        self.resolution_prefix = False
    
    def _validate_filename(self):
        if self.output_filename.strip() == '':
            return None
        if not self.output_filename.endswith('mp4'):
            self.output_filename += '.mp4'
        return self.output_filename

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

    def download_video(self):
        video = YouTube(url=self.url)
        if self.resolution is None:
            return

        prefix = None
        if self.resolution_prefix:
            prefix = f'[{self.resolution}] '
        try:
            # Choose 60fps over 30fps if available
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
        

root = Tk()
app = App(root)

options = OptionsTab(frame=app.tabs.get('Options'))
video = VideoTab(frame=app.tabs.get('Video'), options=options)
channel = ChannelTab(frame=app.tabs.get('Channel'), options=options)
playlist = PlaylistTab(frame=app.tabs.get('Playlist'), options=options)

root.mainloop()