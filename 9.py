import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta
import requests
import plotly.express as px
import plotly.graph_objects as go
import json
import os
from User_Data import UserDataManager
import time
from urllib.parse import quote

# ========== CONFIGURATION ==========
# Add your API Ninja API key here
try:
    API_NINJA_KEY = st.secrets.get("API_NINJA_KEY")
except:
    API_NINJA_KEY = None

if not API_NINJA_KEY:
    st.error("❌ API Key not found. Please add `API_NINJA_KEY` to .streamlit/secrets.toml")
    st.stop()

# API endpoints
RECIPE_API_ENDPOINT = "https://api.api-ninjas.com/v1/recipe"
NUTRITION_API_ENDPOINT = "https://api.api-ninjas.com/v1/nutrition"

ACHIEVEMENTS = {
    "recipe_achievements": [
        {"name": "Recipe Rookie", "requirement": 15, "points": 25, "description": "Generate 15 recipes"},
        {"name": "Recipe Master", "requirement": 45, "points": 50, "description": "Generate 45 recipes"},
        {"name": "Recipe Chef", "requirement": 95, "points": 75, "description": "Generate 95 recipes"}
    ],
    "leftover_achievements": [
        {"name": "Waste Warrior", "requirement": 15, "points": 25, "description": "Manage 15 leftover items"},
        {"name": "Sustainability Star", "requirement": 75, "points": 50, "description": "Manage 45 leftover items"},
        {"name": "Zero Waste Hero", "requirement": 180, "points": 75, "description": "Manage 95 leftover items"}
    ],
    "quiz_achievements": [
        {"name": "Quiz Novice", "requirement": 5, "points": 25, "description": "Answer 5 quiz questions correctly"},
        {"name": "Quiz Expert", "requirement": 15, "points": 50, "description": "Answer 15 quiz questions correctly"},
        {"name": "Quiz Master", "requirement": 30, "points": 100, "description": "Answer 30 quiz questions correctly"},
        {"name": "Perfect Streak", "requirement": 5, "points": 50, "description": "Get 5 correct answers in a row"},
    ],
    "beverage_achievements": [
        {"name": "Beverage Beginner", "requirement": 5, "points": 25, "description": "Create 5 beverage recipes"},
        {"name": "Mixology Master", "requirement": 15, "points": 50, "description": "Create 15 beverage recipes"},
        {"name": "Drink Designer", "requirement": 30, "points": 75, "description": "Create 30 beverage recipes"},
    ],
    "dessert_achievements": [
        {"name": "Sweet Beginner", "requirement": 5, "points": 25, "description": "Create 5 dessert recipes"},
        {"name": "Pastry Chef", "requirement": 15, "points": 50, "description": "Create 15 dessert recipes"},
        {"name": "Dessert Artist", "requirement": 30, "points": 75, "description": "Create 30 dessert recipes"},
    ]
}

