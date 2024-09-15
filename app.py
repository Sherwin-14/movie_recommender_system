import streamlit as st
import pickle
import pandas as pd
import requests
import time
from requests.adapters import HTTPAdapter
from streamlit_lottie import st_lottie  
from google.cloud import dialogflow
from googleapiclient.discovery import build
import pymongo
import streamlit_shadcn_ui as ui
import urllib3
import certifi
import os
import base64
http = urllib3.PoolManager()
headers = {
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36'}

st.set_page_config(layout="wide")


os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'rafael-ivrk-6adb23c97229.json'


def Convert(lst):
    res_dct = map(lambda i: (lst[i], lst[i+1]), range(len(lst)-1)[::2])
    return dict(res_dct)

def convert_to_million(value):
     if value:
        return value / 1000000
     else:
        return 0
    
def calculate_profit_loss(budget, revenue):
    profit = revenue - budget
    return profit    
  
def display_trailer(trailer_key):
    if trailer_key:
        trailer_url = f"https://www.youtube.com/watch?v={trailer_key}"
        print(f"Watch the trailer here: {trailer_url}")
    else:
        print("Trailer not available for this movie.")  


def fetch_actor_biography(actor_id):
    url = f"https://api.themoviedb.org/3/person/{actor_id}?api_key=b3467b23124643ddc4b56a79fa8fc7d1&language=en-US"
    try:
        response = requests.get(url)
        data = response.json()
        biography = data.get('biography', '')
        return biography
    except requests.exceptions.RequestException as e:

        print(f"An error occurred: {e}")
        data = {}
        time.sleep(1)

    return None


def fetch_movie_poster(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key=b3467b23124643ddc4b56a79fa8fc7d1&language=en-US"
    response = requests.get(url)
    data = response.json()

    poster_path = data.get('poster_path', '')
    base_url = 'https://image.tmdb.org/t/p/w500'  # You can change the size as needed

    if poster_path:
        poster_url = base_url + poster_path
        poster_data = requests.get(poster_url).content
    else:
        poster_url = None

    return poster_url    

def fetch_release_date(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key=b3467b23124643ddc4b56a79fa8fc7d1&language=en-US"
    response = requests.get(url)
    data = response.json()

    release_date = data.get('release_date', '')

    return release_date    


def fetch_overview_and_genres(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key=b3467b23124643ddc4b56a79fa8fc7d1&language=en-US&append_to_response=videos"
    response = requests.get(url)
    data = response.json()

    overview = data.get('overview', '')
    genres = [genre['name'] for genre in data.get('genres', [])]
    ratings = data.get('vote_average', '')
    budget = convert_to_million(data.get('budget', ''))
    votes = data.get('vote_count', '')
    revenue = convert_to_million(data.get('revenue', ''))
    profit_loss = calculate_profit_loss(budget, revenue)
    runtime = data.get('runtime', '')
    production_companies = [company['name'] for company in data.get('production_companies', [])]

    trailer_key = ''
    if 'videos' in data and 'results' in data['videos']:
        for video in data['videos']['results']:
            if video.get('type') == 'Trailer':
                trailer_key = video.get('key')
                break

    return overview, genres, ratings,budget, votes ,revenue,profit_loss,runtime,production_companies,trailer_key

def get_color(reviews):
    colors = []
    for review in reviews:
        review = [' '.join(review)]
        
        # Transform the review into a vector
        review_vector = vectorizer.transform(review)
        
        # Use the model to predict the sentiment of the review
        sentiment = sentiment_analysis.predict(review_vector)[0]

        print(sentiment)
        
        if sentiment == '1':
            colors.append('#008000')  # Green for positive reviews
        else:
            colors.append('#FF0000')  # Red for negative reviews
    return colors

    

def fetch_reviews(movie_id,max_reviews=4):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}/reviews?api_key=b3467b23124643ddc4b56a79fa8fc7d1&language=en-US"
    response = requests.get(url)
    data = response.json()
    reviews = [review['content'] for review in data['results'][:max_reviews]]
    
    colors = get_color(reviews)

    review_dict = dict(zip(reviews, colors))

    print(review_dict)

    return review_dict

  

def fetch_cast_and_director(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}/credits?api_key=b3467b23124643ddc4b56a79fa8fc7d1&language=en-US"
    response = requests.get(url)
    data = response.json()
    cast = data['cast']
    director = next((person for person in data['crew'] if person['job'] == 'Director'), None)
    cast_images = ["https://image.tmdb.org/t/p/w500/" + person['profile_path'] for person in cast if person['profile_path'] is not None ]
    director_image = "https://image.tmdb.org/t/p/w500/" + director['profile_path'] if director and director['profile_path'] is not None else None
    actor_ids = [person['id'] for person in cast]
    actor_bios = [fetch_actor_biography(id) for id in actor_ids]
    return cast, cast_images ,director, director_image,actor_bios


def fetch_poster(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key=b3467b23124643ddc4b56a79fa8fc7d1&language=en-US"
    response = requests.get(url)
    data=response.json()

    overview = data.get('overview', '')
    genres = [genre['name'] for genre in data.get('genres', [])]
    
    if data['poster_path'] is not None:
        return "https://image.tmdb.org/t/p/w500/" + data['poster_path']
    else:
        return None

def recommend(movie):
    # Check if the movie exists in the dataframe
    if movie in movies['title'].values:
        index = movies[movies['title'] == movie].index
        # Check if the index list is not empty
        if len(index) > 0:
            index = index[0]
            distances = similarity[index] 
            movies_list=sorted(list(enumerate(similarity[index])),reverse=True,key = lambda x: x[1])[1:6]

            recommended_movies=[]
            recommended_movies_posters=[]
            for i in movies_list:
                # Check if the index exists in the dataframe
                if i[0] < len(movies):
                    movie_id=movies.iloc[i[0]].movie_id
                    recommended_movies.append(movies.iloc[i[0]].title)
                    recommended_movies_posters.append(fetch_poster(movie_id))

            return recommended_movies,recommended_movies_posters    
        else:
            return [], []
    else:
        return [], []
    

movies_list=pickle.load(open('artefacts/movie_dict.pkl','rb'))
movies=pd.DataFrame(movies_list)

similarity=pickle.load(open('artefacts/similarity.pkl','rb'))

sentiment_analysis=pickle.load(open('artefacts/nlp.pkl','rb'))

vectorizer=pickle.load(open('artefacts/vectorizers.pkl','rb'))

st.sidebar.title("Contents")

st.title("Mobiflix")

page = st.sidebar.radio("Choose a Option", ["Introduction","Optional Information","Home","Movie Stats","Cast and Director","Reviews","Rafael for developers","Contributor","About Me"])


st_lottie_url = 'https://lottie.host/de05e050-52f1-4a96-b0f7-790acc763edf/HVfTg7hkjj.json' 
st_lottie_url1= 'https://lottie.host/4320cae9-2dad-47b6-9a18-d436b4a96c81/IKHXmcnDCO.json'
st_lottie_url2= 'https://lottie.host/cd15de8d-31b6-4222-a66e-0cb0c8f441ab/fJ86zPFW8S.json'

session_client = dialogflow.SessionsClient()

session = session_client.session_path('rafael-ivrk', 'S1')



if page=="Introduction":
       intro_paragraphs = [
    "Introducing Mobiflix ,Your Ultimate Entertainment Companion. In the vast landscape of entertainment options, finding the perfect movie or TV show to watch can be a daunting task. Enter Mobiflix, a cutting-edge recommender system designed to simplify your viewing experience and bring the best of entertainment directly to your fingertips.",
        
        "With Mobiflix, discovering your next favorite film or series is as easy as a few clicks. Our advanced algorithm analyzes your viewing preferences and suggests personalized recommendations tailored to your unique tastes. Whether you're in the mood for action-packed blockbusters, heartwarming dramas, or laugh-out-loud comedies, Mobiflix has you covered.",
        
        "Powered by the renowned TMDB API, Mobiflix harnesses the vast database of The Movie Database to provide you with up-to-date information on a wide range of movies and TV shows. By leveraging the rich metadata and comprehensive content available through the TMDB API, Mobiflix ensures that you have access to the latest releases, popular classics, and hidden gems across various genres."
    ]
    # Display each paragraph separately
       st.image("Movie_Posters.jpg",width=990)
       for paragraph in intro_paragraphs:
               st.write(paragraph)

if page=="About Me":
    github_url = "https://github.com/Sherwin-14"
    github_logo = "https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png" 
    linkedin_logo = "https://upload.wikimedia.org/wikipedia/commons/c/ca/LinkedIn_logo_initials.png"
    medium_logo = "https://cdn-images-1.medium.com/fit/c/120/120/1*6_fgYnisCa9V21mymySIvA.png" 
    linkedin_url = "https://www.linkedin.com/in/sherwin14"  # replace with your LinkedIn URL
    medium_url = "https://medium.com/@your_username" 
    html1 = f"""
    <div style="display: flex; justify-content: center; margin-bottom: 20px;">
        <a href="{medium_url}"> <img src="{medium_logo}" alt="Medium logo" width="100" style="margin: 0px 15px;"/> </a>
        <a href="{github_url}"> <img src="{github_logo}" alt="Github logo" width="100" style="margin: 0px 15px;"/> </a>
        <a href="{linkedin_url}"> <img src="{linkedin_logo}" alt="LinkedIn logo" width="100" style="margin: 0px 15px;"/> </a>
    </div>"""
    html = f'<a href="{github_url}"> <img src="{github_logo}" alt="Github logo" width="50"/> </a>'
    st.markdown(html1, unsafe_allow_html=True)
    intro_paragraph=["Hello, my name is Sherwin Varghese and I'm the developer behind this movie recommendation engine. As an AI enthusiast, I enjoy leveraging machine learning to build applications that are helpful, harmless, and honest. My goal with this project was to create a tool that makes finding new movies to watch fun and easy for everyone. In my free time I love exploring new algorithms and techniques to improve people's experiences with technology. I'm excited to continue developing this recommender and adding new features based on user feedback."]
    for paragraph in intro_paragraph:
        st.write(paragraph)

    col1,col2,col3=st.columns(3)
    with col2:
        st_lottie(st_lottie_url1,width=300,height=300)


if page == "Rafael for developers":

   prompt = st.chat_input("enter")

   if prompt:
    st.write(f'User query : {prompt}')
    text_input = dialogflow.TextInput(text=prompt, language_code='en')
    query_input = dialogflow.QueryInput(text=text_input)
    response = session_client.detect_intent(session=session, query_input=query_input)
    st.write(f"Rafael: {response.query_result.fulfillment_text}")




if page=="Contributor":
    st.write("Thank you for considering contributing to our project! Your support means a lot to us. If you would like to contribute, you can support us through Paytm. Your contributions help us continue our work and improve the project for everyone. We appreciate your generosity!")    

    cols = st.columns(5)
   
    with cols[1]:
        ui.metric_card(title="Total Contribution", content="$3.00",key="card1")
    ui.link_button(text="Go To Link", url="https://github.com/ObservedObserver/streamlit-shadcn-ui", key="link_btn")    
  
    with cols[3]:
        st_lottie(st_lottie_url2,width=200,height=200)
                       
if page =="Optional Information":

    name = st.text_input("Enter your name:")
    email = st.text_input("Enter your email:")
    age = st.number_input("Enter your age:")


    user_data = {
        "name": name,
        "email": email,
        "age": age,
    }
    
    trigger_btn = ui.button(text="Submit", key="trigger_btn_1")

    if trigger_btn:
        if all(user_data.values()): 
                ui.alert_dialog(show=trigger_btn, title="Mobiflix", description="Welcome User!", confirm_label="OK", cancel_label="Cancel", key="alert_dialog_1")
        else:
            ui.alert_dialog(show=trigger_btn, title="Mobiflix", description="Please fill all the necessary details", confirm_label="OK", cancel_label="Cancel", key="alert_dialog_1")

else:    
        
        if page == "Home":

            selected_movie_name=st.selectbox(
            'How would you like to proceed',
            movies['title'].values
        )
            if selected_movie_name in movies['title'].values:
                st.session_state.selected_movie_name = selected_movie_name
                st.session_state.selected_movie_id = movies[movies['title'] == selected_movie_name]['movie_id'].values[0]
            else:
                print("Movie not found in the database.")

            col1,col2,col3,col4,col5=st.columns(5)
            
            if 'details1' not in st.session_state:
                st.session_state.details1 = False
            
            placeholder = st.empty()

            if col1.button('Recommend'):
                
                with col3:
                    with placeholder.container():
                            st_lottie(st_lottie_url,width=200,height=200)
                        
                names, posters = recommend(st.session_state.selected_movie_name)
                recommended_movie_ids = [movies[movies['title'] == name]['movie_id'].values[0] for name in names]
                recommended_movie_details = [fetch_overview_and_genres(movie_id) for movie_id in recommended_movie_ids]
  
                time.sleep(3)
                placeholder.empty()

                for i in range(5):  # Assuming you have 5 recommended movies
                    row = st.container()
                    with row:
                        col1, col2, col3, col4, col5 = st.columns(5)
                        with col3:
                            st.markdown(f"<h3 style='text-align: center;'>{names[i]}</h3>", unsafe_allow_html=True)
                            st.image(posters[i],width=200)
                        overview, genres,ratings,budget,votes,revenue,profit_loss,runtime,production_companies,trailer_key = fetch_overview_and_genres(recommended_movie_ids[i])
                        badge_list=[("Profit", "default"), ("Loss", "destructive")]
                        st.write(f"**Overview:** {overview}")
                        st.write("Genres")
                        badges_list_genres=[("Loss", "destructive"),("Profit", "default")]
                        genre_badges = [(genre, badges_list_genres[i % len(badge_list)][1]) for i, genre in enumerate(genres)]
                        production_badges = [(production_badges, badges_list_genres[i % len(badge_list)][1]) for i, production_badges in enumerate(production_companies)]
                        ui.badges(badge_list=genre_badges, class_name="flex gap-2", key=f"genre_badges_{i}")
                        st.write(f"**Ratings:** {ratings}")
                        st.write(f"**Budget:** ${budget} million")
                        st.write(f"**Votes:** {votes}")
                        st.write(f"**Revenue:** ${round(revenue, 3)} million")
                        st.write("**Production House**:")
                        ui.badges(badge_list=production_badges, class_name="flex gap-2", key=f"production_badges_{i}")
                        st.write(f"**Runtime:** {runtime} mins")
                        if trailer_key:
                            st.write("**Trailer:**")
                            st.markdown(f'<iframe width="640" height="360" src="https://www.youtube.com/embed/{trailer_key}" frameborder="0" allowfullscreen></iframe>', unsafe_allow_html=True)
                        if profit_loss > 0:
                            st.write("**Verdict:**")
                            ui.badges(badge_list=[("Profit", "default")], class_name="flex gap-2", key=f"profit_badge_{i}")
                        elif profit_loss < 0:
                            st.write("**Verdict:**")
                            ui.badges(badge_list=[("Loss", "destructive")], class_name="flex gap-2", key=f"loss_badge_{i}")
                        else:
                            st.write("**Verdict:**")
                            st.write("No Profit or Loss")

        elif page == "Movie Stats" :
            col1, col2, col3, col4, col5 = st.columns(5)  
            
            poster = fetch_poster(st.session_state.selected_movie_id)
            movie_name = str(st.session_state.selected_movie_name)
            
            # Check if the movie name has multiple words
            if ' ' in movie_name:
                keyword = '+'.join(movie_name.split())
            else:
                keyword = movie_name

                
            with col3:
                if poster:
                    if st.image(poster, width=200, caption="Movie Poster"):
                        pass
                else:
                    st.write('No poster available') 
                    
            overview, genres,ratings,budget,votes,revenue,profit_loss,runtime,production_companies,trailer_key = fetch_overview_and_genres(st.session_state.selected_movie_id)
                # Display the fetched overview and genres
            st.write('Overview:', overview)
            genres = Convert(genres)
            # Convert genres to badge_list format for ui.badges
            badged_list = [("Profit", "default"), ("Loss", "destructive")]
            badge_list = [(genre, genres[genre]) for genre in genres]

            # Display genres as badges using ui.badges
            st.write("**Genres**:")
            ui.badges(badge_list=badge_list, class_name="flex gap-2", key="badges1")

            release_date = fetch_release_date(st.session_state.selected_movie_id)
            st.write("**Release Date**:",release_date)
            st.write("**Ratings**:", ratings)
            st.write(f"**Runtime:** {runtime}")
            st.write(f"**Budget:** ${budget}")
            st.write(f"**Votes:** {votes}")
            st.write(f"**Revenue:**$ {revenue}")
            badge_list = [("Profit", "default"), ("Loss", "destructive")]
            production_badges = [(production_badge, badge_list[i % len(badge_list)][1]) for i, production_badge in enumerate(production_companies)]
            st.write("**Production House:**")
            ui.badges(badge_list=production_badges, class_name="flex gap-2", key="badges2")
            if trailer_key:
                    st.write("**Trailer:**")
                    st.markdown(f'<iframe width="640" height="360" src="https://www.youtube.com/embed/{trailer_key}" frameborder="0" allowfullscreen></iframe>', unsafe_allow_html=True)
            if profit_loss > 0:
                st.write("**Verdict:**")
                ui.badges(badge_list=[("Profit", "default")], class_name="flex gap-2", key="profit_badge")
            elif profit_loss < 0:
                st.write("**Verdict:**")
                ui.badges(badge_list=[("Loss", "destructive")], class_name="flex gap-2", key="loss_badge")
            else:
                st.write("**Verdict:**")
                st.write("No Profit or Loss")


 
        elif page == "Cast and Director":
            
            if 'selected_movie_name' in st.session_state and st.session_state.selected_movie_name in movies['title'].values:
                st.session_state.selected_movie_id = movies[movies['title'] == st.session_state.selected_movie_name]['movie_id'].values[0]

            placeholder = st.empty()

            if st.button('Show Cast and Director'):  

                with placeholder.container():
                    st_lottie(st_lottie_url,width=200,height=200)

                cast, cast_images ,director, director_image,cast_biography = fetch_cast_and_director(st.session_state.selected_movie_id)

                time.sleep(3)
                placeholder.empty()

                st.title("Director")
                col1, col2, col3,col4,col5 = st.columns(5)

                # Display the director's details in the center column
                with col3:
                    st.text(director['name'])
                    st.image(director_image, width=200) 

                st.title("Actors")    

                top_n = min(5, len(cast))
                
                # Display the details of the top 5 actors
                for i in range(top_n):
                    col1,col2,col3,col4,col5 = st.columns(5)  # Create a new column for each actor
                    with col3:
                        st.text(cast[i]['name'])
                        st.image(cast_images[i],width=200)
                    st.write(f"**Biography:**",cast_biography[i]) 
            else:
                st.warning("Please select a movie in the Home page.")


        elif page == "Reviews":
            if 'selected_movie_id' in st.session_state and st.session_state.selected_movie_id is not None:
                if st.button('Show Reviews'):
                    review_dict = fetch_reviews(st.session_state.selected_movie_id)
                    for review, color in review_dict.items():
                        st.markdown(f'<p style="color: {color}">{review}</p>', unsafe_allow_html=True)
            else:
                st.warning("Please select a movie in the Home page.") 
                  
