import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
from django.shortcuts import redirect, render
import random
import requests

load_dotenv()

scope = "user-library-read"

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
        genres = MOOD_FEATURES.get(mood, [])

        access_token = request.session.get('access_token') or refresh_access_token(request)
        if not access_token:
            return redirect('login_with_spotify')

        sp = spotipy.Spotify(auth=access_token)

        try:
            if genres:
                tracks = []
                for genre in genres:
                    # Search for tracks within each genre related to the mood
                    results = sp.search(q=f'genre:"{genre}"', type='track', limit=5)
                    
                    # Extract track details from the search results
                    for track in results['tracks']['items']:
                        tracks.append({
                            'name': track['name'],
                            'artist': ', '.join([artist['name'] for artist in track['artists']]),
                            'album': track['album']['name'],
                            'image_url': track['album']['images'][0]['url'],
                            'track_url': track['external_urls']['spotify']
                        })

                if tracks:
                    # Remove duplicate tracks if any
                    tracks = list({track['name']: track for track in tracks}.values())
                    return render(request, "tracks.html", {"tracks": tracks})
                else:
                    return render(request, 'error.html', {'message': f"No tracks found for mood {mood}"})
            
            return render(request, 'error.html', {'message': f"No genre mapping found for mood {mood}"})

        except spotipy.exceptions.SpotifyException as e:
            return render(request, 'error.html', {'message': f"Spotify Error: {e}"})

    return render(request, "select_mood.html")