COOKING_QUIZ = [
    {"question": "What temperature is considered safe for cooking chicken?", "options": ["145°F", "165°F", "175°F", "185°F"], "correct": "165°F"},
    {"question": "Which herb is commonly used in Italian cuisine?", "options": ["Basil", "Lemongrass", "Cumin", "Cardamom"], "correct": "Basil"},
    {"question": "What is the main ingredient in traditional guacamole?", "options": ["Tomatoes", "Avocado", "Onions", "Lime"], "correct": "Avocado"},
    {"question": "Which cooking method involves cooking food in hot oil?", "options": ["Braising", "Steaming", "Frying", "Roasting"], "correct": "Frying"},
    {"question": "What does 'al dente' mean when cooking pasta?", "options": ["Soft and mushy", "Firm to the bite", "Overcooked", "Undercooked"], "correct": "Firm to the bite"},
    {"question": "What is the purpose of resting meat after cooking?", "options": ["To cool it down", "To allow juices to redistribute", "To make it easier to cut", "To enhance flavor"], "correct": "To allow juices to redistribute"},
    {"question": "Which spice is commonly known as 'Indian saffron'?", "options": ["Cardamom", "Turmeric", "Cumin", "Mustard"], "correct": "Turmeric"},
    {"question": "What is the primary ingredient in Punjabi lassi?", "options": ["Coconut milk", "Yogurt", "Condensed milk", "Buttermilk"], "correct": "Yogurt"},
    {"question": "Which rice is used for biryani?", "options": ["Jasmine", "Brown", "Basmati", "Arborio"], "correct": "Basmati"},
    {"question": "What is the main ingredient in hummus?", "options": ["Lentils", "Chickpeas", "Black beans", "Peanuts"], "correct": "Chickpeas"},
        {
        "question": "What temperature is considered safe for cooking chicken?",
        "options": ["145°F", "165°F", "175°F", "185°F"],
        "correct": "165°F"
    },
    {
        "question": "Which herb is commonly used in Italian cuisine?",
        "options": ["Basil", "Lemongrass", "Cumin", "Cardamom"],
        "correct": "Basil"
    },
    {
        "question": "What is the main ingredient in traditional guacamole?",
        "options": ["Tomatoes", "Avocado", "Onions", "Lime"],
        "correct": "Avocado"
    },
    {
        "question": "Which cooking method involves cooking food in hot oil?",
        "options": ["Braising", "Steaming", "Frying", "Roasting"],
        "correct": "Frying"
    },
    {
        "question": "What is the process of partially cooking food in boiling water and then quickly cooling it in ice water?",
        "options": ["Sautéing", "Blanching", " Braising", "Roasting"],
        "correct": "Blanching"
    },
    {
        "question": "Which ingredient makes baked goods rise?",
        "options": ["Sugar", "Flour", "Salt", "Baking soda"],
        "correct": "Baking soda"
    },
   {
        "question": "What does 'tempering' mean when working with chocolate?",
        "options": ["Heating and cooling chocolate to stabilize it", " Mixing chocolate with milk", "Melting chocolate over direct heat", " Adding sugar to chocolate"],
        "correct": "Heating and cooling chocolate to stabilize it"
    },
    {
        "question": "Which country is known for originating sushi?",
        "options": ["China", "Korea", "Japan","Thailand"],
        "correct": "Japan"
    },
    {
        "question": "What is the main ingredient in hummus?",
        "options": ["Lentils", "Chickpeas", "Black beans","Peanuts"],
        "correct": "Chickpeas"
    },
    {
        "question": "What does 'sous vide' mean in cooking?",
        "options": ["Cooking with steam", "Cooking food in a vaccum-sealed bag in water", "Cooking over an open flame","Cooking in a pressure cooker"],
        "correct": "Cooking food in a vaccum-sealed bag in water"
    },
    {
        "question": "Which kitchen tool is best for zesting a lemon?",
        "options": ["Knife", "Peeler", "Grater","Microplane"],
        "correct": "Microplane"        
    },
    {
        "question": "What is the purpose of deglazing a pan?",
        "options": ["To remove excess fat", "To dissolve browned bits for added flavor", "To cool down the pan","To thicken a sauce"],
        "correct": " To dissolve browned bits for added flavor"        
    },
    {
        "question": "What does the term 'al dente' mean when cooking pasta?",
        "options": ["Soft and mushy", "Firm to the bite", "Overcooked","Undercooked"],
        "correct": "Firm to the bite"        
    },
    {
        "question": "What is the purpose of resting meat after cooking?",
        "options": ["To cool it down quickly", "To allow juices to redistribute", " To make it easier to cut","To enhance the flavor"],
        "correct": "To allow juices to redistribute"        
    },
    {
        "question": "What does the term 'proofing' mean in baking?",
        "options": ["Checking for quality", " Baking at a low temperature", "Mixing ingredients together","Allowing dough to rise"],
        "correct": "Allowing dough to rise"         
    },
    {
        "question": "What type of sugar is commonly used in making caramel?",
        "options": ["Brown sugar", "Powdered sugar", "Granulated sugar","Coconut sugar"],
        "correct": "Granulated sugar"        
    },
    {
        "question": "Which type of rice is used to make sushi?",
        "options": ["Basmati rice", "Jasmine rice", "Arborio rice","Short-grain rice"],
        "correct": "Short-grain rice"        
    },
    {
        "question": "Which spice is commonly used in Indian cuisine and gives curry its yellow color?",
        "options": ["Saffron", "Paprika", "Turmeric","Cumin"],
        "correct": "Turmeric"        
    },
    {
        "question": "What is the purpose of 'searing' meat?",
        "options": ["To cook it completely", "To keep it cold", "To remove fat","To create a flavorful crust"],
        "correct": "To create a flavorful crust"        
    },
    {
        "question": "What is the French cooking term for 'everything in its place' (organizing ingredients before cooking)?",
        "options": ["Mise en place", "Sous vide", "En papillote","Bain-marie"],
        "correct": "Mise en place"        
    },
    {
        "question": "Which cooking method involves cooking food slowly in a covered pot with a small amount of liquid?",
        "options": ["Braising", "Sautéing", "Boiling","Grilling"],
        "correct": "Braising"        
    },
    {
        "question": "What gas is released when baking soda reacts with an acid?",
        "options": ["Oxygen", "Carbon dioxide", "Hydrogen","Nitrogen"],
        "correct": "Carbon dioxide"        
    },
    {
        "question": "What is the main ingredient in a traditional crème brûlée?",
        "options": ["Flour", "Cream", "Cheese","Butter"],
        "correct": "Cream"        
    },
    {
        "question": "What is the traditional flatbread of Mexico called?",
        "options": ["Tortilla", "Naam", "Roti","Bhature","Pita"],
        "correct": "Tortilla"        
    },
    {
        "question": "Which dish is traditionally made with fermented cabbage?",
        "options": ["Kimchi", "Sushi", "Falafel","Pasta"],
        "correct": "Kimchi"        
    },
    {
        "question": "What is the primary ingredient in a classic French béchamel sauce?",
        "options": ["Milk", "Cream", "Cheese","Butter"],
        "correct": "Milk"        
    },
    {
        "question": "What does 'basting' mean in cooking?",
        "options": ["Cooking with dry heat", "Pouring juices or melted fat over food while cooking", "Cooking food in a water bath","Cutting food into small pieces"],
        "correct": "Pouring juices or melted fat over food while cooking"        
    },
    {
        "question": "What is the term for cooking food in a tightly sealed pouch, usually with parchment paper or foil?",
        "options": ["En papillote", "Roasting", "Poaching","Braising"],
        "correct": "En papillote"        
    },
    {
        "question": "Which tool is best for checking the internal temperature of Water?",
        "options": ["Your hand", "Knife", "Tongs","Thermometer"],
        "correct": "Thermometer"        
    },
    {
        "question": "What is the best way to cut an onion without crying?",
        "options": ["Freeze the onion before cutting", "Use a dull knife", "Cut it under running water","Wear goggles"],
        "correct": "Freeze the onion before cutting"        
    },
    {
        "question": "Which of these dishes is traditionally cooked in a tandoor?",
        "options": ["Tacos", "Paella", "Naan","Sushi"],
        "correct": "Naan"        
    },
    {
        "question": "Which type of lentils are used to make traditional dal makhani?",
        "options": ["Moong dal", "Chana dal", "Masoor dal","Urad dal"],
        "correct": "Urad dal"    
    },
    {
        "question": "What spice gives biryani its distinctive yellow color?",
        "options": ["Saffron", "Turmeric", "Cumin","Spinach"],
        "correct": "Saffron"    
    },
    {
        "question": "What is the key ingredient in a traditional South Indian sambar?",
        "options": ["Chana dal", "Toor dal", "Rajma","Urad dal"],
        "correct": "Toor dal"    
    },
    {
        "question": "Which spice blend is commonly used in Indian chaat dishes?",
        "options": ["Garam Masala", "Chat Masala", "Rajma","Rasam Powder"],
        "correct": "Chat Masala"
    },
    {
        "question": "Which Indian dessert is made by deep-frying balls of khoya and soaking them in sugar syrup?",
        "options": ["Rasgulla", "Jalebi", "Barfi","Gulab Jamun"],
        "correct": "Gulab Jamun"
    },
    {
        "question": "Which spice is commonly known as 'Indian saffron' because of its color and use in Indian cuisine?",
        "options": ["Cardamom", "Turmeric", "Cumin","Mustard seeds"],
        "correct": "Turmeric"
    },
    {
        "question": "Which rice variety is most commonly used for making biryani?",
        "options": ["Jasmine rice", "Brown rice", "Basmati rice","Arborio rice"],
        "correct": "Basmati rice"
    },
    {
        "question": "What is the primary ingredient in traditional Punjabi lassi?",
        "options": ["Coconut milk", "Yogurt", "Condensed milk","Buttermilk"],
        "correct": "Yogurt"
    },
    {
        "question": "Which street food dish consists of hollow, crispy puris filled with spicy and tangy water?",
        "options": ["Dahi Puri", "Bhel Puri", "Pani Puri","Buttermilk"],
        "correct": "Pani Puri"
    }

]

