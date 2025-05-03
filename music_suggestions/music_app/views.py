import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
import requests

load_dotenv()

scope = "user-library-read user-library-modify"
LASTFM_API_KEY = os.getenv("LASTFM_API_KEY")
LASTFM_SHARED_SECRET = os.getenv("LASTFM_SHARED_SECRET")

def login_with_spotify(request):
    sp_oauth = SpotifyOAuth(scope=scope)
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

def spotify_callback(request):
    sp_oauth = SpotifyOAuth(scope=scope)
    session_code = request.GET.get('code')
    
    if session_code:
        token_info = sp_oauth.get_access_token(code=session_code)
        access_token = token_info['access_token']
        refresh_token = token_info['refresh_token']
        request.session['access_token'] = access_token
        request.session['refresh_token'] = refresh_token
        return redirect('mood_selector')
    
    return render(request, 'error.html', {'message': 'Authorization failed.'})

def refresh_access_token(request):
    refresh_token = request.session.get('refresh_token')
    if refresh_token:
        sp_oauth = SpotifyOAuth(scope=scope, cache_path=None)
        token_info = sp_oauth.refresh_access_token(refresh_token)
        access_token = token_info['access_token']
        request.session['access_token'] = access_token
        return access_token
    return None

MOOD_FEATURES = {
    'happy': {'category': 'happy'},
    'sad': {'category': 'sad'},
    'relaxed': {'category': 'chill'},
    'angry': {'category': 'angry'},
    'excited': {'category': 'excited'},
}

def mood_selector(request):
    if request.method == "POST":
        mood = request.POST.get("mood")
        tag = MOOD_FEATURES.get(mood, {}).get('category')

        access_token = request.session.get('access_token') or refresh_access_token(request)
        if not access_token:
            return redirect('login_with_spotify')

        sp = spotipy.Spotify(auth=access_token)

        try:
            if tag:
                tracks = []
                lastfm_url = "http://ws.audioscrobbler.com/2.0/"
                params = {
                    'method': 'tag.gettoptracks',
                    'tag': tag,
                    'api_key': LASTFM_API_KEY,
                    'format': 'json',
                    'limit': 10
                }
                response = requests.get(lastfm_url, params=params)
                data = response.json()
                #lastfm_response_format.txt

                if 'tracks' in data and 'track' in data['tracks']:
                    for item in data['tracks']['track']:
                        track_name = item['name']
                        artist_name = item['artist']['name']
                        query = f'track:{track_name} artist:{artist_name}'
                        search_result = sp.search(q=query, type='track', limit=1)

                        if search_result['tracks']['items']:
                            track = search_result['tracks']['items'][0]
                            tracks.append({
                                'name': track['name'],
                                'artist': ', '.join([a['name'] for a in track['artists']]),
                                'album': track['album']['name'],
                                'image_url': track['album']['images'][0]['url'],
                                'track_url': track['external_urls']['spotify'],
                                'spotify_id': track['id'],
                            })

                return render(request, "tracks.html", {"tracks": tracks})
            else:
                return render(request, 'error.html', {'message': f"No mood mapping found for {mood}"})

        except spotipy.exceptions.SpotifyException as e:
            return render(request, 'error.html', {'message': f"Spotify Error: {e}"})

    return render(request, "select_mood.html")

@csrf_exempt
def add_to_spotify(request):
    if request.method == "POST":
        track_id = request.POST.get("track_id")
        access_token = request.session.get('access_token') or refresh_access_token(request)
        if not access_token:
            return redirect('login_with_spotify')

        sp = spotipy.Spotify(auth=access_token)
        sp.current_user_saved_tracks_add([track_id])  # Adds to liked songs
        return redirect('mood_selector')