# Page configuration
st.set_page_config(page_title="PlatePals - Smart Restaurant Management", page_icon="🍽️", layout="wide")

st.markdown("<div style='text-align:center'><h1 style='margin:0'>🍽️ PlatePals</h1><p style='margin:0;color:gray'>Serve Smart. Waste Less. Know More.</p></div>", unsafe_allow_html=True)

# Initialize session state
if 'user_manager' not in st.session_state:
    st.session_state.user_manager = UserDataManager()

if 'inventory' not in st.session_state:
    st.session_state.inventory = {
        "vegetables": ["spinach", "kale", "carrots", "bell peppers", "cucumber", "tomatoes", "onion", "garlic"],
        "proteins": ["chicken breast", "salmon", "tofu", "eggs", "chickpeas", "paneer", "lamb"],
        "grains": ["quinoa", "brown rice", "bread", "oats", "pasta", "noodles"],
        "fruits": ["apples", "bananas", "berries", "mango", "avocado", "lemon", "orange"],
        "dairy": ["milk", "butter", "cheese", "yogurt", "cream"]
    }

if 'events' not in st.session_state:
    st.session_state.events = []

if 'users' not in st.session_state:
    st.session_state.users = {}

if 'current_user' not in st.session_state:
    st.session_state.current_user = None

# ========== API HELPER FUNCTIONS ==========
def get_recipe_from_api_ninja(dish_name: str):
    """Fetch recipe from API Ninja"""
    try:
        headers = {"X-Api-Key": API_NINJA_KEY}
        params = {"query": dish_name}
        response = requests.get(RECIPE_API_ENDPOINT, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            st.warning("⏳ API rate limit reached. Please wait a moment.")
            return None
        else:
            return None
    except Exception as e:
        st.error(f"Error fetching recipe: {str(e)}")
        return None

def get_nutrition_info(ingredient: str):
    """Get nutrition info from API Ninja"""
    try:
        headers = {"X-Api-Key": API_NINJA_KEY}
        params = {"query": ingredient}
        response = requests.get(NUTRITION_API_ENDPOINT, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def generate_custom_recipe(ingredients: list, diet_prefs=None, meal_type=None):
    """Generate recipe from ingredients using API"""
    try:
        with st.spinner("🔄 Generating your recipe..."):
            for ingredient in ingredients[:3]:
                recipe_data = get_recipe_from_api_ninja(ingredient)
                if recipe_data and len(recipe_data) > 0:
                    return recipe_data[0] if isinstance(recipe_data, list) else recipe_data
            return None
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

# ========== AUTH FUNCTIONS ==========
def check_login_required():
    """Check if user is logged in"""
    if not st.session_state.current_user:
        st.title("🍽️ Welcome to PlatePals")
        st.write("Please login or sign up to continue")
        
        login_tab, signup_tab = st.tabs(["Login", "Sign Up"])
        
        with login_tab:
            username = st.text_input("Username", key="login_user")
            password = st.text_input("Password", type="password", key="login_pass")
            if st.button("Login"):
                success, message = st.session_state.user_manager.verify_user(username, password)
                if success:
                    st.session_state.current_user = username
                    st.session_state.users = st.session_state.user_manager.users
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
        
        with signup_tab:
            new_username = st.text_input("Username", key="signup_user")
            new_password = st.text_input("Password", type="password", key="signup_pass")
            if st.button("Sign Up"):
                success, message = st.session_state.user_manager.add_user(new_username, new_password)
                if success:
                    st.session_state.current_user = new_username
                    st.session_state.users = st.session_state.user_manager.users
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
        st.stop()

def add_points(points, reason):
    """Add points and log activity"""
    user = st.session_state.users[st.session_state.current_user]
    user['points'] += points
    user['activity_log'].append({
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "action": reason,
        "points": points
    })
    st.session_state.user_manager.update_user_data(st.session_state.current_user, user)

def search_ingredients(search_term: str, ingredients_list: list) -> list:
    """Search ingredients with flexible matching"""
    if not search_term:
        return ingredients_list
    
    search_term = search_term.lower()
    if search_term not in [i.lower() for i in ingredients_list]:
        ingredients_list.append(search_term.title())
    
    matches = [item for item in ingredients_list 
               if search_term in item.lower() or item.lower() in search_term or 
               any(word in item.lower() for word in search_term.split())]
    
    return matches or [search_term.title()]

def get_all_ingredients():
    """Get all available ingredients"""
    all_ingredients = []
    for category_items in st.session_state.inventory.values():
        all_ingredients.extend(category_items)
    return list(set(all_ingredients))

def get_user_mentions():
    """Get user preferences"""
    with st.expander("🎤 Special Mentions", expanded=False):
        wants = st.text_area("What do you want in the recipe?", placeholder="Example: Extra spicy, More gravy...")
        dont_wants = st.text_area("What you DON'T want?", placeholder="Example: No garlic, Less oil...")
        additional_notes = st.text_area("Additional Notes", placeholder="Family preferences, time constraints...")
        return {"wants": wants, "dont_wants": dont_wants, "additional_notes": additional_notes}

def check_achievements(user_data, achievement_type):
    """Check and award achievements"""
    if 'achievements' not in user_data:
        user_data['achievements'] = []

    if achievement_type == "dessert":
        dessert_recipes = [r for r in user_data.get('created_recipes', []) if r.get('type') == 'dessert']
        achievements = ACHIEVEMENTS['dessert_achievements']
    elif achievement_type == "beverage":
        beverage_recipes = [r for r in user_data.get('created_recipes', []) if r.get('type') == 'beverage']
        achievements = ACHIEVEMENTS['beverage_achievements']
    elif achievement_type == "recipe":
        count = len(user_data.get('created_recipes', []))
        achievements = ACHIEVEMENTS['recipe_achievements']
    elif achievement_type == "leftover":
        count = len(user_data.get('leftover_ingredients', []))
        achievements = ACHIEVEMENTS['leftover_achievements']
    elif achievement_type == "quiz":
        quiz_stats = user_data.get('quiz_stats', {})
        correct_answers = quiz_stats.get('correct_answers', 0)
        for achievement in ACHIEVEMENTS['quiz_achievements']:
            if achievement['name'] not in [a['name'] for a in user_data['achievements']]:
                if correct_answers >= achievement['requirement']:
                    award_achievement(user_data, achievement)
        return
    else:
        return

    if achievement_type in ["beverage", "dessert"]:
        count = len(beverage_recipes) if achievement_type == "beverage" else len(dessert_recipes)
    
    for achievement in achievements:
        if achievement['name'] not in [a['name'] for a in user_data['achievements']] and count >= achievement['requirement']:
            award_achievement(user_data, achievement)

def award_achievement(user_data, achievement):
    """Award an achievement"""
    user_data['achievements'].append({
        'name': achievement['name'],
        'earned_on': datetime.now().strftime("%Y-%m-%d %H:%M"),
        'description': achievement['description']
    })
    add_points(achievement['points'], f"Achievement unlocked: {achievement['name']}")
    st.balloons()
    st.success(f"🏆 Achievement Unlocked: {achievement['name']}! +{achievement['points']} points")

def show_sidebar():
    """Display sidebar"""
    st.sidebar.title("🍽️ PlatePals")
    st.sidebar.header("Serve Smart. Waste Less. Know More.")

    user = st.session_state.users[st.session_state.current_user]
    st.sidebar.write(f"Welcome, {st.session_state.current_user}!")
    st.sidebar.metric("🏆 Points", user['points'])
    
    if st.sidebar.button("Logout"):
        st.session_state.current_user = None
        st.rerun()

    return st.sidebar.selectbox("Select Feature", 
        ["Dashboard", "Profile", "Search", "Recipe Suggestions", "Leftover Management", 
         "Menu Personalization", "Event Manager", "Cooking Quiz", "Beverage Generator", "Dessert Generator"])

def show_user_profile(user_data):
    """Display user profile"""
    st.title(f"👤 {st.session_state.current_user}'s Profile")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Points", user_data['points'])
    with col2:
        st.metric("Quiz Attempts", user_data['quiz_stats']['total_attempts'])
    with col3:
        accuracy = 0 if user_data['quiz_stats']['total_attempts'] == 0 else \
                  (user_data['quiz_stats']['correct_answers'] / user_data['quiz_stats']['total_attempts']) * 100
        st.metric("Quiz Accuracy", f"{accuracy:.1f}%")
    
    tabs = st.tabs(["Activity Log", "Recipes", "Events", "Achievements", "Leaderboard"])
    
    with tabs[0]:
        st.subheader("📊 Activity History")
        if user_data['activity_log']:
            df = pd.DataFrame(user_data['activity_log'])
            st.dataframe(df, hide_index=True)
        else:
            st.info("No activity recorded yet")

    with tabs[1]:
        st.subheader("🍳 Created Recipes")
        recipes = user_data['created_recipes']
        if recipes:
            for recipe in recipes:
                with st.expander(f"{recipe.get('date', 'N/A')} - {recipe.get('name', 'Recipe')}"):
                    st.write(f"**Ingredients:** {recipe.get('ingredients', 'N/A')}")
                    st.write(f"**Details:** {recipe.get('details', 'N/A')}")
        else:
            st.info("No recipes created yet")

    with tabs[2]:
        st.subheader("🎉 Events")
        if user_data['completed_events']:
            for event in user_data['completed_events']:
                with st.expander(f"{event['date']} - {event['name']}"):
                    st.write(f"**Theme:** {event['theme']}")
                    st.write(f"**Guests:** {event['guests']}")
        else:
            st.info("No events created yet")

    with tabs[3]:
        st.subheader("🏆 Achievements")
        if user_data.get('achievements'):
            for achievement in user_data['achievements']:
                st.write(f"✅ {achievement['name']} - {achievement['description']}")
        else:
            st.info("No achievements unlocked yet")

    with tabs[4]:
        st.subheader("🏅 Leaderboard")
        leaderboard = st.session_state.user_manager.get_leaderboard()
        leaderboard_df = pd.DataFrame(leaderboard)
        st.dataframe(leaderboard_df, hide_index=True)

# ========== MAIN APP FLOW ==========
check_login_required()
app_mode = show_sidebar()
user_data = st.session_state.users[st.session_state.current_user]

if app_mode == "Profile":
    show_user_profile(user_data)

elif app_mode == "Dashboard":
    st.title("🍽️ PlatePals Dashboard")
    st.caption("📈 Insights into your culinary journey")

    # -----------------------------
    # KPIs
    # -----------------------------
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="🍳 Recipes Created",
            value=len(user_data["created_recipes"]),
            delta="+ New!"
        )

    with col2:
        st.metric(
            label="⭐ Total Points",
            value=user_data["points"]
        )

    with col3:
        avg_rating = 4.87
        st.metric(
            label="🏆 Avg Dish Rating",
            value=avg_rating
        )

    st.markdown("---")

    # -----------------------------
    # MENU PERFORMANCE
    # -----------------------------
    st.subheader("📊 Menu Performance")

    menu_df = pd.DataFrame([
        {"Dish": "Truffle Risotto", "Rating": 4.4, "Category": "Main Course"},
        {"Dish": "Seared Salmon", "Rating": 4.7, "Category": "Seafood"},
        {"Dish": "Molten Chocolate Cake", "Rating": 4.9, "Category": "Dessert"},
        {"Dish": "Paneer ki Sabji", "Rating": 4.2, "Category": "Main Course"},
        {"Dish": "Mixed Berry and Seasonal Fruits Smoothie", "Rating": 4.1, "Category": "Beverage"},
    ])

    fig = px.bar(
        menu_df,
        x="Dish",
        y="Rating",
        color="Category",
        text="Rating",
        title="Top Performing Dishes",
    )

    fig.update_traces(textposition="outside")
    fig.update_layout(
        yaxis=dict(range=[0, 5]),
        plot_bgcolor="rgba(0,0,0,0)",
        title_font_size=20
    )

    st.plotly_chart(fig, use_container_width=True)

    # -----------------------------
    # QUICK INSIGHTS
    # -----------------------------
    st.markdown("### 🔍 Quick Insights")

    col4, col5 = st.columns(2)

    with col4:
        st.success("🥇 Highest Rated Dish: **Molten Chocolate Cake**")

    with col5:
        st.info("🔥 Most Popular Category: **Desserts**")



elif app_mode == "Search":
    st.title("🔍 Recipe Search")
    search_query = st.text_input("Enter recipe name:", placeholder="e.g., Butter Chicken, Tiramisu...")
    
    if st.button("Search Recipe", type="primary"):
        if search_query:
            recipe_data = get_recipe_from_api_ninja(search_query)
            if recipe_data:
                st.success("✨ Recipe found!")
                recipes = recipe_data if isinstance(recipe_data, list) else [recipe_data]
                for recipe in recipes:
                    with st.expander(f"🍳 {recipe.get('title', 'Recipe')}"):
                        st.write(f"**Ingredients:** {recipe.get('ingredients', 'N/A')}")
                        st.write(f"**Instructions:** {recipe.get('instructions', 'N/A')}")
                        if 'servings' in recipe:
                            st.write(f"**Servings:** {recipe['servings']}")
                        if 'prep_time_min' in recipe:
                            st.write(f"**Prep Time:** {recipe['prep_time_min']} mins")
                
                add_points(5, f"Searched recipe: {search_query}")
            else:
                st.info("No recipes found. Try different ingredients.")
        else:
            st.warning("Please enter a recipe name")

elif app_mode == "Recipe Suggestions":
    st.title("Recipe Suggestions")
    
    col1, col2 = st.columns(2)
    with col1:
        user_mood = st.selectbox("How are you feeling?", ["Happy 😊", "Neutral 😐", "Sad 😢", "Excited 😃"])
        hunger_level = st.selectbox("Hunger level?", ["Snack", "Light", "Moderate", "Very Hungry"])
    
    with col2:
        time_of_day = st.selectbox("Time of day?", ["Breakfast", "Lunch", "Snack", "Dinner"])
        calorie_limit = st.number_input("Calorie limit", min_value=100, max_value=5000, value=500)

    st.subheader("🥘 Ingredients Selection")
    all_ingredients = get_all_ingredients()
    search_term = st.text_input("Search ingredients")
    
    if search_term:
        filtered_ingredients = search_ingredients(search_term, all_ingredients)
    else:
        filtered_ingredients = all_ingredients
    
    selected_ingredients = st.multiselect("Selected Ingredients", 
                                         options=sorted(filtered_ingredients),
                                         default=[search_term.title()] if search_term else [])

    mentions = get_user_mentions()

    if st.button("Generate Recipe", type="primary"):
        if selected_ingredients:
            recipe_data = generate_custom_recipe(selected_ingredients)
            if recipe_data:
                st.success("✨ Recipe generated!")
                st.write(f"**Recipe:** {recipe_data.get('title', 'Recipe')}")
                st.write(f"**Ingredients:** {recipe_data.get('ingredients', 'N/A')}")
                st.write(f"**Instructions:** {recipe_data.get('instructions', 'N/A')}")
                
                user = st.session_state.users[st.session_state.current_user]
                user['created_recipes'].append({
                    'name': recipe_data.get('title', 'Recipe'),
                    'ingredients': selected_ingredients,
                    'details': recipe_data.get('instructions', 'N/A'),
                    'date': datetime.now().strftime("%Y-%m-%d"),
                    'type': 'recipe'
                })
                
                add_points(5, "Generated recipe")
                check_achievements(user, "recipe")
                st.session_state.user_manager.update_user_data(st.session_state.current_user, user)
            else:
                st.warning("Could not generate recipe. Try different ingredients.")
        else:
            st.warning("Please select ingredients first")

elif app_mode == "Leftover Management":
    st.title("♻️ Leftover Management")
    
    col1, col2 = st.columns(2)
    with col1:
        ingredient_name = st.text_input("Ingredient Name")
        ingredient_type = st.selectbox("Type", ["Vegetable", "Fruit", "Grain", "Protein", "Dairy", "Other"])
        quantity = st.number_input("Quantity (grams)", min_value=1, value=100)
    
    with col2:
        expiry_date = st.date_input("Best Before Date", min_value=datetime.now().date())
        storage = st.selectbox("Storage", ["Refrigerated", "Frozen", "Room Temp", "Pantry"])
        freshness = st.select_slider("Freshness", options=["Use Immediately", "1-2 Days", "Fresh", "Very Fresh"])
    
    if st.button("Add Ingredient", type="primary"):
        if ingredient_name:
            user = st.session_state.users[st.session_state.current_user]
            user['leftover_ingredients'].append({
                'name': ingredient_name,
                'type': ingredient_type,
                'quantity': quantity,
                'storage': storage,
                'freshness': freshness,
                'expiry_date': expiry_date.strftime("%Y-%m-%d"),
                'date_added': datetime.now().strftime("%Y-%m-%d %H:%M")
            })
            st.success(f"Added {quantity}g of {ingredient_name}")
            add_points(2, f"Added leftover: {ingredient_name}")
            check_achievements(user, "leftover")
            st.session_state.user_manager.update_user_data(st.session_state.current_user, user)
            st.rerun()
    
    st.subheader("Current Leftovers")
    user = st.session_state.users[st.session_state.current_user]
    
    if user['leftover_ingredients']:
        leftovers_df = pd.DataFrame(user['leftover_ingredients'])
        st.dataframe(leftovers_df, hide_index=True)
        
        st.subheader("Generate Recipe from Leftovers")
        cooking_time = st.slider("Max Cooking Time (min)", 10, 120, 30)
        selected = st.multiselect("Select ingredients", options=[i['name'] for i in user['leftover_ingredients']])
        meal_type = st.selectbox("Meal Type", ["Quick Snack", "Breakfast", "Lunch", "Dinner"])
        
        if st.button("Generate Leftover Recipe", type="primary") and selected:
            recipe_data = generate_custom_recipe(selected, meal_type=meal_type)
            if recipe_data:
                st.success("✨ Recipe generated!")
                st.write(f"**Recipe:** {recipe_data.get('title', 'Recipe')}")
                st.write(f"**Ingredients:** {recipe_data.get('ingredients', 'N/A')}")
                st.write(f"**Instructions:** {recipe_data.get('instructions', 'N/A')}")
                
                user['leftovers'].append({
                    'name': f"Leftover Recipe ({datetime.now().strftime('%Y-%m-%d')})",
                    'ingredients': selected,
                    'recipe': recipe_data.get('instructions', 'N/A'),
                    'date': datetime.now().strftime("%Y-%m-%d %H:%M")
                })
                
                add_points(5, "Generated leftover recipe")
                st.session_state.user_manager.update_user_data(st.session_state.current_user, user)
    else:
        st.info("No leftovers added yet")

elif app_mode == "Menu Personalization":
    st.title("🍽️ Complete Meal Planner")
    
    col1, col2 = st.columns(2)
    with col1:
        cuisine = st.selectbox("Cuisine", ["Indian", "Italian", "Chinese", "Mexican", "American", "Thai"])
        occasion = st.selectbox("Occasion", ["Regular", "Special Dinner", "Party", "Date Night", "Business"])
    with col2:
        spice_level = st.select_slider("Spice Level", options=["Mild", "Medium", "Spicy", "Very Spicy"])
        servings = st.number_input("Servings", min_value=1, max_value=20, value=2)
    
    dietary = st.multiselect("Dietary Prefs", ["Vegetarian", "Vegan", "Gluten-Free", "Low-Carb"])
    
    st.subheader("🍽️ Menu Courses")
    app_type = st.selectbox("Appetizer", ["Soup", "Salad", "Finger Food", "Dips"])
    main_protein = st.selectbox("Main Protein", ["Chicken", "Fish", "Lamb", "Vegetarian"])
    dessert = st.selectbox("Dessert", ["Cake", "Pudding", "Ice Cream", "Pie"])
    beverage = st.selectbox("Beverage", ["Mocktail", "Juice", "Tea", "Smoothie"])
    
    if st.button("Generate Complete Menu", type="primary"):
        st.success("✨ Menu Generated!")
        st.write(f"**Cuisine:** {cuisine}")
        st.write(f"**Appetizer:** {app_type}")
        st.write(f"**Main:** {main_protein}")
        st.write(f"**Dessert:** {dessert}")
        st.write(f"**Beverage:** {beverage}")
        
        user = st.session_state.users[st.session_state.current_user]
        user['created_recipes'].append({
            'name': f"{cuisine} {occasion} Menu",
            'type': 'menu',
            'details': f"{app_type} | {main_protein} | {dessert} | {beverage}",
            'date': datetime.now().strftime("%Y-%m-%d")
        })
        
        add_points(15, "Generated complete menu")
        st.session_state.user_manager.update_user_data(st.session_state.current_user, user)

elif app_mode == "Event Manager":
    st.title("🎉 Event Manager")
    
    tab1, tab2, tab3 = st.tabs(["Create Event", "View Events", "Analytics"])
    
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            event_name = st.text_input("Event Name")
            event_date = st.date_input("Event Date")
            guests = st.number_input("Number of Guests", min_value=2, value=20)
        with col2:
            theme = st.selectbox("Theme", ["Mediterranean", "Asian Fusion", "Traditional", "Modern", "Indian"])
            restrictions = st.multiselect("Dietary Restrictions", ["Vegetarian", "Vegan", "Gluten-Free"])
        
        cost_per_person = st.number_input("Cost per Person (₹)", min_value=100.0, value=250.0)
        total_cost = cost_per_person * guests
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Cost", f"₹{total_cost:,.2f}")
        with col2:
            st.metric("Cost/Person", f"₹{cost_per_person:.2f}")
        with col3:
            st.metric("Guests", guests)
        
        if st.button("Save Event"):
            if event_name and event_date:
                event = {
                    "name": event_name,
                    "date": event_date.strftime("%Y-%m-%d"),
                    "guests": guests,
                    "theme": theme,
                    "dietary_restrictions": restrictions,
                    "cost_per_person": cost_per_person,
                    "total_cost": total_cost,
                    "status": "Upcoming"
                }
                st.session_state.events.append(event)
                user = st.session_state.users[st.session_state.current_user]
                user['completed_events'].append(event)
                add_points(10, f"Created event: {event_name}")
                st.session_state.user_manager.update_user_data(st.session_state.current_user, user)
                st.success("Event saved successfully!")
                st.rerun()
            else:
                st.error("Please fill in all fields")
    
    with tab2:
        st.subheader("Upcoming Events")
        if st.session_state.events:
            for idx, event in enumerate(st.session_state.events):
                with st.expander(f"{event['date']} - {event['name']}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Theme:** {event['theme']}")
                        st.write(f"**Guests:** {event['guests']}")
                    with col2:
                        st.write(f"**Total Cost:** ₹{event.get('total_cost', 0):,.2f}")
                        st.write(f"**Status:** {event.get('status', 'N/A')}")
                    
                    if st.button(f"Delete {idx}", key=f"delete_{idx}"):
                        st.session_state.events.pop(idx)
                        st.rerun()
        else:
            st.info("No events planned yet")
    
    with tab3:
        st.subheader("Event Analytics")
        if st.session_state.events:
            events_df = pd.DataFrame(st.session_state.events)
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Events", len(events_df))
            with col2:
                st.metric("Total Revenue", f"₹{events_df['total_cost'].sum():,.2f}")

elif app_mode == "Cooking Quiz":
    st.title("👨‍🍳 Cooking Knowledge Quiz")
    
    user = st.session_state.users[st.session_state.current_user]
    quiz_stats = user['quiz_stats']
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Attempts", quiz_stats['total_attempts'])
    with col2:
        accuracy = 0 if quiz_stats['total_attempts'] == 0 else \
                  (quiz_stats['correct_answers'] / quiz_stats['total_attempts']) * 100
        st.metric("Accuracy", f"{accuracy:.1f}%")
    
    if 'current_question' not in st.session_state:
        st.session_state.current_question = random.choice(COOKING_QUIZ)
    
    question = st.session_state.current_question
    st.subheader(question["question"])
    
    user_answer = st.radio("Select your answer:", question["options"], key="quiz_answer")
    
    if st.button("Submit Answer"):
        quiz_stats['total_attempts'] += 1
        
        if user_answer == question["correct"]:
            st.success("🎉 Correct! +5 points")
            add_points(5, "Correct quiz answer")
            quiz_stats['correct_answers'] += 1
            user['current_streak'] = user.get('current_streak', 0) + 1
        else:
            st.error(f"❌ Wrong! Correct answer: {question['correct']}")
            add_points(-5, "Wrong quiz answer")
            user['current_streak'] = 0
        
        check_achievements(user, "quiz")
        st.session_state.user_manager.update_user_data(st.session_state.current_user, user)
        
        new_questions = [q for q in COOKING_QUIZ if q != question]
        if new_questions:
            st.session_state.current_question = random.choice(new_questions)
        
        if st.button("Next Question"):
            st.rerun()

elif app_mode == "Beverage Generator":
    st.title("🍹 Beverage Generator")
    
    col1, col2 = st.columns(2)
    with col1:
        bev_type = st.selectbox("Beverage Type", ["Mocktail", "Juice", "Smoothie", "Tea", "Coffee", "Milkshake"])
        ingredient_search = st.text_input("Search ingredients")
        
        all_ingredients = get_all_ingredients() + [
            "Mint", "Lemon", "Lime", "Orange", "Mango", "Strawberry", "Honey",
            "Ginger", "Cinnamon", "Ice", "Milk", "Yogurt", "Coconut Milk"
        ]
        
        if ingredient_search:
            filtered = search_ingredients(ingredient_search, all_ingredients)
        else:
            filtered = all_ingredients
        
        selected_bev = st.multiselect("Ingredients", options=sorted(filtered), default=[ingredient_search.title()] if ingredient_search else [])
    
    with col2:
        seasonal = st.selectbox("Season", ["All Seasons", "Summer", "Winter", "Spring", "Fall"])
        preferences = st.multiselect("Flavor", ["Sweet", "Refreshing", "Citrus", "Creamy", "Spicy", "Herbal"])
        dietary = st.multiselect("Dietary", ["Dairy-Free", "Sugar-Free", "Vegan", "Gluten-Free"])
    
    mentions = get_user_mentions()
    
    if st.button("Generate Beverage", type="primary"):
        if selected_bev:
            recipe_data = generate_custom_recipe(selected_bev)
            if recipe_data:
                st.success("✨ Beverage recipe generated!")
                st.write(f"**Recipe:** {recipe_data.get('title', 'Beverage')}")
                st.write(f"**Ingredients:** {recipe_data.get('ingredients', 'N/A')}")
                st.write(f"**Instructions:** {recipe_data.get('instructions', 'N/A')}")
                
                user = st.session_state.users[st.session_state.current_user]
                user['created_recipes'].append({
                    'name': recipe_data.get('title', 'Beverage'),
                    'type': 'beverage',
                    'ingredients': selected_bev,
                    'details': recipe_data.get('instructions', 'N/A'),
                    'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
                    'season': seasonal,
                    'dietary_restrictions': dietary
                })
                
                add_points(5, "Generated beverage")
                check_achievements(user, "beverage")
                st.session_state.user_manager.update_user_data(st.session_state.current_user, user)
            else:
                st.warning("Could not generate beverage recipe")
        else:
            st.warning("Please select ingredients")

elif app_mode == "Dessert Generator":
    st.title("🍰 Dessert Generator")
    
    col1, col2 = st.columns(2)
    with col1:
        dessert_type = st.selectbox("Dessert Type", ["Cake", "Pie", "Cookie", "Pudding", "Ice Cream", "Brownie"])
        ingredient_search = st.text_input("Search ingredients")
        
        all_ingredients = get_all_ingredients() + [
            "Sugar", "Flour", "Butter", "Eggs", "Milk", "Cream", "Chocolate",
            "Vanilla", "Cinnamon", "Nuts", "Berries", "Honey", "Caramel"
        ]
        
        if ingredient_search:
            filtered = search_ingredients(ingredient_search, all_ingredients)
        else:
            filtered = all_ingredients
        
        selected_des = st.multiselect("Ingredients", options=sorted(filtered), default=[ingredient_search.title()] if ingredient_search else [])
    
    with col2:
        cuisine = st.selectbox("Cuisine", ["International", "French", "Italian", "Indian", "American"])
        preferences = st.multiselect("Style", ["Quick & Easy", "Rich", "Light", "Healthy", "Traditional"])
        dietary = st.multiselect("Dietary", ["Gluten-Free", "Sugar-Free", "Vegan", "Dairy-Free"])
    
    mentions = get_user_mentions()
    
    if st.button("Generate Dessert", type="primary"):
        if selected_des:
            recipe_data = generate_custom_recipe(selected_des)
            if recipe_data:
                st.success("✨ Dessert recipe generated!")
                st.write(f"**Recipe:** {recipe_data.get('title', 'Dessert')}")
                st.write(f"**Ingredients:** {recipe_data.get('ingredients', 'N/A')}")
                st.write(f"**Instructions:** {recipe_data.get('instructions', 'N/A')}")
                
                user = st.session_state.users[st.session_state.current_user]
                user['created_recipes'].append({
                    'name': recipe_data.get('title', 'Dessert'),
                    'type': 'dessert',
                    'cuisine': cuisine,
                    'ingredients': selected_des,
                    'details': recipe_data.get('instructions', 'N/A'),
                    'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
                    'dietary_restrictions': dietary
                })
                
                add_points(5, "Generated dessert")
                check_achievements(user, "dessert")
                st.session_state.user_manager.update_user_data(st.session_state.current_user, user)
            else:
                st.warning("Could not generate dessert recipe")
        else:
            st.warning("Please select ingredients")